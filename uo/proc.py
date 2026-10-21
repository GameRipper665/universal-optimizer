"""Show or set a running game's priority and CPU affinity (lasts until the process exits).

    uo proc 12345                          # priority, affinity, threads, memory, the machine's cores
    uo proc 12345 --priority above         # idle | below | normal | above | high
    uo proc 12345 --affinity 0-7           # logical CPUs: "0-7", "0,2,4,6", "0-7,16-23"

When it helps: hybrid Intel CPUs (keep the game off E-cores when the scheduler misplaces it) and dual-CCD
X3D Ryzens (keep it on the V-Cache CCD). Measure with `uo bench` before and after: on most single-CCD,
non-hybrid CPUs neither knob changes anything. "realtime" is not offered: it can starve input and audio
threads and hang the machine. Ask the user before changing a process they are playing.
"""
from __future__ import annotations

import argparse
import sys

from uo.bench import find_process

PRIORITIES = ["idle", "below", "normal", "above", "high"]


def parse_cpus(spec: str, count: int) -> list[int]:
    cpus: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lo, _, hi = part.partition("-")
        a, b = int(lo), int(hi or lo)
        if a > b or b >= count:
            raise ValueError(f"CPU range {part} is outside 0-{count - 1}")
        cpus.update(range(a, b + 1))
    if not cpus:
        raise ValueError("empty CPU list")
    return sorted(cpus)


def _priority_value(name: str):
    import psutil
    if sys.platform == "win32":
        return {"idle": psutil.IDLE_PRIORITY_CLASS, "below": psutil.BELOW_NORMAL_PRIORITY_CLASS,
                "normal": psutil.NORMAL_PRIORITY_CLASS, "above": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                "high": psutil.HIGH_PRIORITY_CLASS}[name]
    return {"idle": 19, "below": 10, "normal": 0, "above": -5, "high": -10}[name]


def _priority_name(value) -> str:
    return next((n for n in PRIORITIES if _priority_value(n) == value), str(value))


def main(args):
    import psutil
    p = find_process(args.target)
    count = psutil.cpu_count() or 1
    try:
        if args.priority:
            p.nice(_priority_value(args.priority))
        if args.affinity:
            p.cpu_affinity(parse_cpus(args.affinity, count))
    except ValueError as e:
        sys.exit(f"uo: {e}")
    except psutil.AccessDenied:
        sys.exit("uo: access denied: the game runs elevated or as another user; use an elevated shell")
    with p.oneshot():
        aff = p.cpu_affinity() if hasattr(p, "cpu_affinity") else None
        print(f"{p.name()} (PID {p.pid})")
        print(f"  priority:  {_priority_name(p.nice())}")
        print(f"  affinity:  {'all ' + str(count) if aff and len(aff) == count else aff}")
        print(f"  threads:   {p.num_threads()}")
        print(f"  memory:    {p.memory_info().rss >> 20} MB working set")
    print(f"  machine:   {psutil.cpu_count(logical=False)} cores / {count} logical CPUs")


def register(sub):
    p = sub.add_parser("proc", help="show or set a running game's priority and CPU affinity",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", help="PID or exe name")
    p.add_argument("--priority", choices=PRIORITIES)
    p.add_argument("--affinity", help='logical CPUs, e.g. "0-7" or "0-7,16-23"')
    p.set_defaults(func=main)
