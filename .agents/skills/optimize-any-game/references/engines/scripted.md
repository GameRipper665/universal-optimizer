# Scripted and managed-runtime engines

One playbook, one section per family. Each section follows `_FORMAT.md`, compactly. For the patching routes
(UndertaleModTool, `js/plugins`, asar extraction, `.love` zips, Ren'Py `.rpy`, Paradox script mods) see
[universal-modder `misc-engines.md`](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/misc-engines.md)
and do not re-derive them here. Single-player/offline games only. Do not touch Steam/DRM wrappers or online
clients when swapping runtimes. Back up everything you change; ship changes as patches, never the whole game.

---

# GameMaker

**Identify.** `data.win` (Linux `game.unx`) next to a runner exe. A VM export keeps GML as bytecode in `data.win`;
a YYC export compiles GML to native code inside the exe ([YoYo Compiler](https://manual.gamemaker.io/lts/en/Settings/YoYo_Compiler.htm):
"Compiled code is faster to run, but takes more time to compile"). No official benchmark numbers exist; the gap
depends on the project. In UndertaleModTool, a YYC game will show little or no usable GML (unverified), so treat it as native.

**Where the time usually goes.**
- Too many live instances, and Step/Draw events that do work every frame ([Forager write-up](https://gamemaker.io/en/blog/forager-optimization-in-gamemaker):
  excessive instance count was "the worst performance drag in nearly every project").
- GPU batch breaks: changing shader/surface/primitive state mid-draw splits the batch (same source).
- Frame pacing, not raw speed: wrong timing method or no vsync shows as tearing or uneven frames.
- VM interpretation of hot GML (VM only).
- Confirm: draw `fps_real` (the real rate; `game_get_speed` only returns the *target*, see
  [game_get_speed](https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/General_Game_Control/game_get_speed.htm))
  and `instance_count` in a patched Draw GUI event. Compare before and after on the same save.

## Tier 1: config and launch options
- There is usually no config file. Use the game's own options menu (resolution, vsync, effects) first.
- The vsync option is a baked build flag: "Use synchronization to avoid tearing" under Game Options > Windows >
  Graphics, on by default only for projects created in 2024.14.3 or later
  ([GameMaker blog](https://gamemaker.io/en/blog/screen-tearing)). In `data.win` these are the
  `SyncVertex1/2` bits of the General Info flags
  ([UndertaleGeneralInfo.cs](https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModLib/Models/UndertaleGeneralInfo.cs)).
  Trade-off: vsync fixes tearing and adds a little input latency. It does not raise the cap.
- Do not just raise the room speed to "unlock FPS". Target speed is set by `game_set_speed` / the room speed
  ([manual](https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/General_Game_Control/game_set_speed.htm));
  logic written per-step then runs faster. Only games that scale by [`delta_time`](https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Maths_And_Numbers/Date_And_Time/delta_time.htm)
  survive a higher cap.

## Tier 2: drop-in community fixes and runtime swaps
- None verified. [GMRT](https://manual.gamemaker.io/lts/en/Settings/Runner_Details/GMRT_(GameMaker_Runtime).htm)
  (the new runtime) is documented as experimental, and a shipped game cannot be moved to it by swapping files.
  Do not swap runner exes between games.

## Tier 3: code-level patches
- Route: open `data.win` in [UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool) (GPL-3.0),
  edit the hot script/event in GML, save. VM exports only. Distribute an xdelta patch (see `misc-engines.md`).
- Profiler: GameMaker's profiler lives in the IDE and needs the project (unverified for shipped builds). Without
  it, time the suspect event with `get_timer()` and print the result.
- Patterns that paid off in the Forager write-up (same link as above):
  - Move per-step lookups into Create or run them only when the data changes.
  - Put cheap or usually-false checks first in `&&` chains (GML short-circuits).
  - Spread non-urgent systems over N frames (a counter plus `switch`).
  - Deactivate off-screen instances. Trade-off: deactivated instances break `instance_exists` and similar, so a
    custom cache is needed.
  - Replace never-moving objects with layers, particles or data structures.
- Timing method: games can call `display_set_timing_method`. Vsync timing is the default except on PS4, Ubuntu
  and HTML5; `tm_systemtiming` lets the frame rate run as fast as the machine
  ([manual](https://manual.gamemaker.io/beta/en/GameMaker_Language/GML_Reference/Cameras_And_Display/display_set_timing_method.htm)).

## Gotchas
- Game speed changes after raising room speed -> logic is per-step -> revert, patch to `delta_time` or leave it.
- UTMT cannot compile your edit -> the export is YYC or the data.win version is unsupported -> stop; do not hex-edit.

---

# RPG Maker MV / MZ (NW.js)

**Identify.** `package.json` + `www/` (MV) or loose `js/`, `data/`, `img/` (MZ) beside `Game.exe` / `nw.exe`,
`nw.dll`, `icudtl.dat`. Plugins: `js/plugins.js`. Press F8 (playtest/SDK builds) for the console; type
`PIXI.VERSION` to see the renderer library version.

**Where the time usually goes.**
- A 2018-era Chromium (the runtime MV shipped has not been updated since 2018, see the
  [NW.js update guide](https://itch.io/blog/484532/how-to-update-nwjs-in-rpg-maker-mv-for-rpg-devs)).
- Bitmap/canvas work done on the CPU: menu snapshot/blur, hue shifts, text colour lookups, animations
  ([Performance Upgrade](https://atelieririna.itch.io/performance-upgrade) describes exactly these hotspots).
- Per-frame JS allocation and a fixed 1/60 s update accumulator in `SceneManager`
  ([source](https://github.com/rpgtkoolmv/corescript/blob/master/js/rpg_managers/SceneManager.js)).
- Plugin stacks (every plugin that patches `Scene_Map.update` or `Sprite` adds up). Confirm with the DevTools
  Performance panel (Electron/NW.js section below).
- FPS meter: MV shows it with F2 in `Graphics` ([source](https://github.com/rpgtkoolmv/corescript/blob/master/js/rpg_core/Graphics.js)),
  or launch with the `showfps` option.

## Tier 1: config and launch options
- **Renderer (MV).** `Utils.isOptionValid` reads the URL query string or `nw.App.argv[0]` split on `&`
  ([Utils.js](https://github.com/rpgtkoolmv/corescript/blob/master/js/rpg_core/Utils.js)).
  `SceneManager.preferableRendererType` returns `canvas`, `webgl`, or `auto`. So a shortcut target of
  `Game.exe webgl` forces WebGL and `Game.exe canvas` forces the Canvas renderer; `webgl&showfps` combines them.
  Trade-off: forced WebGL fails to start on machines without a working GPU path; Canvas is the slow path. MZ:
  unverified, a forum post says MZ requires WebGL.
- **`chromium-args` in `package.json`** ([NW.js manifest](https://nwjs.readthedocs.io/en/latest/References/Manifest%20Format/):
  "Specify chromium (content shell) command line arguments"). Test flags without editing the file via the
  `NW_PRE_ARGS` environment variable, which is prepended to `chromium-args`
  ([NW.js command line](https://docs.nwjs.io/References/Command%20Line%20Options/)). The flag table is under
  "Electron / NW.js / HTML5" below.
- `--limit-fps=60` is reported on itch.io to fix games running too fast under a FPS-sync plugin
  ([post](https://itch.io/post/15421024)). (unverified)
- **Fluid timestep.** Yanfly's [FPS Synch Option](https://www.yanfly.moe/wiki/FPS_Synch_Option_(YEP)) lets players
  switch the timestep off on weak hardware. It does not speed anything up.

## Tier 2: drop-in community fixes and runtime swaps
- **Replace the NW.js runtime** (the biggest single lever; guide: [itch.io](https://itch.io/blog/484532/how-to-update-nwjs-in-rpg-maker-mv-for-rpg-devs)).
  - Use the "Stable / Normal" build, not SDK, for a shipped game. SDK only for playtest folders.
  - Copy the new runtime files over the game folder, keep `package.json` and the game data, and set a unique,
    non-empty `"name"` in `package.json` (an empty name gives "Error Loading Extension").
  - If it says the profile is from a newer NW.js, clear the profile folder (`%LOCALAPPDATA%/KADOKAWA/RPGMV` for MV,
    `rmmz-game` for MZ).
  - Risks: versions newer than v0.72.0 do not run on Windows 7/8/8.1 (guide). Reports that 0.88/0.89 may not exit
    during playtest (guide comment, anecdotal). Games with native addons or Steam wrappers are built for one NW.js
    version (unverified): leave those alone. Older runtime is "most likely safe" only offline (guide).
  - Remove: restore the backed-up folder.
- **Core replacements and plugins.**

| Name | What it does | License / terms | Notes |
|---|---|---|---|
| [RMMV Tuned Core](https://aceofaces.itch.io/rmmv-tuned-core) (AceOfAces) | patched core scripts or one "Engine Tuner" plugin, Pixi 4.8.9, claims "10+ fps on average" | MIT | MV only; claim is the author's |
| [Performance Upgrade](https://atelieririna.itch.io/performance-upgrade) (Irina) | moves hue/blur/snapshot work to PIXI filters; PIXI container flush | credit required, **no redistribution** | tested on MV 1.6.2; keep it local, do not repack and share |
| [rpgmaker-optimization](https://github.com/lekoder/rpgmaker-optimization) (lekoder) | swaps core pieces for faster ones | MIT | last push 2016, pins old PIXI; likely stale |
| [thinknathan/corescript](https://github.com/thinknathan/corescript) | fork on PIXI 6.5.x, BitmapText | Apache-2.0 / MIT | "not a drop-in replacement"; author claims only |

  Install: plugins go in `js/plugins/` and `js/plugins.js` (see `misc-engines.md`). Core replacements overwrite
  `js/rpg_*.js` and `js/libs/`; keep a copy. MV 1.6 ships `pixi.js` v4.5.4
  ([libs/pixi.js](https://github.com/rpgtkoolmv/corescript/blob/master/js/libs/pixi.js)). Do not swap PIXI alone:
  a developer reports newer PIXI may be incompatible with RPG Maker's own code (itch.io thread, anecdotal).

## Tier 3: code-level patches
- Profile with the DevTools Performance panel first (NW.js SDK build, or `--remote-debugging-port=9222` as in
  `misc-engines.md`). Patch the plugin or core function that dominates the flame chart.
- Patterns: replace bitmap-based hue/blur with PIXI filters; cache text colours instead of rereading the
  windowskin; skip screen snapshots unless needed; remove textures when sprites are removed
  (all listed by [Performance Upgrade](https://atelieririna.itch.io/performance-upgrade)).
- MV has no official profiler beyond the browser tools; use them.

## Gotchas
- Game runs 2x fast after a refresh-rate change -> FPS-sync plugin on a 144 Hz display (anecdotal, itch.io) ->
  disable the plugin option or apply `--limit-fps=60` (unverified).
- NW.js update leaves a black window -> unique `package.json` name missing or profile folder from the old build.

---

# RPG Maker XP / VX / VX Ace (RGSS) and mkxp-z

**Identify.** `Game.exe` + `Game.ini` + `Data/Scripts.rxdata|rvdata|rvdata2`; `Game.rgssad|rgss2a|rgss3a` archives.

**Where the time usually goes.** The original RGSS player is old and Windows-only. Script-heavy games (Pokemon
Essentials style) spend most of it in Ruby scripts and bitmap work. Confirm with the F2 FPS display in
mkxp-z, or `displayFPS` in `mkxp.json`.

## Tier 1: config and launch options
- None for stock RGSS. Use the game's own options menu.

## Tier 2: drop-in community fixes and runtime swaps
- **[mkxp-z](https://github.com/mkxp-z/mkxp-z)** (GPL-2.0+) is an open-source RGSS player descended from
  mkxp, built to run Pokemon Essentials games. README claims: Windows, Linux (x86/ARM/POWER), macOS (Intel and
  Apple Silicon); runs "all but the most demanding of RGSS projects, given a bit of porting work"; WMA audio
  unsupported; bitmaps larger than the GPU texture limit generally fail; MIDI needs a user-supplied soundfont
  ([README](https://github.com/mkxp-z/mkxp-z/blob/dev/README.md)).
- It does **not** promise higher FPS. Whether it is faster for a given game is unverified: measure it.
- Install: build/release goes next to the game; `gameFolder` resolves relative to the mkxp executable by default
  ([mkxp.json](https://github.com/mkxp-z/mkxp-z/blob/dev/mkxp.json)). The exact file layout and RTP handling
  differ per game (unverified).
- `mkxp.json` options (all verified in that file): `rgssVersion` (0 = auto-detect), `displayFPS`, `printFPS`,
  `vsync` (default off), `fixedFramerate` (0 = off), `frameSkip` (default off), `syncToRefreshrate` (default off;
  reports the real rate back to the game so timers stay right), `smoothScaling`, `textureScalingFactor`.
  Trade-off: `frameSkip` drops draws when behind; `fixedFramerate` can desync game timers (the file says
  `syncToRefreshrate` avoids that).
- Games that call WinAPI directly from scripts can crash under mkxp-z (kernel32 load error, secondary source:
  [linux.org.ru guide](https://www.linux.org.ru/articles/games/17544686)). Remove: delete the mkxp-z files.

## Tier 3: code-level patches
- Scripts are Marshal+zlib Ruby in `Data/Scripts.*`; extract/edit/repack per `misc-engines.md`. Profile by timing
  suspect methods with `Time.now` or `Graphics.frame_count` deltas. Common wins: avoid redrawing bitmaps every
  frame (redraw on change only), avoid creating `Bitmap`/`Sprite` objects per frame, `dispose` what you create.

## Gotchas
- Crash on start after switching to mkxp-z -> WinAPI scripts or missing RTP -> revert to stock `Game.exe`.

---

# Electron / NW.js / HTML5 games

**Identify.** Electron: `resources/app.asar`, `electron.exe` or a renamed binary, `chrome_*.pak`. NW.js:
`package.nw` or loose files, `nw.dll`, manifest `package.json`. Construct (`c3runtime.js`), Phaser, PixiJS:
plain JS. Extract/patch routes are in `misc-engines.md`.

**Where the time usually goes.** Main-thread JS (allocation/GC in the `requestAnimationFrame` loop), canvas or DOM
work, a Chromium that predates your GPU, and GPU-process blocklisting that falls back to software. Confirm with the
[Chrome DevTools Performance panel](https://developer.chrome.com/docs/devtools/performance): record, stop, then read
the FPS chart (red bar = dropped frames) and the Main flame chart (wider bar = longer task). Also check
`chrome://gpu` for the GPU process state (unverified here).

## Tier 1: config and launch options
How to set flags: NW.js `chromium-args` in `package.json` or `NW_PRE_ARGS`; Electron
`app.commandLine.appendSwitch(...)` before the `ready` event
([Electron switches](https://www.electronjs.org/docs/latest/api/command-line-switches)).
Chromium has "no documented list of all switches" (same page); the ones below are from Chromium source.

| Flag | Source | What it does / trade-off |
|---|---|---|
| `--disable-gpu-vsync` | [gl_switches.cc](https://github.com/chromium/chromium/blob/main/ui/gl/gl_switches.cc) | "Stop the GPU from synchronizing presentation with vblank." Tearing; reports it is ignored or only partly works in some NW.js/Electron builds (forum, anecdotal) |
| `--disable-frame-rate-limit` | [viz/switches.cc](https://github.com/chromium/chromium/blob/main/components/viz/common/switches.cc) | Disables begin-frame limiting, implies `--disable-gpu-vsync`. Uncapped means more heat and power; reports on current builds are mixed |
| `--ignore-gpu-blocklist` | [gpu_switches.cc](https://github.com/chromium/chromium/blob/main/gpu/config/gpu_switches.cc) | "Ignores GPU blocklist." Forces GPU paths Chromium disabled for your GPU/driver; may crash or glitch. Try only if `chrome://gpu` shows software rendering |
| `--enable-gpu-rasterization` | same file | Lets Chromium choose Skia GPU raster for tiles. Whether it is already on in your Chromium version is unverified: measure |
| `--use-angle=<backend>` / `--use-gl=` | [gl_switches.cc](https://github.com/chromium/chromium/blob/main/ui/gl/gl_switches.cc) | Pick the ANGLE backend (`d3d11`, `gl`, ...) or GL implementation. A fix for driver bugs, not a speed-up |
| `--force_high_performance_gpu` | [Electron](https://www.electronjs.org/docs/latest/api/command-line-switches) | Use the discrete GPU on multi-GPU laptops (Electron only) |
| `--js-flags=...` | same | V8 flags; must be passed at startup (e.g. `--trace-opt --trace-deopt` to see deopts). Diagnostic, not a fix |
| `--disable-raf-throttling` | [NW.js](https://docs.nwjs.io/References/Command%20Line%20Options/) | `requestAnimationFrame` keeps firing when hidden/minimised. Not a speed-up: more CPU in the background |

- Do not use `app.disableHardwareAcceleration()` ([Electron app](https://www.electronjs.org/docs/latest/api/app),
  "can only be called before app is ready") as an optimisation. It is a diagnostic for GPU bugs and moves
  rendering to the CPU (speed impact unverified, expect slower).
- Test one flag at a time on the same scene; keep only the ones that change the numbers.

## Tier 2: drop-in community fixes and runtime swaps
- **NW.js:** swap in a newer Normal build (see the RPG Maker section for exact steps and risks).
- **Electron:** replacing the Electron binary with a newer prebuilt one is possible in principle, but any native
  Node module in the app is tied to the old ABI and fails with a `NODE_MODULE_VERSION` mismatch unless recompiled
  ([Electron docs](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules)). Also an
  Electron major can drop APIs the game's JS uses. Only swap games with no `.node` files. (rest unverified)
- Remove: restore the backup.

## Tier 3: code-level patches
- Route: extract `app.asar` (`npx @electron/asar extract`) or patch loose JS, then repack or use `resources/app/`
  (see `misc-engines.md`).
- Patterns ([Electron performance](https://www.electronjs.org/docs/latest/tutorial/performance),
  [MDN canvas optimisation](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas)):
  - Keep long CPU work off the renderer main thread (Web Workers); use `requestIdleCallback` for low-priority work.
  - Pre-render static content to an offscreen canvas and reuse it.
  - Use whole-number coordinates; batch draw calls; avoid `shadowBlur`.
  - Use `requestAnimationFrame` instead of `setInterval`; `alpha: false` in `getContext` when not transparent.
  - Do not scale images inside `drawImage` every frame; cache the sizes you need.

## Gotchas
- Flag has no effect -> NW.js/Electron version ignores it, or it is overridden by the GPU blocklist -> check
  `chrome://gpu`, then drop the flag.
- NW.js `--disable-crash-handler` placed in `package.json` does nothing; it must be on the command line (NW.js docs).

---

# Ren'Py

**Identify.** `renpy/` folder, `game/*.rpa` archives and `.rpyc`, `lib/` with Python. `game/options.rpy` and
`gui.rpy` may be compiled; extra `.rpy` files in `game/` are loaded (see `misc-engines.md`).

**Where the time usually goes.**
- Image load hitches when an image is shown before it was predicted.
- RAM/VRAM from the image cache; too small causes reloads, too big causes memory pressure.
- Slow screens (large `use`, heavy Python in screen code, no displayable reuse).
- Slow `init` blocks (start-up time).
- A bad GL driver path. Confirm with the tools listed in Tier 3.

## Tier 1: config and launch options
Set in a new `game/zz_perf.rpy` with `init 999 python:` (higher priority than the game's own `define`s, per
`misc-engines.md`). All defaults below are from the [config reference](https://www.renpy.org/doc/html/config.html).

| Setting | Default | Effect / trade-off |
|---|---|---|
| `config.image_cache_size_mb` | 300 | Image cache size in MB; 4 bytes/pixel, 8 if `cache_surfaces` is on. Bigger = fewer reloads and more RAM (a 1920x1080 image is about 8.3 MB). Raise for reload hitches, lower on low-RAM machines |
| `config.predict_statements` | 32 | Statements looked ahead for predictive loading. 0 disables it; lower saves memory, raises load hitches |
| `config.cache_surfaces` | False | Keeps image data in RAM as well as the GPU. Leave off unless profiling says otherwise (doubles per-pixel cost) |
| `config.optimize_texture_bounds` | True | Crops transparent borders before upload. Leave on |
| `config.mipmap` | True | Mipmap generation. Turning it off should cut memory/load time at a quality cost when scaling (effect unverified) |

- Renderer: hold Shift at start or press **Shift+G** for the "Graphics Acceleration" menu, then restart
  ([display problems](https://www.renpy.org/doc/html/display_problems.html)). Order is `gl2` (OpenGL 3.3 falling
  back to 2.0), `angle2` (Windows DirectX 11), `gles2`; the older `gl`/`angle`/`gles` were removed in 8.4. Pick
  `gl2` or `angle2` if one is glitchy; this is a compatibility fix, not a speed-up.
- Static screens drop to 5 FPS by design to save power. On VRR (G-Sync/FreeSync) displays that can flicker;
  Shift+G > Powersave > Disable fixes it (same page). Trade-off: more GPU/CPU use while idle.
- Env var `RENPY_GL_VSYNC`: `0` disables sync, `1` syncs to every refresh
  ([env vars](https://www.renpy.org/doc/html/environment_variables.html)). The doc warns these "may disappear or change".

## Tier 2: drop-in community fixes and runtime swaps
- No verified drop-in. Swapping `renpy/` between versions breaks games (use only the game's own version);
  `unrpa` / `unrpyc` are for reading, not speeding up.

## Tier 3: code-level patches
- Developer tools need `config.developer = True`; then **Shift+D** opens the developer menu, **Shift+O** the
  console ([developer tools](https://www.renpy.org/doc/html/developer_tools.html)).
- Profilers (verified in the docs): `config.profile = True` prints profiling info to stdout;
  `config.profile_init` (default 0.25 s) logs slow `init` blocks; `renpy.profile_screen(name, ...)` writes
  `profile_screen.txt` in the game folder ([screen optimization](https://www.renpy.org/doc/html/screen_optimization.html)).
  `config.log_events` hurts performance; do not leave it on.
- Screen patterns from the same page: let Ren'Py predict screens (`renpy.start_predict_screen` for screens shown
  from Python), keep displayables reusable between updates, use `define`/`const` expressions so Ren'Py can skip
  re-evaluation. Prefer moving animation delays so prediction has time to load images
  ([GUI docs note](https://www.renpy.org/doc/html/gui.html)).
- `gui.rebuild()` and `gui.history_height = None` are documented as slow; avoid calling them per frame or
  per-screen.

## Gotchas
- Hitch right after a scene change -> image not predicted or cache too small -> raise `image_cache_size_mb`,
  keep `predict_statements` at 32.
- Black or glitchy window -> bad GL driver -> Shift+G, try `angle2` / `gl2`.

---

# LÖVE (Lua)

**Identify.** A `.love` zip, or a zip appended to an exe, with `main.lua` and usually `conf.lua`. Fused games use
`love.dll`. Patching routes (unzip, lovely injection) are in `misc-engines.md`.

**Where the time usually goes.**
- Lua garbage from per-frame table/string allocation in `love.update` / `love.draw`.
- Many small draw calls instead of batching (`love.graphics.getStats()` returns `drawcalls`, `drawcallsbatched`,
  `texturememory`, verified in [wrap_Graphics.cpp](https://github.com/love2d/love/blob/main/src/modules/graphics/wrap_Graphics.cpp)).
- LuaJIT trace aborts (code the JIT cannot compile falls back to the slower interpreter).
- Vsync/frame pacing in `conf.lua`.

## Tier 1: config and launch options
Defaults from LÖVE's own [boot.lua](https://github.com/love2d/love/blob/main/src/modules/love/boot.lua):
`window.vsync = 1`, `window.msaa = 0`, `graphics.gammacorrect = false`, `graphics.lowpower = false`, every
module `true`.
- `t.window.vsync`: `1` on, `0` off, `-1` adaptive. The window code falls back to `1` when adaptive is not
  supported ([Window.cpp](https://github.com/love2d/love/blob/main/src/modules/window/sdl/Window.cpp)). The
  setter accepts a boolean or integer ([wrap_Window.cpp](https://github.com/love2d/love/blob/main/src/modules/window/wrap_Window.cpp)).
  Off = lower latency, tearing, and `love.timer` delta spikes if the game's logic is not delta-based.
- `t.window.msaa`: lower it (default 0) if the game raised it; MSAA costs fill rate and VRAM.
- `t.modules.<name> = false` skips unused modules (physics, video, sensor...). Trade-off: any code calling a
  disabled module errors; only startup cost drops (magnitude unverified).
- `t.graphics.gammacorrect` (11.x: `t.gammacorrect`, deprecated in current boot.lua): off is cheaper; turning it
  on changes colour output.
- Editing `conf.lua` means editing the `.love` zip. Command-line `--renderers` / `--excluderenderers` exist in
  boot.lua; their accepted values are unverified.

## Tier 2: drop-in community fixes and runtime swaps
- Swapping the `love` binary for a newer 11.x release usually works for 11.x games (unverified); 12.0 changed config
  keys (see the `t.graphics` move in boot.lua), so do not swap across majors blindly.
- **lovely** (Lua patch injection, see `misc-engines.md`) can patch a fused game without repacking.

## Tier 3: code-level patches
- **jprof** ([pfirsich/jprof](https://github.com/pfirsich/jprof), MIT): `prof.push(name)` / `prof.pop(name)`
  zones around the frame, `prof.write(file)` or `prof.connect(...)` for live data, flame-graph viewer is itself a
  LÖVE project. Needed because `debug.sethook` is unreliable under LuaJIT.
- **AppleCake** ([EngineerSmith/AppleCake](https://github.com/EngineerSmith/AppleCake), MIT): writes
  `profile.json` for `about://tracing` or Perfetto; tested on LÖVE 11.4 and 12.0; has a jprof-compatible API.
- LuaJIT ([running](https://luajit.org/running.html), [jit.*](https://luajit.org/ext_jit.html)):
  `jit.status()` shows whether the JIT is on; `jit.off(func)` disables compiling one function (useful when a trace
  keeps aborting); `jit.flush()` clears compiled code; `jit.opt.start(...)` sets `-O` options at runtime.
  `-jv`/`-jp` are CLI flags of the `luajit` executable, not of `love`. Defaults like `hotloop=56` rarely need
  changing.
- Patterns: reuse tables instead of allocating per frame; batch with `SpriteBatch`; avoid `love.graphics.newImage`
  in the loop; keep colours in numbers, not strings. (Patterns are general LÖVE practice, unverified here.)

## Gotchas
- Game speed changes after turning vsync off -> logic is frame-based, not `dt`-based -> keep vsync on.
- `love.conf` edits ignored -> packaged `.love` still holds the old `conf.lua` -> repack or inject.

---

# Paradox Clausewitz / Jomini (EU4, CK3, HoI4, Stellaris, Vic3)

**Identify.** `<game>.exe` plus a launcher; user data under `Documents/Paradox Interactive/<Game>/` with
`logs/error.log` and `mod/` (see `misc-engines.md`).

**Where the time usually goes.** The simulation, not graphics. Late-game slowdown is mostly CPU-bound simulation
of pops, characters, countries and units, run mostly on one or two threads (forum observation, anecdotal).
- Stellaris: pop and planet management; the 4.0 rework says the Pop and Jobs system "has always had significant
  performance implications in the late game", so pops are now grouped (actions touch groups of about 100)
  ([Dev Diary #370](https://admin-forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-370-4-0-changes-part-4.1728047/)).
- Vic3: performance is measured as tick speed (a tick is six hours). The employment update is the most
  expensive task, "very strongly correlated with the number of pops" (pop *objects*, not total population)
  ([Dev Diary #76](https://www.paradoxinteractive.com/games/victoria-3/news/dev-diary-76-performance)). 1.6 made
  performance worse for most users because AI and migration changes outweighed other gains
  ([Dev Diary #142](https://admin-forum.paradoxplaza.com/forum/developer-diary/victoria-3-dev-diary-142-2024-in-retrospect.1726056)).
- HoI4: AI division spam; Expert AI's author says the AI "won't spam thousands of divisions" (Steam/forum,
  author claim).
- CK3: living-character count (community reports; unverified).
- Confirm: load the same save, run at top speed for a fixed real time, compare in-game days passed. Do not trust
  the FPS counter: the sim, not rendering, is the limit.

## Tier 1: config and launch options
- **No verified performance launch options.** The only launch options found are debug ones that hurt speed:
  HoI4 `-debug`, and `-crash_data_log` which "slows down the game by a significant amount"
  ([HoI4 wiki](https://hoi4.paradoxwikis.com/Troubleshooting)). Remove them if present.
- **Game setup (before the game starts).** Stellaris: Galaxy Size (200 to 1000 stars), Habitable Worlds
  (Rare to 5x), AI Empires, and two documented late-game costs: Logistic Growth Ceiling ("higher values negatively
  affect late-game performance") and Growth Required Scaling ("lower values negatively affect")
  ([wiki](https://stellaris.paradoxwikis.com/Game_settings), flagged as last verified for 4.4). Trade-off: smaller
  galaxy, fewer habitable planets and fewer AIs reduce what the game can simulate.
- Vic3 and CK3 have no equivalent verified game-rule toggle for performance.
- Windows power plan: one CK3 forum thread reports big gains moving from power-saver to balanced
  ([thread](https://admin-forum.paradoxplaza.com/forum/threads/fluctuating-performance.1625212/latest)), anecdotal
  but cheap to check.
- Graphics settings rarely help late game (player reports); lowering them is for GPU-bound scenes only.

## Tier 2: drop-in community fixes and runtime swaps
Performance mods for these games all work the same way: they simulate less (fewer pops, characters or units, fewer
animations), so they change gameplay. Search the game's Workshop/Nexus for "performance" and treat every speed claim
as the author's until the fixed-save test confirms it. Two long-lived examples:

| Game | Mod | Trade-off |
|---|---|---|
| HoI4 | Expert AI | the AI builds fewer, better divisions; the author says it is slower early and lags less late |
| CK3 | Population Control (Workshop) | culls unimportant characters; it can remove ones you wanted (pin them) |

- Install: a folder in `Documents/Paradox Interactive/<Game>/mod/` with a `.mod` descriptor, or Workshop. Remove:
  disable in the launcher. Mods can break saves or multiplayer sync, and some disable achievements (per game,
  unverified). Single-player only.

## Tier 3: code-level patches
- Everything is script, so the lever is *less simulated state*: fewer pops/characters/units, fewer scripted
  pulses, cheaper triggers. Vic3 splits work into yearly, monthly, weekly, daily and regular ticks (Dev Diary #76),
  so a heavy scripted pulse is cheaper moved to a coarser tick (plausible, unverified).
- CK3 forum tip: raise the health penalty for wandering characters so unimportant ones die sooner; one player
  reported staying under about 24,000 characters (anecdotal).
- There is no public profiler. Measure with the fixed-save top-speed test above, one change at a time.
- Why it cannot be solved by hardware or flags alone: the engine is the limit; Paradox's own fixes are
  structural (Stellaris pop groups, Vic3 pop merging) and ship in patches.

## Gotchas
- Slowdown returns after a patch -> a content/AI patch added work (Vic3 1.6 case above) -> update the mod or lower
  the setup scale.
- `-debug` left in launch options -> constant logging cost -> remove it.

---

# Haxe / OpenFL / HaxeFlixel, and Defold

Short sections: only verified items. Shipped builds bake most settings in at build time, so source is usually
needed for anything beyond asset swaps.

## Haxe / OpenFL / HaxeFlixel
**Identify.** `assets/` folder plus a native exe, or an HTML5 build (then use the Electron/NW.js section above).
Some games embed Polymod (`misc-engines.md`).
- Frame rate in HaxeFlixel: `FlxG.drawFramerate` and `FlxG.updateFramerate` are separate; `FlxG.fixedTimestep`
  is `true` by default ("changing this can lead to issues with physics"); `FlxG.maxElapsed` default 0.1 s
  ([FlxG](https://api.haxeflixel.com/flixel/FlxG.html)).
- Lime window config has `fps`, `vsync`, `hardware`, `antialiasing`, `allowHighDPI` fields
  ([WindowData.hx](https://github.com/openfl/lime/blob/develop/src/lime/tools/WindowData.hx); the defaults are
  `fps: 0`, `hardware: false`, `vsync: false`). They come from `project.xml` at build time; a shipped game cannot
  change them without a rebuild or an in-game options screen.
- Tier 2/3: none verified beyond asset overrides. For a profiler, use the target's own (the DevTools panel for
  HTML5, or a native profiler for hxcpp). (unverified)

## Defold
**Identify.** `game.arcd` / `.arci` archives, Lua scripts (`misc-engines.md`).
- `game.project` [display] settings: `swap_interval` (default 1, `0` disables vsync; `vsync` is deprecated),
  `update_frequency` (Hz; `0` for variable frame rate), `high_dpi`; [Engine] has "Max Time Step"
  ([project settings](https://defold.com/manuals/project-settings/)). These are compiled into the bundle;
  changing them needs the source project (unverified how the archive stores them).
- Profiling ([manual](https://defold.com/manuals/profiling/)): `profiler.enable_ui(true)` shows an on-screen
  profiler; "Debug > Open Web Profiler" (Remotery) shows frame timelines. The profiler is compiled in only if the
  App Manifest Profiler setting allows it ("Debug Only" is the default), so a release build usually has none.
  `profiler.track_detailed_memory` is off by default and "can be expensive on HTML5".
- Trade-off of lowering `update_frequency`: logic and physics run less often; do it only when the game is
  frame-rate-independent (unverified per game).

---

Related: [GameMaker manual](https://manual.gamemaker.io/), [NW.js docs](https://docs.nwjs.io/),
[Electron docs](https://www.electronjs.org/docs/latest/), [Ren'Py docs](https://www.renpy.org/doc/html/).
