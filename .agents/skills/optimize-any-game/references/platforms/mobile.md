# Mobile (Android and iOS)

**Scope.** Games on a phone or tablet. `uo bench` (PresentMon) does not run here, so measurement comes from the
device's own tools (below). Two cases: a player tuning a game they installed, and a developer tuning their own
build. Rooted/jailbroken devices and modified APKs/IPAs are out of scope (see the end).

**Where the time usually goes.**
- **Thermal throttling.** Phones have no fan. After a few minutes the SoC drops clocks and the frame rate sags.
  Confirm it by logging frame rate over 15-30 minutes, not 60 seconds.
- **GPU fill rate / resolution.** Native-resolution rendering on a 120 Hz panel is the usual heavy cost.
- **Battery policy.** Battery saver and low-power modes cap clocks or refresh rate on purpose.
- **CPU main thread / draw calls.** Same as desktop, on slower cores.
- **Memory pressure.** The OS kills background apps and the game reloads; looks like "long loads" or "lost progress".

## Tier 1: player side (no root, no jailbreak)

**In-game settings first.** Frame-rate cap (30/60/90/120), resolution scale, shadows, effects, "high frame rate"
toggles. Same method as PC: change one, play the same scene, compare. Lowering the cap often *raises* smoothness
because the SoC stops throttling and frame pacing evens out.

