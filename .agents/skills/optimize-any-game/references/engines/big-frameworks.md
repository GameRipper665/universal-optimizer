# RE Engine, MT Framework, FromSoftware, RAGE, REDengine 4, Frostbite, CryEngine and Hedgehog Engine

**Identify.** Start with the installed title, executable version and storefront, not a framework DLL found beside it. MT Framework games commonly use `.arc` assets; Hedgehog titles use game-specific `.ar`/`.arl` or `.pac` archives.
The [companion's framework reference](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/big-frameworks.md)
provides the engine-identification and modding routes. Configuration locations below are title-specific examples.
An INI filename by itself does not prove the engine.

Verified on 2026-10-21. Record the game build, API, mod versions and baseline frame times. Online games and modes, including CS2, GTA Online, Elden Ring online, Battlefield and online Monster Hunter,
get only official settings and supported launch options. Never inject DLLs or install runtime patches there.
Do not change anti-cheat, authentication or DRM. A framework's broader instructions do not override this boundary.

**Where the time usually goes.** Use these measurements to decide which engine section matters:

- GPU effects/RT: compare the same camera at lower internal resolution and with one expensive effect changed.
  Distinguish less work from a higher generated-frame count. [Cyberpunk's official graphics changes](https://www.cyberpunk.net/en/news/49060/update-2-0)
- Main-thread scene work: compare dense streets to quiet scenes and check whether resolution changes help.
  Population and extended distance settings can amplify scene cost. [GTA V measurements](https://www.nvidia.com/en-us/geforce/news/grand-theft-auto-v-pc-graphics-and-performance-guide/)
- Streaming/residency: log hitch locations and memory budget while traversing the same route.
  Use an SSD where required; it cannot repair arbitrary CPU stalls. [Cyberpunk 2.0 requirements](https://www.cyberpunk.net/en/news/49060/update-2-0)
- Shader compilation/API overhead: record first-run and warmed results separately when switching renderers.
  [DXVK compilation behavior](https://github.com/doitsujin/dxvk#graphics-pipeline-library)
- Presentation/timing caps: compare frame times with gameplay speed and animation behavior.
  Unlocking a limiter does not make an overloaded frame cheaper. [Frontiers unlocker's documented defects](https://github.com/hedge-dev/HMMCodes/blob/main/Source/Sonic%20Frontiers/Graphics/Display/Disable%20FPS%20Limit%20%28experimental%29.hmm)

## Tier 1: config and launch options (no files added)

### RE Engine

Use the game's graphics menu first. In Monster Hunter Rise, Capcom documents `<game>/config.ini` as the graphics-settings file. Back up an existing file, change one menu option, exit normally and inspect the diff before scripting edits.
Do not transplant another RE game's section names or enum values.
[Capcom's troubleshooting thread](https://steamcommunity.com/app/1446780/discussions/1/3202622816412103096/)

For the supported Resident Evil VR configurations, REFramework's author identifies Image Quality, Shadow Quality, Screen Space Reflections, Ambient Occlusion and Subsurface Scattering as useful cost controls.
Apply only settings present in the actual game: lower resolution loses detail, shadows/reflections lose fidelity,
and disabling ambient/subsurface shading changes lighting. Do not assume the VR ordering predicts every flat-screen game's bottleneck.
[Author's graphics guidance](https://github.com/praydog/REFramework/wiki/VR-Troubleshooting)

No universal RE `config.ini` “CPU unlock” or `-dx11` prescription is supplied.
The executable's actual renderer and branch decide what is supported; use the menu and matching release notes.
[REFramework branch distinction](https://github.com/praydog/REFramework-nightly/releases)

### MT Framework

Dragon's Dogma: Dark Arisen stores configuration at `%LOCALAPPDATA%/CAPCOM/DRAGONS DOGMA DARK ARISEN/config.ini`.
Capcom's FAQ documents changing `VSYNC` to `OFF` for a specific device-lost/black-screen problem.
This is a targeted workaround, not a blanket FPS recommendation; it may introduce tearing.
The same FAQ documents a 150-FPS upper limit to avoid game-breaking behavior. Preserve that bound.
[Capcom's GOG-distributed FAQ](https://items.gog.com/dragons_dogma_faq/Dragons_Dogma_Dark_Arisen_GOG_FAQ.pdf)

For other MT titles, reduce resolution/quality in their own menus and verify the effect on the same scene.
Do not install REFramework: MT Framework and RE Engine have different asset/code routes.
[Companion's engine separation](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/big-frameworks.md)

### FromSoftware

For Elden Ring, begin with official graphics settings and its normal cap; online use stops at those settings. An external FPS unlocker is a memory patch, not an official launch option.
Its own README requires offline operation with anti-cheat absent; the pack does not make that change for the user.
Do not interpret the game's ordinary offline-network setting as proof that runtime modification is permitted.
[Unlocker author's constraints](https://github.com/uberhalit/EldenRingFpsUnlockAndMore)

For DS3 and Sekiro, preserve normal timing until a matching offline timing patch has been evaluated.
Removing synchronization can introduce tearing; raising the cap increases CPU/GPU demand rather than reducing it.
[DS3 project](https://github.com/0dm/DS3DebugFPS), [Sekiro project](https://github.com/uberhalit/SekiroFpsUnlockAndMore)

### RAGE: GTA IV, GTA V and Red Dead Redemption 2

GTA IV's FusionFix settings belong to Tier 2, not a universal RAGE launch-options list.
Start from the official game menu and a repeatable drive; avoid guessed memory-size overrides.
[FusionFix's documented scope](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix)

For **GTA V Legacy story mode**, lower Grass Quality, MSAA and Extended Distance Scaling individually. Grass/shadow detail and edge quality are the visual costs; distance reduction introduces more visible transitions/pop-in.
NVIDIA's measurements identify large costs for extended distance under busy conditions.
This guide covers the original PC renderer, not automatic equivalence with GTA V Enhanced.
[Legacy graphics guide](https://www.nvidia.com/en-us/geforce/news/grand-theft-auto-v-pc-graphics-and-performance-guide/)

Do not add story-mode loaders or modified assets to an installation being used for GTA Online.
This playbook supplies no anti-cheat-disabling flags. Enhanced needs its own official graphics-menu baseline.

RDR2 stores graphics configuration at `Documents/Rockstar Games/Red Dead Redemption 2/Settings/system.xml`. The Graphics API menu selects Vulkan or DirectX 12; the XML values are `kSettingAPI_Vulkan` and `kSettingAPI_DX12`.
Rockstar documents changing the API for initialization errors. Neither API is universally faster.
Restart, repeat the same benchmark/route, and compare steady frame times, first-run compilation and stability.
[Rockstar's API/config instructions](https://support.rockstargames.com/articles/2MQafAtBWiOUJrPDLx5I2U/err-gfx-init-error-when-launching-red-dead-redemption-2-on-pc)

Restore the original API to undo. API changes can alter driver behavior and invalidate warmed results.
Do not repeatedly delete shader caches as an “optimization”; Rockstar's cache reset is an error-recovery procedure.
[Rockstar's troubleshooting context](https://support.rockstargames.com/articles/7xzxylRbekL5tPKLaVhJbJ/red-dead-redemption-2-error-code-ffffffff)

### REDengine 4: Cyberpunk 2077

User settings live at `%LOCALAPPDATA%/CD Projekt Red/Cyberpunk 2077/UserSettings.json`.
Use the menu to produce valid JSON values; back up the existing file and do not invent flat INI equivalents.
[CDPR's settings location](https://support.cdprojektred.com/en/cyberpunk/pc/gameplay/issue/2407/i-am-experiencing-issues-with-controls)

On 2.x, Crowd Density is in Graphics and follows the quick presets unless adjusted separately. Reduce it when the dense-city test is CPU-limited; the trade-off is fewer background people.
Path Tracing/ray-tracing reductions trade lighting accuracy for GPU time; lower upscaling input resolution costs detail.
Use the same traffic/time/weather scene for comparisons. [Official 2.0 changes](https://www.cyberpunk.net/en/news/49060/update-2-0)

The old CPU SMT hex patch is not the default fix for modern builds. Patch 1.05 changed Ryzen core/thread use; 2.0 added **AMD SMT** under Settings → Gameplay → Performance,
with Off, On and Auto modes. Keep Auto as baseline; compare alternatives only on the user's CPU and workloads.
An override can improve one scene and worsen another. [1.05](https://www.cyberpunk.net/en/news/37166/hotfix-1-05),
[2.0 official switch](https://www.cyberpunk.net/en/news/49060/update-2-0)

`memory_pool_budgets.csv` was a development leftover with no effect on released memory allocation.
CDPR removed it in 1.05. Recreating it, expanding its numbers or downloading a “memory pool fix” is placebo.
[CDPR's explicit explanation](https://www.cyberpunk.net/en/news/37166/hotfix-1-05)

Actual mod INIs may live under `<game>/engine/config/platform/pc`, but that directory is not proof that a copied key works.
Treat added INIs as Tier 2 modifications and require current mod documentation plus a measurable A/B result.
[Modding documentation's file map](https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-users/users-modding-cyberpunk-2077)

### Frostbite

For online Battlefield, use official display controls only. Battlefield 2042 documents Dynamic Resolution Scale and DLSS as alternatives; its guide says they are not compatible together.
Dynamic resolution trades sharpness for more consistent frame rates. Lower ambient-occlusion quality loses contact shading.
Keep the test within the options supported by the current installed build.
[EA's PC display guide](https://www.ea.com/able/resources/battlefield-2042/pc/display)

Do not reuse old simulation-rate or thread-count command lines across Frostbite games. This playbook does not verify a universal Frostbite `user.cfg` performance preset.
For offline Dragon Age/Mass Effect titles, start with their own menus; use Frosty only after title/build support is established.
[Frosty project scope](https://github.com/CadeEvs/FrostyToolsuite)

### CryEngine

Crytek documents configuration order as `%USER%/game.cfg`, then `<root>/system.cfg`, then `<root>/user.cfg`. These are engine/SDK conventions; a retail game can restrict commands or change its configuration route.
Under Tier 1, edit only an existing file that the installed title demonstrably reads, or test through its supported console.
[Crytek configuration documentation](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/25535264)

For CryEngine 3 branches exposing these CVars, the following are documented experiments, not portable launch flags:

- `sys_MaxFPS = 60`: caps rendering when VSync is disabled; limits peak throughput while reducing excess work.
  This variable's `0` and `-1` meanings differ from Source's cap. [Crytek definition](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/9895942/pages/9215965)
- `sys_spec = 2`: selects the documented medium specification where supported; lowers multiple quality settings together.
  Use it for a baseline, then inspect individual effects rather than attributing the whole change to one bottleneck.
  [Crytek specification levels](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/9895942/pages/9215965)
- `e_ShadowsMaxTexRes = 512`: lowers shadow-map resolution relative to 1024; saves shadow resources at the cost of definition.
  Do not misspell it as a guessed `r_ShadowMaxTexRes`. [Crytek shadow reference](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1638401/pages/1605703)

Restore previous values to undo. If the title ignores a CVar or locks its console, use official menus rather than bypassing restrictions.
No client patches for online CryEngine games.

### Hedgehog Engine

Use the title's normal graphics configuration as the baseline; Generations, Frontiers and Shadow Generations differ. Do not apply one game's code addresses or frame-limit patch to another.
The maintained code catalog is organized by game, with explicit experimental labels and known defects.
[Hedge Mod Manager](https://github.com/hedge-dev/HedgeModManager), [code catalog](https://github.com/hedge-dev/HMMCodes)

## Tier 2: drop-in community fixes and runtime swaps

### REFramework and post-processing mods — offline single-player targets only

**REFramework**, by praydog, is a loader and scripting/inspection platform, not an automatic FPS upgrade. For non-VR installation the author instructs extracting only `dinput8.dll` into the game folder.
Remove that added DLL and the installed mod files to undo; retain existing files if another tool owned them.
[Installation and features](https://github.com/praydog/REFramework)

Current nightlies use a monolithic package, but exclude old non-RT RE2/RE3/RE7 builds.
Select a documented compatible build, not an arbitrary newest ZIP. Additional hooks/scripts can add CPU cost or crash after updates.
[Current package/legacy-branch notes](https://github.com/praydog/REFramework-nightly/releases)

RE4's graphics module exposes **Scope Image Quality** and **Enable Interlaced Rendering** for scopes. Lower scope resolution or interlacing is a targeted GPU experiment, trading clarity/temporal stability while aiming.
Supported RT graphics modules also expose **Bounce Count** and **Samples Per Pixel**; reducing them changes lighting/noise.
Check which controls exist in the actual build and reset each to its prior value to undo.
[Author's implementation](https://github.com/praydog/REFramework/blob/master/src/mods/Graphics.cpp)

**RE_DisablePostProcessingEffects**, by TonWonton, supports the specific games listed in its README, currently including RE Requiem, PRAGMATA and Monster Hunter Wilds. This is not a universal RE2/RE4 script.
For this pack, evaluate it only on an isolated eligible single-player target, never an online Monster Hunter client.
It can change TAA, fog, film grain and other effects; disabling them changes the image and may not save meaningful GPU time.
[Supported games, effects and caveats](https://github.com/TonWonton/RE_DisablePostProcessingEffects)

Its Lua installation uses `reframework/autorun`; its C# option needs the documented C# API and managed-plugin dependencies. Choose one documented route, retain the package manifest and remove its own script/plugin and configuration to undo.
Keep unneeded effects at Default; the author notes that some options are ineffective with particular upscalers.
[Installation and limitations](https://github.com/TonWonton/RE_DisablePostProcessingEffects/blob/main/README.md)

### MT Framework: DeadRisingEx

**DeadRisingEx**, by grimdoomer, targets the original Dead Rising PC port, not every MT Framework game. Its dynamic graphics memory option addresses rendering-memory-related crashes, potentially using more RAM rather than less.
Install the release in the game root with its supplied layout and launch through `DeadRisingLauncher.exe`.
Rollback restores overwritten files and removes the package's additions; use the normal game launch afterward.
Treat it as a stability repair and measure any performance change separately.
[Author's features and instructions](https://github.com/grimdoomer/DeadRisingEx)

### FromSoftware: unlocker caveats, not unconditional installs

**Elden Ring FPS Unlocker and more**, by uberhalit, hot-patches process memory. Its claim of future-version support is not sufficient: the tracker contains Shadow of the Erdtree-era breakage reports.
Current-build compatibility remains **(unverified)** here. It cannot fix shader compilation merely by lifting the cap.
Do not install it unless an eligible offline setup already exists without requiring anti-cheat/DRM changes.
Closing the tool alone does not undo a live memory patch; restart the game normally to restore its process.
[README](https://github.com/uberhalit/EldenRingFpsUnlockAndMore), [breakage report](https://github.com/uberhalit/EldenRingFpsUnlockAndMore/issues/149)

**Mod Engine 2** is an offline-only modding route for this pack, not an FPS mod. Its development is discontinued in favor of me3; reuse the companion's route only where the same restrictions can be met.
This document supplies no launcher renaming, anti-cheat removal or online instructions.
[Upstream status](https://github.com/soulsmods/ModEngine2), [companion route](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/big-frameworks.md)

For eligible offline **DS3**, **DS3DebugFPS** by 0dm uses `D3DCompiler_43.dll` and `FPSconfig.ini` in the game directory. Its executable variant keeps the INI beside its executable and patches a running game; the project requires windowed/borderless operation.
Use only a release matching the installed build; its old online-safety claims are not accepted here.
Higher FPS has timing risk: the project includes a sprint-slowdown correction. Undo by removing its added files and restarting.
[Author's installation and caveats](https://github.com/0dm/DS3DebugFPS)

For offline **Sekiro**, uberhalit's **Sekiro FPS Unlocker and more** applies runtime patches without editing game files. Download the release from its project, start the game/tool as documented and enable only the FPS feature being evaluated.
Avoid unrelated gameplay switches. Match the monitor and synchronization setup; uncapping may increase tearing and power use.
Close the tool and restart the game to undo. Verify gameplay timing as well as the counter.
[Author's instructions](https://github.com/uberhalit/SekiroFpsUnlockAndMore)

### RAGE: GTA IV FusionFix and DXVK

**GTAIV.EFLC.FusionFix**, maintained in ThirteenAG's repository, targets GTA IV Complete Edition single-player. Legacy 1.0.7.0/1.0.8.0 installations additionally require its documented Legacy Addon; do not downgrade as an optimization ritual.
Extract the release ZIP into the game root or use its official installer. Keep the installed-file manifest for rollback.
[Installation and supported editions](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/blob/master/readme.md)

Current FusionFix exposes **Graphics API** for DirectX 9 or Vulkan through DXVK; changing it requires restart. Prefer that documented integration over stacking extra `d3d9.dll` packages.
Its fixes include presentation/graphics corrections, but optional visual enhancements can cost FPS.
Compare with identical shadow/detail settings and warmed caches. Restore the API and remove the package's own files to undo.
[Author's menu/fix list](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/blob/master/readme.md)

Check [DXVK driver support](https://github.com/doitsujin/dxvk/wiki/Driver-support) before testing Vulkan.
Expect possible compilation or memory trade-offs. This is story-mode work; no GTA Online or RDR Online runtime replacements.

### Cyberpunk: CET and a concrete performance/quality controller

**Cyber Engine Tweaks (CET)** provides scripting and an overlay; it is not a reason to restore pre-2.x binary fixes.
Its documentation explicitly labels the old patch configuration as historical.
[CET configuration documentation](https://wiki.redmodding.org/cyber-engine-tweaks/console/settings/config-file)

**Ultra Plus — Physically Accurate Path Tracing**, by SammiLucia, is a current CET-controlled graphics project. It offers performance/quality trade-offs in path tracing, not free full-quality rendering on any GPU.
Check its release's game/CET/RED4ext compatibility; do not run the old open-source snapshot as though it were the latest package.
[Current author page](https://www.nexusmods.com/cyberpunk2077/mods/10490), [source-snapshot status](https://github.com/sammilucia/cyberpunk-ultra-plus)

Install its required CET/RED4ext versions, then use a manager or the package's documented root-folder layout. Keep the archive manifest; to remove it, follow the author's removal section and restore any prior overridden assets/configs.
Evaluate its faster modes against both vanilla path tracing and ordinary non-PT rendering; inspect lighting, noise and ghosting.
Do not combine it with a second undocumented engine-INI pack.
[Author's installation and removal instructions](https://www.nexusmods.com/cyberpunk2077/mods/10490)

### Frostbite and Hedgehog: use a matching framework, not a universal optimizer

**Frosty Tool Suite** is for supported offline single-player builds only. The new FrostyToolsuite repository describes an unfinished rewrite and directs users to the older stable releases.
Select the exact supported game profile, import/apply a documented mod through Frosty and use its supported launch route.
Disable that mod and restore the original launch/profile to undo. Framework compatibility does not establish a performance benefit.
[Maintainers' status](https://github.com/FrostyToolsuite/FrostyToolsuite), [stable release route](https://github.com/CadeEvs/FrostyToolsuite/releases)

**Hedge Mod Manager**, maintained by hedge-dev, manages supported Sonic titles and game-specific code selections.
Install its release using its current prerequisites; enable one relevant code, save/apply, and retain a clean profile.
Disable that code and reapply/restart to undo. The manager alone does not improve FPS.
[Supported games and installation](https://github.com/hedge-dev/HedgeModManager)

Frontiers' **Disable Grass** code by Hyper removes grass, trading vegetation for potentially less rendering work.
**Fix Shadow Stutter** fixes shadow interpolation as time passes; it is not a general frame-time repair.
The **Disable FPS Limit (experimental)** code lists game-speed and traversal defects; do not enable it by default.
[Grass code](https://github.com/hedge-dev/HMMCodes/blob/main/Source/Sonic%20Frontiers/Graphics/Quality/Disable%20Grass.hmm),
[shadow code](https://github.com/hedge-dev/HMMCodes/blob/main/Source/Sonic%20Frontiers/Fixes/Graphics/Fix%20Shadow%20Stutter.hmm),
[unlocker caveats](https://github.com/hedge-dev/HMMCodes/blob/main/Source/Sonic%20Frontiers/Graphics/Display/Disable%20FPS%20Limit%20%28experimental%29.hmm)

## Tier 3: code-level patches (profile -> patch the hot path)

Reuse the companion's [REFramework, MT native, FromSoftware, RAGE, REDengine and Hedgehog routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/big-frameworks.md).
Only eligible offline targets reach this tier. Sample native CPU stacks with
[Windows Performance Recorder/Analyzer](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/), with symbols for owned plugins.
REFramework object inspection identifies methods; it is not itself proof of where CPU time goes.
Add scoped timing to owned Lua/native callbacks and remove diagnostic overhead before the final measurement.

For accessible CryEngine development builds, use Crytek's built-in profiler to separate Main, Render and GPU time.
Retail builds may not expose the tools; do not bypass restrictions to enable them.
[Crytek profiling guide](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756813/pages/28184591)

Three grounded patch patterns are useful: reduce scope-only rendering cost rather than all image quality
([REFramework scope implementation](https://github.com/praydog/REFramework/blob/master/src/mods/Graphics.cpp));
fix graphics-memory allocation/lifetime defects rather than periodically purging working sets
([DeadRisingEx implementation](https://github.com/grimdoomer/DeadRisingEx)); and correct frame-dependent movement/timing together with an unlock
([DS3DebugFPS](https://github.com/0dm/DS3DebugFPS)). Each needs a regression test for visuals, timing and resource lifetime.

## Gotchas

- Higher FPS but faster/slower gameplay -> timing remains frame-dependent -> restore the cap and remove the experimental unlock.
- More FPS only with generated frames -> different display throughput, not equivalent simulation improvement -> compare base-frame latency too.
- New DLL causes startup failure -> wrong game/build/architecture or overlapping loader -> restore the clean baseline.
- Lower memory counter but worse traversal -> eviction is masking residency -> undo the purge, not the cache.
- “Works in another game on this engine” -> incompatible port/version -> require title-specific evidence.
  No RAM cleaners, registry folklore, `EmptyWorkingSet` loops or anti-cheat/DRM changes belong in these playbooks.
