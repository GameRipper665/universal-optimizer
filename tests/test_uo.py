import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from uo.bench import compare_runs, frame_stats, read_frames
from uo.plan import ENGINE_PLAYBOOK, PLAYBOOK_DIR, is_large_address_aware, levers
from uo.proc import parse_cpus

ROOT = Path(__file__).resolve().parents[1]

PRESENTMON = """Application,ProcessID,SwapChainAddress,PresentRuntime,MsBetweenPresents,MsGPUBusy
game.exe,10,0xA,DXGI,10.0,9.5
game.exe,10,0xB,DXGI,1.0,0.1
game.exe,10,0xA,DXGI,10.0,9.5
game.exe,10,0xA,DXGI,40.0,9.5
game.exe,10,0xA,DXGI,NA,NA
"""

MANGOHUD = """os,cpu,gpu,ram,kernel,driver,cpuscheduler
Linux,Ryzen,RX,32,6.8,mesa,
fps,frametime,cpu_load,gpu_load
60,16.6,40,90
60,16.7,40,90
"""


def test_presentmon_keeps_main_swapchain_and_skips_na():
    frames, gpu = read_frames(PRESENTMON)
    assert frames == [10.0, 10.0, 40.0]
    assert gpu == [9.5, 9.5, 9.5]


def test_mangohud_header_after_preamble():
    frames, gpu = read_frames(MANGOHUD)
    assert frames == [16.6, 16.7] and gpu == []


def test_no_frame_column():
    with pytest.raises(ValueError):
        read_frames("a,b\n1,2\n")


def test_frame_stats():
    s = frame_stats([10.0] * 99 + [50.0], [9.8] * 100)
    assert s["frames"] == 100
    assert s["avg_fps"] == round(1000 * 100 / 1040, 1)
    assert s["low1_fps"] == 20.0
    assert s["stutters"] == 1
    assert s["bound"] == "GPU"
    assert frame_stats([]) == {}


def test_compare_direction_and_noise():
    a = {"frames": {"avg_fps": 60, "p99_ms": 30}, "process": {"rss_peak_mb": 1000}}
    b = {"frames": {"avg_fps": 75, "p99_ms": 20}, "process": {"rss_peak_mb": 1010}}
    rows = {r["metric"]: r["verdict"] for r in compare_runs(a, b)}
    assert rows == {"avg FPS": "better", "p99 frame time ms": "better", "working set peak MB": "~"}


def test_parse_cpus():
    assert parse_cpus("0-3,8", 16) == [0, 1, 2, 3, 8]
    with pytest.raises(ValueError):
        parse_cpus("0-16", 16)


def _pe(tmp_path, characteristics):
    data = bytearray(512)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", data, 0x80 + 22, characteristics)
    f = tmp_path / "x.exe"
    f.write_bytes(bytes(data))
    return f


def test_laa_flag(tmp_path):
    assert is_large_address_aware(_pe(tmp_path, 0x0102 | 0x20)) is True
    assert is_large_address_aware(_pe(tmp_path, 0x0102)) is False
    (tmp_path / "t.txt").write_text("hi")
    assert is_large_address_aware(tmp_path / "t.txt") is None


def test_levers_respect_anti_cheat():
    r = dict(anti_cheat=["EasyAntiCheat"], online_warning=None, graphics_apis=["D3D9"], engine_key="native",
             exes_32bit_not_laa=[], upscalers={}, host={"cpu": "AMD Ryzen 9 7950X3D"}, playbook="x.md")
    out = levers(r)
    assert out[0].startswith("ONLINE / ANTI-CHEAT")
    assert any("X3D" in lv for lv in out)


def test_every_playbook_exists():
    from uo.plan import CODE_GUIDE_DIR, LANG_GUIDE, STRONG_MARKERS, WEAK_MARKERS
    for book in set(ENGINE_PLAYBOOK.values()) | {"native.md", "emulators.md"}:
        assert (ROOT / PLAYBOOK_DIR / book).is_file(), book
    guides = {g for _, _, g in STRONG_MARKERS + WEAK_MARKERS} | {g for _, g in LANG_GUIDE.values()} | {"languages.md"}
    for guide in guides:
        assert (ROOT / CODE_GUIDE_DIR / guide).is_file(), guide
    for doc in ("mobile.md", "cloud.md", "consoles.md"):
        assert (ROOT / "skills/optimize-any-game/references/platforms" / doc).is_file(), doc


