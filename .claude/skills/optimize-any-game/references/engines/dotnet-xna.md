# .NET / XNA / FNA / MonoGame games

**Identify.** Inspect managed assembly references: `Microsoft.Xna.Framework`, `FNA` and
`MonoGame.Framework` distinguish the game frameworks. They do not identify the runtime by themselves.
Reuse the companion's [engine identification and loader routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/dotnet-xna.md).
For modern .NET, inspect the shipped `<app>.runtimeconfig.json` and the launch log's actual runtime.
For .NET Framework, inspect the executable's existing application configuration and assembly metadata.
Do not infer "modern .NET" merely from C# code or a 64-bit executable.
[.NET runtime configuration](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/), [Framework configuration](https://learn.microsoft.com/en-us/dotnet/framework/configure-apps/)

SMAPI's Windows Steam/GOG log is `%APPDATA%\StardewValley\ErrorLogs\SMAPI-latest.txt`; Linux/macOS use
`~/.config/StardewValley/ErrorLogs/SMAPI-latest.txt`. Check for a crash log too. Everest writes `log.txt`
and `error_log.txt` in the Celeste directory. Read versions and repeated errors before adding fixes.
[SMAPI locations](https://smapi.io/log), [Everest diagnostics](https://github.com/EverestAPI/Resources/wiki/Common-Crashes)

Scope: owned games in single-player/offline mode and servers the user hosts. No online-client patches,
anti-cheat changes, authentication changes or DRM work. Research checked **2026-10-21**.
Treat each recommendation as a measured experiment; record game, loader, runtime and mod versions.

**Where the time usually goes.** Separate these workloads:

- Main-thread simulation: sample a busy save and an empty one. Look for AI, repeated searches and mod
  callbacks; a faster renderer cannot fix expensive simulation.
- Garbage collection: correlate frame spikes with allocation rate and GC pause events, not merely a
  rising working-set number. [Runtime counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters)
- Rendering/driver waits: compare the same scene at a lower resolution and sample `Draw` versus present
  waits. FNA backends can behave differently on the same GPU. [FNA backend documentation](https://fna-xna.github.io/docs/7:-FNA-Environment-Variables/)
- Loading/asset processing: trace a save load separately from steady gameplay. Stardew's historical
  FastLoads targets NPC-route rebuilding, not general FPS. [FastLoads scope](https://www.nexusmods.com/stardewvalley/mods/19454)
- Logging and exception storms: inspect logs and exception events. Per-frame logging itself adds CPU,
  allocations and I/O. [MonoGame logging guidance](https://docs.monogame.net/articles/getting_started/logging.html)

## Tier 1: config and launch options (no files added)

### Identify the runtime before setting runtime flags

**.NET Framework** is the older Windows runtime. **Mono** is another runtime, commonly bundled by older
cross-platform games. **.NET Core / .NET 5+** uses the modern runtime configuration and diagnostic stack.
Installing a new SDK does not move an existing game onto that runtime; self-contained applications ship
their own runtime. Do not replace DLLs or force major-version roll-forward as a generic optimization.
[Framework versus modern .NET](https://learn.microsoft.com/en-us/dotnet/standard/choosing-core-framework-server), [deployment models](https://learn.microsoft.com/en-us/dotnet/core/deploying/)

**tModLoader's checked stable branch targets .NET 8**: its shipped `tMLMod.targets` contains `net8.0`.
This verifies the stable 1.4.4-era route, not every legacy or development branch. Confirm the runtime in
the installed build before applying flags. Vanilla Terraria is not automatically the same runtime as tML.
[Stable build target](https://github.com/tModLoader/tModLoader/blob/stable/patches/tModLoader/Terraria/release_extras/tMLMod.targets), [runtime migration guide](https://github.com/tModLoader/tModLoader/wiki/Update-Migration-Guide)
Current Everest source also targets .NET 8 components; its build SDK requirement is separate from its
runtime requirement. Do not apply Mono advice to a modern Everest install just because vanilla Celeste
once used Mono. [Everest build/runtime notes](https://github.com/EverestAPI/Everest)

Use process-local launch environment settings, not permanent machine-wide variables. Restore/unset each
experimental variable after comparison. An existing runtime config or custom host can affect the final
setting: verify observed behavior instead of assuming the variable was honored.
Modern .NET standardizes the `DOTNET_` prefix from .NET 6; older CoreCLR versions use `COMPlus_`.
Do not translate the following table into a Mono or .NET Framework recipe.
[GC configuration conventions](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector)

| Setting | Where it applies / actual effect | Trade-off and decision |
| --- | --- | --- |
| `DOTNET_TieredPGO=1` | Dynamic profile-guided JIT optimization on supporting modern .NET. It cooperates with tiered compilation. [Compilation settings](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation) | Already enabled by default in .NET 8; setting it again is not an upgrade. Instrumentation/recompilation adds warmup work, so compare both cold and warmed sessions. [.NET 8 change](https://devblogs.microsoft.com/dotnet/performance-improvements-in-net-8/) |
| `DOTNET_TieredCompilation=0` | Disables tiered compilation on supporting CoreCLR builds. Default is enabled from .NET Core 3.0. [Compilation settings](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation) | Diagnostic A/B only for proven tiering-related spikes; loses adaptive optimization and may worsen startup or steady-state speed. Restore the default unless measured benefit persists. |
| `DOTNET_gcServer=1` / `0` | Selects server / workstation GC on supporting modern .NET; the matching config property is `System.GC.Server`. [GC settings](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector) | Server GC favors throughput with additional heaps/threads and can use more memory/CPU. Workstation GC can suit an interactive game sharing the PC. Measure pauses and contention; neither is universally faster. [GC comparison](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/workstation-server-gc) |
| `DOTNET_ReadyToRun=0` | Disables use of existing ReadyToRun code on CoreCLR; the default uses it when available. [Compilation settings](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation) | More JIT compilation can worsen startup and early stutter. This does not compile the game ahead of time, and modern tiered PGO does not generally require disabling it. Test only a specific JIT/R2R hypothesis. |

**`DOTNET_GCgen0size` is real, but not a general game-memory setting.** The .NET 8 GC source defines
`GCgen0size` as the minimum generation-0 allocation budget. It is an implementation-level tuning knob,
not a total heap limit or an amount of "RAM assigned to the game". Raising it may reduce collection
frequency while increasing transient memory and collection work. Leave it unset without allocation/GC
evidence and confirmation against the exact runtime. Numeric GC environment values use hexadecimal;
copying a decimal-looking byte count can therefore produce a very different size.
[.NET 8 GC definition](https://github.com/dotnet/runtime/blob/v8.0.0/src/coreclr/gc/gcconfig.h), [numeric encoding](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector)

For **.NET Framework**, the existing application's `<configuration><runtime>` section supports
`<gcServer enabled="true"/>` or `false`; this is a different configuration mechanism. Test only if a
profile justifies changing GC flavor, with the same memory/contention trade-offs above. Check the active
mode through `GCSettings.IsServerGC` in a diagnostic mod rather than assuming the edit took effect.
Restore the original config to undo it. [Framework gcServer reference](https://learn.microsoft.com/en-us/dotnet/framework/configure-apps/file-schema/runtime/gcserver-element)

Do not manufacture a config file for an unidentified host or add Java-style heap flags to a .NET game.
ReadyToRun publishing is a developer build operation with larger binaries and startup benefits; it is
not an optimization achieved by renaming assemblies. [ReadyToRun deployment](https://learn.microsoft.com/en-us/dotnet/core/deploying/ready-to-run)

### FNA-specific backend and presentation experiments

Only use these with a matching FNA/FNA3D build, not arbitrary XNA/MonoGame games. Set the environment
before launch; managed environment changes may not reach native libraries on .NET Core.
[FNA upstream variables](https://github.com/FNA-XNA/docs/blob/main/docs/7%3A-FNA-Environment-Variables.md)

| Variable | Verified values/effect | Trade-off |
| --- | --- | --- |
| `FNA3D_FORCE_DRIVER` | Current strings: `SDL_GPU`, `D3D11`, `OpenGL`. `SDL_GPU` covers Vulkan/Metal/D3D12. | Driver availability is build/platform-specific. Switching may fix stalls, break rendering or fail startup. |
| `FNA3D_ENABLE_LATESWAPTEAR=1` | Requests adaptive presentation where supported. | Can reduce presentation stalls but permits tearing; no simulation benefit. |
| `FNA_GRAPHICS_ENABLE_HIGHDPI=1` | Enables high-DPI support at startup. | More pixels can increase GPU load; a visual preference. |

Command-line equivalents include `/gldevice:OpenGL` and `/enablelateswaptear:1` if the launcher forwards
them. Remove overrides to restore defaults.
[Values and launch syntax](https://fna-xna.github.io/docs/7:-FNA-Environment-Variables/)
Shader/GL-profile overrides are developer/debugging controls, not generic speed tweaks.
[FNA variable reference](https://github.com/FNA-XNA/docs/blob/main/docs/7%3A-FNA-Environment-Variables.md)

### Keep fixed-step simulation intact

Many XNA-style games separate fixed-step updates from drawing. Raising rendering frequency is useful
only if physics, timers and input remain correct; lowering render work can stabilize delivery without
changing update cadence. Do not set a new timestep or suppress updates to produce a higher FPS counter.
Compare the same gameplay sequence and real-time duration. [MonoGame fixed/variable timing](https://docs.monogame.net/articles/getting_to_know/whatis/game_loop/)

## Tier 2: drop-in community fixes and runtime swaps

Use the existing loaders. Follow the companion's [tModLoader, SMAPI, Everest and Harmony/MonoMod routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/dotnet-xna.md)
for installation/build details instead of introducing another injector. Preserve the working mod list and
save before each experiment. Remove a performance-only mod and restart to roll back; do not remove
save-dependent content as though it were a harmless optimization toggle.

### Terraria / tModLoader

**High FPS Support**, by Stellar, targets tModLoader **1.4.4** in the checked Workshop listing. It renders
above 60 FPS while keeping world simulation speed separate, and has optional optimizations disabled by
default. It is primarily an uncapping/smoothing tool, not proof of reduced CPU consumption.
The author requires a display above 60 Hz and warns about visual artifacts and mod-drawing incompatibility.
[Author's Workshop listing](https://steamcommunity.com/sharedfiles/filedetails/?id=3119712528)

Install through tModLoader's Workshop/mod management for the matching branch; enable only in an offline
test instance, then compare frame times, controls, animations and heavy modded effects. Keep optional
optimizations off until isolated. Disable/unsubscribe and restart to remove it. Do not assume its 1.4.4
metadata covers a newer development branch. [tModLoader usage](https://github.com/tModLoader/tModLoader/wiki/Basic-tModLoader-Usage-FAQ)

Prefer a supported tML update for runtime fixes. Replacing bundled FNA/native libraries separately can
break its expected ABI; a framework swap is a game port, not an ordinary drop-in FPS tweak.
[tModLoader source/dependencies](https://github.com/tModLoader/tModLoader)

### Stardew Valley / SMAPI

**FastLoads** is a verified historical fix for expensive NPC-route rebuilding with large expansions.
Its page marks it **1.5 compatible, broken in 1.6**, and says the underlying issue appears fixed in 1.6.
On a retained 1.5 installation, install its SMAPI mod folder using the companion route; remove that folder
to revert. Do not install it on 1.6 or stack it with SpriteMaster, which patches the same code.
Its cache can affect NPC routes if incorrect, so compare NPC behavior as well as load time.
[FastLoads compatibility and scope](https://www.nexusmods.com/stardewvalley/mods/19454)

**SpriteMaster / Clear Glasses:** Clear Glasses builds on SpriteMaster and supports 1.6 graphics changes.
Its author explicitly does **not** recommend it purely for performance: the main pathfinding optimization
is already in 1.6 and some visual optimizations are broken. Do not present it as a current mandatory FPS
fix. Upscaling/filtering changes appearance and can cost resources; existing users should compare with the
mod removed through SMAPI before treating its effects as beneficial.
[Clear Glasses maintainer notice](https://www.nexusmods.com/stardewvalley/mods/21090)

For current Stardew, diagnose the actual expensive mod rather than substitute a generic "stabilizer".
Use the [SMAPI compatibility database](https://smapi.io/mods) to check the user's exact installed versions.
Disabling an optional expansion reduces content and may make its saves unsuitable for the comparison;
use a copied save and preserve dependencies. Fix repeated mod errors before judging rendering settings.

### Celeste / Everest

**Celeste Motion Smoothing** interpolates drawing while retaining a 60 Hz physics update and can render
at 120+ FPS. Its **Fast** and **Fancy** rendering modes take different approaches; Fancy's higher-resolution
rendering can cost GPU resources and some maps mandate it. It is a smoothness option with compatibility
trade-offs, not a CPU/RAM reduction claim. [Project and modes](https://github.com/FancyFurret/celeste-motion-smoothing)

Install its matching release through Olympus/Everest, following the author's linked distribution.
Test the target map and its helpers, including transitions and moving objects; compare the unchanged
simulation at a sustainable rendering rate. Disable/remove the mod through the loader and restart to
undo it. Do not use a smoothing benchmark as evidence that simulation runs faster.
[Compatibility notes and download](https://github.com/FancyFurret/celeste-motion-smoothing)

Update the actual offending map/helper when its author provides a fix. For example, **Berry 143**'s author
documents lag-reduction updates and removal of unnecessary dependencies; that is a map-specific fix,
not a universal Celeste optimizer. Preserve the map version when comparing results.
[Author's update history](https://gamebanana.com/mods/642956)

### Bannerlord and other Harmony-patchable games

**Performance Tweaks**, by Spartan3663, targets repeated romance-state list searches during campaign
daily ticks. Its documented mechanism is a hero-pair cache, not a battle renderer replacement.
It can help long/heavily populated campaigns; the author's FPS example is not a transferable benchmark.
Cache correctness and interaction with other romance patches are the important trade-offs.
[Author's description](https://www.nexusmods.com/mountandblade2bannerlord/mods/9567)

Confirm a release matching the user's Bannerlord build and required dependencies before installing.
Use the normal module layout and enable it under the launcher's single-player Mods view; disable/remove
the module to revert and test a copied campaign. A current-version compatibility claim for this mod is
**(unverified)** here: the description verifies its mechanism but does not establish support for every
late-2026 Bannerlord branch. [Module layout](https://docs.bannerlordmodding.com/_intro/folder-structure.html), [launcher workflow](https://docs.bannerlordmodding.com/_tutorials/basic-csharp-mod)

For other managed games, check which loader and Harmony version the game already uses. Do not install
a second Harmony assembly simply because a patch sample references one. Some apparently managed games
spend their time in native rendering/physics; a managed prefix cannot optimize a native hot path it never
intercepts. Follow the companion route only where its runtime assumptions actually hold.

## Tier 3: code-level patches (profile -> patch the hot path)

### Choose a profiler that can see this runtime

| Runtime / tool | Useful evidence and limits |
| --- | --- |
| Modern .NET: `dotnet-counters` | Allocation, GC, CPU and exception trends; aggregate metrics do not identify an expensive method. [Reference](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters) |
| Modern .NET: `dotnet-trace` / EventPipe | Managed stacks and runtime events across supported platforms. On a .NET 8 target, supplement with OS/native profiling for driver or native-library time. [EventPipe scope](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/eventpipe) |
| Windows .NET Framework / modern .NET: PerfView | CPU samples, ETW runtime/GC data and memory investigation; useful when the game cannot use modern diagnostic IPC. It also reads EventPipe traces. [PerfView](https://github.com/microsoft/perfview) |
| dotTrace | Sampling/timeline profiling of supported .NET runtimes; Mono 5.10+ support uses Timeline. Match tool/runtime/OS support and license. Instrumented tracing has greater overhead than sampling. [Support matrix](https://www.jetbrains.com/help/profiler/dotTrace_Introduction.html) |
| Legacy Mono: Mono log profiler | Runtime allocation, GC, calls and locks if the shipped Mono includes the profiler. It requires the appropriate launch route; default exhaustive logging can be very expensive. [Mono profiler](https://www.mono-project.com/docs/debug+profile/profile/profiler/) |

For a modern .NET game with diagnostics enabled, find its game process rather than attaching to the
launcher. Start with these commands; replace `1234` with the observed game PID:

```text
dotnet-counters monitor --process-id 1234 --counters System.Runtime
dotnet-trace collect --process-id 1234 --duration 00:00:01:00 --output game.nettrace
```

These are diagnostic outputs, not game files. Current `dotnet-trace` defaults include runtime events and
sampled managed-thread time; older releases name profiles differently. Use the installed tool's help
instead of copying an obsolete `cpu-sampling` profile name. Record a busy minute, then stop collecting.
[Counter syntax](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters), [trace syntax/defaults](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace)
Do not equate time waiting in a sampled managed stack with native CPU consumption. Compare threads,
GC pauses and frame timing together. Profiling allocation events also differs from finding objects that
remain reachable; inspect retention when memory grows across scene changes.

For a compatible legacy Mono launch, `mono --profile=log program.exe` produces `output.mlpd`, analyzed
with `mprof-report output.mlpd`. These are the documented example names; preserve the game's real
arguments and working directory. Use a short diagnostic run because logging can distort frame timing.
Do not use this command to replace a CoreCLR game's runtime. [Mono usage](https://www.mono-project.com/docs/debug+profile/profile/profiler/)

### Patch only the measured hot path

Use tModLoader's supported hooks, SMAPI with Harmony, or Everest/MonoMod as described in the
[companion guide](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/dotnet-xna.md).
The following are candidate transformations, not claims that every game benefits:

1. **Remove allocations in `Update`/`Draw`.** Replace measured temporary LINQ results, captured lambdas,
   per-frame strings and fresh scratch lists with clear loops or reusable owned buffers. Avoid changing
   enumeration order or mutating a collection while traversing it. Pool only when the profile warrants
   the retained memory; clear references and dispose owned graphics resources on unload. MonoGame's
   guidance specifically identifies garbage-heavy LINQ and hot-path logging as stutter sources.
   [LINQ guidance](https://docs.monogame.net/articles/getting_started/preparing_for_consoles.html), [logging costs](https://docs.monogame.net/articles/getting_started/logging.html)
2. **Cache reflection and derived lookups.** Resolve members once, then retain typed delegates instead
   of repeatedly invoking reflection with argument arrays. Harmony's `AccessTools.MethodDelegate`
   documents a one-time setup cost for cheaper invocation. Do not retain dead scene objects through
   closed delegates. For cached game answers, define invalidation before optimizing: load/unload,
   object replacement and state changes must all produce the original result.
   [Harmony delegate API](https://harmony.pardeike.net/v2/api/HarmonyLib.AccessTools.html)
3. **Replace repeated all-pairs scans.** If traces show every entity scanning every other entity, maintain
   a spatial index for local queries, or an exact-key dictionary for identity queries. Update on movement,
   spawn/despawn and save load; preserve radius boundaries, tie-breaking and deterministic ordering.
   An index costs memory and maintenance work and can lose on tiny populations. Bannerlord's documented
   romance-cache mod is a concrete example of replacing repeated linear identity searches; spatial
   bucketing is a separate candidate that still needs measurement. [Performance Tweaks mechanism](https://www.nexusmods.com/mountandblade2bannerlord/mods/9567)

Harmony prefixes returning `false` skip the original and can skip other state-changing prefixes.
Do not merely skip an expensive method unless its complete contract is reproduced. Prefer the narrowest
compatible hook/transpiler for a local transformation, and reject unknown method signatures after updates.
[Harmony prefix semantics](https://harmony.pardeike.net/v2/articles/patching-prefix.html)
Validate with the same save, input sequence and rendering settings: warmup, busy scene, transition and
long-session memory trend. Compare frame-time tails, allocations and CPU, then repeat without profiling.
Unhook callbacks and release caches on unload. Keep a one-mod rollback path and test save/reload behavior.

## Gotchas

- PGO flag produces no difference -> already enabled or wrong runtime -> inspect the actual host/defaults.
- More server-GC threads but worse frames -> resource contention -> restore workstation/default GC.
- Backend override fails at launch -> unsupported FNA3D driver string/build -> unset it and read the log.
- Higher FPS but faster physics or jitter -> broken interpolation/update assumptions -> remove the uncap.
- Old mod claims huge gains -> bottleneck may already be fixed upstream -> verify the current game branch.
- Stable managed heap but growing total memory -> inspect native textures/buffers and retained handles.
- "Memory cleaner" makes Task Manager look smaller -> it may only evict pages or force collection -> reject
  RAM boosters, registry folklore and periodic `EmptyWorkingSet` tricks. Evicted pages must be faulted back
  when needed; that is not allocation removal. [Windows API behavior](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset)