**Android Game Mode / Game Dashboard.**
- Android 12+ games that declare it get three modes: `STANDARD`, `PERFORMANCE` (lowest-latency frame rates at the
  cost of battery and fidelity) and `BATTERY` (longest battery life at the cost of fidelity or frame rate). The
  game-specific Battery mode does not touch system Battery Saver
  ([Game Mode API](https://developer.android.com/games/optimize/adpf/gamemode/gamemode-api)).
- Reachable from Game Dashboard's Optimisation widget on Pixel (OEMs ship their own game launchers with similar
  switches). The icon may be missing for sideloaded builds; Google says to install through the Play Store
  ([same page](https://developer.android.com/games/optimize/adpf/gamemode/gamemode-api)). Settings path for
  enabling Game Dashboard: Settings > Apps > Game settings, per a [2022 report](https://9to5google.com/2022/01/29/google-play-pixel-6-optimized-games/)
  (menus vary by Android version and OEM, unverified for current builds).
- Over adb (USB debugging, no root): `adb shell cmd game mode [standard|performance|battery] <package>`
  ([source](https://developer.android.com/games/optimize/adpf/gamemode/gamemode-api)). Use it to A/B the modes
  reproducibly.
- If the game does *not* declare modes, the OEM may apply **interventions**: resolution downscale (Google cites up
  to 30% GPU and 10% system power savings, device-dependent), FPS override (Android 13+) and ANGLE instead of the
  native GLES driver. Developers can opt out with `allowGameDownscaling` / `allowGameFpsOverride`
  ([interventions](https://developer.android.com/games/optimize/adpf/gamemode/gamemode-interventions)).
  Trade-off: a Battery-mode intervention can make the image softer or lock the frame rate lower; if a game looks
  blurry, check which mode is active before blaming the game.

**Thermal throttling: measure it.**
- Developer-grade view without root: `adb shell dumpsys thermalservice` shows the thermal status (unverified
  output format; the status names are documented below).
- Status levels run `NONE`, `LIGHT`, `MODERATE`, then `SEVERE`/`CRITICAL`/`EMERGENCY`/`SHUTDOWN`; Google
  treats SEVERE and above as significant throttling ([Thermal API](https://developer.android.com/games/optimize/adpf/thermal)).
- Practical test: a 20-30 minute session with an overlay that logs FPS (the game's own counter, a developer-options
  profile overlay, or a screen recording with a frame counter). A frame rate that starts at 60 and settles at 40 =
  throttling, not a bad level.
- Mitigations that are real: lower the frame-rate cap or resolution scale, take the phone out of a case, stop
  charging while playing (charging adds heat), lower screen brightness. Not real: "cooling" or "booster" apps.
  Clip-on fans genuinely help but are hardware.

**Battery saver effects.**
- Android system Battery Saver restricts background work and may reduce performance; the exact limits vary by
  version and OEM (unverified, no authoritative page found). Turn it off to test whether it is the cause.
- iOS **Low Power Mode** reduces brightness, background app refresh, some visual effects and automatic downloads
  ([Apple](https://support.apple.com/en-us/101604)). Apple's page does not list a refresh-rate change, but press
  reports it limits ProMotion iPhones to 60 Hz ([9to5Mac](https://9to5mac.com/2025/02/17/low-power-mode-slows-down-iphone/),
  secondary, verify on your device). Turn it off before a benchmark; leave it on if battery matters more than 120 fps.

**Refresh rate.** The display's rate is a system setting (OEM-named, e.g. "Smooth display" or "Motion smoothness",
unverified naming). A 120 Hz panel does not make a game run at 120; the game must offer a high-frame-rate option.
Pinning 60 Hz saves battery and reduces heat.

**iOS Game Mode (iOS 18+).** Starts automatically when a game launches; Apple says it gives the game highest-priority
access to CPU and GPU and doubles the Bluetooth sampling rate to cut controller and AirPods latency. Toggle it from
the Game Overlay under the Controls button ([Apple](https://support.apple.com/en-us/105118)). Gain is
modest and mostly helps latency and background interference; the AirPods part is limited to supported models
(secondary: [PhoneArena](https://www.phonearena.com/news/game-mode-ios-18_id159276)).

**Also real:** keep storage above ~10-15% free (unverified threshold), install the game from the official store so
Game Mode metadata applies, update the OS and GPU driver (Android updates ship via system/Play updates), close
other heavy apps.

## Tier 2: developer side (the user's own mobile game)

| Tool | Use it for | Source |
|---|---|---|
| Android Performance Analyzer (APA) | System profiler: CPU, GPU, memory, power in one view; built on Perfetto; open beta since May 2026; Android 12+ gives best GPU counter support | [Android Developers blog](https://developer.android.com/blog/posts/introducing-android-performance-analyzer-the-next-evolution-in-profiling-for-android) |
| Android GPU Inspector (AGI) | System and frame profiling for Adreno, Mali, PowerVR; the AGI page now points games to APA as the recommended tool | [AGI](https://developer.android.com/agi) |
| Perfetto / system tracing | Frame Timeline shows which stage (app, composition, display) missed its deadline; record from ui.perfetto.dev over USB, Android R+ | [Perfetto](https://perfetto.dev/docs/getting-started/system-tracing) |
| Android Studio profilers | CPU profiler incl. System Trace, memory profiler (GC and allocation events) | [Tracing overview](https://developer.android.com/topic/performance/tracing/) |
| Xcode Instruments | **Game Performance** template (System Trace + Time Profiler + Metal System Trace) for CPU/GPU stutter; Metal System Trace for CPU/GPU/memory timeline; GPU counters for bottlenecks | [Apple Metal tools](https://developer.apple.com/metal/tools/), [WWDC18 612](https://developer.apple.com/videos/play/wwdc2018/612) |

Notes: the template list in Xcode changes between versions (one Apple session names a "Game Performance Overview"
template for multi-minute captures); check the installed Xcode. A Metal performance HUD via the scheme
environment variable `MTL_HUD_ENABLED=1` is widely cited but not verified here (unverified).

**ADPF (Android Dynamic Performance Framework).** Components listed by Google: Thermal API, Game Mode and Game State
API, Fixed Performance Mode (for benchmarking, so dynamic clocking does not skew results), Power Efficiency Mode
(`PerformanceHintManager.Session#setPreferPowerEfficiency`, Android 15) ([ADPF](https://developer.android.com/games/optimize/adpf)).
- `getThermalHeadroom(forecastSeconds)`: 0.0 = no throttling, 1.0 = severe throttling; use 0 for "now". Android 11
  (Java), NDK from Android 12. Call at most once per 10 s from one thread or it returns `NaN`; a `NaN` first value
  means unsupported. If `getCurrentThermalStatus()` stays `NONE` while headroom is ~0.85+, trust the headroom.
  Google's heuristics: >1.0 reduce load now, 0.95 reduce and watch, 0.85 watch ([Thermal API](https://developer.android.com/games/optimize/adpf/thermal)).
- Trade-off: reacting to headroom means dropping resolution/effects/frame rate on purpose. That beats a forced
  throttle that causes hitching, but you must design the quality ladder.
- Declare Game Mode support only if the game implements its own modes; declaring it resets OEM interventions
  ([Game Mode API](https://developer.android.com/games/optimize/adpf/gamemode/gamemode-api)).
- **Android Performance Tuner** is still listed in Google's Optimize docs ([ADPF](https://developer.android.com/games/optimize/adpf)).
  Whether it is being retired in favour of APA is not stated there (unverified).

**Engine settings that matter (the usual mobile levers).**
- **Resolution scaling.** Biggest GPU lever. Unreal: `r.MobileContentScaleFactor` (0 = device-native; fractional
  values trade sharpness for speed), set per device in Device Profiles
  ([UE 4.26 docs](https://docs.unrealengine.com/4.26/SharingAndReleasing/DeviceProfiles); old docs, confirm on
  your engine version). Unity: URP render scale or dynamic resolution (unverified page).
- **Frame rate.** Choose a cap the device can hold for the whole session (30 or 60); Google's guidance for battery
  is a lower refresh rate (30 or 60 Hz) plus [frame pacing](https://developer.android.com/games/sdk/frame-pacing).
  Unity's `Application.targetFrameRate` and Android `vSyncCount` interplay is not verified here (unverified).
- **Texture compression.** ASTC on modern Android GPUs (Adreno 4xx+, Mali T624+, Tegra K1+, PowerVR GX6250+);
  ETC2 for older ones; ASTC HDR is the only compressed HDR option on Android ([Unity manual](https://docs.unity3d.com/2023.2/Documentation/Manual/texture-compression-formats.html)).
  Unreal ASTC settings: not verified (unverified). Trade-off: ASTC encodes slowly, so use it for release builds.
- **Overdraw and fill.** Fewer full-screen transparent layers, cheaper particles, no full-resolution post effects.
  Confirm in AGI/APA GPU counters or Xcode GPU counters, not by feel.
- **Thermal budget.** Test a 30-minute run on a mid-range device, not a flagship on a desk. Unity's Adaptive
  Performance package feeds device thermal data into the engine ([Samsung provider docs](https://docs.unity3d.com/Packages/com.unity.adaptiveperformance.samsung.android@2.0/manual/index));
  device support depends on the provider version.

## Gotchas
- **Flagship-only testing** -> ships a game that throttles on the median phone. Test a mid-range device.
- **Short benchmarks** -> miss throttling. Run 20+ minutes.
- **Charging during tests** -> adds heat; keep test conditions the same before and after.
- **Debug builds** -> slower than release; profile release builds with profiling enabled.
- **Mode changes need a restart** for downscale interventions ([interventions](https://developer.android.com/games/optimize/adpf/gamemode/gamemode-interventions)).

## Out of scope
- **Rooted or jailbroken devices, governor/clock tweaks, modified APKs/IPAs.** For online games these trip
  anti-cheat or store integrity checks (bans, blocked accounts) and break the "no modified game files, no
  anti-cheat bypass" rule. Root-only tools also force-change CPU/GPU clocks, which is hardware tuning the user must
  ask for explicitly. Offline single-player games the user owns can be discussed case by case; the player-side list
  above already covers what is reachable without that.
- **"Booster", "cleaner" and "cooler" apps.** Placebo; they close background apps the OS reopens and add load.
