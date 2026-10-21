# Optimize engine projects with the source open

Use this reference when the developer owns the project and can rebuild it. Work in source, asset import
settings and build profiles. Record the engine, package versions, target hardware and graphics API first.
These are candidates to test, not promised speedups. Documentation checked on 2026-10-21; use the docs
for the project's installed version rather than assuming that a newer engine's defaults apply.

Capture the same scene twice before changing anything. Separate CPU frame time, GPU frame time,
allocation rate, resident memory and loading hitches. Profile to explain the limit; benchmark a release
build without expensive diagnostics to establish the player-visible result. Keep cold-start and warmed
runs separate when investigating shader compilation or streaming. Log the change, trade-off and rollback.
See [the measurement loop](../../optimize-any-game/SKILL.md) and [language hot paths](languages.md).

## Unity project

**Profile.** Connect the Unity Profiler to a **Development Build on target hardware**. Editor Play mode
shares resources with the Editor and can misrepresent both memory and frame cost. Start without Deep
Profiling; use CPU Timeline, GPU and allocation samples to distinguish script work, rendering and waits.
See [profiling a player](https://docs.unity.cn/Manual/profiler-profiling-applications.html).

Use the **Profile Analyzer package** to compare distributions across matched CPU captures, rather than
cherry-picking a frame. It analyzes CPU data, not GPU timings. Compare the same markers, threads and frame
ranges. See [Profile Analyzer](https://docs.unity3d.com/Packages/com.unity.performance.profile-analyzer@1.1/manual/profile-analyzer-window.html).
Use the **Memory Profiler package** for snapshots before loading, after loading, and after unloading;
inspect retained assets and reference chains. Editor snapshots include Editor overhead. See
[Memory Profiler](https://docs.unity3d.com/2022.3/Documentation/Manual/com.unity.memoryprofiler.html).
The **Frame Debugger** explains render passes and batch breaks; it is a frame inspection tool, not a
substitute for GPU timing. See [SRP batch inspection](https://docs.unity3d.com/2021.1/Documentation/Manual/SRPBatcher.html).

**Fixes to test, in bottleneck order:**

1. Remove recurring C# allocations: reuse scratch lists, bound object pools, avoid captured lambdas,
   boxing and materializing queries in update loops, and update UI text when its value changes.
   Cache repeated component/search results with a clear invalidation rule. Verify allocation call stacks
   rather than banning every language feature. See [Unity GC practices](https://docs.unity3d.com/2022.3/Documentation/Manual/performance-garbage-collection-best-practices.html).
   Before, for a temporary list recreated each frame:
   ```csharp
   var visibleIds = new List<int>(128);
   ```
   After, allocate the field once and clear it before filling it again:
   ```csharp
   private readonly List<int> visibleIds = new List<int>(128);

   void Update()
   {
       visibleIds.Clear();
   }
   ```
   Reuse retains capacity; cap exceptional growth and do not share mutable scratch storage across jobs.
2. Choose the rendering path that addresses the measured CPU cost. **SRP Batcher** reduces render-state
   setup for compatible shaders; it does not turn every object into one draw. **GPU instancing** suits
   repeated compatible meshes/materials. **Static batching** can cost extra mesh memory; **dynamic
   batching** spends CPU transforming vertices and is no longer recommended in current Unity guidance.
   Do not enable everything and add the supposed gains: paths have compatibility rules and priority.
   Check the actual batch breaks and CPU/GPU result. See [choosing draw-call optimization](https://docs.unity3d.com/6000.0/Documentation/Manual/optimizing-draw-calls-choose-method.html).
3. Use **Burst + Jobs** for substantial independent numeric work with compatible data, after fixing
   unnecessary work. Burst supports a subset of C# and supplements Mono/IL2CPP; it is usable without ECS.
   Jobs add scheduling, synchronization and data-lifetime costs, so tiny jobs or immediate waits can lose.
   See [Burst](https://docs.unity3d.com/6000.0/Documentation/Manual/script-compilation-burst.html)
   and [the job system](https://docs.unity3d.com/6000.0/Documentation/Manual/job-system-overview.html).
   Consider **Entities** for large homogeneous simulations that benefit from chunked component storage,
   not as a mandatory rewrite of a small GameObject project. Migration and structural changes cost time;
   benchmark one representative system first. See [Entities archetypes](https://docs.unity3d.com/Packages/com.unity.entities@1.3/manual/concepts-archetypes.html).
4. Compare supported **Mono and IL2CPP** player builds using the same scene and release settings.
   IL2CPP is an ahead-of-time backend, not a cure for allocation or bad algorithms. Its **IL2CPP Code
   Generation** choice trades runtime performance against build time and size; test **Faster runtime**
   against **Faster (smaller) builds** where offered. Check native plugins, reflection and stripping in
   the resulting build. See [build settings](https://docs.unity3d.com/2022.3/Documentation/Manual/BuildSettings.html).
5. Test **Use incremental GC** when GC pauses are the issue and the target supports it. It spreads
   collection work across frames, not necessarily less total work; reference mutation also has costs.
   Reduce allocation first and compare tail frame times. Never disable GC indefinitely to hide a leak.
   See [incremental GC](https://docs.unity3d.com/2023.1/Documentation/Manual/performance-incremental-garbage-collection.html).
6. Balance **Addressables** loads and releases; track operation ownership, not only scene ownership.
   Releasing an asset does not necessarily unload its containing bundle while other assets retain it.
   Group assets by lifetime, inspect shared dependencies and prevent unload/reload churn. Smaller bundles
   can increase metadata and loading overhead; keeping everything resident increases memory pressure.
   See [Addressables memory management](https://docs.unity3d.com/Packages/com.unity.addressables@1.21/manual/MemoryManagement.html).

**Gotchas.** Deep Profiling instruments managed calls and can materially change timings and memory use,
even while not recording. Use it briefly to find call structure, then remeasure without it; see
[Deep Profiling](https://docs.unity.com/en-us/engine/7000.0/manual/analysis/profiler/deep-profiling)
(the linked UI describes Unity 7; follow the equivalent controls in the installed version).
Do not report Editor, deep-profiled, Development and release numbers as interchangeable.

## Unreal project

**Profile.** Start with `stat unit`, `stat game`, `stat gpu` and `stat streaming` in a development build
where those stats are available; distinguish game-thread, rendering and GPU limits. See
[stat commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine).
Capture a packaged target build with **Unreal Insights**; for example, pass:
```text
-trace=cpu,gpu,frame,bookmark,loadtime,file -statnamedevents
```
These are documented trace channels; file/platform support and compiled-in tracing vary. `loadtime`
requires CPU tracing, and named events add detail and overhead. Select only channels needed for the
question; enable memory tracing separately when investigating retention. See
[Insights reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-reference-in-unreal-engine-5).

**Fixes to test:**

1. Remove unnecessary per-Actor **Tick** work before changing languages. Prefer events for state changes,
   disable idle ticks, and lengthen intervals only for work that tolerates slower response. C++ still
   pays for expensive queries and excessive tick counts. Move a measured Blueprint numeric loop into a
   coarse C++ function rather than making thousands of tiny boundary calls. See
   [CPU considerations](https://dev.epicgames.com/documentation/en-us/unreal-engine/common-memory-and-cpu-performance-considerations-in-unreal-engine).
   Before, an enabled primary Actor tick runs every frame at interval zero; after, a distant noncritical
   update can run less often, or an idle Actor can stop ticking:
   ```cpp
   SetActorTickInterval(0.1f);
   ```
   ```cpp
   SetActorTickEnabled(false);
   ```
   These are alternatives for different states, not a sequence that enables a periodic tick. Set up the
   Actor to support ticking and handle component ticks separately; re-enable when needed. See
   [AActor APIs](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/AActor).
   **Blueprint nativization was removed in UE5.** Do not recommend a UE4 packaging checkbox for UE5;
   see [Epic's migration guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-migration-guide).
2. Use **Significance Manager** to rank actors and apply project-specific AI, animation or effect budgets.
   Installing/enabling it alone changes no workload. Account for visible and gameplay-critical actors,
   multiple viewpoints, and the cost of scoring. Pair every registration with unregistration. See
   [Significance Manager](https://dev.epicgames.com/documentation/en-us/unreal-engine/significance-manager-in-unreal-engine)
   and [lifetime requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/SignificanceManager/USignificanceManager).
3. Diagnose first-use hitches as **PSO compilation** before blaming streaming. **PSO precaching** collects
   relevant pipeline states and compiles asynchronously; `r.PSOPrecaching` requires RHI support. Validate
   coverage in the actual rendering configuration, not only an Editor flythrough. See
   [PSO precaching](https://dev.epicgames.com/documentation/en-us/unreal-engine/pso-precaching-for-unreal-engine).
   A **bundled PSO cache** records exercised graphics states and can cover gaps; it requires collection,
   cooking and maintenance as content changes. It is not a universal driver-binary shader cache.
   Test a clean-cache launch and previously unseen effects; extra startup compilation and memory are
   trade-offs. See [bundled PSO workflow](https://dev.epicgames.com/documentation/en-us/unreal-engine/manually-creating-bundled-pso-caches-in-unreal-engine).
4. Budget **Nanite, Lumen and Virtual Shadow Maps** independently using GPU pass timings. Nanite does
   not eliminate material, overdraw or shadow cost; inspect dense/overlapping content before assuming
   triangle reduction will solve everything. See [Nanite](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine).
   Compare Lumen GI/reflection scalability and internal resolution against the visual target; feature
   behavior changes between versions. See [Lumen budgets](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine).
   For VSM, inspect light count, shadow casters and cache invalidations from moving/deforming content;
   reduced shadow quality or distance can trade detail for GPU time. See
   [VSM performance](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine).
5. Tune **World Partition** cell size, loading range and streaming sources against traversal speed and
   memory. Preload teleport destinations. Too-small working sets pop or hitch; too-large ones retain
   assets and amplify activation work. Cross-Actor references can bundle actors for loading together.
   Use HLODs for distant representation, then inspect streaming and activation on the target storage.
   See [World Partition](https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine)
   and [HLODs](https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition---hierarchical-level-of-detail-in-unreal-engine).
6. Consider **Mass** for large populations whose data and processing fit chunked, data-oriented systems.
   Prototype one crowd/simulation workload; fragments hold data and processors supply behavior. Frequent
   composition changes and interaction with full Actors can erase benefits. A small actor population
   rarely justifies the integration cost. See [MassEntity](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-mass-entity-in-unreal-engine).

**Gotchas.** Blueprint versus C++ has no universal multiplier. Time actual work and call counts.
Throttling AI can change gameplay; disabling ticks can break dependencies. Verify correctness as well as
frame time, and compare equivalent packaged builds without intrusive tracing for the final result.

## Godot project

**Profile.** Use the built-in **Profiler** for scripts and physics, **Visual Profiler** for rendering CPU/GPU
work, and **Monitors** for object counts, memory and draw statistics. Visual Profiler CPU time excludes
non-rendering script and physics work. Renderer/platform support varies; verify release exports on the
device after debugging. See [Debugger panels](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/debugger_panel.html).

**Fixes to test:**

1. Type hot GDScript operands, parameters and returns so the compiler can use specialized operations;
   do not promise a fixed multiplier. Cache stable node references once rather than walking paths each
   frame. See [static typing](https://docs.godotengine.org/en/4.4/tutorials/scripting/gdscript/static_typing.html)
   and [node references](https://docs.godotengine.org/en/stable/tutorials/scripting/nodes_and_scene_instances.html).
   Before, resolve the sprite during every update; after, retain the ready-time reference:
   ```gdscript
   @onready var sprite: Sprite2D = $Sprite2D

   func _process(delta: float) -> void:
       sprite.rotation += delta
   ```
   Refresh references when replacing nodes; cached references do not grant lifetime ownership.
2. For huge populations, test bypassing individual Nodes with **RenderingServer** and the appropriate
   **PhysicsServer2D/PhysicsServer3D** API. This removes scene-tree overhead, not rendering or collision
   work. You own RID cleanup, state organization and synchronization. Avoid synchronous getters in a
   submission loop. See [using servers](https://docs.godotengine.org/en/stable/tutorials/performance/using_servers.html).
3. Use **MultiMeshInstance2D/3D** for many copies of one mesh. Split instances into spatial groups:
   individual instances are not frustum-culled independently within one MultiMesh. Oversized batches can
   waste GPU work. See [MultiMesh optimization](https://docs.godotengine.org/en/stable/tutorials/performance/using_multimesh.html).
4. Move a proven compute hotspot into **C#** or a **GDExtension**, passing bulk data instead of calling
   across the boundary per element. Native code does not accelerate a GPU-bound frame or an expensive
   engine query. Check platform/export support and deployment costs before choosing C#. See
   [language trade-offs](https://docs.godotengine.org/en/stable/about/faq.html#which-programming-language-is-fastest)
   and [GDExtension](https://docs.godotengine.org/en/stable/engine_details/engine_api/gdextension/what_is_gdextension.html).
5. Change **Physics Ticks per Second** only when physics is the bottleneck and the design tolerates it.
   A lower rate reduces simulation frequency but affects contact quality, responsiveness and stability;
   interpolation smooths rendering, not collision accuracy. See
   [physics ticks and frames](https://docs.godotengine.org/en/stable/tutorials/physics/interpolation/physics_interpolation_introduction.html).
6. Test **occlusion culling** in scenes with substantial opaque blockers. It spends CPU to avoid hidden
   rendering, so open scenes can lose. Build suitable occluders and compare both CPU and GPU time;
   higher occlusion quality costs CPU. See [occlusion settings](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html#class-projectsettings-property-rendering-occlusion-culling-bvh-build-quality).

**Gotchas.** Scene-tree convenience and raw servers have different ownership costs. A leak of nodes,
resources or RIDs is not fixed by changing language. Keep collision behavior and export compatibility
in the before/after checks; do not infer native-code cost solely from a script profiler.

## GameMaker project

**Profile.** Use the Debugger's **Profiler** to identify costly events/functions, then confirm in a normal
target build. Watch the debug overlay's texture swaps, vertex batches and frame time; low swap counts
alone do not prove a fast frame. See [Profiler](https://manual.gamemaker.io/lts/en/IDE_Tools/The_Debugger/The_Profiler.htm)
and [debug overlay](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Debugging/The_Debug_Overlay.htm).

1. Reduce repeated Step-event work; cache results until inputs change or spread noncritical searches
   across frames. Reduced update frequency trades responsiveness for CPU time.
2. Reduce broad collision/search work; a grid or tile-based query can replace repeated world scans,
   when collision shapes and game rules permit it.
3. Keep compatible draws together and organize texture pages for actual draw order. Texture/shader
   changes break batches; reordering transparent sprites can change the image. These patterns and their
   costs are covered in [GameMaker programming practices](https://manual.gamemaker.io/lts/en/Additional_Information/Best_Practices_When_Programming.htm).
4. Compare **VM** and **YYC** on supported targets for a CPU-bound workload. YYC compilation is a build
   choice with toolchain/build-time costs; it cannot cure excess GPU work. See
   [compiling and target choices](https://manual.gamemaker.io/lts/en/Introduction/Compiling.htm).

**Gotchas.** Profiled debug execution and compiled shipping code differ. Test object reuse against
create/destroy behavior carefully; reset alarms, references and gameplay state if introducing a pool.

## LÖVE project

**Profile.** Sample LuaJIT with **jit.p** where the runtime includes it; its statistical profiler sees
interpreted and compiled code. See [LuaJIT profiling](https://luajit.org/ext_profiler.html).
Inspect `love.graphics.getStats()` for draw calls and texture memory, and time simulation separately
from rendering; see [graphics API definitions](https://github.com/love2d-community/love-api/blob/master/modules/graphics/Graphics.lua).

1. Preload images/fonts/audio needed in the scene instead of constructing them in update/draw loops.
   This trades bounded resident memory for less loading and resource-creation work during play.
2. Reuse frequently rebuilt Lua tables and avoid long repeated string concatenation; see the Lua section
   of [language hot paths](languages.md) for runtime-specific limits.
3. Let automatic batching work by limiting texture, shader and render-state switches. Consider
   **SpriteBatch** for suitable repeated content, particularly retained geometry; it is not automatically
   faster than already-batched draws. See [batch flush rules](https://github.com/love2d-community/love-api/blob/master/modules/graphics/Graphics.lua)
   and [SpriteBatch uploads](https://github.com/love2d-community/love-api/blob/master/modules/graphics/types/SpriteBatch.lua).
4. Pre-render unchanged layers to a **Canvas** only when reuse saves more rendering than the extra
   render-target switch and memory cost. See [Canvas](https://github.com/love2d-community/love-api/blob/master/modules/graphics/types/Canvas.lua).

**Gotchas.** Some platforms disable JIT compilation. Verify the bundled runtime; do not assume desktop
LuaJIT performance everywhere. GPU time is not explained by a Lua-only CPU profile.

## MonoGame / FNA project

**Profile.** Use a profiler compatible with the actual CLR/Mono runtime; see [C# tools](languages.md).
For MonoGame, **GraphicsMetrics** helps count draws and state changes, but is not a GPU timing profiler;
see [GraphicsMetrics](https://docs.monogame.net/api/Microsoft.Xna.Framework.Graphics.GraphicsMetrics.html).
Do not assume a MonoGame diagnostic extension exists in FNA; check the pinned framework source.

1. Batch compatible sprites within fewer **SpriteBatch.Begin/End** regions. **SpriteSortMode.Texture**
   can reduce texture changes but can reorder alpha-blended content; **Immediate** gives up deferred
   batching. See [MonoGame SpriteBatch](https://docs.monogame.net/api/Microsoft.Xna.Framework.Graphics.SpriteBatch.html)
   and [FNA implementation](https://github.com/FNA-XNA/FNA/blob/master/src/Graphics/SpriteBatch.cs).
2. Reuse game-loop collections and transient objects when allocation profiles justify it; cap pools so
   an exceptional scene does not retain an oversized heap. See [C#](languages.md).
3. Retain static geometry in GPU buffers; for changing geometry, compare supported dynamic-buffer
   uploads rather than rebuilding resources every frame. See [graphics buffer types](https://docs.monogame.net/api/Microsoft.Xna.Framework.Graphics.html).
4. Load content outside the critical update path and explicitly dispose owned graphics resources;
   preserve content-manager ownership. See [ContentManager](https://docs.monogame.net/api/Microsoft.Xna.Framework.Content.ContentManager.html).

**Gotchas.** Fixed-step catch-up can create multiple updates per rendered frame under load. Measure
update counts and preserve simulation semantics; see [Game timing](https://docs.monogame.net/api/Microsoft.Xna.Framework.Game.html).

## Bevy (Rust) project

**Profile.** Use optimized builds and Bevy's tracing spans. Its documented Tracy route is
`cargo run --release --features bevy/trace_tracy`; match Tracy to the version required by the pinned
Bevy dependency. Separate ECS-system timing from render/GPU work. See
[Bevy profiling](https://github.com/bevyengine/bevy/blob/main/docs/profiling.md).

1. Narrow queries and mutable access to what the system uses; unnecessary write access constrains
   scheduling. See [Query access rules](https://docs.rs/bevy/latest/bevy/ecs/system/struct.Query.html).
2. Gate work with run conditions or change detection when inputs are unchanged. **Changed<T>** still
   checks matching entities; it is not a free list of changed objects. Mutable dereferencing marks a
   change even if the value stays equal. See [Changed](https://docs.rs/bevy/latest/bevy/ecs/query/struct.Changed.html).
3. Reuse scratch vectors and avoid collecting query results solely to loop over them again; retain
   bounded capacity. See the [Rust hot-path guidance](languages.md).
4. Reduce unnecessary spawn/despawn and component composition churn; compare stable entities and
   reusable data against the cost of more resident state. See [archetypes](https://docs.rs/bevy/latest/bevy/ecs/archetype/index.html).

**Gotchas.** ECS does not make every system parallel: data conflicts and dependencies still serialize
work. APIs/features evolve quickly; use the profiling guide and API docs for the project's exact version.

## libGDX project

**Profile.** Use **GLProfiler** for GL call/draw/texture-binding counts and **PerformanceCounter** for
timed regions; use JFR or async-profiler for JVM stacks and allocation. Counters explain workload, not
GPU duration. See [libGDX profiling](https://libgdx.com/wiki/graphics/profiling).

1. Keep compatible **SpriteBatch** draws together and use atlases to reduce texture switches, while
   preserving transparent order. See [SpriteBatch](https://libgdx.com/wiki/graphics/2d/spritebatch-textureregions-and-sprites).
2. Reuse temporary vectors and scratch arrays where allocation rate is high; use primitive collections
   when boxing appears in profiles. libGDX's reusable iterators have nested-iteration caveats; see
   [collections](https://libgdx.com/wiki/utils/collections).
3. Move loading out of render/update using **AssetManager**, then budget upload/activation work;
   asynchronous loading does not make every operation free. See [asset management](https://libgdx.com/wiki/managing-your-assets).
4. Dispose native/GPU resources according to ownership when leaving scenes; JVM GC does not replace
   explicit resource disposal. See [memory management](https://libgdx.com/wiki/articles/memory-management).

**Gotchas.** Separate JVM warm-up from steady-state measurements. Test Android/device behavior directly;
desktop allocation tolerance and GPU throughput are not mobile budgets.

## Web games: Phaser / PixiJS / Three.js / Babylon.js

**Profile.** Record a repeatable interaction in **Chrome DevTools Performance**. Inspect main-thread
tasks, scripting, rendering and GC; use allocation recordings separately when needed. Remote-device
results matter more than a desktop emulation score. See [Performance recording](https://developer.chrome.com/docs/devtools/performance/reference).

1. Use the engine's loop, or **requestAnimationFrame** for a custom loop; use timestamps rather than
   assuming 60 Hz. Avoid duplicate animation loops. Background tabs throttle/pause callbacks, so clamp
   or reset elapsed time according to game rules. See [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).
2. Reuse frequent transient objects where GC is measured. Phaser **Groups** support pool-style reuse;
   reset visibility, activity, physics and listeners together, and bound the pool. See
   [Phaser Group](https://docs.phaser.io/api-documentation/3.88.2/class/gameobjects-group).
3. Reduce **WebGL draw calls** with compatible materials, atlases and instancing. PixiJS batches suitable
   sprites, but mixing object types/state can split batches; see [PixiJS performance](https://pixijs.com/7.x/guides/production/performance-tips).
   Three.js **InstancedMesh** suits repeated geometry/materials; update bounds when needed and preserve
   culling behavior. See [InstancedMesh](https://threejs.org/docs/pages/InstancedMesh.html).
   In Babylon, compare instances/merged geometry and scene evaluation costs; freezing mutable content
   produces stale state. See [Babylon optimization](https://doc.babylonjs.com/features/featuresDeepDive/scene/optimize_your_scene).
4. Avoid rebuilding geometry, text and typed buffers per frame when inputs are unchanged. This trades
   cache memory and invalidation logic for less CPU/GC/upload work; see [JS hot paths](languages.md).
5. Move independent work to **Workers**, or rendering to **OffscreenCanvas** where the engine and target
   browser support it. Test capability and transfer costs; workers cannot directly access the DOM.
   See [worker rendering](https://developer.mozilla.org/en-US/docs/Web/API/DedicatedWorkerGlobalScope/requestAnimationFrame)
   and [Three.js OffscreenCanvas](https://threejs.org/manual/pages/offscreencanvas.html).

**Gotchas.** A worker can improve input responsiveness without reducing GPU time. Batching may weaken
culling or change transparency. Profile the shipping browser/engine version; old articles can contain
obsolete browser-support statements. Keep only changes that improve the target scene beyond run noise.
