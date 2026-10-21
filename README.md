<div align="center">

# universal-optimizer

**Make any game run faster with your AI coding agent, and prove it with numbers.**

Games you play (PC, emulated, console and cloud settings) and games you make (any engine, any language).

[![test](https://github.com/GameRipper665/universal-optimizer/actions/workflows/test.yml/badge.svg)](https://github.com/GameRipper665/universal-optimizer/actions/workflows/test.yml)
![license: MIT](https://img.shields.io/badge/license-MIT-blue)
![python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![agents](https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Grok%20Build%20%C2%B7%20Antigravity%20%C2%B7%20Cursor-8A2BE2)

</div>

## Install in one message

Paste this into Claude Code, Codex, Grok Build, Antigravity, Cursor or any other coding agent:

```text
Install https://github.com/GameRipper665/universal-optimizer for yourself by following its INSTALL.md.
```

Your agent installs the `uo` CLI, registers the skills with itself, asks before fetching PresentMon, and tells
you what it did. Everything it runs is in [`INSTALL.md`](INSTALL.md). Then just ask:

> My game stutters every few seconds. Find out why and fix it.

## What it does

No magic switch makes every game twice as fast, and anything that claims to is selling placebo. This does what
a good performance engineer would, one measured step at a time:

1. **Finds what limits the game:** GPU, one saturated CPU thread, shader compilation, streaming, memory,
   network, frame pacing, or one hot function in the code.
2. **Changes the cheapest thing that moves that limit:** the 2-3 settings that cost the most, config and
   launch options the engine actually honours, maintained community fixes, universal layers (DXVK,
   dgVoodoo2, OptiScaler, Special K, Large Address Aware), or a code fix in your project or through a mod.
3. **Keeps it only if the numbers say so:** the same scene, measured twice before and twice after. Anything
   inside the noise is reverted.

| You have | Skill | What the agent can change |
|---|---|---|
| A PC game you play, any engine | `optimize-any-game` | settings, config and launch options, community fixes, universal layers, code patches through mods |
| An online game with anti-cheat | `optimize-any-game` | in-game settings, official launch options, documented config, driver and OS only |
| Console games you dumped, on an emulator | `optimize-any-game` | the emulator's renderer, shader, CPU and per-game settings, built-in patches |
| A console, phone or cloud-gaming service | `optimize-any-game` | what the platform exposes: modes, system settings, network, stream quality |
| The source of a game you make: Unity, Unreal, Godot, GameMaker, LÖVE, MonoGame, Bevy, libGDX, web, C/C++, Python, Lua... | `optimize-game-code` | the code itself, profiled with the engine's own tools |

## See it work

`uo plan` tells the agent what it's dealing with before it touches anything. Real output from a CS2 install:

```text
$ uo plan "counter-strike 2"
Counter-Strike 2
  engine:    Source 2
  host:      AMD Ryzen 7 5800X 8-Core Processor, 8C/16T, 63.9 GB RAM
  APIs:      D3D11, D3D9, Vulkan
  WARNING:   'counter strike 2' is an online competitive game: modding its client breaks the ToS ...
  levers, in order:
    1. ONLINE / ANTI-CHEAT: in-game settings, launch options, driver and OS knobs only. No wrappers,
       no injected DLLs, no memory patches, not even for single-player modes that share the client.
    2. Frame pacing: a frame cap a little under the 1% lows (in-game or the driver's) often removes
       stutter that raw FPS hides.
    3. Read next: skills/optimize-any-game/references/engines/source.md
```

Point it at a project folder and it switches to developer mode:

```text
$ uo plan ./my-godot-game
my-godot-game  (source project)
  kind:      Godot project (GDScript / C#)
  languages: GDScript 5
  levers, in order:
    1. Profile before touching code: the profilers for this engine and language are in the guide.
    2. Fix the hottest path first: algorithm, per-frame work, allocations, draw calls, network.
    3. One change at a time, re-measure the same scene, keep or revert (optimize-game-code skill).
    4. Guide: skills/optimize-game-code/references/engine-projects.md + .../languages.md
```

Then `uo bench` measures a running game, and `uo compare` says what actually changed:

```text
$ uo bench Game.exe --seconds 60 -o before.json
$ uo bench Game.exe --seconds 60 -o after.json
$ uo compare before.json after.json
```

It reports average FPS, 1% and 0.1% lows, p99 frame time, stutters per minute, whether the GPU or the CPU is the
limit, the busiest thread's load and memory. Changes under 3% are marked as noise.

## Try asking

> Skyrim SE drops to 40 FPS in Whiterun. Find out why and fix it without making it ugly.

> This old DX9 game stutters on my Ryzen 7 5800X and RTX 5060. Can DXVK help? Measure it.

> My Unity game's frame time spikes every few seconds. Profile it and fix the worst offender.

> My Godot game hitches when enemies spawn. Find out why.

> RPCS3 runs this game at 25 FPS. What settings actually help?

## Safe by design

- **No bans.** Online games with anti-cheat only get in-game settings, official launch options, documented
  config and driver/OS settings. No injection, wrappers or patched files, and never an anti-cheat or DRM
  bypass. `uo plan` detects anti-cheat and removes every injection lever on its own.
- **Undo for everything.** Every file is backed up before it's touched, and the restore path is logged.
- **No placebo.** No "RAM boosters", working-set trimming, registry packs or unmeasured "FPS boost" scripts.
  The guides say plainly why they don't work.
- **Your code stays yours.** Server authority stays on the server, behaviour doesn't change without asking,
  and edits follow your project's style.
- **Owned games only.** Emulated games and firmware come from the user's own hardware. The guides never link
  download sources.

## FAQ

<details>
<summary><b>Will it get me banned?</b></summary>

Not by following its rules: for games with anti-cheat it only changes what the game and your driver officially
expose. `uo plan` recognises anti-cheat and online-only games and drops every lever that would inject or patch.
</details>

<details>
<summary><b>Does it work on my engine?</b></summary>

Almost certainly. There are playbooks for Unity, Unreal, Godot, Java/Minecraft, .NET/XNA, Source, Bethesda,
RE Engine, FromSoft, RAGE, REDengine, CryEngine, GameMaker, RPG Maker, Ren'Py, Electron, LÖVE, Paradox and
emulators. Anything else falls back to the native-engine playbook and the engine-independent layers. For your
own projects, the code guides cover the major engines and languages.
</details>

<details>
<summary><b>Is this a "game booster"?</b></summary>

No. Boosters flip the same switches for every game whether they help or not. This measures your game on your
machine, changes one thing, and keeps it only if it measurably helped.
</details>

<details>
<summary><b>Does it cost anything?</b></summary>

The toolkit is free and MIT-licensed, and so are PresentMon, DXVK and the other tools it uses. You only pay for
your own AI agent. A few tools the guides mention are paid (Lossless Scaling, Superluminal, dotTrace), and
they're marked as paid.
</details>

## Install by hand

<details>
<summary>Per-agent commands, the CLI on its own, PresentMon</summary>

| Agent | Install |
|---|---|
| **Claude Code** | `/plugin marketplace add GameRipper665/universal-optimizer`<br>`/plugin install universal-optimizer@universal-optimizer` (add universal-modder's plugin too) |
| **Grok Build** | reads Claude Code plugins automatically; or `git clone https://github.com/GameRipper665/universal-optimizer ~/.grok/plugins/universal-optimizer` and enable it in `/plugins` |
| **Antigravity** | `agy plugin install https://github.com/GameRipper665/universal-optimizer` |
| **Codex** | `codex plugin marketplace add GameRipper665/universal-optimizer`, then `codex plugin add universal-optimizer@universal-optimizer` |
| **Skills only** (any agent) | `npx skills add https://github.com/GameRipper665/universal-optimizer` |
| **Anything else** | `git clone https://github.com/GameRipper665/universal-optimizer` and start your agent inside it (`AGENTS.md`) |

The CLI for every agent, with universal-modder's `um` included:

```bash
uv tool install --with-executables-from universal-modder git+https://github.com/GameRipper665/universal-optimizer
```

For frame times, put the [PresentMon](https://github.com/GameTechDev/PresentMon/releases) 2.x console exe
(`PresentMon-<version>-x64.exe`) in `~/.universal-optimizer/tools/` or on PATH. Capturing needs an elevated
shell. On Linux and Steam Deck, record with MangoHud and load the CSV with `uo bench --from-csv`.
</details>

## CLI reference

<details>
<summary><code>uo plan</code>, <code>uo bench</code>, <code>uo compare</code>, <code>uo proc</code></summary>

| Command | What it does |
|---|---|
| `uo plan "<game>"` | Engine, graphics APIs, 32-bit exes without Large Address Aware, shipped DLSS/FSR/XeSS DLLs, installed wrappers and injectors, anti-cheat, emulators, CPU → the levers to try, in order, and the guide to read |
| `uo plan <project folder>` | For source you develop: the kind of project, languages by file count, and the code guide |
| `uo bench <pid\|exe> -o run.json` | Frame times (PresentMon), avg / 1% / 0.1% lows, p99, stutters/min, GPU- vs CPU-bound, CPU use, busiest thread, working set and private bytes |
| `uo compare a.json b.json` | Before/after table; changes under 3% are marked as noise |
| `uo proc <pid> --priority --affinity` | Priority and CPU affinity (hybrid Intel, dual-CCD X3D) |
| `um ...` | universal-modder's CLI from the same install: `backup`, `win`, `kb`, `scan` |
</details>

## What's inside

<details>
<summary>2 skills, 14 engine and platform guides, code guides, a knowledge base</summary>

- `skills/optimize-any-game/`: the loop for games you play.
  - `references/profiling.md`: reading `uo bench`, kinds of stutter, WPR/WPA, engine profilers, memory.
  - `references/universal-layers.md`: engine-independent levers and the placebo list.
  - `references/engines/`: Unity, Unreal, Godot, Java/Minecraft, .NET/XNA, Source, Bethesda, big frameworks
    (RE Engine, FromSoft, RAGE, REDengine, CryEngine...), scripted engines (GameMaker, RPG Maker, Ren'Py,
    Electron, LÖVE, Paradox), native and DX8/9-era games, emulators.
  - `references/platforms/`: consoles, mobile, cloud gaming.
- `skills/optimize-game-code/`: the loop for games you develop.
  - `references/engine-projects.md`: Unity, Unreal, Godot, GameMaker, LÖVE, MonoGame/FNA, Bevy, libGDX, web.
  - `references/languages.md`: hot-path guidance per language and the universal checklist.
  - more per-platform code guides in the same folder.
- `knowledge/`: field notes from optimization runs, by agents for agents. Add yours from `TEMPLATE.md`.

Every guide cites its sources inline. Claims that couldn't be verified are marked `(unverified)` rather than
left out silently.
</details>

## Built on

[universal-modder](https://github.com/rehan-remade/universal-modder) for the engine scanner, backups, window
tools and the modding routes that code-level fixes go through.
[PresentMon](https://github.com/GameTechDev/PresentMon) for frame times, and [uv](https://docs.astral.sh/uv/)
for installs.

## License

MIT.
