# Unity (Mono and IL2CPP)

**Identify.** Look for `UnityPlayer.dll` and `<Game>_Data/`. Mono games normally expose
`<Game>_Data/Managed/Assembly-CSharp.dll`; IL2CPP games normally have `GameAssembly.dll` and
`<Game>_Data/il2cpp_data/Metadata/global-metadata.dat`.
Use the companion [Unity identification and modding routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/unity.md).
Read the exact engine version and graphics device from the startup log before selecting a patch.
On Windows, the usual log is `%USERPROFILE%\AppData\LocalLow\<CompanyName>\<ProductName>\Player.log`.
See Unity's [log locations](https://docs.unity3d.com/2022.3/Documentation/Manual/LogFiles.html).

Work only on an owned offline/single-player installation or an explicitly supported user-hosted server.
Do not modify online clients, anti-cheat, DRM, or protected loading paths.
Keep the game version, save, mod list, scene, resolution, and benchmark route fixed during comparisons.

**Where the time usually goes.** Confirm a bottleneck before changing it:

- Main-thread simulation and scripts: measure hot methods and call counts with a compatible Mono profiler.
  Large object populations can cost CPU even when the GPU is idle.
  [Simple Mono Profiler](https://github.com/BepInEx/BepInEx.Debug#simple-mono-profiler) provides method data.
- Managed allocation and GC: correlate allocation bursts with hitches. Temporary strings, closures, boxing,
  and array-returning APIs can create pressure; this affects Mono and is not automatically cured by IL2CPP.
  [Unity allocation guidance](https://docs.unity3d.com/cn/2022.3/Manual/performance-garbage-collection-best-practices.html).
- UI work: compare the same scene with the expensive panel closed. Repeated changes can dirty a large
  Canvas and trigger mesh/batch rebuilding. [Unity UI guidance](https://unity.com/how-to/unity-ui-optimization-tips).
- GPU rendering: lower resolution for a diagnostic run; compare GPU and display-frame durations with
  [PresentMon](https://github.com/GameTechDev/PresentMon). A resolution-sensitive slowdown suggests GPU work.
- Loading/streaming: repeat the same traversal, separating a first visit from a warm revisit. Record disk
  activity and thread stalls; frame-time spikes alone do not prove either GC or shader compilation.
  Unity documents OS-level investigation with [Event Tracing for Windows](https://docs.unity3d.com/2019.3/Documentation/uploads/ExpertGuides/Analyzing_your_game_performance_using_Event_Tracing_for_Windows.pdf).

## Tier 1: config and launch options (no files added)

Edit existing config only in this tier. Save its original contents and original launch options for rollback.
Try one change at a time. Restart for startup controls; remove the change if the log or measurement cannot
confirm its effect. Do not paste an entire game's boot configuration into another game.

### Graphics API and window mode

The following flags are documented in the [2020.3 Player reference](https://docs.unity3d.com/2020.3/Documentation/Manual/PlayerCommandLineArguments.html)
and the [2022.3 Player reference](https://docs.unity3d.com/2022.3/Documentation/Manual/PlayerCommandLineArguments.html).
These are verified version examples, not a claim that every older Unity release supports them.

- `-force-d3d11`: Windows Direct3D 11. Test for driver or frame-pacing differences; it can lose features
  or performance that the game's other backend supports.
- `-force-d3d12`: Windows Direct3D 12. It may improve CPU submission or regress stability and stutter.
- `-force-vulkan`: select Vulkan where the Player supports it. Driver behavior and available features differ.
- `-screen-fullscreen 0` or `-screen-fullscreen 1`: start windowed or fullscreen. Presentation behavior changes;
  this does not guarantee lower latency or higher FPS.
- `-popupwindow`: remove the window frame. It does not itself choose a lower render resolution or guarantee
  exclusive fullscreen. Convenience is the reason to use it; measure any presentation benefit.
- `-screen-width <pixels>` and `-screen-height <pixels>`: request resolution. Lowering it sacrifices sharpness
  and only helps work that scales with pixel count.

Check the selected API in `Player.log`. Do not stack mutually exclusive API flags.
An argument does not add a renderer, shader variants, or native plugins absent from the shipped build.
For newer games, compare against the [Unity 6 Player reference](https://docs.unity3d.com/6000.0/Documentation/Manual/PlayerCommandLineArguments.html).

`-force-gfx-jobs native` and `-force-gfx-jobs legacy` are documented as platform-dependent tests for
**Development** Players, including [2019.4 native jobs](https://docs.unity3d.com/cn/2019.4/ScriptReference/Rendering.RenderingThreadingMode.NativeGraphicsJobs.html)
and [legacy jobs](https://docs.unity3d.com/jp/2019.4/ScriptReference/Rendering.RenderingThreadingMode.LegacyJobified.html).
`-force-gfx-jobs split` is documented in [2023.1](https://docs.unity3d.com/cn/2023.1/ScriptReference/Rendering.RenderingThreadingMode.NativeGraphicsJobsSplitThreading.html)
with DX12 support there; [Unity 6](https://docs.unity3d.com/cn/6000.0/ScriptReference/Rendering.RenderingThreadingMode.NativeGraphicsJobsSplitThreading.html)
lists additional APIs. Do not advertise these as universal retail-build switches.
Changing threading can introduce synchronization overhead or driver faults; more workers are not free FPS.

### boot.config: distinguish real controls from copied folklore

The existing file normally sits at `<Game>_Data/boot.config`; confirm the actual game layout before editing.
Unity documents a Standalone Player's `boot.config` in its
[2019.3 worker-count documentation](https://docs.unity3d.com/2019.3/Documentation/Manual/CommandLineArguments.html).
The entries below are independent investigations, not a recommended preset.

- `job-worker-count=<N>`: documented in 2019.3; also documented in the
  [2022.3 Editor argument reference](https://docs.unity3d.com/2022.3/Documentation/Manual/EditorCommandLineArguments.html)
  as a Player boot override. The corresponding argument is `-job-worker-count <N>`.
  This controls the JobQueue worker count, not arbitrary game-code parallelism.
  Reduce it only to test measured contention; raising it can increase scheduling overhead and hurt other threads.
  Keep the game's default unless repeated runs improve.
- `wait-for-native-debugger=0`: actually emitted by the
  [2019.4 build postprocessor](https://github.com/Unity-Technologies/UnityCsReference/blob/2019.4/Editor/Mono/Modules/DefaultBuildPostprocessor.cs)
  and [2022.3 build postprocessor](https://github.com/Unity-Technologies/UnityCsReference/blob/2022.3/Editor/Mono/Modules/DefaultBuildPostprocessor.cs).
  It concerns debugger waiting at startup. Keeping the normal zero value is not a gameplay optimization;
  changing debugger controls can prevent an intended debugging workflow.
- `gc-max-time-slice`: those same versioned postprocessors emit `gc-max-time-slice=3` when incremental GC
  is selected and the platform supports the required write barriers. This verifies emission in those versions,
  not an ability to retrofit incremental GC into every compiled Player.
  Do not prescribe another boot value without matching-version runtime evidence.
- `gfx-enable-gfx-jobs=1` and `gfx-enable-native-gfx-jobs=1`: these circulate as boot tweaks, but the exact
  retail-runtime version/API support is **(unverified)** here. Do not apply them as a universal preset.
  The verified neighboring feature is build-time
  [PlayerSettings.graphicsJobs](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/PlayerSettings-graphicsJobs.html),
  plus the Development-only tests above. Potential benefit is parallel graphics work; risk is crashes or regressions.
- `scripting-runtime-version=latest`: a universal boot-file performance interpretation is **(unverified)**.
  The historical `-scripting-runtime-version Latest` example applies to the Editor in
  [Unity's mixed-callstack documentation](https://github.com/Unity-Technologies/UnityMixedCallstack).
  Legacy Mono was removed in 2019.3 according to
  [Unity's runtime-version declaration](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Editor/Mono/PlayerSettings.bindings.cs).
  Do not add it to modern games or replace their Mono runtime with a random newer DLL.

### PlayerPrefs and incremental collection

Windows Standalone PlayerPrefs live under
`HKEY_CURRENT_USER\Software\<CompanyName>\<ProductName>`, not the Editor's registry branch.
The names come from the game's Player settings. See [PlayerPrefs](https://docs.unity3d.com/ja/current/ScriptReference/PlayerPrefs.html).
Graphics preference names and encodings belong to the game; there is no universal `GraphicsQuality` key.
Change a setting in the menu and compare that game's registry values before editing anything.
Export only the relevant branch first. Restore it to undo an experiment; do not delete all preferences.
Lower graphics settings trade image quality for the specific workload they control.

Incremental GC arrived experimentally in
[2019.1](https://docs.unity3d.com/ja/2019.1/Manual/UnderstandingAutomaticMemoryManagement.html).
It spreads collection work across frames instead of making all collection work disappear.
The [2022.3 incremental GC documentation](https://docs.unity3d.com/2022.3/Documentation/Manual/performance-incremental-garbage-collection.html)
explains write-barrier overhead and cases where excessive reference changes defeat incremental progress.
It is a build/runtime capability, not a guaranteed user-facing graphics preference.
For a compatible code patch, inspect
[`GarbageCollector.isIncremental`](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Scripting.GarbageCollector-isIncremental.html)
before considering
[`GarbageCollector.incrementalTimeSliceNanoseconds`](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Scripting.GarbageCollector-incrementalTimeSliceNanoseconds.html).
A larger slice uses more time now; a smaller slice can leave more outstanding collection work.
Do not disable GC to make a short benchmark look smooth: memory can grow until the game fails.

## Tier 2: drop-in community fixes and runtime swaps

Use the game's existing ecosystem first. Follow the companion
[BepInEx/MelonLoader/Harmony routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/unity.md)
for loader selection rather than reinstalling a second loader. Match game, engine, backend, and architecture.
Test one fix at a time on a copied save. Keep a manifest of added files for removal.

- **RimWorld — [Performance Fish](https://github.com/bbradson/Performance-Fish).** Targets method efficiency
  and late-game tick times. Its README requires Prepatcher and Fishery; install their compatible releases
  through the game's mod system. Patches can be individually disabled; the author says it stores no
  session-specific save data. Remove its mod through that same system to revert.
  Trade-off: mod compatibility, especially the README's incompatible-mod list; no universal speedup percentage.
- **RimWorld — [RocketMan](https://github.com/kbatbouta/RimWorld-RocketMan).** A performance mod with caching
  and a compatibility rules system. Use the Workshop link in its README, enable it in the game's mod list,
  and follow its instruction to place it last. Disable/unsubscribe to remove.
  Its README rejects RimThreaded compatibility; test simulation correctness as well as tick rate.
- **Valheim — [ValheimPerformanceOptimizations](https://github.com/ontrigger/ValheimPerformanceOptimizations).**
  Provides object-streaming, terrain, structural-support caching, and rendering optimizations.
  Install the game-compatible release via its linked community package and existing BepInEx setup.
  Remove that package/plugin to revert. The README flags experimental threaded terrain collision;
  terrain disappearance is a reason to disable that feature. Optional physics caps sacrifice accuracy.
  Evaluate only offline or on an explicitly supported server the user hosts.
- **Cities: Skylines (original) — [Loading Screen Mod Revisited](https://github.com/algernon-A/LSM-Revisited).**
  Targets custom-asset loading performance and memory footprint, not a promised simulation-FPS fix.
  Follow the release/Workshop installation route
  linked by the project and remove it with the same mod manager. Check its version against the game.
  Trade-off: loading-mod conflicts and optional content-skipping choices; do not enable skipping blindly.
- **Kerbal Space Program — [KSPCommunityFixes](https://github.com/KSPModdingLibs/KSPCommunityFixes).**
  Covers KSP 1.8.0–1.12.5, with patch-specific applicability. Examples include avoiding PQS allocations
  and redundant terrain coroutines. Use CKAN, or its documented `GameData/KSPCommunityFixes` install
  with HarmonyKSP and ModuleManager. Remove its own folder/package to revert; retain shared dependencies.
  Disable a conflicting patch in its settings. Back up the save before testing physics-related changes.

Do not swap `UnityPlayer.dll`, `GameAssembly.dll`, or Mono libraries across arbitrary engine versions.
A loader is an access route, not an engine upgrade or a performance improvement by itself.

## Tier 3: code-level patches (profile -> patch the hot path)

### Profiling a shipped game

Unity's built-in Profiler requires a Development Player; adding `-profiler-enable` does not restore stripped
instrumentation. See [profiling applications](https://docs.unity3d.com/2022.2/Documentation/Manual/profiler-profiling-applications.html).
Use PresentMon for external frame times; it cannot identify a particular C# allocation site.

For Mono, [BepInEx.Debug's Simple Mono Profiler](https://github.com/BepInEx/BepInEx.Debug#simple-mono-profiler)
supports Players able to run BepInEx 5.x, including ordinary shipped builds.
Follow its release layout. Its allocation figures are estimates, it continuously adds substantial overhead,
and custom debugging Mono DLLs can cause hard crashes. Remove/disable the profiler and restart for final timings.

[dotTrace's Unity workflow](https://www.jetbrains.com/help/profiler/Profile_Unity_Application.html) launches the
game executable using a Unity run configuration and Timeline profiling; optional native profiling adds context.
The [support matrix](https://www.jetbrains.com/help/profiler/dotTrace_Introduction.html) lists Unity Mono
2018.3+ and says attaching to an already running Unity process is unsupported.
Do not promise Mono managed-method profiling for IL2CPP, which compiles game code natively.

[UnityExplorer](https://github.com/sinai-dev/UnityExplorer) inspects objects and components in Mono/IL2CPP games.
It is useful for finding the owner of expensive behavior, not a replacement for a CPU or allocation profiler.
The original repository is archived; choose a loader-compatible maintained release/fork and remove it for benchmarks.
For IL2CPP, use compatible interop hooks plus narrowly scoped timings, or native sampling with available symbols.
Follow the companion's backend-specific patching route; do not assume managed IL bodies exist.

### Patch patterns

1. **Cache repeated lookups with invalidation.** Replace a measured per-frame `FindObjectOfType` or repeated
   `GetComponent` with a per-instance reference. Clear/rebind it on object replacement and scene transitions.
   Unity explicitly warns against per-frame
   [`FindObjectOfType`](https://docs.unity3d.com/es/530/ScriptReference/Object.FindObjectOfType.html).
   Avoid process-wide caches that retain destroyed scene objects.
   Old `Camera.main` implementations searched tags without caching; prioritize old-game hot loops.
   Unity [2020.2 release notes](https://unity.com/releases/editor/beta/2020.2.0b7) report a faster query;
   [current API docs](https://docs.unity3d.com/cn/6000.0/ScriptReference/Camera-main.html) describe an internal
   tag cache with remaining lookup overhead. Do not claim the old cost for every modern release.
2. **Update UI on changes.** Patch a hot HUD method to compare the displayed value before changing text.
   Throttle cosmetic counters only when a small display delay is acceptable; preserve input, timers, and game logic.
   Split dynamic/static Canvas work only if object/layout ownership is understood.
   This targets the rebuilding described in [Unity's UI guidance](https://unity.com/how-to/unity-ui-optimization-tips).
3. **Remove hot allocations.** Replace measured LINQ materialization/closures with a reused collection or loop;
   avoid rebuilding identical strings each frame. Preserve iteration order and query semantics.
   Clear pooled collections and bound their size, or lower allocation rates can become retained-memory leaks.
   These follow [Unity's allocation guidance](https://docs.unity3d.com/cn/2022.3/Manual/performance-garbage-collection-best-practices.html),
   not a claim that every LINQ call allocates identically on every runtime.

Use a Harmony prefix/postfix for the smallest semantic change; use a transpiler only when required.
Check the patched method still matches after updates. Make the patch individually switchable.
Measure both method time/allocation and external frame times; remove instrumentation before acceptance runs.

## Gotchas

- More average FPS but worse hitches -> changed scheduling or GC pressure -> restore defaults and compare
  long-frame counts, not just averages. Keep loading and traversal in the test route.
- Boot edit produces no observable change -> unsupported key, wrong build/API, or an already-enabled feature ->
  revert it. A line remaining in a text file does not prove the Player consumed it.
- Stutter returns after scene changes -> invalid cache or newly allocated objects -> invalidate caches and
  sample that transition, rather than retaining the old scene forever.
- Low reported RAM after a cleaner -> residency was trimmed, not game work removed -> remove the cleaner.
  [`EmptyWorkingSet`](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset)
  removes working-set pages; it is not a managed-heap optimization. RAM boosters and registry folklore
  are not substitutes for reducing measured allocations, retained assets, or simulation work.
