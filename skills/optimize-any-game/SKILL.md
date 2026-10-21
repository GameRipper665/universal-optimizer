---
name: optimize-any-game
description: Make a PC game the user owns run faster and smoother, measured before and after. It covers low FPS, stutter, bad 1% lows, long loads, high CPU or RAM use, out-of-memory crashes and frame pacing, in any engine (Unity, Unreal, Godot, Source, Bethesda, Minecraft/Java, .NET/XNA, GameMaker, RPG Maker, Ren'Py, native C++, old DX8/9 games). Use when the user wants a game optimized, "more FPS", "less lag", "fix stutter", "use less RAM", "why does this run badly", or a performance mod. It works through recon, a measured baseline, finding the bottleneck, then config, drop-in fixes and code-level patches, keeping only what the numbers prove.
---

# Optimize any game

You are the performance engineer. The user names a game and a complaint; you find what limits it, change the
cheapest thing that moves that limit, and prove the result with numbers from the same scene.

Be straight with the user about what is possible. There is no switch that makes every game twice as fast.
What does happen, often:
- a setting, cvar or launch option that costs a lot and looks like little (shadows, volumetrics, crowd
  density, a broken default) gives 10-50%;
- an upscaler, or a newer one, gives a large GPU-side win;
- a community fix (FPS fixes, engine fixes, Sodium-class mods, DXVK on DX9) fixes stutter or CPU limits the
  developer never did;
- a code patch on the one hot function a profiler finds can give more than all of the above, in games
  that let you patch code.
And sometimes the machine is simply the limit. Say so when the numbers show it.

What this skill reaches, and what it doesn't:
- **PC games, any engine:** the full loop below. Unknown engines fall back to `engines/native.md` and the
  engine-independent layers.
- **Online games with anti-cheat (including Roblox as a player):** settings, official launch options,
  documented config, driver and OS only.
- **Console games via emulators** of games the user dumped from hardware they own: `engines/emulators.md`.
- **Consoles, mobile, cloud gaming:** only what the platform exposes (modes, system settings, network,
  stream quality): `platforms/consoles.md`, `platforms/mobile.md`, `platforms/cloud.md`.
- **A game the user develops** (they have the source or scripts, Roblox experiences included): use the
  **optimize-game-code** skill instead.

## Your tools

`uo` is this toolkit's CLI (`bin/uo`; the Claude Code plugin puts it on PATH). It builds on `um` from
[universal-modder](https://github.com/rehan-remade/universal-modder), which it installs as a dependency;
use `um` for backups, window control and the modding routes.

| Need | Command |
|---|---|
| Engine, graphics APIs, 32-bit/LAA, upscalers, installed wrappers, anti-cheat, CPU, ordered levers | `uo plan "<game>"` |
| Frame times, 1%/0.1% lows, stutters, GPU-vs-CPU bound, CPU, busiest thread, RAM of a running game | `uo bench <pid or exe> -o run.json` |
| Before/after table that marks noise | `uo compare before.json after.json` |
| Priority and CPU affinity of a running game (hybrid CPUs, X3D) | `uo proc <pid> ...` |
| Snapshot config/saves/game files before changing them; undo | `um backup create/diff/restore` |
| Launch, screenshot, drive input, kill by PID | `um win ...` |
| Prior art | `um kb search "<game>"`, then the community (see Recon) |

`uo bench` needs PresentMon 2.x for frame times (see `uo bench --help`). On Linux/Steam Deck, capture with
MangoHud (`MANGOHUD_CONFIG=output_folder=/tmp/mh,autostart_log=10,log_duration=60`) and load the CSV with
`uo bench --from-csv`.

## The loop

### 0. Intake
- The game, store and version; the complaint in one sentence ("drops to 40 in cities", "hitches every few
  seconds", "crashes after an hour", "uses 14 GB of RAM"); the target (a locked 60, the monitor's refresh
  rate, under 8 GB).
- Online or offline. If the game is online with anti-cheat, only in-game settings, official launch options,
  and driver/OS settings are in scope (Hard rules).
- Start `OPTLOG.md` in a working folder: every change, its exact file/key/value, the numbers, keep or revert.

### 1. Recon
- `uo plan "<game>"`. It reports the engine and the playbook to read
  (`references/engines/*.md`), the graphics APIs, whether a 32-bit exe lacks Large Address Aware, which
  upscaler DLLs ship, what wrappers are already installed, and the levers in order. Read the playbook.
- Search `knowledge/notes` in this repo and `um kb search "<game>"`, then the community for the game's known
  performance fixes: PCGamingWiki's page for the game (its "Essential improvements" and "Issues fixed"
  sections), the game's subreddit, Nexus and GitHub for "fps fix", "stutter fix", "performance". A maintained community fix beats anything you write.
- Note what is already installed: two wrappers fighting over `dxgi.dll` is a common reason a game runs badly.

### 2. Lab
- `um backup create "<config folder>" --name <game>-config` before the first change, and the same for any
  game file you will replace or add next to the exe (copy the originals into the backup). Write the restore
  command into OPTLOG.md.
- Pick one repeatable test scene: a save in the heaviest area, a benchmark mode, a fixed camera path, a
  replay. Same resolution, same settings, same duration every run; the game's own built-in benchmark is
  ideal. Close overlays and background downloads, and let shaders compile before measuring (play the scene
  once, then measure the second pass), unless shader stutter is the complaint.

### 3. Baseline
- `uo bench <exe> --seconds 60 -o base1.json`, then again `-o base2.json`. If the two disagree by more than
  ~3%, the scene is not repeatable yet: fix that first.
- Look at the frames, not just the average: 1% and 0.1% lows and stutters/min are what the player feels.

### 4. Find the bottleneck
Read `references/profiling.md`. In short:

| Signal | Bottleneck | Levers that move it |
|---|---|---|
| `bound: GPU` (GPU busy ~ frame time) | GPU | resolution/upscaler, the heavy settings, the engine's GPU cvars |
| `bound: CPU/engine` and `busiest_thread_pct` ~ 100 | one engine thread | simulation/draw-call load (view distance, crowds, physics rate), API translation (DXVK on DX9), engine fixes, code patches |
| CPU-bound, all threads busy | CPU overall | thread-count settings, background load, the same as above |
| stutters only the first time through a scene | shader/PSO compilation | shader cache settings, precompile options, DXVK async-type features, driver shader cache size |
| stutters while moving, every run | streaming, GC, or a frame-rate-tied loop | streaming pool/VRAM, GC settings, frame cap, engine fix |
| RAM/private bytes keep climbing | leak or cache growth | community memory fixes, the engine's cache limits, a patch |
| crashes near 2 GB (32-bit exe) | address space | Large Address Aware patch |
| frame time swings but average is fine | pacing | a frame cap under the 1% lows, VRR, flip model |

When the cause isn't clear from `uo bench`, profile (Windows Performance Recorder, the engine's own profiler,
spark/JFR for Java, dotTrace/PerfView for .NET): `references/profiling.md` says which and how.

