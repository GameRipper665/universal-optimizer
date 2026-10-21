# Source 1 and Source 2

**Identify.** Source 1 uses a game-specific `gameinfo.txt`, VPK archives and engine binaries.
Source 2 uses `game/<mod>/gameinfo.gi` and, on Windows, `game/bin/win64/engine2.dll`.
Use the [companion's Source reference](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/source.md)
to identify the game folder and its supported modding route. Do not infer the renderer or executable architecture from the engine name.

Verified against upstream documentation on 2026-10-21. Record the installed build, branch, OS and renderer before testing.
For online multiplayer, including CS2 and TF2, use only official settings and supported launch options.
Never inject DLLs, replace graphics runtimes, change anti-cheat configuration or apply code patches to an online client.
The community configuration and code sections below apply only to isolated offline play or server-side work on a server the user hosts.

**Where the time usually goes.** Treat these as profiling hypotheses, not automatic diagnoses:

- Main-thread entity and script work: compare the same offline scene with optional addons disabled.
  In an instrumented Source SDK mod, use the engine's `VPROF_BUDGET` scopes to identify expensive work.
  [Valve example](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/player_lagcompensation.cpp)
- Render submission and materials: compare resolution changes with material-queue changes separately.
  Little improvement at lower resolution suggests investigating CPU work rather than lowering every visual setting.
  [Material queue definition](https://wiki.facepunch.com/gmod/ConVars_In_Garrysmod)
- GPU shading and bandwidth: repeat a fixed camera route at two resolutions and texture-quality settings.
  Compare GPU time and memory residency, not just average FPS. [DXVK diagnostic counters](https://github.com/doitsujin/dxvk#hud)
- First-use shader compilation: compare cold and warmed repetitions separately.
  DXVK's pipeline compilation can move work to loading time; this is not a promise of zero stutter.
  [DXVK pipeline documentation](https://github.com/doitsujin/dxvk#graphics-pipeline-library)
- Address-space pressure in addon-heavy GMod: compare crashes and process memory between official 32-bit and 64-bit launches.
  The 64-bit update targets this limit; it does not promise lower RAM consumption.
  [Facepunch's explanation](https://gmod.facepunch.com/news/september-2026-update)

## Tier 1: config and launch options (no files added)

### Configuration and a repeatable baseline

Use Steam's game Properties to edit launch options. A `-` option is an engine startup argument;
a `+` command executes a supported console command. Do not assume every console command can run at startup.
[Steam's documentation](https://help.steampowered.com/en/faqs/view/7D01-D2DD-D75E-2955)

For TF2, an existing personal configuration normally lives at `<TF2>/tf/cfg/autoexec.cfg`.
With mastercomfig, its supported override location is `<TF2>/tf/cfg/overrides/autoexec.cfg`.
That distinction matters because later configuration execution can overwrite earlier values.
[Author's installation instructions](https://docs.comfig.app/latest/setup/install/)

Tier 1 edits existing configuration only. If no autoexec exists, use the console for the experiment;
creating a persistent personal config is a separately recorded file addition, not a prerequisite for optimization.
For other Source games, resolve their own game folder first; do not put TF2 configuration into CS2.
[Companion's folder identification](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/source.md)

An example experiment is `+fps_max 120`, or `fps_max 120` inside an existing config.
The value is a chosen test target, not a universal optimum. A sustainable cap reduces excess work but limits peak FPS.
`fps_max 0` removes the cap on the documented Source branches; it can increase power use and worsen pacing under saturation.
Verify the actual value and frame-time trace after launch. [TF2 console definitions](https://docs.comfig.app/latest/tf2/cvarlist_win/)
Current TF2 documentation says `fps_max` cannot be changed while connected to a server; set it before connecting.
For diagnostics, mastercomfig documents `tf/vprof_spikes.log` for its spike logger; diagnostic logging adds overhead and files.
Enable it only during an offline capture, outside the no-new-files Tier 1 baseline.
[Logger documentation](https://docs.comfig.app/latest/customization/custom_configs/)

TF2 already executes autoexec at startup; repeatedly adding `+exec autoexec` is unnecessary there.
Keep one owner for the cap and graphics overrides. Restore the original values to undo the experiment.
[Author's correction of duplicated execution](https://docs.comfig.app/latest/tf2/misconceptions/)

### Useful flags, harmful defaults and obsolete advice

- `-novid`: skips the startup video in TF2. It saves startup time, not in-match frame time; the trade-off is losing the intro.
  Do not advertise it as a CS2 FPS fix. [Current TF2 launch guide](https://docs.comfig.app/latest/customization/launch_options/)
- `-high`: requests high Windows process priority on supporting Source builds, not a faster CPU or extra cores.
  It can starve competing work and reduce performance. Leave it out of the baseline.
  [TF2 warning](https://docs.comfig.app/latest/tf2/misconceptions/), [Windows priority semantics](https://learn.microsoft.com/en-us/windows/win32/procthread/scheduling-priorities)
- `-threads`: overrides engine worker selection where supported. It does not parallelize game logic.
  Prefer automatic selection; do not copy the logical-core count or the CS2 “cores plus one” recipe between branches.
  [TF2 author's warning](https://docs.comfig.app/latest/tf2/misconceptions/)
- `mat_queue_mode`: Source 1's material queue control uses `-1` for default, `0` for synchronous single-thread operation,
  and `2` for queued multithreading. GMod's published list reports `2` already; forcing it again buys nothing.
  Test only if the active value differs. Queuing may change latency or expose addon/rendering problems.
  [Facepunch console definitions](https://wiki.facepunch.com/gmod/ConVars_In_Garrysmod)
- `cl_forcepreload`: do not add it. The TF2 author documents its removal and its association with hitching.
  A name still existing in an older fork would not establish a benefit. Do not substitute `sv_forcepreload`.
  [Explanation](https://docs.comfig.app/latest/tf2/misconceptions/)

### TF2: current 64-bit and renderer behavior

Valve added 64-bit Windows/Linux client and server support on April 18, 2024.
Use the official current executable rather than an old binary bundle. [Valve announcement](https://www.teamfortress.com/post.php?id=220436)

On Windows, current mastercomfig documentation still recognizes `-dxlevel 90` and the higher-quality `-dxlevel 100` route.
These select Source shader/feature levels; “100” does not mean a Direct3D 10 renderer.
Lower quality trades rendering features for possible GPU savings, not guaranteed CPU improvement.
[Current launch guide](https://docs.comfig.app/latest/customization/launch_options/)

The same guide supports TF2's built-in `-vulkan` route through DXVK.
Its prerequisite is a launch with `-dxlevel 95`; remove the `-dxlevel` argument afterward before testing Vulkan.
Leaving that argument in place can reset graphics settings. Avoid old DX8 presets, especially with Vulkan.
Trade-offs include driver-dependent performance, compilation work and possible compatibility regressions.
[Renderer instructions and DX8 warning](https://docs.comfig.app/latest/customization/launch_options/)

This built-in renderer is distinct from downloading a replacement DLL.
For online TF2, retain only the official renderer option; do not install an external DXVK build.
Measure the same route with each backend and restart between tests.

### Half-Life 2: do not confuse it with Half-Life 2: Deathmatch

Valve's November 18, 2022 HL2 update already updated its bundled DXVK to 2.0.
Thus Vulkan support is not evidence of a 2024–2025 64-bit conversion.
[Valve update feed](https://store.steampowered.com/news/posts/?appids=220&enddate=1668817906&feed=steam_community_announcements)

Source's documented `-vulkan` path requires a compatible feature level; DX8 settings can cause corruption or crashes.
Use a one-time `-dxlevel 95` reset where the installed Source branch supports it, then remove the reset argument.
The trade-off is reinitializing graphics settings; preserve their old values first.
[Valve developer documentation](https://developer.valvesoftware.com/wiki/DirectX_Versions?mobile-app=true&theme=dark)

The claim that retail single-player HL2 received TF2's 2024–2025 64-bit update is **(unverified)**.
Do not prescribe x64 replacement DLLs on that assumption. Valve's multiplayer update named HL2:DM separately.
Check the executable's architecture and the actual loaded renderer on the user's installation.
[Valve's multiplayer announcement](https://www.teamfortress.com/)

### Garry's Mod: branch advice has changed

As of September 16, 2026, official 64-bit Windows binaries are available on every branch;
the Steam launch selector chooses the 64-bit client. Switching to the `x86-64` beta is no longer necessary solely for that.
Use the beta only for its documented differences, with a backup and addon compatibility check.
The benefit is greater address space; costs can include larger memory use and incompatible native addons.
[Facepunch update](https://gmod.facepunch.com/news/september-2026-update)

The `x86-64` branch also has Chromium-related differences; inspect the branch's current description rather than treating it as a preset.
[Facepunch web-renderer documentation](https://wiki.facepunch.com/gmod/HTML_Web_Engine)

`-noaddons -noworkshop` is an official diagnostic pair for local tests: it disables legacy/folder and Workshop addons respectively.
The trade-off is missing addon content and functionality. Remove the flags to restore normal loading.
[Facepunch launch parameters](https://wiki.facepunch.com/gmod/Command_Line_Parameters)

GMod support for TF2's exact `-vulkan`/`-dxlevel` recipe on current branches is **(unverified)**.
Do not transfer it. Use GMod's video menu and official branch notes; 64-bit support alone says nothing about Vulkan.
[Current branch announcement](https://gmod.facepunch.com/news/september-2026-update)

### Source 2

CS2 personal autoexec files belong at `<CS2>/game/csgo/cfg/autoexec.cfg`, not the old CS:GO `csgo/cfg` location.
If one exists, edit only supported native commands there; do not import the rest of somebody else's preset.
[Maintained configuration author's folder instructions](https://github.com/maxgry/autoexec)

CS2 still supports `fps_max`; Valve's August 2025 changes prevent modifying it while connected to a server.
Set the cap before connecting, through the menu/console or a startup command such as `+fps_max 120`.
This trades peak throughput for a sustainable load; restore the prior value to undo.
[Valve's release notes](https://store.steampowered.com/news/posts/?appids=730&enddate=1758150954&feed=steam_community_announcements),
[Steam's command-at-startup syntax](https://help.steampowered.com/en/faqs/view/7D01-D2DD-D75E-2955)

CS2, Dota 2 and other online Source 2 clients stay on official graphics menus and documented launch options.
Use their own FPS limit, resolution and quality controls, and record the visual trade-off of each reduction.
Do not paste `mat_queue_mode`, `cl_forcepreload`, `-dxlevel` or a TF2 autoexec into Source 2.
The companion identifies these as a different engine/toolchain, not a compatible Source 1 configuration target.
[Source 2 identification](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/source.md)

## Tier 2: drop-in community fixes and runtime swaps

### mastercomfig — TF2, offline configuration experiments

Use the [mastercomfig/comfig generator](https://comfig.app/app/) and choose a preset close to the user's visual requirements.
Lower presets reduce detail; they cannot guarantee a gain on a CPU-limited scene or repair server-side slowdown.
Install the generated `tf` folder into the TF2 installation and preserve personal configs in the documented overrides folder.
[Installation](https://docs.comfig.app/latest/setup/install/), [customization](https://docs.comfig.app/latest/customization/custom_configs/)

Keep the downloaded archive's file manifest. Remove only its installed files and restore the earlier configs to roll back.
Values may persist in saved configuration after a VPK is removed; compare against the backup after relaunching.
The author's full reset is destructive to settings, so use it only when a complete reset is wanted.
[Reset behavior](https://docs.comfig.app/latest/setup/clean_up/)

### DXVK — older offline Source games without a satisfactory bundled backend

[DXVK](https://github.com/doitsujin/dxvk) translates Direct3D to Vulkan. Treat it as an A/B experiment when driver submission is costly.
Prefer a game's bundled Vulkan implementation; do not replace its DLLs merely to chase a newer version number.
For a verified Direct3D 9 target, the required library is `d3d9.dll`, with architecture matching the game process.
Use a game-local deployment documented for that title, never a system-wide DLL replacement.
[Upstream API/library mapping](https://github.com/doitsujin/dxvk#dll-dependencies)

Windows use is a compatibility experiment, not an upstream performance guarantee.
Check [driver requirements](https://github.com/doitsujin/dxvk/wiki/Driver-support); compare warmed runs and visual correctness.
Trade-offs include shader compilation, altered memory use and rendering bugs. Restore any original DLL and remove only the added files to undo.
No external DXVK in online games. [Upstream multiplayer warning](https://github.com/doitsujin/dxvk#online-multi-player-games)

## Tier 3: code-level patches (profile -> patch the hot path)

Reuse the companion's [Source SDK, VScript, GMod Lua and server-plugin routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/source.md).
Its broader multiplayer guidance does not override this playbook's stricter online-client restriction.
For an owned SDK mod, instrument candidate functions with `VPROF_BUDGET` and retain symbols.
Valve's [SDK implementation](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/server/player_lagcompensation.cpp)
shows early exits and avoiding unnecessary per-frame work; it is a profiling example, not a reason to alter network behavior.

For GMod addon work, measure repeated queries before caching them. Facepunch documents that `ents.GetAll()` creates a table;
`ents.Iterator()` offers cached iteration. Keep entity lifetime invalidation correct and measure the actual callback cost.
[GetAll](https://wiki.facepunch.com/gmod/ents.GetAll), [Iterator](https://wiki.facepunch.com/gmod/ents.Iterator)

For owned maps, reduce unnecessary visibility and render work using the existing Hammer route.
Compare the same camera positions before and after geometry/visibility changes; inspect missing surfaces as well as FPS.
Valve's [visibility optimization documentation](https://developer.valvesoftware.com/wiki/Visibility_optimization)
is the route for map-level work, not a license to disable visibility globally.

## Gotchas

- Settings revert on launch -> a reset flag or later config wins -> remove persistent `-dxlevel` and inspect execution order.
  [Launch guide](https://docs.comfig.app/latest/customization/launch_options/)
- Vulkan looks slower on its first run -> compilation may dominate -> compare cold and warm results separately.
  [DXVK compilation](https://github.com/doitsujin/dxvk#graphics-pipeline-library)
- 64-bit GMod still stalls -> address space was not the only limit -> isolate addons and remeasure.
  [Official isolation flags](https://wiki.facepunch.com/gmod/Command_Line_Parameters)
- Config “boost” changes nothing -> unsupported or already-default commands -> query the active value and remove the placebo.
  Do not add RAM cleaners, registry recipes or working-set purges. They do not remove the measured engine workload.