def test_skill_copies_match():
    src = ROOT / "skills"
    for copy in (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills"):
        for f in src.rglob("*"):
            if f.is_file():
                assert (copy / f.relative_to(src)).read_bytes() == f.read_bytes(), f"{copy}: {f.relative_to(src)} differs"


def test_cli_help():
    for g in ([], ["plan"], ["bench"], ["compare"], ["proc"]):
        r = subprocess.run([sys.executable, "-m", "uo", *g, "--help"], cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


def test_bench_from_csv(tmp_path):
    cap = tmp_path / "cap.csv"
    cap.write_text(PRESENTMON)
    out = tmp_path / "run.json"
    r = subprocess.run([sys.executable, "-m", "uo", "bench", "--from-csv", str(cap), "-o", str(out)],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(out.read_text())["frames"]["frames"] == 3


NOTE_KEYS = {"title", "game", "engine", "kind", "hardware", "status", "date"}


def test_knowledge_notes_frontmatter():
    for note in (ROOT / "knowledge" / "notes").glob("*.md"):
        text = note.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{note.name}: no frontmatter"
        head = text.split("---\n", 2)[1]
        meta = dict(line.split(":", 1) for line in head.splitlines() if ":" in line)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        assert NOTE_KEYS <= meta.keys(), f"{note.name}: missing {NOTE_KEYS - meta.keys()}"
        assert meta["kind"] in ("shipped", "project", "platform"), note.name
        assert meta["status"] in ("verified", "partial", "dead-end"), note.name


def test_plan_projects(tmp_path):
    from uo.plan import project_kind
    rbx = tmp_path / "scripts"
    rbx.mkdir()
    (rbx / "a.luau").write_text("--!strict\n")
    (rbx / "package.json").write_text("{}")
    assert project_kind(rbx)[1] == "roblox-luau.md"
    unity = tmp_path / "unity"
    (unity / "ProjectSettings").mkdir(parents=True)
    (unity / "ProjectSettings" / "ProjectVersion.txt").write_text("m_EditorVersion: 6000.0.1f1\n")
    (unity / "Game.exe").write_bytes(b"MZ")
    assert project_kind(unity)[0].startswith("Unity")
    shipped = tmp_path / "shipped"
    (shipped / "renpy").mkdir(parents=True)
    (shipped / "Game.py").write_text("")
    (shipped / "Game.exe").write_bytes(b"MZ")
    assert project_kind(shipped) is None
    built = tmp_path / "cpp"
    (built / "build" / "Release").mkdir(parents=True)
    (built / "build" / "Release" / "game.exe").write_bytes(b"MZ")
    (built / "CMakeLists.txt").write_text("")
    (built / "main.cpp").write_text("")
    assert project_kind(built)[1] == "languages.md"


def test_levers_emulator_and_roblox():
    base = dict(anti_cheat=[], online_warning=None, graphics_apis=["D3D9"], engine_key="native",
                exes_32bit_not_laa=["x.exe"], upscalers={}, host={}, playbook="p.md")
    emu = levers(dict(base, emulator=True, engine="Emulator: PCSX2 (PS2)"))
    assert len(emu) == 2 and "DXVK" not in " ".join(emu)
    rbx = levers(dict(base, anti_cheat=["Hyperion (Roblox)"], special_lever="Roblox player side: ..."))
    assert rbx[0].startswith("ONLINE") and rbx[1].startswith("Roblox") and "DXVK" not in " ".join(rbx)


def test_manifests_agree():
    for f in ("plugin.json", "gemini-extension.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        assert json.loads((ROOT / f).read_text(encoding="utf-8"))["name"] == "universal-optimizer", f
