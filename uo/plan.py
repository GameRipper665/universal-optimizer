"""Read-only recon for optimizing one game: what it runs on, and which levers apply.

    uo plan terraria                  # fuzzy name (Steam/Epic/Xbox) or an install folder
    uo plan "C:\\Games\\Foo" --json
    uo plan roblox                    # the installed Roblox client (player side: settings only)
    uo plan ./my-game                 # a source project you develop: kind, languages, the code guide

Builds on `um scan` (universal-modder) for the engine, executables and anti-cheat, then adds what matters for
performance:
  - graphics APIs the exes and engine DLLs reference (D3D8/9/10/11/12, Vulkan, OpenGL, DirectDraw)
  - 32-bit exes and whether they are Large Address Aware (the 2 GB vs 4 GB cap)
  - upscaler DLLs shipped with the game (DLSS, XeSS, FSR): the hooks OptiScaler and DLL swaps use
  - wrappers and injectors already installed (local d3d*/dxgi DLLs, DXVK, dgVoodoo, ReShade, Special K, ASI)
  - the host CPU and RAM
It ends with the levers worth trying, in order, and the engine playbook to read.

A folder holding a game's source (Roblox/Rojo, Unity, Unreal, Godot, GameMaker, LÖVE, Rust, .NET, JVM, JS/TS,
C/C++, Python) is reported as a project instead: kind, languages by file count, and the guide in
skills/optimize-game-code. Emulators (RPCS3, Dolphin, PCSX2, Cemu, Xenia, DuckStation, PPSSPP...) get the
emulator playbook, and the Roblox client is treated as online with anti-cheat.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
from pathlib import Path

PLAYBOOK_DIR = "skills/optimize-any-game/references/engines/"
PLAYBOOKS = {
    "unity.md": ["unity-mono", "unity-il2cpp"],
    "unreal.md": ["unreal"],
    "godot.md": ["godot"],
    "java.md": ["java"],
    "dotnet-xna.md": ["xna-fna", "dotnet", "bannerlord"],
    "source.md": ["source", "source2"],
    "bethesda.md": ["creation"],
    "big-frameworks.md": ["re-engine", "mt-framework", "fromsoft", "rage", "hedgehog", "blackrock", "redengine",
                          "frostbite", "cryengine"],
    "scripted.md": ["gamemaker", "rpgmaker-mvmz", "rpgmaker-rgss", "renpy", "electron", "love2d", "haxe", "defold",
                    "clausewitz"],
}
ENGINE_PLAYBOOK = {key: book for book, keys in PLAYBOOKS.items() for key in keys}

CODE_GUIDE_DIR = "skills/optimize-game-code/references/"
# (root patterns, kind, guide). Strong markers win even next to an exe; weak ones only count in a folder with no
# exe at its root, because shipped games carry them too (Ren'Py ships *.py, engines ship Makefiles).
STRONG_MARKERS = [
    (("default.project.json", "*.project.json", "*.rbxl", "*.rbxlx"), "Roblox experience (Luau)", "roblox-luau.md"),
    (("ProjectSettings/ProjectVersion.txt",), "Unity project (C#)", "engine-projects.md"),
    (("*.uproject",), "Unreal project (C++ / Blueprints)", "engine-projects.md"),
    (("project.godot",), "Godot project (GDScript / C#)", "engine-projects.md"),
    (("*.yyp",), "GameMaker project (GML)", "engine-projects.md"),
]
WEAK_MARKERS = [
    (("conf.lua", "main.lua"), "LÖVE / Lua project", "engine-projects.md"),
    (("Cargo.toml",), "Rust project (Bevy?)", "engine-projects.md"),
    (("*.csproj", "*.fsproj", "*.sln"), ".NET project (MonoGame / FNA?)", "engine-projects.md"),
    (("build.gradle", "build.gradle.kts", "pom.xml"), "JVM project (libGDX?)", "engine-projects.md"),
    (("package.json",), "JavaScript / TypeScript project", "engine-projects.md"),
    (("CMakeLists.txt", "*.vcxproj", "meson.build", "premake5.lua", "Makefile"), "C / C++ project", "languages.md"),
    (("pyproject.toml", "requirements.txt", "*.py"), "Python project", "languages.md"),
]
SOURCE_EXT = {".luau": "Luau", ".lua": "Lua", ".cs": "C#", ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".c": "C",
              ".h": "C/C++ header", ".hpp": "C/C++ header", ".gd": "GDScript", ".gml": "GML", ".rs": "Rust",
              ".java": "Java", ".kt": "Kotlin", ".js": "JavaScript", ".ts": "TypeScript", ".py": "Python",
              ".go": "Go", ".zig": "Zig", ".hx": "Haxe", ".fs": "F#"}
SKIP_DIRS = {".git", "node_modules", "library", "temp", "obj", "bin", "intermediate", "saved", "deriveddatacache",
             "target", ".venv", "venv", "build", "dist", ".godot", "packages", "__pycache__"}
# a dominant language that names the platform better than any build file next to it
LANG_GUIDE = {"Luau": ("Roblox experience (Luau)", "roblox-luau.md"),
              "GML": ("GameMaker scripts (GML)", "engine-projects.md"),
              "GDScript": ("Godot scripts (GDScript)", "engine-projects.md")}
ROBLOX_LEVER = ("Roblox player side: Graphics Quality and Maximum Frame Rate in Roblox's settings; ClientAppSettings.json "
                "Fast Flags only from Roblox's official allowlist (others are ignored, and old 'FPS flag packs' are mostly "
                "placebo). To optimize an experience you develop, open it in Studio and use the optimize-game-code skill.")
# exe stem prefix -> what it is; `um scan` knows neither
SPECIAL = {
    "robloxplayerbeta": dict(label="Roblox client", anti_cheat="Hyperion (Roblox)", lever=ROBLOX_LEVER,
                             guide=CODE_GUIDE_DIR + "roblox-luau.md"),
    "rpcs3": dict(label="Emulator: RPCS3 (PS3)"),
    "dolphin": dict(label="Emulator: Dolphin (GameCube / Wii)"),
    "pcsx2": dict(label="Emulator: PCSX2 (PS2)"),
    "cemu": dict(label="Emulator: Cemu (Wii U)"),
    "xenia": dict(label="Emulator: Xenia (Xbox 360)"),
    "ryujinx": dict(label="Emulator: Ryujinx family (Switch)"),
    "citron": dict(label="Emulator: Citron (Switch)"),
    "eden": dict(label="Emulator: Eden (Switch)"),
    "duckstation": dict(label="Emulator: DuckStation (PS1)"),
    "ppsspp": dict(label="Emulator: PPSSPP (PSP)"),
    "retroarch": dict(label="Emulator: RetroArch"),
    "shadps4": dict(label="Emulator: shadPS4 (PS4)"),
    "vita3k": dict(label="Emulator: Vita3K (PS Vita)"),
}
ROBLOX_ROOTS = ("Roblox", "Bloxstrap", "Fishstrap")

APIS = {
    "DirectDraw": rb"(?i)\bddraw\.dll",
    "D3D8": rb"(?i)\bd3d8\.dll",
    "D3D9": rb"(?i)\bd3d9\.dll",
    "D3D10": rb"(?i)\bd3d10(_1)?\.dll",
    "D3D11": rb"(?i)\bd3d11\.dll",
    "D3D12": rb"(?i)\bd3d12\.dll",
    "Vulkan": rb"(?i)\bvulkan-1\.dll",
    "OpenGL": rb"(?i)\bopengl32\.dll",
}
RENDER_DLL = re.compile(r"render|engine|graphics|gfx")
ENGINE_DLLS = ("unityplayer.dll", "gameassembly.dll", "engine.dll", "shaderapidx9.dll", "materialsystem.dll")
UPSCALERS = {
    "nvngx_dlss.dll": "DLSS Super Resolution",
    "nvngx_dlssg.dll": "DLSS Frame Generation",
    "nvngx_dlssd.dll": "DLSS Ray Reconstruction",
    "libxess.dll": "XeSS",
    "amd_fidelityfx_dx12.dll": "FSR 3.1+ (DX12)",
    "amd_fidelityfx_vk.dll": "FSR 3.1+ (Vulkan)",
    "ffx_fsr2_api_x64.dll": "FSR 2",
}
LAYERS = {
    "dxvk.conf": "DXVK config",
    "dgvoodoo.conf": "dgVoodoo2",
    "reshade.ini": "ReShade",
    "optiscaler.ini": "OptiScaler",
    "specialk64.dll": "Special K",
    "specialk32.dll": "Special K",
}
WRAPPABLE = {"d3d8.dll", "d3d9.dll", "d3d10.dll", "d3d11.dll", "d3d12.dll", "dxgi.dll", "ddraw.dll", "opengl32.dll",
             "dinput8.dll", "winmm.dll", "version.dll", "winhttp.dll"}


def is_large_address_aware(path: Path) -> bool | None:
    """IMAGE_FILE_LARGE_ADDRESS_AWARE (0x20) in the COFF header; None if not a PE file."""
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
    except OSError:
        return None
    if head[:2] != b"MZ" or len(head) < 0x40:
        return None
    off = struct.unpack_from("<I", head, 0x3C)[0]
    if off + 24 > len(head) or head[off:off + 4] != b"PE\0\0":
        return None
    return bool(struct.unpack_from("<H", head, off + 22)[0] & 0x20)


def host_hardware() -> dict:
    import psutil
    name = None
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                name = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    else:
        try:
            m = re.search(r"model name\s*:\s*(.+)", Path("/proc/cpuinfo").read_text())
            name = m.group(1).strip() if m else None
        except OSError:
            pass
    return dict(cpu=name, logical_cores=psutil.cpu_count(), physical_cores=psutil.cpu_count(logical=False),
                ram_gb=round(psutil.virtual_memory().total / (1 << 30), 1))


def levers(r: dict) -> list[str]:
    if r.get("emulator"):
        return [f"{r['engine']}: the levers are the emulator's own settings (renderer, shader compilation, resolution "
                "scale, CPU/recompiler options), its per-game configs and its built-in patches. No wrappers or "
                "game-file edits.",
                f"Playbook: {r['playbook']}."]
    out = []
    locked = bool(r["anti_cheat"] or r["online_warning"])
    if locked:
        out.append("ONLINE / ANTI-CHEAT: in-game settings, launch options, driver and OS knobs only. No wrappers, "
                   "no injected DLLs, no memory patches, not even for single-player modes that share the client.")
    if r.get("special_lever"):
        out.append(r["special_lever"])
    apis = set(r["graphics_apis"])
    if not locked and apis and apis <= {"DirectDraw", "D3D8"}:
        out.append("DirectDraw/D3D8 only: dgVoodoo2 (or d3d8to9 + DXVK) moves it onto a modern API "
                   "(universal-layers.md, render API translation).")
    elif not locked and "D3D9" in apis and not apis & {"D3D11", "D3D12", "Vulkan"}:
        out.append("D3D9 only: DXVK often cuts CPU-side draw overhead on DX9 games. Measure: it can also lose FPS "
                   "(universal-layers.md, DXVK).")
    for exe in [] if locked else r["exes_32bit_not_laa"]:
        out.append(f"{exe} is 32-bit without Large Address Aware: if it crashes or stutters as memory nears 2 GB, "
                   "a LAA patch raises the cap to 4 GB on 64-bit Windows (universal-layers.md, memory).")
    if r["upscalers"]:
        names = ", ".join(sorted(set(r["upscalers"].values())))
        out.append(f"Ships {names}: " + ("use the in-game upscaler and the driver's official override (NVIDIA app) only."
                   if locked else "newer upscaler DLLs or OptiScaler (swap DLSS/FSR/XeSS inputs) are usually the "
                   "biggest GPU-side win (universal-layers.md, upscalers)."))
    cpu = (r["host"].get("cpu") or "")
    if "X3D" in cpu.upper():
        out.append(f"{cpu}: on dual-CCD X3D parts, keep the game on the V-Cache CCD (AMD's driver + Game Bar, "
                   "or `uo proc --affinity`); measure both CCDs.")
    capper = "in-game or the driver's" if locked else "in-game, RTSS or Special K"
    out.append(f"Frame pacing: a frame cap a little under the 1% lows ({capper}) often removes "
               "stutter that raw FPS hides.")
    out.append(f"Read next: {r['playbook']}")
    return out


def _matches(root: Path, markers: list) -> list[tuple[str, str]]:
    return [(kind, guide) for pats, kind, guide in markers if any(any(root.glob(p)) for p in pats)]


def survey(root: Path, limit: int = 50_000) -> tuple[dict[str, int], bool]:
    """Source files per language, and whether an exe sits outside build-output folders (a shipped game)."""
    counts: dict[str, int] = {}
    seen, shipped = 0, False
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            shipped = shipped or ext == ".exe"
            if ext in SOURCE_EXT:
                counts[SOURCE_EXT[ext]] = counts.get(SOURCE_EXT[ext], 0) + 1
        seen += len(filenames)
        if seen > limit:
            break
    return dict(sorted(counts.items(), key=lambda kv: -kv[1])), shipped


def project_kind(root: Path) -> tuple[str, str, dict[str, int]] | None:
    """(kind, guide, languages) if the folder is a game's source rather than an installed game."""
    if not root.is_dir():
        return None
    strong = _matches(root, STRONG_MARKERS)
    langs, shipped = survey(root)
    if strong:
        return (*strong[0], langs)
    if shipped:
        return None
    top = next(iter(langs), None)
    if top in LANG_GUIDE:
        return (*LANG_GUIDE[top], langs)
    weak = _matches(root, WEAK_MARKERS)
    if weak:
        return (*weak[0], langs)
    return (f"{top} source", "languages.md", langs) if top else None


