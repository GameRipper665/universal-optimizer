# Unreal Engine (4 / 5)

**Identify.** A typical packaged game has `<Project>/Binaries/Win64/<Project>-Win64-Shipping.exe`
and `<Project>/Content/Paks/`. Newer packages can contain `.utoc`/`.ucas` alongside `.pak` files.
Use the companion [Unreal identification and modding routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/unreal.md).
Read the actual engine version from available startup logs or binary version evidence; do not infer UE5
from a game's visual style. Treat modified engine forks separately.

Generated settings are often in `%LOCALAPPDATA%\<Project>\Saved\Config\Windows\` or
`%LOCALAPPDATA%\<Project>\Saved\Config\WindowsNoEditor\`, containing `Engine.ini` and
`GameUserSettings.ini`. Portable layouts can use `<Project>\Saved\Config\<Platform>\`.
These are search candidates, not guaranteed installation paths. The companion documents the LocalAppData
layout; Epic documents the general
[`Saved/Config/[Platform]/[Category].ini` hierarchy](https://dev.epicgames.com/documentation/en-us/unreal-engine/configuration-files?application_version=4.27).
Confirm the active file by changing one menu setting and checking which file changes after exit.

Apply this playbook only to owned offline/single-player games or supported servers the user hosts.
Do not modify online clients, anti-cheat, DRM, executable protections, or package verification.
Record the build, API, resolution, route, settings, and first-run/warm-run status for every measurement.

**Where the time usually goes.** Separate these causes before installing a tweak pack:

- GPU rendering: use resolution scaling and, if available, `stat gpu` to identify costly passes.
  Lumen and virtual shadows can be expensive without causing shader-compilation stutter.
  [Epic's profiling commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine).
- CPU game/render threads: use `stat unit` when compiled in, or external CPU sampling otherwise.
  A busy game thread and low GPU utilization need different changes from a pixel-bound scene.
- PSO creation: first encounters with a material/render-state combination may stall in the graphics driver.
  Repeat encounters and available traces help test that hypothesis.
  [PSO cache design](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/RenderCore/FShaderPipelineCache).
- Traversal/loading: package I/O, decompression, UObject creation, actor registration, and gameplay setup can
  stall at world boundaries. A repeatable location hitch is not automatically a shader hitch.
  Use CPU/I/O traces where supported; [Insights](https://dev.epicgames.com/documentation/unreal-engine/unreal-insights-reference-in-unreal-engine-5)
  exposes only the channels compiled into that game.
- Memory/streaming/GC: correlate hitches with VRAM pressure, texture residency, and collection events.
  A texture pool can be over budget without the entire GPU being out of memory.
  [Texture streaming controls](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-streaming-configuration-in-unreal-engine).

## Tier 1: config and launch options (no files added)

Edit existing files only here. If `Engine.ini` is absent, use the game's settings first; optional config
creation and runtime tools belong to Tier 2. Back up existing files and original launch arguments.
Close the game before editing. Remove only the added lines to revert; do not replace the whole config.

### Sections, precedence, and Shipping limits

Put console-variable assignments under `[SystemSettings]` in the active `Engine.ini`.
The companion documents this route; Epic documents `ECVF_SetBySystemSettingsIni` and the priority order
in [console-variable handling](https://dev.epicgames.com/documentation/en-us/unreal-engine/console-variables-cplusplus-in-unreal-engine).
`GameUserSettings.ini` contains game/user-setting sections; do not paste renderer cvars under an arbitrary
section there. Games can subclass their settings and overwrite them when applying a menu preset.

For a deliberate **60 FPS cap experiment**, an existing Engine.ini can contain:

```ini
[SystemSettings]
t.MaxFPS=60
```

`t.MaxFPS` caps rendering FPS; `0` removes that particular cap. `r.VSync=0` disables engine VSync and
`r.VSync=1` enables it. These names are in
[Epic's cvar reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-console-variables-reference).
A sustainable cap can reduce load but lowers maximum FPS; VSync avoids tearing with pacing/latency trade-offs.
Driver controls and game-specific limiters can still impose a different effective limit.

Shipping normally strips console commands, stats, and profiling tools; see
[build configurations](https://dev.epicgames.com/documentation/unreal-engine/build-configurations-reference-for-unreal-engine).
This does **not** mean all renderer cvars are stripped. Many normal scalability cvars remain functional.
Debug/editor-only or cheat cvars, read-only/startup controls, unsupported features, and higher-priority
assignments are different reasons an edit can fail. Query the value and its help/`LastSetBy` when possible.
An unlocker cannot reconstruct compiled-out functionality. Do not circumvent protected config loading.

### Texture streaming: UE4.27 and UE5

Both keys below appear in the
[UE4.27 texture-streaming reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-streaming-configuration?application_version=4.27)
and [current reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-streaming-configuration-in-unreal-engine).

- `r.Streaming.PoolSize=<MB>`: texture-pool budget; `0` means unlimited, not automatic safe sizing.
  Raise it only when a measured texture-budget problem exists and total VRAM has headroom.
  Too large can cause paging/crashes; too small can produce blurry textures and residency churn.
- `r.Streaming.LimitPoolSizeToVRAM=1`: limit the texture pool to available GPU memory.
  It is not a reservation for every other GPU allocation. A tighter pool can increase texture pop-in.

Do not set the pool equal to the GPU's advertised capacity: render targets, geometry, and other resources
also consume VRAM. Do not disable streaming as a generic fix; fully resident textures can exceed memory.

### PSO/shader controls: UE4 cache versus UE5 precaching

In packaged games, driver PSO creation is different from the Editor compiling all source shader permutations.
An ini does not generate shader variants or a complete cache that the developer never shipped.
The [UE4.27 cache API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/RenderCore/FShaderPipelineCache?application_version=4.27)
documents the dependencies on shader libraries and cached PSO descriptions.

- `r.ShaderPipelineCache.Enabled=1`: permit loading/precompiling existing pipeline-cache data.
  It helps only where the game supplies/uses that mechanism. Work and memory move into precompilation.
- `r.ShaderPipelineCache.BatchSize=<count>`: maximum PSOs per fast-mode batch.
- `r.ShaderPipelineCache.BackgroundBatchSize=<count>`: maximum PSOs per background-mode batch.
  Larger batches can finish earlier while competing for CPU and causing hitches during play; smaller batches
  finish later. The game selects the batch mode. Do not publish one universal batch count.
  These are described by [FShaderPipelineCache](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/RenderCore/FShaderPipelineCache).

UE5.1 introduced earlier DX12 PSO compilation when components load; Epic explicitly warned that late loads
can still stall and may require game-code changes. See
[5.1 release notes, DX12 PSO compilation improvements](https://dev.epicgames.com/documentation/es-es/unreal-engine/unreal-engine-5.1-release-notes?application_version=5.1).
Do not assume UE5.1 has the coverage/defaults of later versions.

The following are verified in the [UE5.3 precaching documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine?application_version=5.3):

- `r.PSOPrecaching=1`: enable automatic precaching when the RHI supports it; it is already enabled by default
  in that reference. Repeating the default is not a measured optimization.
- `r.PSOPrecache.Components=1`: component-derived precaching; additional up-front CPU/memory work.
- `r.PSOPrecache.Resources=1`: resource precaching; can compile unnecessary or incomplete-state PSOs,
  using more work/memory without full coverage. It is disabled by default in that reference.
- `r.PSOPrecache.ProxyCreationWhenPSOReady=1`: delay component proxy creation until required PSOs finish.
  This trades a render stall for objects appearing late. Startup/config applicability depends on the build.

`r.PSOWarmup` as a portable UE cvar is **(unverified)**; do not add it or invent a value.
Do not label every `r.ShaderPipelineCache.*` key as a precaching switch; each has a different role.
Warm-cache traversal can improve one kind of hitch without repairing synchronous loading or gameplay spikes.
Keep caches between ordinary runs. Clear them only for an explicitly labeled cold-cache diagnostic.

### UE5 rendering features

Lumen, Nanite, and Virtual Shadow Maps are UE5 features; do not transplant their controls into stock UE4.
Use the game's graphics menu/scalability settings first, then query each cvar in the actual build.

- `r.ScreenPercentage=<percent>` changes internal rendering resolution in UE4/5; `100` is native scale.
  Lower values reduce pixel work and sharpness. Temporal upscalers/dynamic resolution can manage their own
  input scale. [Screen-percentage documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine).
- `r.DynamicGlobalIlluminationMethod`: UE5 selector, `0` none, `1` Lumen, `2` SSGI.
- `r.ReflectionMethod`: UE5 selector, `0` none, `1` Lumen, `2` SSR.
  Definitions: [Epic cvar reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-console-variables-reference).
  Changing either can lose lighting/reflection information; a cooked build may lack the replacement path.
  Per-volume settings and game code can affect the result. Restart and inspect dark interiors and reflective scenes.
- `r.Lumen.Reflections.Allow=0`: disables Lumen reflections; Epic describes an SSR substitution strategy in
  its [Lumen performance guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine).
  SSR has off-screen visibility limitations; the game must support the fallback.
  Other `r.Lumen.*` controls are feature-specific; do not disable the entire family with a copied list.
- `r.Nanite.MaxPixelsPerEdge`: target triangle edge size in pixels; raising it reduces detail.
  [Definition](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-console-variables-reference).
  This is an experiment, not a promise of faster rendering. Disabling Nanite wholesale can expose unsuitable
  fallback meshes or move work to a slower geometry path; see
  [Nanite fallback meshes](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine).
- `r.Shadow.Virtual.Enable=0`: disable Virtual Shadow Maps. Alternative shadows must be usable in the game;
  missing/changed shadows are possible.
- `r.Shadow.Virtual.ResolutionLodBiasDirectional` and `r.Shadow.Virtual.ResolutionLodBiasLocal`:
  increasing the bias reduces requested resolution, trading shadow detail for reduced page/rendering demand.
  Test moving lights and camera motion, not just a screenshot.
  [Virtual Shadow Maps reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine).

### Loading, garbage collection, and thread overlap

The exact names below are verified in the
[current cvar reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-console-variables-reference).
Do not assume their implementation or defaults match every older UE4/UE5 game.

- `s.AsyncLoadingThreadEnabled`: the current reference calls this a **placeholder unused at runtime**.
  Do not sell `=1` as a modern traversal fix. Older implementations require matching-version evidence;
  runtime support in an arbitrary legacy game is **(unverified)** here.
- `s.ForceGCAfterLevelStreamedOut=0`: avoids that forced post-stream-out collection when implemented.
  Trade-off: delayed reclamation and higher memory pressure; other triggers still collect.
- `gc.TimeBetweenPurgingPendingKillObjects`: interval in game-time seconds between purges.
  Raising it retains objects longer; reducing it can make cleanup more frequent.
- `gc.AllowParallelGC`: controls parallel collection, often already enabled. More threads can add overhead.
  Do not disable validation, collection, or arbitrary `gc.*` checks as a generic performance preset.

Epic's [GC settings](https://dev.epicgames.com/documentation/en-us/unreal-engine/garbage-collection-settings-in-the-unreal-engine-project-settings)
explain the memory/collection trade-off. Deferring a hitch is not removing its work.
Measure a long traversal and unloading cycle, including RAM peak and return to the starting area.

`r.OneFrameThreadLag=1` allows game/render-thread overlap; `0` can reduce queueing while reducing throughput.
This is a latency-versus-overlap experiment, not a universal CPU optimization. See
[low-latency frame syncing](https://dev.epicgames.com/documentation/en-us/unreal-engine/low-latency-frame-syncing-in-unreal-engine).
Keep VSync, FPS cap, and this control separate during comparisons.

### Direct3D launch selection

`-dx11` / `-d3d11` request D3D11; `-dx12` / `-d3d12` request D3D12.
Epic lists these in its [argument reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-command-line-arguments-reference).
Verify the selected RHI from available logs. A packaged game must include the corresponding RHI/shaders.
D3D11 can change driver/PSO behavior but lose UE5 features; D3D12 can enable those features and regress
on a particular driver or workload. Never claim D3D11 removes all traversal stutter.
Remove the argument to revert; test one API per run.

## Tier 2: drop-in community fixes and runtime swaps

If a game's verified guide requires creating `Engine.ini`, add only the measured `[SystemSettings]`
assignments in its active config directory. Remove the new file to revert only if the experiment created it.
Avoid entire replacement presets: unknown/default/redundant entries can hide which change helped.

[Universal Unreal Engine Unlocker (UUU)](https://framedsc.com/GeneralGuides/universal_ue4_consoleunlocker.htm)
can recreate the console in supported UE4 shipping games. Follow the author's supported-game/version
instructions, select the running offline game in its client, and inject the documented DLL.
Restart without injection to remove the session hooks. It is a diagnostic access tool, not an FPS fix.
The linked free UE4 release is not a guarantee for UE5; obtain an explicitly compatible release for the game.
An available console does not imply `stat` instrumentation survived compilation.

For UE4SS, reuse the companion [UE4SS route](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/unreal.md).
Do not install multiple proxy loaders over each other. Remove only the experiment's plugin/mod files to revert.

Verified game-specific engine-tweak projects include:

- **Final Fantasy VII Rebirth — [FF7RebirthFix](https://github.com/Lyall/FF7RebirthFix).** Adjusts the FPS limit
  and other presentation settings. The author's README links current development on
  [Codeberg](https://codeberg.org/Lyall/FF7RebirthFix). Extract the matching release into the game folder
  and configure `FF7RebirthFix.ini`; remove the release's own files to uninstall.
  Raising the cap increases load; its optional improved shadows can cost FPS rather than save it.
- **Clair Obscur: Expedition 33 — [ClairObscurFix](https://github.com/Lyall/ClairObscurFix).** Enables the console,
  changes sharpening, and removes the cutscene 30 FPS cap. Its README likewise points to
  [Codeberg](https://codeberg.org/Lyall/ClairObscurFix). Extract the matching release into the game folder,
  configure `ClairObscurFix.ini`, and remove its files to revert.
  Uncapped cutscenes require more work; console access enables experiments, not automatic stutter repair.
- **Final Fantasy VII Rebirth — [FFVIIHook](https://www.nexusmods.com/finalfantasy7rebirth/mods/4).** The
  [FF7RebirthFix README](https://github.com/Lyall/FF7RebirthFix#recommended-mods) verifies console/cvar override
  support and links the author's release. Its install places `xinput1_3.dll` in `End\Binaries\Win64\`;
  its config location is `Documents\My Games\FINAL FANTASY VII REBIRTH\Saved\Config\WindowsNoEditor\`.
  Follow the current archive instructions and keep a file manifest for removal. Version-specific hooks
  can break after updates. Do not substitute a Remake build.

These are feature-specific projects, not endorsements of universal "stutter fix" ini packs.
Keep only the options whose effects and trade-offs have been observed in the user's build.

## Tier 3: code-level patches (profile -> patch the hot path)

If available after unlocking, `stat fps` reports frame rate, `stat unit` separates frame/game/draw/GPU
timings, and `stat gpu` provides GPU-pass timings. See
[stat commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine).
They are commonly absent in Shipping; a console unlocker cannot guarantee them.
Use [PresentMon](https://github.com/GameTechDev/PresentMon) for external frame times when absent.

Unreal Insights is **not strictly Development-only**. It requires trace support and the needed channels
to be compiled in. Development builds are the usual controlled route; compatible Shipping builds can
also expose traces. The [Insights reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-insights-reference-in-unreal-engine-5)
documents `UE_TRACE_ENABLED` and `-trace=cpu,frame,bookmark`.
Do not promise usable function names, all channels, or source-level detail from an arbitrary retail executable.
Tracing adds CPU/I/O overhead; disable it for final acceptance measurements.

UE4SS offers Lua UFunction hooks and C++ mods; follow its
[Lua API](https://docs.ue4ss.com/release/lua-api.html) and the companion route.
Set a supported runtime cvar through an exposed console-command path or a matching C++ console-manager
integration. Query the result. Do not assume there is a universal Lua `SetCVar` function.
Use `ExecuteInGameThread` for game-object work and unregister hooks when unloading.

Patch one profiled behavior, preserving gameplay and object lifetimes:

1. Cache repeated actor/component searches in a hot UFunction; invalidate when actors are destroyed or
   levels unload. Do not hold every actor alive just to avoid a lookup.
2. Replace per-frame cosmetic HUD rebuilding with a change-triggered update or bounded refresh rate.
   Preserve input and gameplay events; delayed visuals are the explicit trade-off.
3. Move proven synchronous optional asset work to an existing safe preload point, or reduce the batch size.
   This can increase loading time and resident memory. Lua hooks cannot automatically make native loading,
   Blueprint setup, or an unsupported PSO system asynchronous.

These are candidate patch designs, not measured fixes for every Unreal game.
Keep hooks version-checked and individually reversible. Benchmark after removing profilers and debug views.

## Gotchas

- Ini stays unchanged but FPS does too -> key ignored, already default, overridden, or irrelevant -> query
  effective state and revert unproven additions. File persistence is not runtime verification.
- Textures sharpen but traversal worsens -> oversized pool competes for VRAM -> restore headroom and retest.
- Hitch becomes invisible objects -> PSO proxy delay trades stall for late rendering -> revert if unacceptable.
- Long session crashes after "GC fix" -> delayed reclamation raises memory -> restore collection behavior.
- RAM booster lowers Task Manager usage -> residency trim does not remove engine work -> remove the booster.
  [`EmptyWorkingSet`](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset)
  trims working-set pages; it is not a shader, streaming, or GC fix. No registry folklore or memory cleaners.
