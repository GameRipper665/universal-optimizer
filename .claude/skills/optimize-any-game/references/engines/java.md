# Java / JVM games

**Identify.** Start with Minecraft Java, then identify the other game's actual JVM and launcher.
Minecraft instance logs are `<instance game directory>/logs/latest.log`; read the loader, game version,
Java version and failures there. Open the game directory through the user's launcher instead of assuming
the official launcher's directory. [Fabric logging](https://docs.fabricmc.net/develop/debugging)
JARs and a bundled Java runtime indicate a JVM application; LWJGL/libGDX dependencies identify graphics
libraries, not interchangeable engines. Native graphics allocations need separate investigation from the
Java heap. [libGDX memory management](https://libgdx.com/wiki/articles/memory-management)

Scope: owned games in single-player/offline mode and servers the user hosts. No public-server client
changes, anti-cheat work, authentication changes or DRM work. Measurements below are proposed experiments,
not promised gains. Record the exact game, loader, runtime, mod versions and save used for each comparison.
Release checks below are dated **2026-10-21**; check matching release metadata again before installing.

**Where the time usually goes.** Confirm the limiting subsystem before changing it:

- Terrain/entity rendering: compare the same camera position at two render distances; inspect frame
  times and the render thread. A renderer mod cannot fix a saturated simulation thread.
- Entity AI, collisions and block ticking: capture the integrated/dedicated server tick loop with
  [spark](https://spark.lucko.me/docs/guides/The-tick-loop); compare a busy base with an empty area.
- Chunk generation and disk loading: compare new terrain with the same route after it is generated.
  [C2ME](https://modrinth.com/mod/c2me-fabric) targets this workload, not every low-FPS scene.
- Allocations and retained objects: correlate pauses with GC activity and heap growth using JFR;
  inspect allocation stacks separately from retained memory. [JFR diagnostics](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jcmd.html)
- Native textures/buffers: growing process memory with a stable Java heap suggests native allocations;
  inspect graphics resource lifetime instead of increasing heap. [libGDX disposal](https://libgdx.com/wiki/articles/memory-management)

## Tier 1: config and launch options (no files added)

### Minecraft: runtime and heap first

Use the runtime selected for the instance, not whichever `java` happens to be on PATH.
Prism can autodetect and download Mojang's runtime; its Java settings include a runtime/argument test.
Changing runtime can break older loaders, so retain the working selection. [Prism Java settings](https://prismlauncher.org/wiki/help-pages/Java-settings/)

| Minecraft release | Java baseline and source |
| --- | --- |
| Older packs through 1.16.5 | Java 8 is the practical launcher baseline; ancient loaders may need a specific compatible build. [Prism](https://prismlauncher.org/wiki/getting-started/installing-java/) |
| 1.17–1.17.1 | Java 16 minimum; follow the pack's tested runtime if using a newer one. [Mojang 1.17 notes](https://www.minecraft.net/en-us/article/caves---cliffs--part-i-out-today-java) |
| 1.18–1.20.4 | Java 17. [Mojang 1.18 notes](https://feedback.minecraft.net/hc/en-us/articles/4415128577293-Minecraft-Java-Edition-1-18) |
| 1.20.5–1.21.11 | Java 21; 1.20.5 introduced this requirement. [Mojang 1.20.5 notes](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5) |
| 26.1–26.3 | Java 25 baseline; the 26.1 development cycle introduced it. Do not apply a Java-21-only launch recipe. [Mojang 26.1 notes](https://feedback.minecraft.net/hc/en-us/articles/42011663817357-Minecraft-Java-Edition-26-1-Snapshot-1) |

`-Xms` sets initial/minimum heap and `-Xmx` its maximum; neither caps total process memory.
An illustrative starting pair is `-Xms1G -Xmx4G`, not a requirement for every pack.
Use the launcher's memory controls instead of also supplying conflicting heap flags.
Larger initial heaps reduce growth work but commit more memory earlier. [Java launcher reference](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)

Size the maximum from a representative session's live heap plus allocation headroom, leaving RAM for the
OS, native buffers and other applications. Too little produces frequent collections or out-of-memory
failures; excessive committed heap can cause paging and leave less filesystem cache. A larger maximum
alone does not necessarily lengthen every collection. Judge pause distributions, not the heap-size number.
[G1 tuning](https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-garbage-collector-tuning.html)
Prism explicitly cautions that allocating more RAM is not automatically faster. Large packs need their
own measurements rather than its small-instance example. [Prism memory guidance](https://prismlauncher.org/wiki/help-pages/Java-settings/)

### Collector choices: one experiment at a time

- **G1:** `-XX:+UseG1GC` is a reasonable explicit baseline on compatible HotSpot runtimes. Start with
  ergonomic defaults; forced generation sizes can defeat pause-time adaptation. It balances throughput
  and pauses, rather than minimizing either at all costs. [Oracle G1 tuning](https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-garbage-collector-tuning.html)
- **Generational ZGC on Java 21/22:** `-XX:+UseZGC -XX:+ZGenerational`. Test when GC pauses actually
  explain stutter; concurrent collection still needs CPU and heap headroom and may reduce throughput.
  [OpenJDK ZGC version history](https://wiki.openjdk.org/display/zgc/Main)
- **Java 23+:** selecting `-XX:+UseZGC` selects generational mode by default. Java 24 removed the
  non-generational implementation; omit the obsolete `ZGenerational` switch on Java 25. This does not
  make ZGC the JVM's default collector. [JDK 23 change](https://inside.java/2024/05/07/jep474-targeted-to-jdk23/), [flag lifecycle](https://mail.openjdk.org/pipermail/hotspot-runtime-dev/2025-October/082324.html)
- **Aikar's flags:** a G1 tuning recipe developed for Minecraft servers, documented by Paper; not a
  universal desktop-game preset. Compare it with defaults on a hosted server that has measured GC
  pressure. Its fixed-heap/pretouch choices cost startup time and memory; do not combine its G1 tuning
  switches with ZGC. [Paper's recipe and rationale](https://docs.papermc.io/paper/aikars-flags/)
- **`-XX:+AlwaysPreTouch`:** touches heap pages before application use. It moves page-fault work earlier
  but slows startup and increases immediate physical-memory pressure, especially with equal large
  `Xms`/`Xmx`. **`-XX:+UseLargePages`:** requires OS support/configuration, including appropriate Windows
  privileges or Linux huge-page provisioning. It can waste/reserve scarce memory; verify actual use and
  benchmark before retaining it. Neither is a default recommendation. [Java options and large pages](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)

Remove each experimental argument to roll back. Do not copy a second game's complete JVM argument list.

### Minecraft: reduce the work being requested

Use the existing video menu to lower render distance when terrain submission dominates. The cost is a
shorter visible horizon. Lower simulation distance only when ticks dominate: distant entities stop being
simulated, changing farms and activity. The separate simulation control arrived in 1.18.
[Mojang 1.18 simulation-distance notes](https://feedback.minecraft.net/hc/en-us/articles/4415128577293-Minecraft-Java-Edition-1-18)

On a hosted dedicated server, edit its existing `server.properties`: `view-distance` controls the chunk
data sent to players; `simulation-distance` controls the active simulation radius. Lowering the former
reduces loaded/transmitted terrain and visibility; lowering the latter reduces ticking and changes distant
activity. Keep a copy of the prior values and restart to compare. These are distinct limits, not two names
for client rendering distance. [Paper property reference](https://docs.papermc.io/paper/reference/server-properties/)

For Minecraft 1.20.2+, `F3+1` toggles the profiler pie and `F3+2` the FPS/TPS charts; earlier releases used
Shift/Alt combinations with F3. Use the pie to locate a subsystem and the frame chart to see spikes,
then sample code with a profiler. Do not interpret the FPS counter alone as smoothness.
[Mojang debug-screen changes](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2)

### Other JVM games: preserve the shipped launch route

- **Project Zomboid:** the native launcher reads `<game install>/ProjectZomboid64.json`; heap arguments
  are strings in its `vmArgs` array. Replace the existing `-Xmx` entry, for example with `"-Xmx6G"`
  only if measured heap pressure and free RAM justify it. If an `-Xms` entry exists, keep it no larger
  than the maximum. Preserve other entries and JSON syntax. [Developer support advice](https://theindiestone.com/forums/topic/87389-crash-42121/), [launcher argument evidence](https://theindiestone.com/forums/topic/24620-startup-script-ignores-servername-xmx-and-xms-options/)
  A batch-script launch or separately hosted server may use a different command line; inspect the actual
  process instead of assuming client settings affect it. More heap does not fix zombie simulation or
  native rendering, and updates may replace the file. Revert the edited entry if frame times worsen.
- **Starsector:** edit the existing Windows `vmparams` file used by its launcher, preserving its name
  without a `.txt` extension. Change only `-Xms`/`-Xmx` initially. A larger heap can accommodate mods but
  costs RAM; old 32-bit runtimes cannot accept arbitrary large heaps. The developer confirms these flags
  and warns that launch failures can be runtime-bitness or syntax problems. [Fractal Softworks support](https://fractalsoftworks.com/forum/index.php?topic=8691.0)
  Locate that file through the installed launcher, not a guessed Steam directory. Do not assert one
  bundled Java version for every release or reuse old Java-upgrade instructions without matching the build.
- **Slay the Spire:** preserve its tested runtime and ModTheSpire launch route; upstream documents
  Java 8. Do not force Java 21/25 solely to obtain another collector. Compare the same combat/transition
  with suspect mods disabled; keep the save's required content. [ModTheSpire](https://github.com/kiooeht/ModTheSpire)
- **Mindustry:** use the shipped runtime and compare the same offline map with cosmetic effects or
  optional mods disabled. Changing factory content changes the benchmark. Its official mod documentation
  supports Java mods and identifies sprite-atlas mistakes as a source of lag. [Mindustry guide](https://github.com/MindustryGame/wiki/blob/master/docs/modding/1-modding.md)
- **Generic LWJGL/libGDX:** there is no common game configuration or magic heap size. Locate the actual
  launcher's JVM argument field; compare rendering, simulation and allocations separately. On libGDX,
  `GLProfiler` exposes draw calls and texture bindings for a diagnostic build. Instrumentation costs CPU;
  disable it for the final timing run. [libGDX profiling](https://libgdx.com/wiki/graphics/profiling)

## Tier 2: drop-in community fixes and runtime swaps

### Install into the user's launcher and keep a reversible instance

In **Prism**, select the instance, use **Edit > Version** to install its matching loader, then
**Edit > Mods > Download mods** to select matching releases. Dependencies still matter; retain the
loader/version chosen by a content pack. Disable/remove the added mods in that instance to undo the
experiment. [Prism installation workflow](https://prismlauncher.org/wiki/getting-started/download-mods/)

In **Modrinth App**, use the instance's **Settings > Installation** for game/loader selection, then its
content management to install the matching projects. A linked modpack is locked: duplicate/preserve its
working setup before unlinking to customize it; unlinking loses the pack-update relationship. Remove the
added content to roll back. [Installation settings](https://support.modrinth.com/en/articles/8827653-installing-updating-mod-loaders-and-game-versions), [unlinking](https://support.modrinth.com/en/articles/8797558-unlinking-an-instance)

### Minecraft stack by version and loader

These are compatible-version candidates, not a claim that every combination has been benchmarked.
Install one layer at a time. Use only one terrain renderer and each file's exact loader/game metadata.
All client-rendering recommendations here are for offline play.

| Game / loader | Starting candidates, checked 2026-10-21 |
| --- | --- |
| 26.3 Fabric | Sodium **0.9.3-beta.1**; Lithium **0.26.2**; FerriteCore **9.0.0**. Add ImmediatelyFast **1.17.1** and Entity Culling **1.11.3** only for the corresponding measured workload. Sodium is a beta here. [Sodium files](https://modrinth.com/mod/sodium/versions), [Lithium files](https://modrinth.com/mod/lithium/versions), [FerriteCore files](https://modrinth.com/mod/ferrite-core/versions), [ImmediatelyFast files](https://modrinth.com/mod/immediatelyfast/versions), [Entity Culling files](https://modrinth.com/mod/entityculling/versions) |
| 26.3 NeoForge | The same project versions have native NeoForge files; use those files, not Fabric JARs or an old renderer fork. ModernFix has no matching 26.3 release in the checked catalog. [Sodium metadata](https://api.modrinth.com/v2/project/sodium/version), [ModernFix metadata](https://api.modrinth.com/v2/project/modernfix/version) |
| 26.1.2 / 26.2 Fabric or NeoForge | Sodium **0.9.2** has release builds. Resolve other projects for the exact point release; ModernFix's **5.27.24+mc26.1.2** is NeoForge-specific, not proof of 26.2 support. [Sodium files](https://www.curseforge.com/minecraft/mc-mods/sodium), [ModernFix files](https://www.curseforge.com/minecraft/mc-mods/modernfix/files/all) |
| 1.21.1 Fabric or NeoForge | Sodium **0.8.13**, Lithium **0.15.4**, FerriteCore **7.0.3** have matching files. ModernFix is **5.25.1** on Fabric and **5.27.26** on NeoForge; optional renderer helpers also need this branch's files. [Sodium](https://api.modrinth.com/v2/project/sodium/version), [Lithium](https://api.modrinth.com/v2/project/lithium/version), [FerriteCore](https://api.modrinth.com/v2/project/ferrite-core/version), [ModernFix](https://api.modrinth.com/v2/project/modernfix/version) |
| 1.20.1 Fabric | Sodium **0.5.13**, Lithium **0.11.4**, FerriteCore **6.0.1**, ModernFix **5.25.2**. Do not substitute a newer Minecraft branch's JAR. [Sodium](https://api.modrinth.com/v2/project/sodium/version), [Lithium](https://api.modrinth.com/v2/project/lithium/version), [FerriteCore](https://api.modrinth.com/v2/project/ferrite-core/version), [ModernFix](https://api.modrinth.com/v2/project/modernfix/version) |
| 1.20.1 Forge | Embeddium **0.3.31**, FerriteCore **6.0.1**, ModernFix **5.27.89** are matching candidates. Upstream Lithium has no Forge file here; do not install its Fabric build. [Embeddium](https://api.modrinth.com/v2/project/embeddium/version), [FerriteCore](https://api.modrinth.com/v2/project/ferrite-core/version), [ModernFix](https://api.modrinth.com/v2/project/modernfix/version), [Lithium](https://api.modrinth.com/v2/project/lithium/version) |

What each layer buys, and what can go wrong:

- **Sodium:** terrain/rendering optimization; test modded blocks and graphics-driver compatibility.
  It supports Fabric and NeoForge directly. [Project/support policy](https://github.com/CaffeineMC/sodium/wiki/Support-Policy)
- **Lithium:** game-logic/tick optimization; useful for the integrated server as well as a hosted server.
  Check behavior-sensitive mods rather than assuming it improves GPU-bound FPS. [Project](https://github.com/CaffeineMC/lithium)
- **FerriteCore:** reduces retained memory through data-structure optimizations; less memory is not an
  automatic FPS gain. Verify model/state compatibility and compare heap after loading the same content.
  [Project](https://modrinth.com/mod/ferrite-core)
- **ModernFix:** startup, memory and bug fixes; optional dynamic-resource behavior can introduce
  compatibility problems. Start with defaults. Recent Forge/NeoForge releases disprove blanket claims
  that the whole project is abandoned; availability is branch-specific. [Project](https://modrinth.com/mod/modernfix)
- **ImmediatelyFast:** batches/optimizes immediate rendering; test HUDs, particles and entity renderers
  for regressions. **Entity Culling:** skips occluded entity rendering; visibility mistakes can hide
  modded objects and culling itself costs CPU. [ImmediatelyFast](https://modrinth.com/mod/immediatelyfast), [Entity Culling](https://modrinth.com/mod/entityculling)
- **C2ME:** parallel chunk generation/loading/I/O. Both Fabric and NeoForge have 26.3 **alpha** builds;
  test a copied world, watch CPU contention/RAM, and verify custom world generators. It can worsen frame
  times while increasing generation throughput. [Fabric](https://modrinth.com/mod/c2me-fabric), [NeoForge](https://modrinth.com/mod/c2me-neoforge)
- **Krypton:** networking-stack optimization; Fabric **0.3.2** targets 26.3. Consider only on a hosted
  server with measured networking CPU cost, not as a single-player FPS remedy or public-server client
  tweak. Network-path changes need compatibility testing. [Project/files](https://modrinth.com/mod/krypton)
- **Nvidium:** optional Sodium backend using NVIDIA-specific mesh-shader extensions; requires supported
  Turing-or-newer hardware and disables itself with active Iris shaders. **0.4.4-beta7-26.3** exists for
  Fabric. Check its exact Sodium dependency and backend compatibility, not merely the GPU brand.
  Mesh-shader/driver failures and extra graphics-memory pressure make this an opt-in test. [Project/files](https://modrinth.com/mod/nvidium)
- **Distant Horizons:** **3.3.4-26.3** has Fabric/NeoForge metadata. LOD terrain permits long horizons at
  reduced detail; it adds generation work, cache storage and memory use. Compare against a similar visible
  horizon, not plain short-distance rendering. Lower its CPU load or disable distant generation if these
  cause stutter; shaders require explicitly compatible versions/packs. [Project/files](https://modrinth.com/mod/distanthorizons)

**Legacy/merged functionality:** Embeddium remains useful for older Forge packs; its checked release
catalog tops out at older branches, including 1.21.1 NeoForge **1.0.15**. Its repository is not archived,
so do not equate no 26.3 release with a verified abandonment announcement. Rubidium's last listed release
is **0.7.1** for 1.20.1 from 2023; treat it as superseded for new setups, not a current NeoForge solution.
Never stack either with Sodium or each other. [Embeddium source](https://github.com/FiniteReality/embeddium), [release metadata](https://api.modrinth.com/v2/project/embeddium/version), [Rubidium files](https://api.modrinth.com/v2/project/rubidium/version)
Indium's former Fabric Rendering API role is built into Sodium **0.6+**; Indium is incompatible there.
Older Sodium 0.5 packs may still require it for dependent mods. This is integrated functionality, not a
reason to keep adding old helper mods. [Indium maintainer notice](https://modrinth.com/mod/indium)

### Hosted servers and other games

**Paper** is a server replacement with optimizations, not a Fabric/NeoForge mod loader. Migration changes
world layout and can change vanilla behavior; test a backed-up world and retain the original server for
rollback. **Purpur** adds configurability/gameplay features atop Paper, not guaranteed extra speed.
**Folia** runs independent regions in parallel; it suits distributed activity and requires compatible
plugins. It does not make one crowded region arbitrarily parallel. Do not swap it into an existing plugin
stack without checking every plugin. [Paper migration](https://docs.papermc.io/paper/migration/), [Purpur](https://purpurmc.org/docs/purpur/), [Folia design](https://github.com/PaperMC/Folia)

**Chunky by pop4959** pre-generates chunks. Install the matching plugin/mod through its documented loader,
select the intended world and a bounded radius, then generate during maintenance. For example,
`chunky world world`, `chunky radius 1000`, `chunky start`; radius is in blocks. Confirm the world name first.
This trades up-front CPU/disk use and a larger world for less exploration-time generation. It does not
fix loaded-chunk ticking. Removing Chunky leaves generated terrain; restore the world backup to undo that.
[Chunky commands](https://github.com/pop4959/Chunky/wiki/Commands)

For other JVM games, reuse the companion's [Java modding routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/misc-engines.md#java-games-non-minecraft):
ModTheSpire/BaseMod for Slay the Spire, Mindustry's built-in loader, Starsector's API, and Zomboid's mod APIs.
No cross-game performance pack is implied. Keep runtime swaps game/build-specific; a bundled JVM plus
native libraries is not safely upgraded by dropping in an arbitrary newer JRE.

## Tier 3: code-level patches (profile -> patch the hot path)

Install the matching [spark build](https://spark.lucko.me/docs/Installation), or use the server's bundled
integration. `/spark profiler start --timeout 60` records a representative interval;
`/spark profiler stop` ends a manual recording. `/spark heapsummary` reports object-class memory totals,
not a complete retaining-reference analysis. Its viewer workflow uploads data; review it before sharing.
Client profiling uses `/sparkc`; distinguish that from server ticks in a single-player session.
[Commands](https://spark.lucko.me/docs/Command-Usage), [client installation](https://spark.lucko.me/docs/Installation)

For a compatible JVM, capture JFR with `jcmd <pid> JFR.start name=game settings=profile duration=60s filename=game.jfr`.
`game.jfr` is a chosen output, not a game configuration file. Open it in **JDK Mission Control** and inspect
execution samples, allocation/GC, locks and file I/O. Profiling has overhead; repeat the final benchmark
without it. [jcmd syntax](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jcmd.html), [JMC](https://openjdk.org/projects/jmc/)
**async-profiler** adds Java/native CPU, allocation and lock sampling; upstream distributes Linux/macOS
builds, so do not assume the same attachment route on Windows. Use JFR there when supported.
**VisualVM** offers CPU/memory sampling and heap analysis; instrumenting every allocation can materially
distort timings. [async-profiler](https://github.com/async-profiler/async-profiler), [VisualVM overhead](https://visualvm.github.io/startupprofiler.html)

Use the companion [Minecraft Fabric/NeoForge + Mixin route](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/minecraft.md), not a second loader tutorial.
Profile-driven patch candidates, rather than universal edits:

1. **Allocation hot path:** reuse owned scratch collections or primitive storage where allocation stacks
   prove churn. Bound caches and clear world/entity references on unload; pooling can retain more memory.
   libGDX documents both pooling and its stale-reference hazards. [Memory patterns](https://libgdx.com/wiki/articles/memory-management)
2. **Repeated lookup:** cache stable derived results or use spatial buckets for nearby-object queries.
   Invalidate on movement, spawn/despawn and world changes; preserve ordering and exact query boundaries.
   Lithium is a concrete source of simulation optimizations to study before inventing replacements.
   [Lithium source](https://github.com/CaffeineMC/lithium)
3. **Redundant render work:** skip invisible work only after confirming it has no required simulation
   side effects. Compare visibility and modded renderers. Use narrow Mixin injections over wholesale
   overwrites; cancellable callbacks must reproduce the skipped method's observable contract.
   [Mixin callback semantics](https://github.com/SpongePowered/Mixin/wiki/Advanced-Mixin-Usage---Callback-Injectors)

Pin the target method/version, test the packaged mod in the user's copied instance, and retain an easy
disable path. Compare the same warmed scene, new-terrain route and long-session memory trend.

## Gotchas

- Low FPS with healthy ticks -> rendering bottleneck -> profile the client, not only the server.
- More chunk throughput but worse frame spikes -> worker contention -> reduce optional generation work.
- Heap stays flat while process memory grows -> native resources -> inspect disposal and graphics caches.
- Missing models/entities after optimization -> renderer/culling conflict -> remove the last layer first.
- JVM refuses to start -> conflicting collectors, obsolete flags or wrong Java -> restore launcher defaults.
- No gain from a flag -> it may already be the default or the launcher may not pass it -> inspect the
  actual runtime/arguments and repeat the same workload before retaining it.
- "RAM cleaner" lowers a displayed memory figure -> no evidence of less game work -> reject memory
  boosters, registry folklore and working-set trimming. Windows `EmptyWorkingSet` only evicts resident
  pages; subsequent access can fault them back in. [API behavior](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset)