def project_plan(root: Path, kind: str, guide: str, langs: dict[str, int]) -> dict:
    guides = CODE_GUIDE_DIR + guide + ("" if guide == "languages.md" else f" + {CODE_GUIDE_DIR}languages.md")
    return dict(project=True, name=root.name, path=str(root), kind=kind, languages=langs,
                guide=CODE_GUIDE_DIR + guide,
                levers=["Profile before touching code: the profilers for this engine and language are in the guide.",
                        "Fix the hottest path first: algorithm, per-frame work, allocations, draw calls, network.",
                        "One change at a time, re-measure the same scene, keep or revert (optimize-game-code skill).",
                        f"Guide: {guides}"])


def roblox_client() -> Path | None:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    found = [p for r in ROBLOX_ROOTS for p in (Path(local) / r / "Versions").glob("*/RobloxPlayerBeta.exe")]
    return max(found, key=lambda p: p.stat().st_mtime).parent if found else None


def plan(query: str) -> dict:
    project = project_kind(Path(query))
    if project:
        return project_plan(Path(query).resolve(), *project)
    if query.strip().lower() == "roblox":
        client = roblox_client()
        if not client:
            raise SystemExit(r"uo: no Roblox client under %LOCALAPPDATA%\{Roblox,Bloxstrap,Fishstrap}\Versions")
        query = str(client)
    try:
        from um.scan import Index, grep_file, scan
    except ImportError:
        raise SystemExit("uo: plan needs universal-modder: pip install git+https://github.com/rehan-remade/universal-modder")
    s = scan(query)
    root = Path(s["path"])
    ix = Index(root)
    key = s["engine"]["key"]
    exes = s.get("executables") or {}
    native = [e for e, info in exes.items() if not info.get("managed")][:4]
    exe_dirs = {e.rsplit("/", 1)[0] if "/" in e else "" for e in exes}
    engine_dlls = [f for f in ix.files if f.endswith(".dll") and (f.rsplit("/", 1)[0] if "/" in f else "") in exe_dirs
                   and (f.rsplit("/", 1)[-1] in ENGINE_DLLS or RENDER_DLL.search(f.rsplit("/", 1)[-1]))]
    sniff = native + engine_dlls[:6]
    apis: set[str] = set()
    for rel in sniff:
        found = grep_file(ix.path(rel), list(APIS.values()), limit_mb=200, budget_s=4.0)
        apis |= {name for name, pat in APIS.items() if pat in found}
    no_laa = [e for e in native if exes[e].get("arch") == "x86" and is_large_address_aware(ix.path(e)) is False]
    base = {f: f.rsplit("/", 1)[-1] for f in ix.files}
    upscalers = {f: UPSCALERS[b] for f, b in base.items() if b in UPSCALERS}
    layers = {f: LAYERS[b] for f, b in base.items() if b in LAYERS}
    for f, b in base.items():
        d = f.rsplit("/", 1)[0] if "/" in f else ""
        if b in WRAPPABLE and d in exe_dirs:
            layers.setdefault(f, "local system-DLL name next to an exe: a wrapper or loader (DXVK, ReShade, Special K, ASI...)")
        elif b.endswith(".asi"):
            layers.setdefault(f, "ASI plugin")
    r = dict(name=s["name"], path=s["path"], engine=s["engine"]["label"], engine_key=key,
             executables=exes, graphics_apis=sorted(apis), exes_32bit_not_laa=no_laa,
             upscalers=upscalers, layers_installed=layers, anti_cheat=s["anti_cheat"],
             online_warning=next((w for w in s["warnings"] if "online competitive" in w), None),
             warnings=s["warnings"], host=dict(s.get("host") or {}, **host_hardware()),
             playbook=PLAYBOOK_DIR + ENGINE_PLAYBOOK.get(key, "native.md"))
    special = next((v for e in exes for k, v in SPECIAL.items() if Path(e).stem.startswith(k)), None)
    if special and special.get("anti_cheat"):
        r.update(name=special["label"], engine=special["label"], anti_cheat=r["anti_cheat"] + [special["anti_cheat"]],
                 playbook=special["guide"], special_lever=special["lever"])
    elif special:
        r.update(engine=special["label"], emulator=True, playbook=PLAYBOOK_DIR + "emulators.md")
    r["levers"] = levers(r)
    return r


