"""Measure a running game (frame times, CPU, busiest thread, memory) and compare runs.

    uo bench 12345 --seconds 60 --label before -o before.json    # by PID
    uo bench Terraria.exe --seconds 60 -o after.json              # by exe name (the biggest match if several)
    uo bench --from-csv capture.csv -o run.json                   # a PresentMon / CapFrameX / MangoHud capture
    uo compare before.json after.json [--json]

Frame times come from PresentMon 2.x (https://github.com/GameTechDev/PresentMon/releases): put the console exe
(any PresentMon*.exe) in ~/.universal-optimizer/tools or on PATH, or set PRESENTMON. It uses ETW, so run from an elevated shell (or a user in
"Performance Log Users"). Without it, bench still records CPU and memory and says so. The raw CSV is kept next
to the JSON.

What the numbers mean:
  low1_fps / low01_fps  average FPS of the slowest 1% / 0.1% of frames (what stutter feels like)
  stutters_per_min      frames over twice the median frame time (and 5 ms over it)
  gpu_busy_ratio        median GPU busy time / median frame time: ~1 = GPU-bound, low = CPU/engine-bound
  busiest_thread_pct    CPU of the single busiest thread: ~100 = one thread (usually the main or render
                        thread) is the wall, and more cores or a faster GPU won't help

Measure the same scene, same settings, same length, at least twice per side: single runs differ by a few
percent on their own, and compare marks changes under 3% as noise.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

FRAME_COLUMNS = ("MsBetweenPresents", "frametime")
GPU_COLUMNS = ("MsGPUBusy", "msGPUActive")
NOISE_PCT = 3.0
TOOLS_DIR = Path.home() / ".universal-optimizer" / "tools"


def die(msg: str, code: int = 1):
    print(f"uo: {msg}", file=sys.stderr)
    sys.exit(code)


def _num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def read_frames(text: str) -> tuple[list[float], list[float]]:
    """Frame times and GPU busy times (ms) from a PresentMon (1.x/2.x), CapFrameX or MangoHud CSV."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if any(c in [h.strip() for h in line.split(",")] for c in FRAME_COLUMNS)), None)
    if start is None:
        raise ValueError("no frame-time column (MsBetweenPresents or frametime) in the CSV")
    rows = list(csv.DictReader(lines[start:], skipinitialspace=True))
    if not rows:
        return [], []
    # overlays and launchers can present from the same process: keep the swap chain with the most frames
    if "SwapChainAddress" in rows[0]:
        top = Counter(r["SwapChainAddress"] for r in rows).most_common(1)[0][0]
        rows = [r for r in rows if r["SwapChainAddress"] == top]
    col = next(c for c in FRAME_COLUMNS if c in rows[0])
    gcol = next((c for c in GPU_COLUMNS if c in rows[0]), None)
    frames = [f for f in (_num(r.get(col)) for r in rows) if f]
    gpu = [g for g in (_num(r.get(gcol)) for r in rows) if g] if gcol else []
    return frames, gpu


def frame_stats(frames: list[float], gpu: list[float] | None = None) -> dict:
    if not frames:
        return {}
    s = sorted(frames)
    n, total = len(s), sum(s)

    def low(frac: float) -> float:
        worst = s[-max(1, int(n * frac)):]
        return round(1000 * len(worst) / sum(worst), 1)

    med = statistics.median(s)
    # ponytail: fixed 2x-median stutter rule; a perceptual model (e.g. CapFrameX's) if this misleads
    stutters = sum(1 for f in frames if f > 2 * med and f - med > 5)
    out = dict(frames=n, seconds=round(total / 1000, 1), avg_fps=round(1000 * n / total, 1),
               low1_fps=low(0.01), low01_fps=low(0.001), median_ms=round(med, 2),
               p99_ms=round(s[min(n - 1, int(n * 0.99))], 2), max_ms=round(s[-1], 2),
               stutters=stutters, stutters_per_min=round(stutters * 60000 / total, 1))
    if gpu:
        ratio = statistics.median(gpu) / med
        out["gpu_busy_ratio"] = round(ratio, 2)
        out["bound"] = "GPU" if ratio >= 0.9 else "CPU/engine" if ratio <= 0.75 else "mixed"
    return out