### 5. Change one thing, measure, keep or revert
Work down the tiers; stop when the target is met.
1. **In-game settings.** The cheapest wins. Find the 2-3 settings that cost the most for this game
   (PCGamingWiki, the game's own optimization guides, or measure them one by one) and tell the user the visual
   trade-off.
2. **Config files and launch options** from the engine playbook (ini/cfg/cvars/boot.config/JVM flags).
3. **Drop-in fixes and universal layers.** Maintained community fixes for this game first, then
   `references/universal-layers.md`: API translation (DXVK, dgVoodoo2), upscaler swaps (OptiScaler, DLL
   updates), Special K or a frame limiter, LAA, priority/affinity, driver and OS knobs.
4. **Code-level patches.** Profile to the hot function, then patch it through the game's modding route
   (universal-modder's `mod-any-game` and `reverse-engineering` skills: Harmony, Mixin, UE4SS, ASI + hooks).
   Typical wins: caching a lookup done every frame, removing per-frame allocations, replacing an O(n^2) scan,
   throttling work that doesn't need to run every frame, fixing a busy-wait frame limiter. Ship it as a mod
   in the user's mod folder, never as an edited game binary.

After each change: `uo bench` twice, `uo compare`, write the row into OPTLOG.md. Keep it only if it wins
beyond noise (or fixes the complaint) without breaking anything; otherwise revert it now, not later.
Stacking ten unmeasured "tweaks" is how games end up slower and unstable.

### 6. Verify it still works
Play the scene, load a save, open menus: a fix that breaks saves, physics, or game speed (FPS-tied logic) is a
regression, not an optimization. Check the game's log for new errors.

### 7. Report
- The `uo compare` table from the original baseline to the final state, and the list of kept changes with
  their trade-offs, plus how to undo each one.
- A field note for the next agent in `knowledge/notes/` (copy `knowledge/TEMPLATE.md`): exact game version,
  hardware, what moved the numbers, what didn't, and gotchas. With the user's OK, open the PR.

## Hard rules
- **Online and anti-cheat.** For online games with anti-cheat (EasyAntiCheat, BattlEye, Vanguard, VAC on
  official servers, Ricochet, ACE...): in-game settings, official launch options, config files the game
  documents, and driver/OS settings only. No wrappers, injected DLLs, overlays that inject, memory patches or
  modified game files. Never bypass anti-cheat or DRM, and never disable anti-cheat except through an official
  offline launch option.
- **Back up first.** Every file you change or add next to the game is backed up, and its restore path is in
  OPTLOG.md. Never delete the user's files.
- **Ask first** before installing anything into the game folder, changing the registry, power plan, driver
  profiles or BIOS-level settings, or changing priority/affinity of a game they are playing.
- **No placebo.** Don't apply "RAM cleaners", working-set trimming, random registry packs, disabling the page
  file, or unmeasured "FPS boost" scripts. If the user asks for one, explain in one line why it does nothing
  or hurts.
- **Nothing irreversible to hardware.** No overclocking, undervolting, fan or power-limit changes unless the
  user explicitly asks and owns the risk.
- **Process hygiene.** Kill by exact PID (`um win kill`), never by name pattern.

## References
- `references/profiling.md`: finding the bottleneck, which profiler sees what, how to read the results.
- `references/universal-layers.md`: engine-independent levers (API translation, upscalers, frame pacing,
  LAA, OS/driver knobs) and the placebo list.
- `references/engines/`: `unity.md`, `unreal.md`, `godot.md`, `java.md` (Minecraft and JVM games),
  `dotnet-xna.md` (Terraria, Stardew, Celeste, Bannerlord), `source.md`, `bethesda.md`, `big-frameworks.md`
  (RE Engine, FromSoft, RAGE, REDengine, CryEngine, Frostbite...), `scripted.md` (GameMaker, RPG Maker,
  Ren'Py, Electron/HTML5, LÖVE, Paradox), `native.md` (unknown native engines, DX8/9 era games, hooking hot
  functions), `emulators.md` (RPCS3, Switch emulators, Dolphin, PCSX2, Cemu, Xenia, DuckStation, PPSSPP,
  shadPS4, Vita3K, RetroArch).
- `references/platforms/`: `consoles.md`, `mobile.md`, `cloud.md`.
- `knowledge/` at the repo root: field notes from earlier runs; search it in Recon and add one in Report.
