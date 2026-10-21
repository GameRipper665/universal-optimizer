# Bethesda: Gamebryo, Creation Engine and Creation Engine 2

**Identify.** Match the executable to its `Data` masters and BSA/BA2 archives before choosing tools.
Skyrim LE, Skyrim SE/AE, Fallout 3/New Vegas, Fallout 4 and Starfield are separate binary targets.
Use the [companion's Bethesda identification and modding routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/bethesda.md).
An “AE” purchase or collection name is not a runtime version. Record the executable version, storefront, extender and native plugins.

Verified on 2026-10-21. These instructions are for the user's single-player installations.
Fallout 76 and other online clients are limited to official settings; do not inject DLLs or change anti-cheat or DRM.
Keep a separate mod-manager profile and a pre-change save. Never remove script-bearing mods from the only copy of a campaign.

**Where the time usually goes.** Confirm the bottleneck before applying a fix:

- Main/render-thread work: repeat a crowded exterior at two resolutions; flat FPS despite a large resolution reduction merits CPU investigation.
  Skyrim Engine Fixes has concrete form-lookup and tree-LOD caching patches, rather than a generic “use more cores” switch.
  [Patch definitions](https://github.com/aers/EngineFixesSkyrim64/blob/master/Skyrim/Data/SKSE/Plugins/EngineFixes.toml)
- Physics/presentation timing: compare frame times and game speed, not just the displayed FPS number.
  [SSE Display Tweaks](https://www.nexusmods.com/skyrimspecialedition/mods/34705) and
  [FO4 High FPS Physics Fix](https://www.nexusmods.com/fallout4/mods/44798) address specific timing defects.
- Texture residency: compare hitch locations and VRAM budget before and after a smaller texture set.
  [Cathedral Assets Optimizer](https://github.com/Guekka/cathedral-assets-optimizer) provides texture conversion/optimization, not free memory.
- Papyrus workload: correlate script activity with the scene; a large log is not itself a CPU profile.
  [Papyrus Profiler](https://github.com/DennisSoemers/PapyrusProfiler) records function activity for analysis.
- Fallout 4 visibility/draw calls: compare an affected cell with and without the conflicting world edits.
  Broken precombines/previs can defeat the engine's batching and visibility optimizations.
  [Precombine author documentation](https://www.nexusmods.com/fallout4/articles/4316)

## Tier 1: config and launch options (no files added)

### Locate the active files; preserve the current values

- Skyrim SE/AE: `Documents/My Games/Skyrim Special Edition/Skyrim.ini`, `SkyrimPrefs.ini` and `SkyrimCustom.ini`.
  These are the paths used by [Bethini's Skyrim SE plugin](https://github.com/DoubleYouC/Bethini-Pie-Skyrim-Special-Edition-Plugin/blob/master/settings.json).
- Fallout 4: `Documents/My Games/Fallout4/Fallout4.ini`, `Fallout4Prefs.ini` and `Fallout4Custom.ini`.
  The folder is **Fallout4**, without a space. [Bethesda support](https://help.bethesda.net/app/answers/detail/a_id/31475/)
- Starfield: `Documents/My Games/Starfield/StarfieldPrefs.ini` and `StarfieldCustom.ini`.
  [Bethesda support](https://help.bethesda.net/app/answers/detail/a_id/66619/)

“Documents” means the user's actual Documents location, including redirection where applicable.
If the mod manager supplies profile-specific INIs, edit those instead of an inactive global copy.
Confirm the target by changing one menu setting, exiting normally and checking which existing file changed.
Do not create several competing override files or copy a complete INI from another machine.

### Skyrim SE/AE and Fallout 4: reduce actual rendering work

In Skyrim SE/AE's existing `SkyrimPrefs.ini`, `[Display] fShadowDistance` controls shadow reach,
and `iShadowMapResolution` controls shadow-map detail. A trial of `fShadowDistance=3000`
or `iShadowMapResolution=2048` uses documented preset values, not magic performance numbers.
Shorter reach causes earlier shadow disappearance; smaller maps lose shadow detail.
Test each change separately. [Bethini's setting/preset definitions](https://github.com/DoubleYouC/Bethini-Pie-Skyrim-Special-Edition-Plugin/blob/master/settings.json)

Fallout 4's `Fallout4Prefs.ini` exposes the same two names under `[Display]`.
Their appropriate distances differ from Skyrim; lower the active value incrementally rather than copying Skyrim's whole section.
The same visual trade-offs apply. [FO4 definitions](https://github.com/DoubleYouC/Bethini-Pie-Fallout-4-Plugin/blob/master/settings.json)

Do not present `[Display] iPresentInterval=0` in FO4 as a complete high-FPS fix.
It changes synchronization, not every physics/animation dependency. Keep ordinary capped gameplay until a matching timing fix is installed.
Disabling synchronization can introduce tearing and excess GPU work.
[Setting definition](https://github.com/DoubleYouC/Bethini-Pie-Fallout-4-Plugin/blob/master/settings.json),
[timing fix scope](https://www.nexusmods.com/fallout4/mods/44798)

Keep `[General] bUseCombinedObjects=1` in FO4's effective INI configuration.
Setting it to `0` disables precombines globally and defeats much of previs; it is not a performance optimization.
The price of retaining batching is that arbitrary object-removal mods need proper rebuilt data and compatibility patches.
[Precombine/previs explanation](https://www.nexusmods.com/fallout4/articles/4316)

### Starfield: a small verified INI surface

Use the game's display menu first, then verify the saved values in `StarfieldPrefs.ini`.
Bethini's Starfield plugin identifies `[Display] fRenderResolutionScaleFactor` and `bEnableVsync` there.
For example, a render-scale experiment from `1.0` to `0.75` lowers internal resolution;
the trade-off is reconstruction softness and artifacts, and it will not remove a CPU limit.
`bEnableVsync=0` allows unsynchronized presentation, trading tearing/excess work for different latency behavior.
[Author-maintained Starfield schema](https://github.com/DoubleYouC/Bethini-Pie-Starfield-Plugin/blob/master/settings.json)

The same schema puts `[ContactShadows] bContactShadowsEnabled` in the quality-preset files, not in that Preferences section.
Use Bethini or the game menu to generate the intended preset rather than scattering copied keys into `StarfieldCustom.ini`.
Turning contact shadows off loses small-scale contact shading; measure GPU time before retaining the reduction.
[Setting ownership and presets](https://github.com/DoubleYouC/Bethini-Pie-Starfield-Plugin/blob/master/settings.json)

No giant “threading,” heap or preload INI is recommended. A recognized name alone does not prove a current performance benefit.
Restore the earlier files after each failed experiment; preserve bindings when resetting configuration.
[Bethesda's reset guidance](https://help.bethesda.net/app/answers/detail/a_id/66619/)

### Older games and Oblivion Remastered

For Skyrim LE, Fallout 3/New Vegas and original Oblivion, start with each game's own launcher presets and resolution.
Lower detail and shorter distances cost visual fidelity. Keep the original frame cap until the game's matching timing fix is verified.
Never copy SE DLLs or Fallout 4 INI sections into these titles.
[Extender/runtime separation](https://skse.silverlock.org/), [NVTF's specific target](https://github.com/carxt/New-Vegas-Tick-Fix)

Oblivion Remastered keeps original gameplay/world logic underneath an Unreal Engine 5 visual layer.
Treat its graphics settings as a distinct UE5 target; classic Oblivion's OBSE plugins and renderer tweaks are not interchangeable.
[Bethesda's engine description](https://elderscrolls.bethesda.net/en-ZA/news/5tFF7zRQyRL9XzJK5AidPa/the-elder-scrolls-iv-oblivion-remastered-extended-look)

## Tier 2: drop-in community fixes and runtime swaps

### Runtime matching is mandatory

The SKSE team currently lists classic SKSE 1.7.3 for Skyrim LE, SKSE64 2.0.20 for SE 1.5.97,
and separate Anniversary/GOG builds. As checked, Steam's current AE listing is game 1.7.104,
while GOG's listing is 1.6.1179. Do not assume that “latest AE” still means Steam 1.6.1170.
Use the archived build matching a retained 1.6.x installation. [SKSE team's download page](https://skse.silverlock.org/)

The F4SE team lists 0.6.23 for FO4 1.10.163, 0.7.2 for next-gen 1.10.984,
and 0.7.9 for 1.11.240. Extender support alone does not certify every plugin.
Do not force unsupported storefronts through executable conversion or DRM changes.
[F4SE team's runtime table](https://f4se.silverlock.org/)

### Skyrim: Engine Fixes and Display Tweaks

**SSE Engine Fixes**, credited to aers, Nukem and Ryan, repairs engine defects and includes caching improvements.
Its current main file names SE 1.5.97 and AE 1.6.1170+; older 1.6.x releases require the corresponding archived files.
The optional all-in-one packages and the main-plugin-plus-preloader route are alternatives, not cumulative requirements.
[Author's downloads and compatibility notes](https://www.nexusmods.com/skyrimspecialedition/mods/17230?tab=files)

Install the matching Address Library and follow the selected package's layout.
The separate SKSE64 preloader belongs in the game root, not `Data`; the AIO can be extracted to the game root.
Retain the archive manifest and restore prior files to uninstall. Do not mix old “Part 2” instructions with a different-generation package.
The trade-off is runtime-sensitive native code and potential conflicts with overlapping fixes.
[Package instructions](https://www.nexusmods.com/skyrimspecialedition/mods/17230?tab=files)

**SSE Display Tweaks**, by SlavicPotato, addresses presentation, high-FPS physics and frame limiting.
Its changelog covers AE 1.6.629, GOG 1.6.659 and 1.6.1130, and now also the 1.7.x line.
Use its current matching release and Address Library; do not install it into Skyrim LE.
[Author page and changelog](https://www.nexusmods.com/skyrimspecialedition/mods/34705)

Install through the manager using the archive's `Data` layout.
The documented persistent override is `Data/SKSE/Plugins/SSEDisplayTweaks_Custom.ini`.
For an existing installation, `[Render] FramerateLimit=120` is a reasonable measurement target, not a requirement.
Use one limiter; a higher limit increases hardware load. Borderless flip presentation can change overlay compatibility.
[Override location](https://www.nexusmods.com/skyrimspecialedition/mods/34705),
[annotated INI](https://github.com/SlavicPotato/SSEDisplayTweaks/blob/master/SSETweaks/SSEDisplayTweaks.ini)

To remove Display Tweaks, disable its files and restore the original cap/synchronization configuration before loading a save.
Do not stack it with another Havok timing plugin. Its author explicitly lists Havok Fix as incompatible.
[Compatibility](https://www.nexusmods.com/skyrimspecialedition/mods/34705)

### Fallout 4: separate stability, timing and visibility repairs

**Buffout 4 NG and VR**, maintained by alandtse from the original Buffout 4 project,
explicitly supports 1.10.163, 1.10.984 and VR. It explicitly does **not** support the Anniversary Edition runtime.
The page directs Anniversary users to Addictol; that is a separate project to evaluate, not an interchangeable Buffout binary.
Read the next-gen status report: not every legacy patch is active on 1.10.984.
[Maintainer's compatibility statement](https://www.nexusmods.com/fallout4/mods/64880)

Install its matching release and listed dependencies through the manager, following the selected archive's layout.
Use the crash logger to investigate faults; a crash log alone does not show that FPS improved.
Native allocator and engine patches can conflict with other fixes, so retain defaults until a measured reason requires a change.
Remove the plugin's own files to undo, restoring overwritten dependencies only if no remaining mod needs them.
[Project and releases](https://github.com/alandtse/Buffout4)

**High FPS Physics Fix**, by Antonix35, is the FO4 timing/presentation fix.
The author documents 1.10.980 support from 0.8.7 and 1.10.984 from 0.8.10;
current requirements also include 1.11.159–1.11.240. Select the file for the actual runtime, with matching F4SE/Address Library.
Install its archive through the manager or according to the author's manual layout.
[Author's requirements, release history and installation](https://www.nexusmods.com/fallout4/mods/44798)

Use its bundled configuration for gameplay and loading-screen limits; do not import an old release's entire INI.
Higher loading-screen FPS may shorten waits, but increases transient load and needs testing of transitions/new-game startup.
To remove it, disable the plugin and restore capped vanilla timing first.
[Configuration and fixes](https://www.nexusmods.com/fallout4/mods/44798)

**Previsibines Repair Pack Stable Branch — PRP**, by BenRierimanu, repairs/rebuilds visibility and combined geometry.
Choose the distribution and compatibility patches for the installed game data and world-editing mods.
Its files distinguish legacy/GOG-era data from newer builds; a compatible executable is not enough.
[Project](https://www.nexusmods.com/fallout4/mods/46403), [version-specific downloads](https://www.nexusmods.com/fallout4/mods/46403?tab=files)

Install in a separate profile through a manager. Inspect cell conflicts before testing affected locations.
Trade-offs are additional disk/data requirements and a compatibility burden with settlement or world edits.
Undo by restoring the previous profile and its save, including the previous visibility assets; do not leave orphaned patches active.
[Author's conflict/installation documentation](https://www.nexusmods.com/fallout4/mods/46403)

### Fallout: New Vegas

Use **xNVSE**, maintained by the xNVSE team, as the current script-extender route.
Its README supports Steam/GOG and separates unsupported editions. Install its DLL/EXE files beside `FalloutNV.exe`, not in `Data`.
It is infrastructure, not an FPS boost by itself. Remove only its installed files to undo, after disabling dependent plugins.
[Official project](https://github.com/xNVSE/NVSE)

**NVTF — New Vegas Tick Fix** credits Carxt, Tgspy, lStewieAl and WallSoGB.
It fixes tick-count stutter, optimizes expensive functions and handles high-FPS timing.
Install the release with a mod manager; keep the bundled DLL and INI together in its plugin layout.
Remove New Vegas Stutter Remover first: the author explicitly warns that they clash.
Renderer options may affect compatibility; start with the shipped defaults and test. Disable NVTF and restore the cap to roll back.
[Author's project page](https://www.nexusmods.com/newvegas/mods/66537)

**JIP LN NVSE Plugin**, from jazzisparis and LuthienAnarion, supplies engine fixes and additional script functions.
Treat it as a dependency/bug-fix layer, not a standalone FPS guarantee.
Install the release through the manager and check dependent mods before removing it.
[Author repository](https://github.com/jazzisparis/JIP-LN-NVSE), [release page](https://www.nexusmods.com/newvegas/mods/58277)

**FNV 4GB Patcher**, by Roy Batty and LuthienAnarion, makes supported executables Large Address Aware and can auto-load xNVSE.
This raises address-space availability on a suitable 64-bit OS; it does not convert the game to 64-bit or reduce RAM use.
GOG is already LAA; its additional patching benefit is extender loading. The author supports Steam/GOG, not every storefront.
[Author's description](https://www.nexusmods.com/newvegas/mods/62552)

Back up the owned executable, use the matching patcher from its release page and retain its unpatched backup.
Restore the original executable to undo. Do not use a replacement executable or a DRM-removal tool to make an unsupported edition fit.
The trade-off is an on-disk executable change that updates/verification can overwrite.
[Patcher instructions](https://www.nexusmods.com/newvegas/mods/62552)

### Fallout 3 and original Oblivion

For Fallout 3, **High FPS Physics Fix** by c6-dev is a separate project from Antonix35's FO4 plugin.
It recommends no more than 120 FPS and includes the functionality of Fallout 3 Tick Fix and Stewie's tick option.
Do not stack those fixes. Establish support for the installed FOSE/runtime before installation; otherwise keep the official cap.
Install/remove only the selected release's files, restoring capped timing when removing it.
[Author's README](https://github.com/c6-dev/fose-fps-fix)

For original Oblivion, **Oblivion Display Tweaks**, by Ersh/Ershin, is an OBSE plugin with tick and high-framerate fixes.
Use the author's package and its OBSE dependency, with a separate profile; it is not for Oblivion Remastered.
Its optional D3D9Ex changes have compatibility/performance trade-offs, so test rather than enabling every option.
Uninstall its package and restore the original frame cap to undo.
[Author's description and requirements](https://www.nexusmods.com/oblivion/mods/50348)

### INI generation, texture optimization and “precache” claims

**Bethini Pie (Performance INI Editor)** is maintained by DoubleYou/DoubleYouC.
Select the plugin for the actual game and active profile, back up the INIs, choose a preset and inspect the diff.
Lower presets spend visual quality for reduced work; Recommended is a baseline, not a benchmark result.
Rollback means restoring the INIs, not merely deleting the editor.
[Author repository and download link](https://github.com/DoubleYouC/Bethini-Pie-Performance-INI-Editor)

**Cathedral Assets Optimizer**, by G_k/Guekka, handles supported Bethesda asset conversion, texture processing and archive creation.
Process a copy of a texture mod using the correct game profile; deploy the output as an isolated override.
Downscaling/compression can reduce residency and streaming cost but loses detail or introduces compression artifacts.
Keep source assets; undo by disabling the generated override. Do not batch-convert the only copy of the game.
[Project](https://github.com/Guekka/cathedral-assets-optimizer), [author release](https://www.nexusmods.com/skyrimspecialedition/mods/23316)

Archive optimization is not a universal shader precache. Keep warm/cold measurements separate and do not routinely purge caches.
Avoid “preload everything” prescriptions that simply move stalls or consume more address space.

## Tier 3: code-level patches (profile -> patch the hot path)

Reuse the companion's [xEdit, Creation Kit, Papyrus and native-extender routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/bethesda.md).
For Skyrim scripts, [Papyrus Profiler](https://github.com/DennisSoemers/PapyrusProfiler) reveals call frequency and stack activity;
instrument durations separately before labeling a frequent function CPU-expensive. Check its binary requirements before installation.
For native code, collect sampled call stacks with [Windows Performance Recorder/Analyzer](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/)
and symbols for the plugin being changed. A Papyrus trace cannot diagnose a renderer stall.

Three established patterns justify targeted work: cache repeated form/tree-LOD lookups with correct invalidation
([Engine Fixes source](https://github.com/aers/EngineFixesSkyrim64)); repair tick/timestep handling rather than merely lifting a cap
([NVTF source](https://github.com/carxt/New-Vegas-Tick-Fix)); and regenerate matching precombine/previs data after owned cell edits
([author's build explanation](https://www.nexusmods.com/fallout4/articles/4316)).
Keep patches version-gated and compare the same save, route and warmed state before accepting a result.

## Gotchas

- Startup crash after an update -> native plugin/runtime mismatch -> disable the plugin and select matching releases.
  [SKSE support guidance](https://skse.silverlock.org/)
- FO4 walls disappear or a city suddenly slows down -> conflicting cell/previs data -> restore a coherent profile and resolve the conflict.
  [Previs explanation](https://www.nexusmods.com/fallout4/articles/4316)
- A “fix” improves averages but breaks physics -> incomplete timing correction -> restore the previous cap and matching plugin setup.
  [FO4 timing-fix scope](https://www.nexusmods.com/fallout4/mods/44798)
- RAM use falls while traversal hitches increase -> eviction is not optimization -> undo the cleaner/purge and measure frame times.
  Do not use RAM boosters, registry folklore or `EmptyWorkingSet` loops as engine fixes.