def format_project(r: dict) -> str:
    langs = ", ".join(f"{k} {v}" for k, v in list(r["languages"].items())[:6]) or "no source files found"
    lines = [f"{r['name']}  (source project)", f"  path:      {r['path']}", f"  kind:      {r['kind']}",
             f"  languages: {langs}", "  levers, in order:"]
    lines += [f"    {i}. {lv}" for i, lv in enumerate(r["levers"], 1)]
    return "\n".join(lines)


def format_plan(r: dict) -> str:
    if r.get("project"):
        return format_project(r)
    h = r["host"]
    lines = [r["name"], f"  path:      {r['path']}",
             f"  engine:    {r['engine']}",
             f"  host:      {h.get('cpu') or '?'}, {h.get('physical_cores')}C/{h.get('logical_cores')}T, {h.get('ram_gb')} GB RAM",
             "  exes:      " + (", ".join(f"{e} [{i['arch']}{', .NET' if i.get('managed') else ''}]"
                                          for e, i in list(r["executables"].items())[:5]) or "none found"),
             f"  APIs:      {', '.join(r['graphics_apis']) or 'none referenced (managed, Java or script runtime?)'}",
             f"  upscalers: {', '.join(f'{v} ({k})' for k, v in r['upscalers'].items()) or 'none shipped'}",
             f"  installed: {'; '.join(f'{k}: {v}' for k, v in r['layers_installed'].items()) or 'no wrappers or injectors'}",
             f"  anti-cheat: {', '.join(r['anti_cheat']) or 'none found'}"]
    lines += [f"  WARNING:   {w}" for w in r["warnings"]]
    lines.append("  levers, in order:")
    lines += [f"    {i}. {lv}" for i, lv in enumerate(r["levers"], 1)]
    return "\n".join(lines)


def main(args):
    r = plan(args.game)
    print(json.dumps(r, indent=2) if args.json else format_plan(r))


def register(sub):
    p = sub.add_parser("plan", help="engine, graphics API, LAA, upscalers, installed layers, anti-cheat -> levers",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("game", help='name (fuzzy), install folder, source project folder, or "roblox"')
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=main)