def find_process(target: str):
    import psutil
    if target.isdigit():
        try:
            return psutil.Process(int(target))
        except psutil.NoSuchProcess:
            die(f"no process with PID {target}")
    want = target.lower().removesuffix(".exe")
    found = [p for p in psutil.process_iter(["name", "memory_info"])
             if (p.info["name"] or "").lower().removesuffix(".exe") == want]
    if not found:
        die(f"no running process named {target}")
    found.sort(key=lambda p: p.info["memory_info"].rss if p.info["memory_info"] else 0, reverse=True)
    if len(found) > 1:
        print(f"uo: {len(found)} processes named {target}; measuring PID {found[0].pid} (most memory)", file=sys.stderr)
    return found[0]


def _thread_times(p) -> dict[int, float] | None:
    import psutil
    try:
        return {t.id: t.user_time + t.system_time for t in p.threads()}
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return None


def sample_process(p, seconds: float, interval: float = 0.5) -> dict:
    import psutil
    cores = psutil.cpu_count() or 1
    t0 = _thread_times(p)
    p.cpu_percent(None)
    w0 = time.perf_counter()
    cpu, rss, private = [], [], []
    while time.perf_counter() - w0 < seconds:
        time.sleep(interval)
        try:
            cpu.append(p.cpu_percent(None))
            mi = p.memory_info()
        except psutil.NoSuchProcess:
            break
        rss.append(mi.rss)
        private.append(getattr(mi, "private", 0))
    wall = time.perf_counter() - w0
    t1 = _thread_times(p)
    mb = 1 << 20
    out = dict(pid=p.pid, name=p.name(), sampled_s=round(wall, 1), cores=cores,
               cpu_avg_cores=round(statistics.mean(cpu) / 100, 2) if cpu else None,
               cpu_avg_pct_of_machine=round(statistics.mean(cpu) / cores, 1) if cpu else None,
               rss_avg_mb=round(statistics.mean(rss) / mb) if rss else None,
               rss_peak_mb=round(max(rss) / mb) if rss else None)
    if any(private):
        out["private_peak_mb"] = round(max(private) / mb)
    if t0 is not None and t1 is not None:
        out["threads"] = len(t1)
        out["busiest_thread_pct"] = round(max((t1[i] - t0.get(i, 0.0) for i in t1), default=0.0) / wall * 100, 1)
    return out


def presentmon_exe(given: str | None) -> str | None:
    for c in (given, os.environ.get("PRESENTMON"), shutil.which("PresentMon")):
        if c and Path(c).is_file():
            return c
    for d in [str(TOOLS_DIR), *os.environ.get("PATH", "").split(os.pathsep)]:
        hits = sorted(Path(d).glob("PresentMon*.exe")) if d and Path(d).is_dir() else []
        if hits:
            return str(hits[-1])
    return None


