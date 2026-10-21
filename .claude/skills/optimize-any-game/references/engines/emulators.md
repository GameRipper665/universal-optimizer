# Console emulators on PC

**Legal scope first.** Only optimize offline games the user owns, using games and firmware/BIOS/keys dumped from hardware the user owns. Never link or describe ROM, firmware, BIOS, or key download sources. Never bypass console DRM beyond the emulator's own documented dumping process. Ownership is a scope requirement, not a claim that every dumping method is lawful everywhere. No online-client or anti-cheat changes.

**Verification date: 2026-10-21.** Settings below refer to the cited desktop documentation/source inspected on this date, unless a version is specified. Nightlies change: record the exact build, game serial/region, update/build ID, backend, driver, patches, and cache state. A live website alone does not prove maintenance.

**Identify.** Identify the emulator process and guest game separately; a console image's extension does not identify the emulator. Locate its actual user directory before editing: portable installs and frontends can redirect it. Back up configuration and saves with `um backup`; record restore commands in `OPTLOG.md`.

**Where the time usually goes.** CPU emulation, synchronization, shader compilation, GPU rendering, and storage/cache misses. Single-thread throughput often matters, but modern emulators also distribute work across cores. GPU cost grows with internal resolution; GPUs can also limit native-resolution accuracy paths and ubershaders. “GPU only matters at high resolution” is not a safe rule. [PCSX2 counters](https://pcsx2.net/docs/troubleshooting/performance/), [Dolphin ubershaders](https://dolphin-emu.org/blog/2017/07/30/ubershaders/).

Shader compilation is a common first-run stutter cause; a universal “#1 complaint” ranking is **(unverified)**. Compare a cold traversal with a repeat traversal. Ubershaders spend GPU work to cover compilation; async compilation may omit graphics; persistent/precompiled caches trade disk space and startup time for fewer later stalls. Generate caches from the user's own play; use documented pre-build/compile-before-start options on those caches. A downloaded pre-built cache is not a universal stutter fix. Do not distribute game-derived shader bundles here. [Dolphin guide](https://dolphin-emu.org/docs/guides/performance-guide/).

Measure `uo bench <emulator-pid> --seconds 60 -o before1.json` twice, then repeat after one change and run `uo compare before1.json after1.json`. Use PresentMon 2.x on the rendering process, not its launcher. Also record the emulator's FPS/VPS/speed% counters where available: presentation can duplicate guest frames, and 60 presents need not mean 60 distinct game frames. PPSSPP explicitly offers duplicate presentation.
[PPSSPP graphics](https://www.ppsspp.org/docs/settings/graphics/). Keep scene, game speed, cache warmth, and frame target constant; a 60 FPS mod is a separate workload. Keep improvements beyond repeat-run noise, then check saves, menus, audio, physics, and effects; otherwise restore.

## RPCS3 — PlayStation 3

**Identify.** `rpcs3.exe`; Windows configurations include `config.yml` and logs include `RPCS3.log` in the emulator directory. Record the title serial and custom configuration, not just global settings. [Configuration/log layout](https://github.com/RPCS3/rpcs3/issues/16478).

**Where the time usually goes.** PPU/SPU execution, compilation, RSX synchronization, and scaled rendering; compare warm runs at 100% scale and inspect busiest-thread/GPU times before changing CPU knobs. [Configuration definitions](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/system_config.h).

### Tier 1: config and launch options (no files added)

- CPU: use `PPU decoder` and `SPU decoder` → `Recompiler (LLVM)` normally; cached compilation costs startup time. Interpreters are compatibility/debug fallbacks; SPU ASMJIT is another fallback. [Decoder tooltips](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/rpcs3qt/tooltips.h).
- `SPU block size`: `Safe` favors compatibility; `Mega`/`Giga` join larger compilation units and can improve speed or regress compatibility. `Preferred SPU threads`: start `Auto`; fewer can reduce stalls in particular games, but can also slow them down. This is not a host-core-count setting. [CPU tooltips](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/rpcs3qt/tooltips.h).
- GPU: start `Renderer = Vulkan`; compare OpenGL for rendering problems. Keep `Default resolution = 1280x720` and adjust `Resolution scale`; higher scale costs GPU work/memory, and below 100% usually does not help. [GPU tooltips](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/rpcs3qt/tooltips.h).
- `Write color buffers` fixes required effects/lighting but can cost performance and stutter. Apply the title's wiki recommendation; never disable a required buffer write just to improve a counter. [Per-title configuration index](https://wiki.rpcs3.net/index.php?title=Help:Configurations).
- `Shader mode = Async with Shader Interpreter` renders approximations while shaders compile; plain `Async` may show pop-in. Interpreter-only is slow. Use the installed build's labels. [Shader tooltips](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/rpcs3qt/tooltips.h).
- CPU capability matters beyond clock speed: AVX-512 can reduce SPU instruction/register overhead on supported CPUs; no fixed percentage applies to every game. It is a benefit, not a universal requirement. Do not change BIOS/microcode to obtain it. Check the current [requirements](https://rpcs3.net/quickstart) and [developer explanation](https://whatcookie.github.io/posts/why-is-avx-512-useful-for-rpcs3/).

### Tier 2: drop-in community fixes and runtime swaps

Use a per-game configuration and the title's recommended wiki settings. Use RPCS3's Patch Manager for matching 60 FPS/fix patches; match executable hash, serial, and update. Disable the patch and restore the custom config to undo. Higher targets need more CPU/GPU capacity and can expose timing bugs. [Patch guide](https://wiki.rpcs3.net/index.php?title=Help:Game_Patches), [manager source](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/rpcs3qt/patch_manager_dialog.cpp).

### Tier 3: code-level patches (profile → patch the hot path)

Use the shared profiling route below; separate guest SPU cost from host RSX waits. Prefer existing patch entries or an upstream emulator fix over guest-binary edits; AVX-512 lowering is a verified optimization pattern. [RPCS3 releases](https://github.com/RPCS3/rpcs3/releases).

### Gotchas

Missing effects after a “boost” → restore buffer/accuracy requirements. Worse stutter after a cache purge → allow compilation again. A 60 FPS patch can conflict with a game's stability fixes. [Fallout 3 example](https://wiki.rpcs3.net/index.php?title=Fallout_3).

## Switch emulation — identify the actual fork

**Project status, as checked 2026-10-21.** Original yuzu and Citra development ended in March 2024 following Nintendo's lawsuit; Citra was a **3DS**, not Switch, emulator. Do not treat a reused name as official continuity. The original team's [shutdown statement](https://citra-emu.org/?lang=hi) confirms both projects ended. Original Ryujinx ended on **2024-10-01**; Ryubing explicitly identifies itself as a fork/QoL continuation. [Ryubing statement](https://docs.ryujinx.app/).

- **Eden:** active development verified: the official repository showed commits through **2026-10-19**. Follow the source/release links from [eden-emu.dev](https://eden-emu.dev/) to its [own Forgejo repository](https://git.eden-emu.dev/eden-emu/eden/).
- **Ryubing/Ryujinx continuation:** provenance verified through the [Ryubing organization](https://github.com/Ryubing) and [own documentation](https://docs.ryujinx.app/). Its linked forge timed out during this audit; current emulator release cadence/maintenance freshness is **(unverified)**. Organization activity alone is insufficient.
- **Citron:** current maintenance and the reported discontinuation are **(unverified)** from accessible primary material; its [original forge](https://git.citron-emu.org/Citron/Emulator) was unavailable. Do not recommend it as active or endorse a similarly named successor without a verified ownership/source chain.
- **Sudachi:** current maintenance and the reported discontinuation are **(unverified)** from accessible primary material; the [original site](https://sudachi.emuplace.app/) was unavailable. Do not substitute an unofficial mirror.

**Identify.** Ryubing uses `Config.json` in `File > Open Ryujinx Folder`; Windows data normally lives under `%APPDATA%\Ryujinx`, including logs. Eden exposes `File > Open Eden Folder`; Windows logs normally live in `%APPDATA%\Eden\log`, or the portable user folder. [Ryubing](https://docs.ryujinx.app/), [Eden log guide](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/docs/user/HowToAccessLogs.md).

**Where the time usually goes.** ARM translation, shader/pipeline compilation, texture decoding, and GPU/VRAM pressure. Compare warm runs, native scale, and memory use; Ryubing's PPTC addresses CPU translation/loading. [Setup guide](https://docs.ryujinx.app/guides/setup-guide/).

### Tier 1: config and launch options (no files added)

- Test Vulkan against the fork's supported alternative; preserve game-specific accuracy defaults. Eden's `Advanced/Use persistent cache` and `Advanced/Use Vulkan pipeline cache` retain different cache layers; keep them enabled normally, paying disk/startup costs. Unsafe CPU arithmetic can break games. [Eden settings](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/docs/user/Settings.md).
- Eden's ASTC decoder supports CPU, GPU, and asynchronous CPU decoding: move work according to the measured bottleneck; async decoding can expose textures late. ASTC recompression `Uncompressed`/`BC1`/`BC3` trades memory against recompression work and lossy texture quality; compare VRAM and visuals, not just FPS. [Setting definitions](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/src/common/settings.h), [ASTC tooltips](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/dist/languages/cs.ts).
- Start at 1× resolution. Higher scale costs GPU/VRAM; handheld mode can lower the game's own quality/resolution versus docked, depending on the title. Keep Ryubing `PPTC` enabled; its benefit requires multiple launches and is primarily loading/translation, not guaranteed sustained FPS. [Ryubing configuration](https://docs.ryujinx.app/guides/setup-guide/).
- Eden's `use_asynchronous_shaders` is a rendering hack, distinct from cache persistence; test for missing graphics before keeping it. Do not assume Eden, Citron, Sudachi, and Ryubing share keys or defaults. [Eden source](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/src/common/settings.h).

### Tier 2: drop-in community fixes and runtime swaps

Use Eden's `Open Mod Data Location` or Ryubing's `Manage Mods`/`Open Mods Directory`; a 60 FPS or widescreen mod must match the game update. Cheat files use `<mod-name>/cheats/<build-id>.txt` beneath the game's mod directory. These are loaders, not a promise that patches ship for every game. Disable the entry and move only that added mod aside to undo; check game speed/physics. [Eden mods](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/docs/user/Mods.md), [cheat layout](https://git.eden-emu.dev/eden-emu/eden/src/branch/master/docs/user/Storage.md), [Ryubing manager](https://docs.ryujinx.app/guides/setup-guide/).

### Tier 3: code-level patches (profile → patch the hot path)

Use the shared host-profile route; investigate translation, synchronization, or texture conversion only after warm-cache tests. Submit emulator fixes to the verified fork; keep guest changes in its mod loader.

### Gotchas

Faster animations with an FPS unlock → mismatched/timing-unsafe patch; disable it. New update breaks cheats → recheck build ID. Unreachable upstream → maintenance unknown, not permission to use a download impersonator.

## Dolphin — GameCube / Wii

**Identify.** Dolphin's user directory contains `Config`, `GameSettings`, and `Logs`; portable paths differ. Record game ID/revision and the per-game overrides. [User/data folders](https://github.com/dolphin-emu/dolphin/wiki/User-and-Data-Folders).

**Where the time usually goes.** CPU emulation, EFB readbacks, shader compilation, and GPU upscaling; confirm with native-resolution/warm-cache comparisons and FPS versus emulation speed. [Performance guide](https://dolphin-emu.org/docs/guides/performance-guide/).

### Tier 1: config and launch options (no files added)

- Compare Vulkan and D3D11/D3D12 on Windows; backend/driver behavior varies. Lower `Internal Resolution` when GPU-bound; clarity falls. `Hybrid Ubershaders` reduces compilation pauses with extra GPU work; `Exclusive Ubershaders` costs more. `Compile Shaders Before Starting` lengthens boot. [Guide](https://dolphin-emu.org/docs/guides/performance-guide/).
- `Skip Drawing` avoids compilation waits by omitting unfinished draws: visible pop-in or missing effects can persist until redrawn. This is a visual compromise, not free performance. [Ubershader design](https://dolphin-emu.org/blog/2017/07/30/ubershaders/).
- `Enable Dual Core (speedhack)` allows parallel emulation work; respect per-game overrides and revert for timing instability. Do not raise emulation speed to claim a performance gain. [General settings](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/DolphinQt/Settings/GeneralPane.cpp).
- `Skip EFB Access from CPU`, `Store EFB Copies to Texture Only`, and `Disable Bounding Box` can save work but break games that need those operations. Keep the game's compatibility settings. [Hack descriptions](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/DolphinQt/Config/Graphics/HacksWidget.cpp).

### Tier 2: drop-in community fixes and runtime swaps

Use per-game Properties' Gecko/Action Replay/patch controls with exact revision codes from the official wiki; bundled game settings supply compatibility overrides. A 60 FPS/widescreen code can increase load or introduce effects/culling bugs. Uncheck it and restart to undo. [Super Mario Sunshine example](https://wiki.dolphin-emu.org/index.php?title=Super_Mario_Sunshine), [shipped GameSettings](https://github.com/dolphin-emu/dolphin/tree/master/Data/Sys/GameSettings).

### Tier 3: code-level patches (profile → patch the hot path)

Profile host CPU/GPU work as below; use Dolphin's guest debugger for code patches. Shader fallback plus background specialization is an established upstream pattern, not a reason to rewrite game binaries. [Design](https://dolphin-emu.org/blog/2017/07/30/ubershaders/).

### Gotchas

Broken targeting/effects after EFB tweaks → restore access/copies. Ubershaders make steady FPS worse → GPU headroom is insufficient; lower resolution or compare specialized shaders with a warm cache.

## PCSX2 — PlayStation 2

**Identify.** Qt builds load `inis/PCSX2.ini` under the selected data root and write `emulog.txt` in the logs directory; the startup log prints configuration paths. [Qt startup source](https://github.com/PCSX2/pcsx2/blob/master/pcsx2-qt/QtHost.cpp), [path example](https://github.com/PCSX2/pcsx2/issues/7954).

**Where the time usually goes.** EE/VU CPU work, GS rendering, blending, and readback synchronization. Use `Settings > Graphics > OSD` counters; compare EE/GS/GPU load and native internal resolution. [Counters](https://pcsx2.net/docs/troubleshooting/performance/).

### Tier 1: config and launch options (no files added)

- Use a hardware renderer, compare Vulkan/D3D12, then lower internal resolution if GPU-bound; software rendering is an accuracy fallback with different CPU costs. Keep `Disable Shader Cache` unchecked; shader/pipeline reuse costs disk space. Do not confuse asynchronous texture loading with shader compilation. [Graphics source](https://github.com/PCSX2/pcsx2/blob/master/pcsx2-qt/Settings/GraphicsSettingsWidget.cpp).
- `Enable Multithreaded VU1 (MTVU1)` generally helps CPUs with four or more cores, but some games hang. `EE Cycle Rate = 100% (Normal Speed)` is the baseline; higher rates increase host CPU demand, while lower rates reduce guest work. `EE Cycle Skipping` often harms performance. [CPU tooltips](https://github.com/PCSX2/pcsx2/blob/master/pcsx2-qt/Settings/EmulationSettingsWidget.cpp).
- `Blending Accuracy` trades shader work for correct effects; higher is slower. Preserve automatic game fixes instead of lowering accuracy globally. A native-resolution test distinguishes costly upscaling. [Graphics tooltips](https://github.com/PCSX2/pcsx2/blob/master/pcsx2-qt/Settings/GraphicsSettingsWidget.cpp).

### Tier 2: drop-in community fixes and runtime swaps

Use the per-game Patches/Cheats controls: releases bundle `patches.zip` from the official patch repository. Select matching widescreen/no-interlacing/available frame-rate entries; 60 FPS availability is per title. External `.pnach` files go in the documented `patches` or `cheats` directory. Uncheck and restart; move only added files aside. Higher FPS may increase CPU load or break timing. [Patch format and locations](https://pcsx2.net/docs/advanced/writing-patches/), [shipped patches](https://github.com/PCSX2/pcsx2_patches).

### Tier 3: code-level patches (profile → patch the hot path)

Profile host EE/VU/GS work before using the guest debugger and `.pnach` route; interpreter/recompiler boundaries matter when interpreting samples. [PCSX2 execution model](https://wiki.pcsx2.net/index.php/PCSX2_Documentation/PCSX2_Optimization).

### Gotchas

Higher reported speed but choppier animation after cycle changes → restore normal EE timing and compare internal game frames. Hangs after MTVU → revert only that game's override; leave GameDB fixes active.

## Cemu — Wii U

**Identify.** `Cemu.exe`; Windows portable layouts use `settings.xml`, `gameProfiles`, and `log.txt` beside the executable. Check the active data root when using packaged builds. [Settings/log evidence](https://github.com/cemu-project/Cemu/blob/main/.gitignore), [game profile source](https://github.com/cemu-project/Cemu/blob/main/src/gui/wxgui/GameProfileWindow.cpp).

**Where the time usually goes.** CPU recompilation, shader/pipeline creation, GPU rendering, and CPU/GPU synchronization; compare shader notifications, warm passes, and lower-resolution graphic packs. [Graphics settings](https://github.com/cemu-project/Cemu/blob/main/src/gui/wxgui/GeneralSettings2.cpp).

### Tier 1: config and launch options (no files added)

- On PC, try `Graphics API = Vulkan` and `Async shader compile`: fewer compilation waits, but temporarily absent objects are possible. Retain locally generated caches; first-visit shaders can still compile. [UI/tooltips](https://github.com/cemu-project/Cemu/blob/main/src/gui/wxgui/GeneralSettings2.cpp).
- Per-game CPU mode: start `Auto (recommended)`; compare `Multi-core recompiler` where CPU-bound. More parallelism can expose compatibility differences. Leave `Thread quantum` alone without a game-specific reason: it changes virtual scheduling, not host clock speed. [Game profile settings](https://github.com/cemu-project/Cemu/blob/main/src/gui/wxgui/GameProfileWindow.cpp).
- OpenGL's `Full sync at GX2DrawDone()` honors guest-requested synchronization at a performance cost; removing it can break effects. Do not apply old OpenGL advice blindly to Vulkan. [Backend/UI logic](https://github.com/cemu-project/Cemu/blob/main/src/gui/wxgui/GeneralSettings2.cpp).

### Tier 2: drop-in community fixes and runtime swaps

Download community graphic packs through Cemu's Graphic Pack window. Enable only the game's resolution, widescreen, or performance/fix entries needed; lower resolution saves GPU work at a clarity cost. For Breath of the Wild, `Mods/FPS++` includes a 60 FPS target and timing fixes, but high FPS still has caveats. Disable the selected packs and restart to undo; do not add obsolete DLL helpers as a routine tweak. [Pack project](https://github.com/cemu-project/cemu_graphic_packs), [FPS++ rules](https://github.com/cemu-project/cemu_graphic_packs/blob/master/src/BreathOfTheWild/Mods/FPS%2B%2B/rules.txt).

### Tier 3: code-level patches (profile → patch the hot path)

Profile host threads; use the graphic-pack patch route for guest timing fixes. FPS++ demonstrates frame timing and fence changes with explicit compatibility costs; retain its default safeguards. [FPS++ implementation](https://github.com/cemu-project/cemu_graphic_packs/tree/master/src/BreathOfTheWild/Mods/FPS%2B%2B).

### Gotchas

Invisible objects on first encounter → test async compilation off. Cutscene crashes after an FPS patch → restore its cutscene limits and retest native FPS; a higher average does not override a regression.

## Xenia / Xenia Canary — Xbox 360

**Identify.** Record master versus Canary. Master's `xenia.config.toml` normally lives in `Documents\Xenia`; Canary/portable builds use the executable directory. Inspect the generated config and `xenia.log`; keys can differ by revision. [Options](https://github.com/xenia-canary/xenia-canary/wiki/Options), [application source](https://github.com/xenia-canary/xenia-canary/blob/canary_experimental/src/xenia/app/xenia_main.cc).

**Where the time usually goes.** CPU translation, GPU command processing, pipeline creation, and readbacks; compare cold/warm runs and 1× scaling, then inspect CPU/GPU timings. [Pipeline implementation](https://github.com/xenia-canary/xenia-canary/blob/canary_experimental/src/xenia/gpu/d3d12/pipeline_cache.cc).

### Tier 1: config and launch options (no files added)

- Windows baseline: `gpu = "any"` or D3D12; the project's options page does not recommend its older Vulkan path. `draw_resolution_scale_x = 1` and `draw_resolution_scale_y = 1` is the baseline; raising both costs pixels/VRAM and can break rendering. `render_target_path_d3d12` RTV favors speed, ROV accuracy; follow the game report. [Options](https://github.com/xenia-canary/xenia-canary/wiki/Options).
- Current Canary's `d3d12_pipeline_creation_threads = -1` selects threads automatically; `0` disables multithreaded creation. Async creation can skip draws until ready. Keep the persistent shader/pipeline store; more compiler threads compete with guest CPU work. [Exact source](https://github.com/xenia-canary/xenia-canary/blob/canary_experimental/src/xenia/gpu/d3d12/pipeline_cache.cc).
- Readback fixes such as the wiki's `d3d12_readback_resolve` cost synchronization; enable only as required by the title and generated build config. Keep `vsync = true` normally: here disabling it can change guest speed and does not simply control tearing. There is no verified universal CPU-thread “boost” preset. [Options](https://github.com/xenia-canary/xenia-canary/wiki/Options).

### Tier 2: drop-in community fixes and runtime swaps

Canary's official `game-patches` repository supplies title/update-specific 60 FPS, widescreen, and fixes. Extract its `patches` directory beside `xenia_canary.exe`, enable `apply_patches` and the desired entry's `is_enabled` flag. Preserve existing files first. Disable the entry and restart to undo; the documented system is not supported on master. Higher FPS/modified aspect can introduce timing or visual issues; aspect patches require `present_letterbox = false`, which otherwise stretches the picture. [Installation](https://github.com/xenia-canary/game-patches).

### Tier 3: code-level patches (profile → patch the hot path)

Use host profiling plus Xenia's developer facilities, then a matching `.patch.toml` entry for guest code; avoid copying unmeasured CPU/GPU hacks between games. [Developer guide](https://github.com/xenia-canary/xenia-canary/wiki/For-Developers).

### Gotchas

Twice-speed gameplay after `vsync` changes → restore it and use a compatible timing patch. Wrong update → patch may not apply. CPU-heavy games will not become faster merely by raising resolution scale.

## DuckStation — PlayStation

**Identify.** Use `Tools > Open Data Directory` for settings/saves; portable mode uses the executable directory. When file logging is enabled, `duckstation.log` is written in that data root. Record game serial and per-game overrides. [User directories](https://github.com/stenzek/duckstation#user-directories), [log destination](https://github.com/stenzek/duckstation/blob/master/src/core/settings.cpp).

**Where the time usually goes.** CPU execution, enhancements, shader setup, and GPU resolution/blending; compare native resolution, default enhancements, and repeated scenes. [Features](https://github.com/stenzek/duckstation#features).

### Tier 1: config and launch options (no files added)

- Compare Vulkan/D3D11/D3D12 hardware rendering; software rendering sacrifices scaling/performance for compatibility. `Internal Resolution` above 1× needs more GPU capacity. Leave `Disable Shader Cache` unchecked; compiling every run adds work. [Graphics tooltips](https://github.com/stenzek/duckstation/blob/master/src/duckstation-qt/graphicssettingswidget.cpp).
- Keep `Execution Mode = Recompiler (Fastest)` normally. `Enable Clock Speed Control` changes the emulated CPU: overclocking can remove original slowdown but costs host work and can break games. `Enable Recompiler ICache` improves console timing accuracy at a small performance cost. [CPU tooltips](https://github.com/stenzek/duckstation/blob/master/src/duckstation-qt/consolesettingswidget.cpp).
- `Widescreen Rendering` changes 3D geometry projection and can expose culling/HUD errors; it is not a performance improvement. PGXP/enhancement costs should be measured independently. [Graphics source](https://github.com/stenzek/duckstation/blob/master/src/duckstation-qt/graphicssettingswidget.cpp).

### Tier 2: drop-in community fixes and runtime swaps

Current releases ship a cheat/patch database, including frame-rate and aspect-ratio enhancements. Select only matching per-game entries; availability is title-specific. Uncheck and restart to undo. Validate animation speed and cutscenes after 60 FPS patches. [Official database](https://github.com/duckstation/chtdb), [README](https://github.com/stenzek/duckstation#cheats-and-patch-database).

### Tier 3: code-level patches (profile → patch the hot path)

Profile host work, then use the supported patch database format for guest changes. Check the current source license before distributing emulator modifications; a public repository is not automatically permissive. [Repository/license](https://github.com/stenzek/duckstation).

### Gotchas

PAL game “faster” after forcing 60 Hz → timing change, not optimization. Clock hacks causing crashes → restore 100% and reproduce before reporting. [Timing/overclock warnings](https://github.com/stenzek/duckstation/blob/master/src/duckstation-qt/consolesettingswidget.cpp).

## PPSSPP — PlayStation Portable

**Identify.** `ppsspp.ini` belongs to the selected memory-stick configuration; a Windows ZIP install uses `memstick` beside PPSSPP. `--log=FILE` selects an explicit diagnostic log destination. [Configuration source](https://github.com/hrydgard/ppsspp/blob/master/Core/Config.cpp), [storage](https://www.ppsspp.org/docs/troubleshooting/my-saves-wont-load/), [CLI](https://github.com/hrydgard/ppsspp/blob/master/Core/CmdLine.cpp).

**Where the time usually goes.** CPU/JIT, draw submission/skinning, texture conversion, and GPU scaling; compare rendering resolution, software skinning, and repeated scenes independently. [Graphics docs](https://www.ppsspp.org/docs/settings/graphics/).

### Tier 1: config and launch options (no files added)

- Prefer Vulkan where supported; D3D11 is a Windows alternative. Lower `Rendering resolution` to reduce GPU work at a sharpness cost. Keep JIT and the default shader cache; no universal ubershader toggle is established here. [Recommended settings](https://www.ppsspp.org/docs/settings/recommended/), [cache/JIT source](https://github.com/hrydgard/ppsspp/blob/master/Core/Config.cpp).
- Leave `Hardware transform` enabled. A/B `Software skinning`: CPU skinning can combine draw calls, but GPU skinning wins on some combinations. `Lazy texture caching` skips change checks and may corrupt text/textures. [Exact trade-offs](https://www.ppsspp.org/docs/settings/graphics/).
- `Disable GPU readbacks` and `Skip buffer effects` can remove severe overhead and required effects. `Frameskipping` discards displayed frames; it is a last-resort compromise, not better rendering FPS. Smaller `Buffer graphics commands` lowers latency but reduces parallelism. [Recommendations](https://www.ppsspp.org/docs/settings/recommended/).

### Tier 2: drop-in community fixes and runtime swaps

`Enable Cheats`, then the pause menu's Cheats controls, can download/import a database and toggle individual CWCheat entries. Use matching 60 FPS/widescreen codes only where supplied; PSP games are already widescreen, so aspect patches target a specific issue. Disable the entry and restart to undo; codes can crash games or alter timing. [Official CWCheat documentation](https://www.ppsspp.org/docs/reference/cwcheats/).

### Tier 3: code-level patches (profile → patch the hot path)

Profile host draw submission/texture work, then use the debugger and CWCheat route for guest patches; do not replace the user's image. Validate patched timing against native behavior. [Code format](https://www.ppsspp.org/docs/reference/cwcheats/).

### Gotchas

60 presents with a 30 FPS game → `Render duplicate frames` may be active; measure distinct guest frames. Missing effects after a speedhack → restore readbacks/buffering before diagnosing a driver problem. [Graphics](https://www.ppsspp.org/docs/settings/graphics/).

## shadPS4 — PlayStation 4, early/experimental

**Identify.** Record the emulator commit, launcher, CUSA ID, and update. Current source writes `config.json` in its user directory, with separate game JSON configs; older builds used `config.toml`. Resolve logs through the active user directory (`log` subfolder), not a copied old guide. [Path names](https://github.com/shadps4-emu/shadPS4/blob/main/src/common/path_util.h), [Config migration](https://github.com/shadps4-emu/shadPS4/blob/main/src/core/emulator_settings.cpp), [paths](https://github.com/shadps4-emu/shadPS4/blob/main/src/common/path_util.cpp).

**Where the time usually goes.** Vulkan translation/pipelines, synchronization/readbacks, CPU services, and missing implementation. Check [compatibility](https://github.com/shadps4-compatibility/shadps4-game-compatibility) before interpreting every slowdown as tunable. [Project scope](https://github.com/shadps4-emu/shadPS4).

### Tier 1: config and launch options (no files added)

- Use the supported Vulkan device/driver required by the current [quickstart](https://github.com/shadps4-emu/shadPS4/wiki/I.-Quick-start-%5BUsers%5D). Current source exposes `Enable Shader Cache`; compare cold and warm traversal, accepting disk use and possible cache regressions. A universal async/ubershader prescription is **(unverified)**. [Current UI](https://github.com/shadps4-emu/shadPS4/blob/main/src/imgui/big_picture/settings_dialog_imgui.cpp).
- Resolution changes may require a title-specific patch; resizing the window is not proof of lower internal rendering cost. A general internal-resolution multiplier is **(unverified)** in the inspected settings. Higher-resolution patches increase GPU/memory demand. [GPU settings](https://github.com/shadps4-emu/shadPS4/blob/main/src/core/emulator_settings.h).
- Leave `Vblank Frequency` and `Readbacks Mode` at the build/game's required values; changing timing or omitting readbacks can break gameplay/effects. There is no verified generic CPU-decoder speed preset; keep diagnostic shader dumping off during benchmarks. [Settings source](https://github.com/shadps4-emu/shadPS4/blob/main/src/core/emulator_settings.h).

### Tier 2: drop-in community fixes and runtime swaps

Use the project's cheats/patches support for matching title/update FPS, resolution, or aspect fixes where available; historical Qt builds exposed `Settings > Utils > Download Cheats/Patches`, but launcher layouts change. Disable entries and restart to undo. Avoid claiming any patch makes all PS4 games playable. [Patch announcement](https://shadps4.net/blog/patches-and-cheats-support/), [version-match checks](https://shadps4.net/blog/shadps4-v0110-relased/).

### Tier 3: code-level patches (profile → patch the hot path)

Profile the matching host build and capture the rendering problem; fix missing emulator behavior upstream before hiding it with effect-removal patches. Apply supported guest patches without editing original dumps.

### Gotchas

Boots but crashes in gameplay → check the exact compatibility report. Missing effects after readback changes → restore them. A frame-rate patch can improve motion while worsening frame times or stability.

## Vita3K — PlayStation Vita

**Identify.** Windows: `config.yml`, `logs`, `cache`, and `patch` sit beside `Vita3K.exe` in the documented layout; portable mode changes roots. Record title ID/update and the compatibility entry. [Official FAQ](https://vita3k.org/faq.html).

**Where the time usually goes.** CPU/JIT, shader/pipeline creation, GPU surface synchronization, and scaled rendering; compare native scale and warm-cache runs with the performance overlay. [Tooltips](https://github.com/Vita3K/Vita3K/blob/master/vita3k/gui-qt/src/settings_dialog_tooltips.cpp).

### Tier 1: config and launch options (no files added)

- `Backend Renderer`: Vulkan is recommended for most systems; OpenGL is a comparison/fallback. `Internal Resolution Upscaling` above 1× costs GPU work and is experimental. Keep `Enable CPU Optimizations` for normal JIT performance; investigate regressions per game. [Current tooltips](https://github.com/Vita3K/Vita3K/blob/master/vita3k/gui-qt/src/settings_dialog_tooltips.cpp).
- Shader caching reduces subsequent-run stutter. Async pipeline compilation trades stalls for temporary graphics glitches. Higher renderer accuracy costs performance; `Disable Surface Sync` can save work but breaks games needing CPU/GPU surface coherence. [Trade-offs](https://github.com/Vita3K/Vita3K/blob/master/vita3k/gui-qt/src/settings_dialog_tooltips.cpp).
- `FPS Hack` may change 30 FPS to 60 FPS, or simply make the game twice as fast. It is not a universal performance fix. Check elapsed gameplay time and audio, not only the counter. [FPS warning](https://github.com/Vita3K/Vita3K/blob/master/vita3k/gui-qt/src/settings_dialog_tooltips.cpp).

### Tier 2: drop-in community fixes and runtime swaps

Current Qt source includes `Patch Manager` and `Download latest patches`, with title/version metadata; use its matching FPS/resolution entries when available. Vita is already widescreen; a general widescreen patch library is **(unverified)**. Patching is experimental; the [official patch repository](https://github.com/Vita3K/vita3k-patches) says cheats are not supported yet. Uncheck entries and apply/restart to undo. [Manager](https://github.com/Vita3K/Vita3K/blob/master/vita3k/gui-qt/src/patch_manager_dialog.cpp), [project patch feed](https://github.com/Vita3K/Vita3K/blob/master/vita3k/patch/include/patch/patch.h).

### Tier 3: code-level patches (profile → patch the hot path)

Profile host CPU/GPU waits and use the project's patch format for guest changes; experimental modules need correctness fixes before generic speed hacks. [Developer links](https://vita3k.org/faq.html).

### Gotchas

Twice-speed animation → disable `FPS Hack`. Corrupt textures after scaling/sync changes → restore 1× and surface synchronization. A non-playable compatibility status is not fixed by promising more FPS.

## RetroArch — identify the loaded core, not just the frontend

**Identify.** Record core name/version plus content hash. `retroarch.cfg`, `.opt` core options, and `.cfg` overrides are separate; `Settings > Directory` resolves paths. Use `Settings > Logging` for a diagnostic log, then turn verbose logging back off. [Overrides](https://docs.libretro.com/guides/overrides/), [logs](https://docs.libretro.com/guides/generating-retroarch-logs/).

**Where the time usually goes.** Core emulation, GPU renderer/post-processing, speculative frames, and sync waits. Compare core-only native output before adding shaders or latency reductions. [Pacing guide](https://docs.libretro.com/guides/optimal-vsync/).

### Tier 1: config and launch options (no files added)

- Choose a video driver compatible with the core: Vulkan is not universally faster or supported. For example, Beetle PSX HW documents Vulkan/OpenGL rendering and core-specific internal resolution; higher scale costs GPU work, software rendering shifts costs to CPU. Cache/async options belong to the core; a universal RetroArch ubershader switch is **(unverified)**. [Core documentation](https://docs.libretro.com/library/beetle_psx_hw/).
- `Run-Ahead` reduces input latency by simulating extra frames and restoring state; each extra frame increases CPU demand. It requires reliable, fast core save states. Start disabled for throughput tests; set only the measured internal lag when enabling it. [Run-ahead guide](https://docs.libretro.com/guides/runahead/).
- `Frame Delay`/`Automatic Frame Delay` postpone emulation closer to presentation: less latency, less processing headroom, possible stutter/audio crackle. Reduce delay when deadlines are missed. [Frame delay](https://www.libretro.com/index.php/category/frame-delay/).
- Hard sync and short queues trade throughput headroom for latency. Core CPU overclocks, frameskip, and reduced accuracy can alter timing or correctness; use that core's documented overrides, not a universal “fastest” config. Preserve full-speed audio/video synchronization. [Sync troubleshooting](https://docs.libretro.com/guides/optimal-vsync/).

### Tier 2: drop-in community fixes and runtime swaps

Use core-supported cheats or softpatches with matching hashes; 60 FPS/widescreen availability is specific to the core/game, not a frontend guarantee. A different core can trade accuracy/features for speed, and save states may not transfer. Disable the patch/override and return to the recorded core to undo. [Cheats](https://docs.libretro.com/guides/cheat-codes/), [softpatching](https://docs.libretro.com/guides/softpatching/).

### Tier 3: code-level patches (profile → patch the hot path)

Profile the loaded core library with matching symbols; patch that core or use its guest-patch facility. Do not optimize only the frontend when the measured cost belongs to a core or shader preset.

### Gotchas

Crackling after latency tweaks → disable run-ahead/frame delay and restore headroom. Shader stutter in one core → inspect its renderer/cache implementation. Removing required sync can hide drops without fixing them.

## Shared Tier 3 method and acceptance checks

Use the host sampling tools in [profiling.md](../profiling.md), with symbols for the exact emulator build. Host samples expose compilation, allocations, driver calls, and waits; guest JIT blocks need emulator debugger/disassembly context. A hot wait is not proof the wait can safely be removed. Verified patterns worth investigating are cached translation (Ryubing PPTC), background shader specialization with a fallback (Dolphin ubershaders), and guest timing/fence patches (Cemu FPS++); their sources and costs are linked above. These are precedents, not promised gains in another emulator. Ship a reversible emulator-supported patch or reviewable upstream emulator change, never a rewritten game image. Report before/after frame times and guest speed together, plus the kept trade-off and exact undo step. No RAM cleaners, working-set trimming, registry packs, arbitrary affinity presets, or unmeasured “FPS boosts”.
