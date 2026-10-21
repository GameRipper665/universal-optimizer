# Universal optimization layers

Single-player/offline games the user owns, or servers the user hosts. Exclude protected clients, online clients,
anti-cheat and DRM changes. Engine-independent means reusable across engines, not compatible with every game.
Sources checked 2026-10-21; match instructions to the downloaded release, not a different branch's configuration.

**Identify.** Record the actual game executable, its architecture, graphics API, GPU, driver, OS and existing DLL mods.
Use [DUMPBIN headers](https://learn.microsoft.com/en-us/cpp/build/reference/headers) and
[imports](https://learn.microsoft.com/en-us/cpp/build/reference/imports-dumpbin); confirm dynamically because imports can be indirect.
Keep a manifest of added files and copies of originals outside the game folder. Never replace Windows system DLLs.
For loaded-module checks, select the game in [Process Explorer](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer)
and use its DLL-mode lower pane to inspect the full path/version. A file beside the EXE is not proof that Windows loaded it.

**Where the time usually goes.** Capture a repeatable scene with [PresentMon](https://github.com/GameTechDev/PresentMon).
Compare frame-time graphs, tail frame times, CPU/GPU busy time, memory pressure and loading time, not just average FPS.
Lower resolution temporarily: a large gain suggests GPU work; little gain suggests CPU, pacing or another limit.
Separate cold shader compilation from repeat runs. Change one layer at a time and repeat the same route several times.
For generated frames, report base/rendered FPS separately from displayed FPS and measure responsiveness too.

## Tier 1: config and launch options (no files added)

### GPU selection, power and presentation

- **Per-app GPU:** Windows Settings > System > Display > Graphics, add the actual executable, choose High performance,
  save and restart. Verify the selected GPU in the capture. This fixes wrong-adapter selection, not a slow dGPU.
  It costs battery/heat; remove the preference or restore Let Windows decide to undo.
  [Windows graphics preferences](https://support.microsoft.com/en-au/windows/hardware/display-graphics/optimizations-for-windowed-games-in-windows-11).
- Preferences live under `HKCU\Software\Microsoft\DirectX\UserGpuPreferences`; let Settings serialize the value.
  Preserve any existing fields instead of replacing the entire key with a tweak pack.
  [Microsoft support confirmation](https://learn.microsoft.com/en-us/answers/questions/3938578/managing-the-list-of-apps-on-multiple-videocards).
- **Power:** record the current Control Panel > Power Options plan. Start with Balanced; on AC, compare
  Settings > System > Power & battery > Power mode > Best performance. Restore the original mode after testing.
  Higher power can help constrained clocks, but adds heat and can worsen sustained thermal throttling.
  A custom plan can hide the power-mode selector; select Balanced to expose it.
  [Microsoft power-mode instructions](https://support.microsoft.com/en-us/windows/change-the-power-mode-for-your-windows-pc-c2aff038-22c9-f46d-5ca0-78696fdf2de8).
- **Game Mode:** Settings > Gaming > Game Mode. Keep enabled as the baseline, then A/B only for a reproducible regression.
  It changes resource scheduling, not engine work; background workloads may receive less attention.
  Restore the toggle to undo. [Xbox instructions](https://support.xbox.com/en-US/help/games-apps/game-setup-and-play/use-game-mode-gaming-on-pc).
- **HAGS:** Hardware-accelerated GPU scheduling in Display > Graphics settings, where supported. Restart after changing.
  It moves scheduling work to supported GPU hardware/drivers; gains are workload-dependent and regressions are possible.
  Compare the same driver and scene; restore and restart to undo. Check any frame-generation implementation's prerequisites.
  [Microsoft HAGS explanation](https://devblogs.microsoft.com/directx/hardware-accelerated-gpu-scheduling/).
- **Windowed optimization:** Windows 11's Optimizations for windowed games upgrades compatible windowed/borderless
  D3D10/11 presentation from blt to flip. Enable in Display > Graphics; restart and compare latency/presentation mode.
  Disable per application if it causes a regression; Auto HDR can also enable it.
  [Microsoft scope and steps](https://support.microsoft.com/en-au/windows/hardware/display-graphics/optimizations-for-windowed-games-in-windows-11).
- **Fullscreen optimizations:** leave Windows defaults first. If a specific game regresses, EXE Properties > Compatibility >
  Disable fullscreen optimizations is a reversible A/B test. It can change overlay, alt-tab and presentation behavior.
  Disabling it globally is not an FPS prescription. [Microsoft explanation](https://devblogs.microsoft.com/directx/demystifying-full-screen-optimizations/).

### Driver settings and CPU placement

- **Shader cache:** NVIDIA Control Panel > Manage 3D settings > Shader Cache Size. Driver Default first; raise the disk
  budget only when cache eviction is plausible and space is available. More disk use can avoid repeat compilation;
  it cannot precompile unseen shaders. Restore the prior limit to undo. Do not clear caches between normal play sessions.
  Driver installation can invalidate them. [NVIDIA setting, introduced in R495](https://www.nvidia.com/content/Control-Panel-Help/vLatest/en-gb/mergedProjects/nv3dENG/Manage_3D_Settings_%28reference%29.htm).
- **NVIDIA Profile Inspector:** download from [Orbmu2k](https://github.com/Orbmu2k/nvidiaProfileInspector), extract,
  open `nvidiaProfileInspector.exe`, select the game's profile and export its `.nip` backup before changing a setting.
  Apply Changes, relaunch and measure; import the backup or restore the individual setting to undo.
  Hidden compatibility bits are driver/game-specific and can break rendering; never import a global performance pack.
- **AMD equivalent:** use AMD Software's per-game profile rather than NVIDIA bit values. Where exposed, Radeon Chill
  reduces work with a cap, while Radeon Anti-Lag targets latency. These are different objectives; legacy implementations
  cannot enable both simultaneously. Restore the profile to undo; availability depends on driver, API and GPU.
  [AMD controls](https://www.amd.com/en/resources/support-articles/faqs/DH-026.html).
  AMD's older Shader Cache control is AMD optimized by default; it is not a promise that current Adrenalin exposes a size slider.
  [AMD legacy settings reference](https://www.amd.com/en/resources/support-articles/faqs/dh-012.html).
- **Resizable BAR / Smart Access Memory:** check platform, motherboard BIOS and GPU firmware support before changing firmware.
  Follow that board's documented ReBAR/Above 4G decoding/UEFI requirements; do not blindly change boot mode on an existing install.
  Verify NVIDIA Control Panel > System Information > Resizable BAR: Yes; AMD platforms use the supported SAM status/control.
  Measure per game: enabled hardware does not guarantee a gain. Restore the previous supported setting for regressions.
  [NVIDIA requirements and verification](https://nvidia.custhelp.com/app/answers/detail/a_id/5165),
  [AMD SAM status/toggle in Performance Tuning](https://www.amd.com/en/resources/support-articles/faqs/DH3-020.html).
- **Priority:** Normal first. Only test Above normal after a trace shows competing runnable CPU work; revert after the run.
  Priority does not add CPU capacity. High can starve supporting work; Realtime can make Windows unresponsive.
  [Windows priority classes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setpriorityclass).
- **Hybrid P/E cores:** keep current Windows 11 scheduling and chipset support first. For a measured placement problem,
  test a temporary process affinity in Task Manager > Details > Set affinity after identifying the actual core topology.
  Do not publish a universal hexadecimal mask. Restricting cores can starve loading/worker threads and overrides Thread Director.
  Restore all processors or restart the process. [Intel hybrid guide](https://www.intel.com/content/www/us/en/developer/articles/guide/12th-gen-intel-core-processor-gamedev-guide.html).
- **Multi-CCD X3D:** for asymmetric dual-CCD parts such as 7900X3D/7950X3D, install AMD's appropriate chipset package,
  including AMD 3D V-Cache Performance Optimizer support; retain Game Mode and an installed, updated Xbox Game Bar.
  Game identification participates in placing games on the cache CCD. Do not remove those dependencies as debloat.
  Check thread placement/parking under the actual game before trying a temporary single-CCD affinity; fewer workers can hurt.
  This is not a requirement to park half of a single-CCD X3D CPU.
  [AMD setup guide](https://community.amd.com/t5/gaming/how-to-set-up-your-system-with-a-new-amd-ryzen-9-7950x3d-or/ba-p/589464).

### Memory and false optimizations

The working set is resident pageable memory, not total allocation, private commit or reserved address space.
High reported RAM is not itself a leak. Correlate rising commit/address-space use or hard faults with the hitch;
soft faults do not require disk access. [Windows working-set definitions](https://learn.microsoft.com/windows/win32/memory/working-set).
Reduce texture quality or remove oversized texture mods when residency/streaming pressure is measured: less detail buys memory headroom.
Use a game's documented allocator/leak fix only for the matching build; a smaller Task Manager number alone proves nothing.
For a concrete example, [SilentPatch for classic San Andreas](https://silentsblog.com/mods/gta-sa/) fixes an in-game camera-photo
memory leak. That supports fixing the leaking path, not installing an arbitrary heap replacement in every native game.

- **RAM cleaners / RAM boosters / EmptyWorkingSet:** useless as game optimization. Trimming evicts resident pages,
  then later accesses fault them back; it does not repair a leak or reduce required allocations and can worsen hitches.
  [What EmptyWorkingSet actually does](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset).
- **Disable the page file:** not an FPS fix. It reduces commit headroom and can turn a busy scene into an allocation failure.
  Keep system-managed sizing unless measured requirements justify a deliberate alternative; restore it if previously disabled.
  [Microsoft commit-limit explanation](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/introduction-to-the-page-file).
- **Random registry packs:** reject changes without a documented mechanism, matching OS applicability, baseline and rollback.
  A bundle changing many variables cannot establish which change helped; some changes can disable useful scheduling or caching.
- **Timer-resolution tools:** not a universal FPS boost. Since Windows 10 2004, `timeBeginPeriod` no longer guarantees
  a global higher resolution for other processes. On Windows 11, fully occluded/minimized/invisible or inaudible window-owning
  processes are not guaranteed higher resolution. It can improve timed waits in the requesting process, at a power/scheduling cost;
  it does not improve the performance counter's accuracy. Fix a demonstrated limiter/wait bug, not the system clock by folklore.
  [Current Microsoft contract](https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod).

## Tier 2: drop-in community fixes and runtime swaps

### Render API translation

**DXVK: D3D8/9/10/11 to Vulkan.** Prefer official [releases](https://github.com/doitsujin/dxvk/releases).
Native Windows use is [not officially supported](https://github.com/doitsujin/dxvk/wiki/Windows).
CPU-bound, draw-call-heavy DX9/DX11 titles are candidates, especially when native driver overhead dominates the trace.
That is a test hypothesis, not an engine-wide gain. GPU-bound work, translation overhead, extra memory and cold compilation
can make it slower. Windows presentation, overlays and vendor-specific graphics extensions can also regress.

1. Close the game; back up colliding local DLLs. Select `x32` or `x64` for the executable, not for the OS.
2. Copy only the required set beside the rendering executable, all from the same release:
   D3D8: `d3d8.dll` + `d3d9.dll`; D3D9: `d3d9.dll`; D3D10: `d3d10core.dll` + `d3d11.dll` + `dxgi.dll`;
   D3D11: `d3d11.dll` + `dxgi.dll`. [Official dependency list](https://github.com/doitsujin/dxvk#dll-dependencies).
3. In the launch working directory, create `dxvk.conf` containing `dxvk.hud = version,api,devinfo,compiler,frametimes`.
   Confirm the version/API/GPU overlay and compiler activity. An absolute `DXVK_CONFIG_FILE` overrides the config location.
   [Config lookup](https://github.com/doitsujin/dxvk/wiki/Configuration), [HUD fields](https://github.com/doitsujin/dxvk#hud).
4. Benchmark cold and warm runs separately. Remove the copied DLLs/config and restore originals to uninstall.
   If it does not load locally, stop and inspect modules; do not replace system copies to force it.

Relevant keys are release-specific; use the downloaded release's [annotated dxvk.conf](https://github.com/doitsujin/dxvk/blob/master/dxvk.conf):

| Key / test | Purpose and trade-off |
| --- | --- |
| `dxgi.maxFrameLatency = 1` / `d3d9.maxFrameLatency = 1` | Restrict queued frames; can reduce latency but lose throughput. Default `0` leaves the override inactive. |
| `dxgi.maxFrameRate = 60` / `d3d9.maxFrameRate = 60` | Compatibility cap when a better limiter is unavailable; lower maximum FPS. Upstream recommends external limiters instead. |
| `dxvk.numCompilerThreads = 0` | Automatic use of available cores; a smaller positive count reduces contention but prolongs compilation. |
| `dxvk.enableGraphicsPipelineLibrary = Auto` | Leave automatic supported-driver use enabled; disabling can increase stutter. |
| `dxvk.allowFse = True` | Windows-only troubleshooting for fullscreen presentation/VRR issues; retest alt-tab and stability. [Windows notes](https://github.com/doitsujin/dxvk/wiki/Windows). |

Remove each override to undo. Do not inflate reported VRAM as a substitute for memory capacity.
DXVK 2.0 introduced graphics pipeline library use to compile earlier when shaders are loaded; it does not eliminate all stutter.
Older releases have different GPU/driver requirements; check the [selected release](https://github.com/doitsujin/dxvk/releases/tag/v2.0)
and [driver support](https://github.com/doitsujin/dxvk/wiki/Driver-support).
`dxvk.enableAsync` is not an upstream configuration key. Async forks are separate builds, not a switch to paste into stock DXVK;
do not mix their instructions or assume skipped/wait-free compilation has no rendering trade-off.

**dgVoodoo2: Glide, DirectDraw and D3D1–8-era games.** It implements these APIs over D3D11/12; current releases also support D3D9.
Download from [Dege](https://dege.freeweb.hu/dgVoodoo2/); do not confuse it with similarly named download sites.
For a typical x86 game, copy the required `MS\x86` wrappers beside the EXE: `DDraw.dll`/`D3DImm.dll` for old DX,
or `D3D8.dll` for DX8. For Glide use the matching `3Dfx\x86` DLLs (`Glide.dll`, `Glide2x.dll`, `Glide3x.dll`) as required.
Use `dgVoodooCpl.exe` to select that game directory and save `dgVoodoo.conf`; leave resolution/MSAA unforced first.
Confirm the dgVoodoo watermark or the loaded local wrapper. Remove only added wrappers/config and restore originals to undo.
Compatibility can improve while FPS falls; forced resolution, MSAA and software WARP rendering add substantial work.
[Official behavior/configuration](https://dege.freeweb.hu/dgVoodoo2/ReadmeGeneral/),
[wrapper filenames confirmed by DxWnd's developer](https://sourceforge.net/p/dxwnd/discussion/general/thread/4370aa3d0d/).

**d3d8to9:** D3D8 calls/shaders become D3D9, not Vulkan. Download [crosire's release](https://github.com/crosire/d3d8to9/releases),
place `d3d8.dll` beside the game EXE and verify its local module path; remove it/restore any prior wrapper to undo.
Useful for compatibility or a D3D9 tool chain. VSync can now follow the game's request correctly and appear to lower FPS.
Do not combine its `d3d8.dll` with another DX8 wrapper. [Project scope and VSync caveat](https://github.com/crosire/d3d8to9).

**vkd3d-proton:** D3D12 to Vulkan, primarily a Proton component. Native Windows use is mainly developer testing, not a routine upgrade.
Only trial it for an identified D3D12 compatibility/driver problem: matching-architecture `d3d12.dll` + `d3d12core.dll`,
plus compatible DXVK `dxgi.dll` (DXVK 2.1+), all locally beside the actual EXE. Confirm local loaded modules and Vulkan activity.
Translation/features can regress; if system/Agility runtime loading bypasses the proxy, do not force system-wide replacements.
Remove added files and restore originals to undo. [Official Windows scope and dependencies](https://github.com/HansKristian-Work/vkd3d-proton#using-vkd3d-proton).

### Upscaler and frame-generation injection

**OptiScaler:** needs existing DLSS 2+, FSR 2+ or XeSS inputs. Current upstream supports D3D11, D3D12 and Vulkan,
with backend-specific restrictions; experimental OptiFG is D3D12-only. It cannot infer missing motion/depth inputs in an arbitrary game.
FSR2/custom integrations vary; UE XeSS inputs lack depth needed by some replacements.
[Compatibility and API matrix](https://github.com/optiscaler/OptiScaler#which-apis-and-upscalers-are-supported).

1. Get the official [stable release](https://github.com/optiscaler/OptiScaler/releases/latest); check its game compatibility entry.
2. Extract the complete package beside the actual game EXE; run the included `setup.bat` and select the actual GPU/input route.
   Manual alternative: rename `OptiScaler.dll` to supported `dxgi.dll`, provided that name is free. Keep `OptiScaler.ini` unchanged in name.
   [Automated steps](https://github.com/optiscaler/OptiScaler/wiki/Automated-Installation), [manual steps](https://github.com/optiscaler/OptiScaler/wiki/Manual-Installation).
3. Select the game's supported upscaler as input; press Insert and select the replacement output in OptiScaler.
   Verify both active input and output, not merely that the overlay opened. Compare reconstructed detail, ghosting and GPU time.
4. Remove the package's added files/renamed proxy and restore originals using the installation manifest to uninstall.
   D3D11-to-D3D12 interop can add overhead; a newer/higher-quality output may be slower. [Upstream limitations](https://github.com/optiscaler/OptiScaler).

**DLSS DLL swaps:** [DLSS Swapper](https://github.com/beeradmoore/dlss-swapper) upgrades/downgrades existing integrations;
it does not add DLSS. Install the official release, select/add the game, download the chosen library version and swap that component.
Restore the original through the tool to undo. For a manual Super Resolution swap, back up and replace the matching `nvngx_dlss.dll`;
do not rename SR into the frame-generation or ray-reconstruction component. Verify loaded module path/version, then visual output.
The game can load another copy or an NVIDIA override; a changed disk version alone is insufficient. Crashes/artifacts/slower inference are possible.
[NVIDIA DLSS SDK and libraries](https://github.com/NVIDIA/DLSS).

**NVIDIA override:** for supported RTX games, NVIDIA app > Graphics > game's Driver Settings > DLSS Override - Model Presets.
Use the current Recommended option where offered; select the game's DLSS mode too. This can update behavior without replacing game files.
For verification, Alt+Z > Statistics > Statistics View > DLSS shows override status; Alt+R toggles it in-game.
Compare an A/B capture; restore Use the 3D application setting to undo.
Model cost and GPU eligibility differ; do not freeze a “latest preset” letter in a universal recipe.
[NVIDIA instructions](https://nvidia.custhelp.com/app/answers/detail/a_id/5620),
[current Recommended behavior](https://www.nvidia.com/en-gb/geforce/news/nvidia-app-dlss-4-5-dynamic-multi-frame-generation-available-now/),
[overlay verification](https://www.nvidia.com/en-us/geforce/news/nvidia-app-global-dlss-overrides-rtx-40-series-smooth-motion/).

**FSR3 frame-gen mods:** [Nukem9's standalone dlssg-to-fsr3](https://github.com/Nukem9/dlssg-to-fsr3) replaces existing DLSS-G;
its README targets GeForce 16/RTX 20/30-series hardware. Do not extend that support claim to every fork or bundled version.
For its documented Universal Method, copy `version.dll` and `dlssg_to_fsr3_amd_is_better.dll` beside the game's EXE.
Confirm `dlssg_to_fsr3.log`, enable the game's FG control and check frame delivery; remove these added files/log to undo.
This route requires no signature-registry changes. OptiScaler 0.9+ bundles a related route; use its own FG input/output instructions instead
of installing two copies. [OptiScaler FG routes](https://github.com/optiscaler/OptiScaler/wiki/Frame-Generation-Options).
Expect HUD/motion artifacts, more GPU/VRAM work and possible latency. Generated frames do not accelerate simulation or input sampling.

**Lossless Scaling:** paid [Steam application](https://store.steampowered.com/app/993090/Lossless_Scaling/), independent of the game's rendering API.
Buy/install in Steam, run the game windowed/borderless, choose scaling and/or LSFG in the app, activate Scale and focus the game.
Verify its capture/output counter and visible scaling; exit scaling or close/uninstall the app to remove, with no game DLLs to restore.
It can capture most windowed games without built-in upscaler inputs; “anything windowed” is not guaranteed capture compatibility.
Leave GPU headroom and a steady base cap. Interpolation adds artifacts and processing/buffering latency; high displayed FPS can still feel sluggish.

### Frame pacing: Special K and RTSS

**Special K global:** install [Special K](https://www.special-k.info/), open its frontend and launch the selected offline game through it.
The global injector lives outside the game; stop its injection service and relaunch the game to remove injection.
[Global mode](https://wiki.special-k.info/SpecialK/Global).
**Local:** use `SpecialK32.dll` or `SpecialK64.dll` matching the process; copy beside the EXE and rename to `d3d9.dll` (DX9),
`dxgi.dll`/`d3d11.dll` (DX11), `dxgi.dll` (DX12) or `opengl32.dll` (OpenGL). Remove that added proxy to undo.
Do not overwrite another layer's proxy. Confirm the startup banner and Ctrl+Shift+Backspace control panel.
[Local installation and API restrictions](https://wiki.special-k.info/SpecialK/Local).

In the panel, enable Framerate Limit; Ctrl+click allows a precise number. Test a sustainable cap below saturation/VRR ceiling,
not an arbitrary maximum. Special K can force flip-model presentation in D3D11; retest alt-tab, overlays and latency after enabling it.
Latency features are API/GPU-specific, and aggressive queue limits can reduce throughput. Restore panel settings to undo.
[Video controls](https://wiki.special-k.info/en/Advanced/Video).
Its D3D11 texture cache can avoid repeated texture creation at the cost of retained RAM/VRAM and compatibility risk.
If textures corrupt or memory grows, disable Enable Texture Caching under D3D11 texture management and restart.
[Official cache troubleshooting](https://wiki.special-k.info/Compatibility/Issues).

**RTSS:** install the official [Guru3D package](https://www.guru3d.com/download/rtss-rivatuner-statistics-server-download/),
use Add to select the actual EXE and set its Framerate limit, initially e.g. 60 where gameplay supports it.
It supports DirectX, OpenGL and Vulkan applications; wrapper/overlay compatibility still needs checking.
Verify a frame-time plateau around 16.67 ms at 60 FPS; close RTSS and restart the game for a clean no-hook comparison.
Remove the profile/restore its settings or uninstall RTSS to undo.
Use one active limiter. A cap can remove saturation-induced queuing and pacing variation by leaving CPU/GPU headroom;
it trades peak FPS for consistency and cannot fix a 100 ms asset/shader stall. Prefer a good native limiter when it measures better.

### 32-bit memory headroom

On 64-bit Windows, a non-large-address-aware x86 game normally has 2 GB user virtual address space; LAA allows up to 4 GB.
This is an address-space limit, not a physical-RAM allocation or a general FPS multiplier.
Check the PE header first; skip x64 and already-LAA games. Only consider a patch for demonstrated allocation/address-space exhaustion
in a compatible unprotected executable. [Windows limits](https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases).
Download [NTCore's 4GB Patch](https://ntcore.com/4gb-patch/), close the game, back up the actual EXE, run the tool and select that EXE.
The tool also creates a backup. Verify the LAA header flag, then replay the failing scene/long session and check allocation failures.
Restore the original EXE to undo. Game updates can overwrite the patch; signed-pointer/address assumptions can cause new crashes.
It cannot cure a leak, texture overcommit or fragmentation. Lower texture/mod budgets or use the matching game's proven memory fix as needed.

### Linux / Steam Deck, briefly

Select Valve's supplied Proton version per game first. In Steam Properties > Launch Options, use one diagnostic change at a time:
`PROTON_LOG=1 %command%` creates `~/steam-<APPID>.log` for verification, with logging overhead/disk use.
`PROTON_USE_WINED3D=1 %command%` tests OpenGL instead of DXVK for DX9/10/11; usually a compatibility fallback, possibly slower.
`PROTON_NO_D3D11=1 %command%` only helps games with a working DX9 fallback and can lose rendering features.
`PROTON_NO_FSYNC=1` / `PROTON_NO_NTSYNC=1` disable synchronization paths for diagnosed regressions; they can cost CPU performance.
Do not force historical synchronization recipes across Proton versions. Remove variables to revert.
[Current Proton runtime options](https://github.com/ValveSoftware/Proton#runtime-config-options).

With distro-provided packages installed, `gamemoderun %command%` requests temporary OS tuning; compare power/thermals and remove to undo.
[GameMode](https://github.com/FeralInteractive/gamemode).
`mangohud %command%` measures FPS/frame times/load for supported Vulkan/OpenGL paths; remove to undo overlay overhead.
Under gamescope use its supported mangoapp integration instead; Steam Deck's built-in performance overlay is the simpler baseline.
[MangoHud usage and gamescope limitation](https://github.com/flightlessmango/MangoHud#normal-usage).

## Tier 3: code-level patches (profile -> patch the hot path)

If a layer only moves the bottleneck, use the [native playbook](engines/native.md) to identify the expensive caller or wait.
Patch the proven engine path rather than stacking more wrappers. Keep the layer version and a complete rollback manifest with the result.

## Gotchas

- Startup crash -> wrong architecture, colliding proxies or an incompatible API path -> restore the last layer and inspect loaded modules.
- Overlay visible, performance unchanged -> successful injection is not proof of a useful optimization -> compare the actual bottleneck.
- First run worse -> cold shader work -> report cold and warm results, preserving caches for normal play.
- More displayed FPS, worse control -> interpolation/queue latency -> raise base FPS, reduce saturation or disable frame generation.
- Higher RAM after caching -> retained useful assets or excess residency -> inspect faults/commit and cache growth before disabling it.
