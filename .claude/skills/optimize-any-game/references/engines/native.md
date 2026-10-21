# Native C/C++ and legacy engines

Unknown native engines, id Tech derivatives, ZenGin/Gothic, Cocos2d-x, Genie/Age of Empires and generic DX8/9-era games.
Single-player/offline games the user owns, or servers the user hosts. Exclude online clients, anti-cheat and DRM work.
Sources checked 2026-10-21. “Native” identifies a patching route, not a shared set of performance settings.

**Identify.** Inspect the actual process, not only its launcher. Record EXE version/hash, architecture, graphics API,
loaded mods and the exact reproducible scene. [DUMPBIN /HEADERS](https://learn.microsoft.com/en-us/cpp/build/reference/headers)
reports PE headers; [DUMPBIN /IMPORTS](https://learn.microsoft.com/en-us/cpp/build/reference/imports-dumpbin) lists direct/delay imports.
An imported graphics DLL is a lead; confirm which backend is actually active.

- **id Tech:** Quake III's `baseq3`/PK3 layout and generated `q3config.cfg` identify that branch, not all id engines.
  [Filesystem source](https://github.com/id-Software/Quake-III-Arena/blob/master/code/qcommon/files.c).
  Original Doom 3 uses `base/pak000.pk4` and further PK4s; BFG is a separate target.
  [Game-data inventory](https://dhewm3.org/).
- **ZenGin:** Gothic I/II with their `System` directory and `Gothic.ini`; confirm the edition before installing a renderer.
  A renderer's `System/GD3D11/UserSettings.ini` is its own configuration, not a vanilla engine file.
  [GD3D11 supported builds and paths](https://github.com/kirides/GD3D11#installation--usage).
- **Cocos2d-x:** verify Cocos classes/exports/version strings against the shipped binary and
  [engine source](https://github.com/cocos2d/cocos2d-x/tree/v4/cocos). A statically linked game may have no separate engine DLL.
  A similarly named asset directory alone is not proof. Do not substitute a random Cocos DLL from another game.
- **Genie/AoE2 DE:** distinguish the original game, HD and Definitive Edition; they do not share a universal INI or binary patch.
  DE's documented [Enhanced Graphics Pack](https://support.ageofempires.com/hc/en-us/articles/360047305452-How-do-I-download-and-enable-the-Enhanced-Graphics-Pack-DLC)
  is a DX11/64-bit PC target. Do not apply an old 32-bit AoE fix to DE.
- **Unknown:** discover configuration/log locations from actual file activity using
  [Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon), filtered to the game's process.
  Change one menu setting, exit normally and inspect the file written. Never invent an `Engine.ini` for an unknown engine.

**Where the time usually goes.** Treat these as hypotheses and confirm before changing anything:

1. **Main-thread simulation / draw submission:** one busy thread, little gain from lower resolution; sample the process
   and separate game code from graphics-driver overhead. Whole-machine CPU percentage can hide a saturated thread.
2. **Limiter spinning or bad waits:** busy CPU despite a low fixed FPS, samples around clocks/yields;
   compare CPU time at the same cap, then inspect the loop rather than assuming all high CPU is useful work.
3. **Streaming / shader work:** spikes only when entering areas/seeing effects; correlate disk activity, CPU stacks and GPU idle time.
   Repeat the route warm. A second pass alone cannot prove a patch helped.
4. **GPU / old graphics paths:** resolution scaling helps, or CPU stalls in locks/readbacks despite idle GPU gaps;
   compare GPU timing with driver stacks before replacing the renderer.
5. **Memory / address-space exhaustion:** allocation failure, rising commit or large residency churn after a long session;
   examine allocation lifetimes and hard faults. A full working set is not automatically a leak.

[WPR/WPA graph selection](https://learn.microsoft.com/en-us/troubleshoot/windows-server/support-tools/support-tools-xperf-wpa-wpr),
[PresentMon frame measurements](https://github.com/GameTechDev/PresentMon),
[working-set definitions](https://learn.microsoft.com/windows/win32/memory/working-set).

## Tier 1: config and launch options (no files added)

### id Tech: scope every cvar to the actual branch

For stock Quake III-derived builds which retain the upstream implementation:

- Query and record `com_maxfps`, then try `com_maxfps 60` in the console for a supported gameplay cap.
  Lower peak FPS can reduce delivered-frame variation, but the stock limiter itself spins; it need not reduce CPU use.
  `com_maxfps 0` removes this cap and can expose timing/gameplay differences. Restore the original value to undo.
  [Declaration and actual limiter loop](https://github.com/id-Software/Quake-III-Arena/blob/master/code/qcommon/common.c).
- Increase `r_picmip` by one only when texture bandwidth/residency is the bottleneck; restart the game to reload textures.
  It shifts eligible texture dimensions down, so image detail falls. Restore the prior value and restart to undo.
  [Texture upload implementation](https://github.com/id-Software/Quake-III-Arena/blob/master/code/renderer/tr_image.c).

The values persist in the active mod's `q3config.cfg`; identify the actual write location instead of assuming every port uses the install folder.
Prefer console/menu edits to hand-editing a generated configuration while the game is running.
[Config writing and command-line handling](https://github.com/id-Software/Quake-III-Arena/blob/master/code/qcommon/common.c).
Quake I/II, Quake III, Doom 3 and later id Tech games require separate cvar checks. An OpenGL renderer cannot use DXVK directly.

For original Doom 3/id Tech 4, `r_shadows 0` disables shadows: a diagnostic for expensive stencil-shadow scenes,
with major visual loss. Restore `r_shadows 1` for the original behavior; do not present it as a free optimization.
[Original renderer declaration](https://github.com/id-Software/DOOM-3/blob/master/neo/renderer/RenderSystem_init.cpp).
Use the game's menu for resolution/quality first. Do not copy giant texture-cache values from unrelated machines or ports.

### ZenGin / Gothic

Use the original view-distance/detail controls first and compare the same crowded location; shorter visibility buys CPU/GPU headroom
at the cost of pop-in. For the Gothic II configuration route documented by the OpenGothic maintainer,
`System/Gothic.ini` contains `zMaxFPS`; set a finite cap such as `zMaxFPS=60` only after checking the installed engine/patch honors it.
Restore the previous value to undo. A lower cap loses temporal smoothness but avoids runaway rendering;
verify movement, animation and input as well as FPS. [Maintainer's path/key](https://github.com/Try/OpenGothic/discussions/340).
Union/SystemPack/replacement renderers can supply another limiter; keep one active and use that version's documentation.

### Cocos2d-x

There is no engine-wide end-user performance INI/launch switch to prescribe. Use the game's own resolution, effects and cap controls.
The source-level `Director::setAnimationInterval` API is not a launch flag and is not guaranteed to be exported by a shipping game.
It controls the frame interval; changing it can change scheduling/update behavior and must be tested against that game's logic.
[Cocos2d-x v4 Director declaration](https://github.com/cocos2d/cocos2d-x/blob/v4/cocos/base/CCDirector.h),
[template's 60 Hz setup](https://github.com/cocos2d/cocos2d-x/blob/v4/templates/cpp-template-default/Classes/AppDelegate.cpp).
Do not raise the tick/render rate to “optimize” a CPU-bound scene. Use a lower sustainable cap only if its gameplay remains correct.

### Genie / Age of Empires II: Definitive Edition

In Options > Graphics > Show Advanced Options, uncheck **Enhanced Graphics (UHD)** and restart for an A/B run.
It removes the optional higher-fidelity graphics workload; the trade-off is lower-resolution art/changed zoom presentation.
Restore the checkbox to undo. Uninstall the optional Steam DLC separately only if disk space is the goal.
[Publisher's exact option and DLC controls](https://support.ageofempires.com/hc/en-us/articles/360047305452-How-do-I-download-and-enable-the-Enhanced-Graphics-Pack-DLC).
Compare the same offline save and simulation speed, especially in a large battle: less graphics work cannot be assumed to fix pathfinding.
No undocumented launch switches or simulation-thread count are prescribed here.

### Generic DX8/9-era games

Use the original game's supported cap first. Test resolution/texture/detail reductions separately to identify the limiting resource.
External caps, per-app GPU choice and presentation settings are in [universal layers](../universal-layers.md).
Do not extrapolate “disable VSync” into a universal fix: tearing, latency and engine timing change with the presentation path.
Back up changed settings, then restore those exact values if the measured benefit does not survive repeat runs.

## Tier 2: drop-in community fixes and runtime swaps

Install one fix at a time. Record the release, supported game builds and archive manifest; preserve colliding originals elsewhere.
Verification means the correct module/feature is active **and** the symptom improves. Removal means undoing that manifest,
not deleting a shared `scripts` directory full of other mods.

### Native fixes with documented results

- **GTA IV FusionFix:** for The Complete Edition, download `GTAIV.EFLC.FusionFix.zip` from
  [official releases](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/releases) and extract beside the game EXE.
  Confirm added graphics/FPS menu entries. It documents faster loading, shadow improvements and frame-rate bug fixes;
  extra graphics options can add cost, so compare equivalent visual settings.
  [Installation and supported behavior](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix).
  In `plugins/GTAIV.EFLC.FusionFix.ini`, `[FRAMELIMIT] FrameLimitType=2` is sleep-yield; `1` is thread-lock.
  The former uses less CPU, with a possible pacing/latency trade-off. Compare at the same cap, not unlocked versus capped.
  [Shipped INI](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/blob/master/data/plugins/GTAIV.EFLC.FusionFix.ini).
  Remove only archive-added files and restore overwritten ones to uninstall; keep saves untouched.
- **ThirteenAG Widescreen Fixes Pack:** choose the exact game's package from the
  [project index](https://fusionfix.io/wfp), then extract as instructed into that game's root.
  For example, Condemned: Criminal Origins includes a fix for FPS falling to roughly 20–30 after several minutes;
  King Kong includes CPU-frequency/timing fixes and selective caps to avoid crashes. These are game-specific fixes,
  not evidence that widescreen/FOV changes improve FPS. Wider FOV can actually increase rendering work.
  Verify the documented feature and replay the affected scene; remove manifest-listed files to uninstall.
  [Pack installation/removal](https://github.com/ThirteenAG/WidescreenFixesPack#building-and-installing).
- **SilentPatch for classic GTA III:** the author documents a more precise limiter and reduced limiter-related spikes,
  while still recommending the original Frame Limiter remain on because high FPS breaks other behavior.
  Follow that game's [download and setup links](https://silentsblog.com/mods/gta-iii/), preserving the package's file list.
  Verify at the original cap; remove its added plugin files and any solely used loader to undo.
  This entry concerns classic GTA III, not the Definitive Edition or arbitrary RenderWare games.

### Engine replacements

- **Doom 3:** [dhewm3](https://dhewm3.org/) supports original Doom 3 data updated to 1.3.1, not BFG.
  Extract a matching official binary release into a separate directory, then copy owned `base/*.pk4` and, if owned,
  expansion `d3xp/*.pk4` into those respective directories. Run the port instead of overwriting the original EXE.
  Verify its version and loaded data; compare compatible scenes/settings and saves before adopting it.
  Remove the separate port directory to undo. Modern fixes/64-bit availability can improve compatibility or headroom;
  mod/save compatibility and exact original behavior are not guaranteed. [Scope](https://github.com/dhewm/dhewm3#game-data-and-patching).
- **Gothic:** [GD3D11](https://github.com/kirides/GD3D11) supports Gothic I 1.08k and Gothic II Night of the Raven 2.6
  in the documented builds. Extract the release ZIP's contents into the corresponding `System` directory.
  Confirm its version at top left; press F11, choose Graphics Preset and Save Settings.
  The renderer writes `System/GD3D11/UserSettings.ini`. Start conservatively: added shadows/distance/effects can cost more than they save.
  Remove only installed files, including its `ddraw.dll`, and restore originals to undo; never install another `ddraw.dll` on top.
  [Exact supported versions and controls](https://github.com/kirides/GD3D11#installation--usage).

For stock Gothic compatibility, inspect [SystemPack releases](https://github.com/GothicFixTeam/GothicFix/releases)
and the installed game's existing patch state before layering anything. Do not stack multiple compatibility distributions blindly.
For generic legacy renderers, use the documented [DXVK / dgVoodoo2 / d3d8to9 routes](../universal-layers.md#render-api-translation),
matching API and process architecture. A compatibility wrapper is not an automatic speedup.
There is no universal drop-in engine replacement prescribed for closed Cocos2d-x titles or AoE2 DE.

## Tier 3: code-level patches (profile -> patch the hot path)

### Profile a binary with no game symbols

1. Install the Windows ADK's Windows Performance Toolkit for the WPR GUI and WPA; Windows also ships command-line WPR.
   In WPR choose CPU Usage with stack sampling; add relevant disk/file activity for streaming symptoms.
   Record a short repeatable hitch window, save the ETL outside the mod repository and stop recording.
   Tracing has overhead/disk cost; compare final builds without the profiler too.
   [Microsoft collection workflow](https://learn.microsoft.com/en-us/troubleshoot/windows-server/support-tools/support-tools-xperf-wpa-wpr).
2. Open the ETL in WPA. Select the bad interval, then CPU Usage (Sampled), grouped by Process > Thread ID > Stack.
   Use inclusive cost to locate expensive call trees and exclusive cost to locate the actual executing leaf.
   A sleeping thread can dominate elapsed time with few CPU samples; use CPU Usage (Precise)/wait analysis for that case.
   [WPA table workflow](https://devblogs.microsoft.com/performance-diagnostics/wpa-intro/).
3. Load available Microsoft/vendor symbols; missing game PDBs do not prevent instruction sampling.
   Keep module plus relative virtual address (RVA), not a guessed function name. Optimized x86 stacks may be incomplete;
   corroborate an address across recordings and inspect disassembly before trusting a call chain.
4. Alternative: [Superluminal](https://www.superluminal.eu/docs/documentation.html), a commercial sampling profiler,
   can Run or Attach without adding instrumentation. Inspect the problematic thread/time interval, sampled stacks and wait states.
   Without game symbols, retain unresolved addresses/module offsets; it cannot manufacture source or original function names.
5. [Intel VTune Hotspots](https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2026-0/basic-hotspots-analysis.html)
   provides user-mode or hardware-event sampling; select the supported mode, collect stacks and inspect bottom-up hot spots/disassembly.
   [AMD uProf](https://www.amd.com/en/developer/uprof/uprof-performance-analysis.html) offers statistical CPU profiling too.
   Hardware counters/drivers require supported hardware and permissions; counter availability is not identical across vendors.
   uProf 5.3 distinguishes launch-only Hotspots from attach-capable TBP; verify collection mode before promising attach.
   [AMD mode limitations](https://docs.amd.com/r/en-US/68658-uProf-getting-started-guide/AMD-uProf-Time-Sampling-Methods).
6. Use [Tracy](https://github.com/wolfpld/tracy) only when source and a rebuild are available in this workflow.
   Instrument candidate zones/frame boundaries in a release-like build; compare allocation, lock and frame timing.
   It is not a drop-in symbol recovery tool for a closed executable.

### Turn a sampled address into a verified target

Compute `RVA = sampled address - loaded module base`; ASLR makes an absolute live address unstable.
Open the matching on-disk binary in Ghidra/IDA and navigate to that RVA in the correct image mapping.
Use strings, imports and cross-references to recover the caller's role; label speculative interpretations as hypotheses.
Inspect enough instructions to identify function boundaries, arguments, calling convention and object lifetime.
Confirm the candidate in the same offline scene with a bounded trace/breakpoint, then profile again without instrumentation.
Use the companion [reverse-engineering workflow](https://github.com/rehan-remade/universal-modder/blob/main/skills/reverse-engineering/SKILL.md).

Record build hash, module/RVA, evidence, a signature with relocation bytes masked, expected match count and original instruction bytes.
Make the plugin refuse an unsupported build or ambiguous signature; do not patch the first coincidental byte match.
Keep decompiled code/game assets outside the mod repository and distribute only original patch code and required notices.

### Load the patch through a proxy / ASI host

Inspect imports and loaded modules to choose a supported local proxy name, commonly `dinput8.dll`.
Download the appropriate x86/x64 [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader), place its proxy beside
the game EXE, and put the compiled DLL renamed to `.asi` in `scripts` (or another documented plugin directory).
Keep the default deferred loading. Export `InitializeASI` for initialization outside the loader lock; do substantial work there,
not inside `DllMain`. `[GlobalSets] DebugLog=1` in `global.ini` enables the loader's named log for load verification.
Disable debug logging after diagnosis to avoid ongoing I/O and log growth.
Remove the plugin first to undo; remove the loader only when no other plugin uses it. Restore any original proxy.
[Loader initialization/configuration contract](https://github.com/ThirteenAG/Ultimate-ASI-Loader#usage).

For the detour, [MinHook](https://github.com/TsudaKageyu/minhook) supports Windows x86/x64:
initialize once, create the hook with an original trampoline, check status, then enable only that target.
Disable/remove it when no caller can still execute its code, then uninitialize.
[Exact API declarations](https://github.com/TsudaKageyu/minhook/blob/master/include/MinHook.h).
Alternatively [SafetyHook](https://github.com/cursey/safetyhook) provides inline/mid-function hooking;
retain the hook object for its entire lifetime and call the original through its trampoline when required.
Match x86 conventions and x64 ABI/register/stack requirements. Mid-function hooks require explicit register/liveness analysis.
Neither library proves that a chosen function is safe to alter. Keep per-frame hooks allocation-free and avoid synchronous log spam.

### Patterns worth investigating, with actual precedents

- **Busy-wait / Sleep(0) limiter:** sample the cap loop. Stock Quake III's frame loop visibly spins until its time budget elapses.
  `Sleep(0)` merely yields to another runnable thread and may immediately return; it is not a timed sleep.
  Replace only the proven limiter with a deadline-based wait or a proven community implementation, preserving input/event servicing.
  Sleeping saves CPU/power but can worsen pacing if deadlines overshoot; compare equal caps, CPU milliseconds and tail frame times.
  [Stock loop](https://github.com/id-Software/Quake-III-Arena/blob/master/code/qcommon/common.c),
  [Sleep contract](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-sleep),
  [FusionFix's two real limiter modes](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/blob/master/data/plugins/GTAIV.EFLC.FusionFix.ini).
- **Frame-rate-tied logic:** rendering more often can speed animation, physics or scripted events. Retain a known-safe cap until
  the specific timestep dependencies are fixed; do not change one global delta and assume all subsystems use it.
  FusionFix documents high-FPS gameplay fixes; SilentPatch still recommends GTA III's original limiter.
  Verify movement distance, mission triggers, cutscenes and save/load at multiple rates. Higher render rates cost CPU/GPU work.
  [FusionFix changes](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/releases), [SilentPatch limits](https://silentsblog.com/mods/gta-iii/).
- **Single-threaded loading / artificial waits:** distinguish useful decompression, blocking I/O and deliberate delays in the trace.
  A busy loading thread is not permission to parallelize renderer/object creation with unknown ownership.
  Narrow candidates are removing a verified redundant wait or preparing independent data before main-thread publication.
  More buffering/workers cost memory and can race. FusionFix's faster loading and loading-cap controls are a real precedent,
  not proof that its fix parallelizes loading or that uncapping every loading screen is safe.
  [Documented loading improvements](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix),
  [loading controls and freeze guard](https://github.com/ThirteenAG/GTAIV.EFLC.FusionFix/blob/master/data/plugins/GTAIV.EFLC.FusionFix.ini).
- **D3D9 lock-heavy submission:** static-buffer locks while the GPU reads can serialize the pipeline.
  Investigate batching or correctly scoped dynamic-buffer renaming; `D3DLOCK_DISCARD` discards the whole buffer,
  and `D3DLOCK_NOOVERWRITE` promises not to touch in-flight data. Never force these flags blindly in every Lock hook.
  Trade-offs are extra transient memory, ordering complexity and corruption if lifetime assumptions are wrong.
  [Microsoft's measured-mechanism guidance](https://learn.microsoft.com/en-us/windows/win32/direct3d9/performance-optimizations).
  Cocos2d-x likewise recommends fixing measured batching/texture costs with source available; atlas/layout changes can alter output.
  [Cocos optimization guide](https://docs.cocos2d-x.org/cocos2d-x/v4/en/advanced_topics/optimizing.html).
- **32-bit address-space exhaustion:** on 64-bit Windows, a non-LAA x86 executable normally has 2 GB user space;
  LAA permits up to 4 GB, not more physical RAM or a guaranteed contiguous allocation.
  Check the PE flag first. For an unprotected compatible executable with demonstrated exhaustion, use
  [NTCore 4GB Patch](https://ntcore.com/4gb-patch/) on a backed-up EXE, verify the header changed and replay the failing workload.
  Restore the original to undo. Skip already-LAA/x64 binaries. Pointer/sign assumptions can break; updates can overwrite the patch.
  Texture reductions or a proven mod-specific allocator/leak fix may still be necessary.
  [Windows address limits](https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases).

## Gotchas

- Hook loads but FPS stays flat -> wrong bottleneck or changed visual workload -> compare the same scene/settings and inspect the new profile.
- More FPS, broken missions/physics -> timestep dependency -> restore the safe cap and use a build-specific correction.
- Missing function names -> absent/private symbols -> use module/RVA and disassembly; never invent a PDB or function identity.
- Low CPU samples during a stall -> blocked thread, I/O or GPU wait -> inspect wait/context-switch and GPU timelines.
- Crash after a game update -> stale signature/ABI -> refuse the unsupported build and relocate from a fresh trace.
- Crash on first hook -> wrong architecture/proxy collision/loader-lock work -> remove the plugin and inspect initialization/modules.
- Less reported RAM after a cleaner -> resident pages were evicted -> remove the cleaner and measure real commit/fault pressure.
  [EmptyWorkingSet semantics](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset).
