# universal-optimizer

**Skills and tools that let any AI coding agent make games run faster, and prove it.** That covers games you
play, PC or emulated, and games you make, in any engine or language, Roblox included.
The agent finds what limits the game (GPU, one CPU thread, shader compilation, streaming, memory, network,
pacing, a hot function in the code), changes the cheapest thing that moves that limit, and keeps it only if a
before/after measurement of the same scene says so.

It's a companion to [universal-modder](https://github.com/rehan-remade/universal-modder): `uo` builds on its
engine scanner, backups and window tools, and code-level fixes to shipped games go through its modding routes
(Harmony, Mixin, UE4SS, ASI hooks).

No magic switch makes every game twice as fast. What the agent does is the work a good performance engineer
would: the 2-3 settings that cost the most, the config and launch options the engine actually honours, the
community fixes that exist, universal layers (DXVK, dgVoodoo2, OptiScaler, Special K, Large Address Aware), and
profiling down to the hot function and fixing it, in your own code or through a mod.

## What it covers

| You have | Skill | What the agent can change |
|---|---|---|
| A PC game you play, any engine | **optimize-any-game** | settings, config/launch options, community fixes, universal layers, code patches through mods |
| An online game with anti-cheat (Roblox as a player, competitive shooters...) | **optimize-any-game** | in-game settings, official launch options, documented config, driver/OS only |
| Console games you dumped, on an emulator | **optimize-any-game** (`engines/emulators.md`) | the emulator's renderer, shader, CPU and per-game settings, built-in patches |
| A console, phone or cloud-gaming service | **optimize-any-game** (`platforms/`) | what the platform exposes: modes, system settings, network, stream quality |
| The source of a game you make: Roblox (Luau), Unity, Unreal, Godot, GameMaker, LÖVE, MonoGame, Bevy, libGDX, web, C/C++, Python... | **optimize-game-code** | the code itself, profiled with the engine's own tools |

## Install

**The easy way: let your agent do it.** Paste this into Claude Code, Codex, Grok Build, Antigravity, Gemini
CLI, Cursor or any other coding agent:

```text
Install https://github.com/GameRipper665/universal-optimizer for yourself by following its INSTALL.md.
```

It installs the `uo` CLI, registers the skills with whichever agent it is, offers to fetch PresentMon, and
tells you what it did. [`INSTALL.md`](INSTALL.md) is written for agents, so you can read exactly what they'll run.

**By hand:**

| Agent | Install |
|---|---|
| **Claude Code** | `/plugin marketplace add GameRipper665/universal-optimizer`<br>`/plugin install universal-optimizer@universal-optimizer` (add universal-modder's plugin too) |
| **Grok Build** | reads Claude Code plugins automatically; or `git clone https://github.com/GameRipper665/universal-optimizer ~/.grok/plugins/universal-optimizer` and enable it in `/plugins` |
| **Antigravity** | `agy plugin install https://github.com/GameRipper665/universal-optimizer` |
| **Codex** | `codex plugin marketplace add GameRipper665/universal-optimizer`, then `codex plugin add universal-optimizer@universal-optimizer` |
| **Gemini CLI** | `gemini extensions install https://github.com/GameRipper665/universal-optimizer` |
| **Skills only** (any agent) | `npx skills add https://github.com/GameRipper665/universal-optimizer` |
| **Anything else** | `git clone https://github.com/GameRipper665/universal-optimizer` and start your agent inside it (`AGENTS.md`) |

The CLI, for every agent:
```bash
uv tool install --with-executables-from universal-modder git+https://github.com/GameRipper665/universal-optimizer
```
That gives you `uo` and universal-modder's `um`. In a clone, `bin/uo` (`bin\uo.cmd` on Windows) also works and
sets itself up with [uv](https://docs.astral.sh/uv/). For frame times, put the
[PresentMon](https://github.com/GameTechDev/PresentMon/releases) 2.x console exe (`PresentMon-<version>-x64.exe`)
in `~/.universal-optimizer/tools/` or on PATH; capturing needs an elevated shell. On Linux/Steam Deck, record
with MangoHud and load the CSV.

## Try it
> Skyrim SE drops to 40 FPS in Whiterun. Find out why and fix it without making it ugly.

> This old DX9 game stutters on my 5800X. Can DXVK help? Measure it.

> My Roblox server's heartbeat drops with 30 players. Profile the scripts and fix the worst ones.

> My Godot game stutters when enemies spawn. Find out why.

> RPCS3 runs this game at 25 FPS on my machine. What settings actually help?

## The loop
Both skills run the same loop: intake (the complaint, the target, online or offline) → recon (`uo plan`,
the knowledge base, community fixes) → back up anything they'll touch → baseline measured twice → find the
bottleneck → one change at a time, measured, kept or reverted → verify the game still plays right → report
the numbers and leave a field note.

## The `uo` CLI

| Command | What it does |
|---|---|
| `uo plan "<game>"` | Engine, graphics APIs, 32-bit exes without Large Address Aware, shipped DLSS/FSR/XeSS DLLs, installed wrappers and injectors, anti-cheat, emulators, CPU → the levers to try, in order, and the playbook to read |
| `uo plan <project folder>` | For source you develop: the kind of project (Roblox/Rojo, Unity, Unreal, Godot, GameMaker, ...), languages by file count, and the guide to read |
| `uo plan roblox` | The installed Roblox client: online with anti-cheat, player-side settings only |
| `uo bench <pid\|exe> -o run.json` | Frame times (PresentMon), avg / 1% / 0.1% lows, p99, stutters/min, GPU- vs CPU-bound, CPU use, busiest thread, working set and private bytes |
| `uo compare a.json b.json` | Before/after table; changes under 3% are marked as noise |
| `uo proc <pid> --priority --affinity` | Priority and CPU affinity (hybrid Intel, dual-CCD X3D) |
| `um ...` | universal-modder's CLI from the same environment: `backup`, `win`, `kb`, `scan` |

## What's inside
- `skills/optimize-any-game/`: the loop for games you play.
  - `references/profiling.md`: reading `uo bench`, kinds of stutter, WPR/WPA, engine profilers, memory.
  - `references/universal-layers.md`: engine-independent levers and the placebo list.
  - `references/engines/`: Unity, Unreal, Godot, Java/Minecraft, .NET/XNA, Source, Bethesda, big frameworks
    (RE Engine, FromSoft, RAGE, REDengine, CryEngine...), scripted engines (GameMaker, RPG Maker, Ren'Py,
    Electron, LÖVE, Paradox), native and DX8/9-era games, emulators.
  - `references/platforms/`: consoles, mobile, cloud gaming.
- `skills/optimize-game-code/`: the loop for games you develop.
  - `references/roblox-luau.md`: Roblox experiences, from MicroProfiler to Parallel Luau.
  - `references/engine-projects.md`: Unity, Unreal, Godot, GameMaker, LÖVE, MonoGame/FNA, Bevy, libGDX, web.
  - `references/languages.md`: hot-path guidance per language and the universal checklist.
- `knowledge/`: field notes from optimization runs, by agents for agents. Add yours from `TEMPLATE.md`.

## Rules
Online games with anti-cheat only get in-game settings, official launch options, documented config and
driver/OS settings: no injection, wrappers or patched files, and never an anti-cheat or DRM bypass. Emulated
games come from the user's own hardware. Every touched file is backed up first. No placebo "RAM boosters" or
registry packs. In code, server authority stays and behaviour doesn't change without asking. Full rules in the
skills.

## License
MIT.