def bench(args):
    out = Path(args.out)
    report = dict(label=args.label or out.stem, when=time.strftime("%Y-%m-%d %H:%M:%S"), notes=[])
    if args.from_csv:
        frames, gpu = read_frames(Path(args.from_csv).read_text(encoding="utf-8", errors="replace"))
        report.update(source=str(args.from_csv), frames=frame_stats(frames, gpu))
    else:
        if not args.target:
            die("give a PID or exe name, or --from-csv")
        p = find_process(args.target)
        pm, pm_proc, csv_path = presentmon_exe(args.presentmon), None, out.with_suffix(".csv")
        if pm:
            csv_path.unlink(missing_ok=True)
            pm_proc = subprocess.Popen(
                [pm, "--process_id", str(p.pid), "--output_file", str(csv_path), "--timed", str(int(args.seconds)),
                 "--terminate_after_timed", "--no_console_stats", "--stop_existing_session", "--session_name", "uo_bench"],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        else:
            report["notes"].append("no PresentMon found: CPU and memory only (see `uo bench --help`)")
        print(f"uo: measuring {p.name()} (PID {p.pid}) for {args.seconds:g}s; keep the game in the same scene",
              file=sys.stderr)
        report["process"] = sample_process(p, args.seconds)
        if pm_proc:
            try:
                _, err = pm_proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                pm_proc.kill()
                _, err = pm_proc.communicate()
            if csv_path.is_file():
                frames, gpu = read_frames(csv_path.read_text(encoding="utf-8", errors="replace"))
                report.update(frames=frame_stats(frames, gpu), frames_csv=str(csv_path))
            else:
                report["notes"].append("PresentMon wrote no CSV (needs an elevated shell): "
                                       + (err or "").strip()[-300:])
    if not report.get("frames"):
        report["notes"].append("no frames captured")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(format_run(report))
    print(f"-> {out}")


def format_run(r: dict) -> str:
    lines = [f"{r['label']}  ({r['when']})"]
    f, p = r.get("frames") or {}, r.get("process") or {}
    if f:
        lines.append(f"  frames:  {f['avg_fps']} avg FPS, 1% low {f['low1_fps']}, 0.1% low {f['low01_fps']}, "
                     f"p99 {f['p99_ms']} ms, {f['stutters_per_min']} stutters/min over {f['seconds']}s")
        if "bound" in f:
            lines.append(f"  bound:   {f['bound']} (GPU busy {f['gpu_busy_ratio']:.0%} of the frame)")
    if p:
        lines.append(f"  cpu:     {p['cpu_avg_cores']} cores avg ({p['cpu_avg_pct_of_machine']}% of {p['cores']})"
                     + (f", busiest thread {p['busiest_thread_pct']}% of {p['threads']}" if "busiest_thread_pct" in p else ""))
        lines.append(f"  memory:  {p['rss_avg_mb']} MB working set avg, {p['rss_peak_mb']} MB peak"
                     + (f", {p['private_peak_mb']} MB private peak" if "private_peak_mb" in p else ""))
        if p.get("busiest_thread_pct", 0) >= 90:
            lines.append("  hint:    one thread is saturated: the engine's main/render thread is the wall")
    for n in r.get("notes", []):
        lines.append(f"  note:    {n}")
    return "\n".join(lines)


METRICS = [  # (path, label, +1 = higher is better)
    ("frames.avg_fps", "avg FPS", +1),
    ("frames.low1_fps", "1% low FPS", +1),
    ("frames.low01_fps", "0.1% low FPS", +1),
    ("frames.p99_ms", "p99 frame time ms", -1),
    ("frames.stutters_per_min", "stutters/min", -1),
    ("frames.gpu_busy_ratio", "GPU busy ratio", 0),
    ("process.cpu_avg_cores", "CPU cores used", -1),
    ("process.busiest_thread_pct", "busiest thread %", -1),
    ("process.rss_peak_mb", "working set peak MB", -1),
    ("process.private_peak_mb", "private bytes peak MB", -1),
]


def _get(d: dict, path: str):
    for k in path.split("."):
        d = d.get(k) if isinstance(d, dict) else None
    return d


def compare_runs(a: dict, b: dict) -> list[dict]:
    rows = []
    for path, label, sign in METRICS:
        x, y = _get(a, path), _get(b, path)
        if x is None or y is None:
            continue
        pct = (y - x) / x * 100 if x else 0.0
        verdict = "~" if abs(pct) < NOISE_PCT or not sign else ("better" if pct * sign > 0 else "worse")
        rows.append(dict(metric=label, before=x, after=y, change_pct=round(pct, 1), verdict=verdict))
    return rows


def compare(args):
    a, b = (json.loads(Path(f).read_text(encoding="utf-8")) for f in (args.before, args.after))
    rows = compare_runs(a, b)
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    print(f"{a.get('label')} -> {b.get('label')}")
    for r in rows:
        print(f"  {r['metric']:<24} {r['before']:>9} -> {r['after']:<9} {r['change_pct']:+6.1f}%  {r['verdict']}")
    if not rows:
        print("  nothing comparable: both runs need frames or process data")


def register(sub):
    p = sub.add_parser("bench", help="measure a running game: frame times, CPU, busiest thread, memory",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", nargs="?", help="PID or exe name of the running game")
    p.add_argument("-o", "--out", required=True, help="JSON to write (the PresentMon CSV goes next to it)")
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--label", help="name shown by compare (default: the file name)")
    p.add_argument("--presentmon", help="path to the PresentMon console exe")
    p.add_argument("--from-csv", help="read frames from an existing capture instead of measuring")
    p.set_defaults(func=bench)

    c = sub.add_parser("compare", help="before/after table of two `uo bench` runs")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=compare)
