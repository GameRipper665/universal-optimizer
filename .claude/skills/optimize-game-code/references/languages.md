# Language hot paths in game code

Profile the shipping runtime, not a language stereotype. Find the function on the frame's critical path,
its call count, allocation rate and input size. A faster worker that already finishes early may not move
frame time. Record compiler/runtime versions and use the same scene before and after each change.
Documentation checked on 2026-10-21; version-specific features below are not universal defaults.

The examples are small fragments: buffers and game data already exist unless allocation is the subject.
They illustrate candidates to measure, not benchmark results. Preserve ordering, ownership, precision
and gameplay behavior. See [engine projects](engine-projects.md) for engine-specific thread/API limits.

## C and C++

**Profile.** Sample optimized code with symbols using [Superluminal](https://superluminal.eu/docs/documentation.html)
on supported platforms. Use [Intel VTune Memory Access](https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2024-0/memory-access-analysis.html)
or [AMD uProf](https://docs.amd.com/r/en-US/57368-uProf-user-guide/Analyze-Profile-Data) when cache misses,
bandwidth or false sharing are suspected; PMU access and supported counters depend on hardware/OS.
On Linux, `perf record -g -- ./game`, then `perf report`, samples stacks; reliable unwinding needs
appropriate symbols/frame pointers or another configured unwind method. See [perf record](https://man7.org/linux/man-pages/man1/perf-record.1.html).
Use **Tracy** instrumentation to correlate systems, frames and waits. `ZoneScoped` marks a scope and
`FrameMark` a frame boundary when enabled; include/configure its client according to the pinned release.
See [Tracy's macros](https://github.com/wolfpld/tracy/blob/master/public/tracy/Tracy.hpp).

**Fixes to test:**

1. Fix algorithms first. An all-pairs neighbor scan remains quadratic after inlining. Use a spatial
   structure when neighborhood size and movement patterns justify maintenance costs; see the checklist.
2. Improve locality when memory stalls dominate: contiguous hot fields, fewer pointer-chasing objects,
   and separating cold metadata from the update data. Structure-of-arrays is useful when a loop touches
   only a few fields; array-of-structs may win when each operation needs the whole entity. Validate with
   hardware counters and frame time, not layout fashion; see [VTune's memory analysis](https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2024-0/memory-access-analysis.html).
3. Remove repeated allocation and growth from measured loops. Reserve realistic capacity and reuse
   scratch storage; bound it after exceptional peaks. Before, recreating a C++ scratch vector per frame:
   ```cpp
   std::vector<int> hits;
   hits.reserve(maxHits);
   ```
   After, reserve once during setup and clear the retained vector before refilling:
   ```cpp
   hits.clear();
   ```
   Clearing destroys elements but retains capacity; references/iterators may become invalid. In C, use
   an owned reusable buffer and logical length with checked capacity, not unchecked writes. See
   [vector capacity and clear](https://learn.microsoft.com/en-us/cpp/standard-library/vector-class).
4. Compare **GCC `-O2` / `-O3`, LTO (`-flto`) and PGO**. For GCC PGO, build with `-fprofile-generate`,
   exercise representative workloads, then rebuild with `-fprofile-use`; follow matching build/profile
   requirements. Apply LTO at compilation and linking. These are GCC spellings, not interchangeable
   flags for every compiler. More optimization can increase compile time/code size and lose instruction
   cache locality. See [GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).
5. Check whether a supposed release benchmark still enables debug iterators, instrumentation or costly
   assertions. MSVC `_ITERATOR_DEBUG_LEVEL` defaults differ between Debug and Release; keep ABI settings
   consistent across linked components. See [checked iterators](https://learn.microsoft.com/en-us/cpp/standard-library/checked-iterators).
   Preserve correctness checks in development and never put required side effects in `assert`; see
   [assert and NDEBUG](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/assert-macro-assert-wassert).

**Gotchas.** Undefined behavior is not optimization. Do not enable unsafe floating-point transformations
without accepting their numerical effects. Sampling, instrumentation, sanitizers and shipping builds
answer different questions; retain symbols separately when stripping the distribution.

## C#: .NET / Mono / IL2CPP

**Profile.** Match the tool to the runtime. [dotTrace](https://www.jetbrains.com/help/profiler/dotTrace_Introduction.html)
supports documented .NET/Mono/Unity configurations; [PerfView](https://github.com/microsoft/perfview)
analyzes CPU and GC/ETW/EventPipe data. For a supported modern .NET process, start with
`dotnet-trace collect --process-id <PID>`; see [dotnet-trace](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace).
IL2CPP is native AOT output: do not assume desktop CLR attachment works. Use the Unity Profiler and
native symbols/tools as appropriate; see [IL2CPP](https://docs.unity3d.com/2023.1/Documentation/Manual/IL2CPP.html).

**Fixes to test:**

1. Measure bytes allocated per frame and GC pauses. Reuse bounded lists/buffers, avoid rebuilding
   unchanged strings, and remove captured delegates created every frame. Pooling retains memory and
   needs complete reset/lifetime handling; see [allocation patterns](https://docs.unity3d.com/2022.3/Documentation/Manual/performance-garbage-collection-best-practices.html).
2. Remove boxing at a proven site: value-to-`object`/interface conversions and nongeneric containers
   can allocate. Small structs can improve locality; large copies, mutable-value semantics and boxing
   can make a blanket class-to-struct rewrite worse. See [struct/ref trade-offs](https://learn.microsoft.com/en-us/dotnet/csharp/advanced-topics/performance/ref-tutorial).
3. Replace allocating **LINQ** pipelines only where the profile warrants it. `ToArray` materializes a
   result; iterators and captured predicates may add overhead. `foreach` over an interface can box a
   struct enumerator, while a concrete collection's loop may not. Modern JITs can remove some costs;
   verify the shipped runtime instead of claiming every `foreach` or LINQ call allocates. See
   [.NET collection optimizations](https://devblogs.microsoft.com/dotnet/performance-improvements-in-net-5/).
   Before, collect merely to sum active values:
   ```csharp
   var active = entities.Where(entity => entity.Active).ToArray();
   float total = active.Sum(entity => entity.Energy);
   ```
   After, when `entities` is an existing array and a snapshot is unnecessary:
   ```csharp
   float total = 0;
   foreach (var entity in entities)
   {
       if (entity.Active)
       {
           total += entity.Energy;
       }
   }
   ```
   Check floating-point accumulation and concurrent modification assumptions before keeping this.
4. Use **Span<T>** for synchronous slices/views instead of allocating copies. It does not own data and
   has lifetime restrictions; it is not a replacement for every persistent or asynchronous buffer.
   Check the engine's API profile; see [memory and spans](https://learn.microsoft.com/en-us/dotnet/standard/memory-and-spans/).
5. Use **ArrayPool<T>** for sufficiently large transient arrays when reuse beats rent/return overhead.
   `Rent` provides at least the requested size; operate on the logical length. Return to the same pool
   in cleanup, never use a returned array, and clear reference/sensitive contents where necessary.
   See [ArrayPool return rules](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.arraypool-1.return).

**Gotchas.** A CLR microbenchmark does not establish Mono or IL2CPP behavior. Pooling everything can
increase retained memory. Disabling GC hides allocation pressure until memory runs out.

## Java and Kotlin on the JVM

**Profile.** Record **JDK Flight Recorder** during the actual scene, for example:
```text
jcmd <PID> JFR.start duration=1m settings=profile filename=game.jfr
```
The profile preset adds overhead; use short captures and inspect allocations, pauses and CPU stacks.
See [JFR commands](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html).
Use **async-profiler** for CPU, allocation or wall-time questions on supported systems; `asprof -e alloc`
selects allocation profiling. See [options](https://github.com/async-profiler/async-profiler/blob/master/docs/ProfilerOptions.md)
and [sampling limits](https://github.com/async-profiler/async-profiler/blob/master/docs/ProfilingModes.md).

1. Reduce measured allocation rate in simulation/render submission: reuse temporary math objects and
   buffers, remove unnecessary result lists, and bound long-lived pools. Check pause time and retained
   heap as well as allocation throughput; not every short-lived allocation needs manual pooling.
2. Keep dense numerical data in primitive arrays/collections where boxing dominates. Kotlin/JVM's
   `IntArray` is not `Array<Int>`; generic collections may box. See [Kotlin arrays](https://kotlinlang.org/docs/arrays.html)
   and [libGDX primitive collections](https://libgdx.com/wiki/utils/collections).
3. Do not rely on **escape analysis** to erase every temporary. HotSpot can scalar-replace eligible
   nonescaping objects, but storing/returning objects or opaque calls can prevent elimination. Inspect
   actual allocations after warm-up; see [HotSpot escape analysis](https://docs.oracle.com/en/java/javase/14/vm/java-hotspot-virtual-machine-performance-enhancements.html).
4. Cache expensive derived results and reduce repeated searches before tuning JVM flags. Preserve
   invalidation and thread ownership; a bigger heap does not fix a quadratic scan.
5. Batch engine/native calls over primitive data when the boundary dominates. Copying and buffer
   conversion can consume the gain; confirm both JVM and native time in the trace.

**Gotchas.** Separate JIT warm-up, asset warm-up and steady state. Kotlin on Native/JS is not a JVM
runtime; this toolchain guidance does not transfer unchanged. Avoid collector/heap folklore without a
recording showing a GC problem.

## Lua / LuaJIT / Luau

**Profile.** Use the host engine's script profiler for Lua/Luau. With **LuaJIT**, `luajit -jp game.lua`
uses the sampling profiler (**jit.p**), which also samples interpreted code; see [profiler](https://luajit.org/ext_profiler.html).
`luajit -jv game.lua` enables verbose tracing (**jit.v**) to expose compilation/abort behavior; see
[jit.v source and usage](https://github.com/LuaJIT/LuaJIT/blob/v2.1/src/jit/v.lua).
Embedded runtimes may not expose these command-line routes or ship the modules; check their build.

1. Prefer scoped locals and stable table shapes in hot code. In plain Lua, caching a repeatedly accessed
   global may avoid lookups; measure first. Luau already imports many global chains such as `math.max`,
   so mechanically aliasing every builtin is not a universal win. See [Lua performance tips](https://lua.org/gems/sample.pdf)
   and [Luau's optimizer](https://luau.org/performance/).
2. Reuse scratch tables where allocation/GC is measured. Luau `table.create` preallocates array storage;
   `table.clear` retains capacity. These are not standard Lua APIs. Clear stale references and cap
   capacity; see [Luau table.clear](https://rfcs.luau.org/function-table-clear.html).
3. Avoid creating a capturing closure per entity per frame when the profile shows allocation cost.
   Reuse a suitable function or pass explicit state; do not capture a loop variable with the wrong
   lifetime. Compilers can optimize some closures, so count actual allocations. See [Luau closures](https://luau.org/performance/).
4. Build many fragments into a table and concatenate once. Before:
   ```lua
   local text = ""
   for i = 1, #parts do
       text = text .. parts[i]
   end
   ```
   After, for an existing dense sequence of strings:
   ```lua
   local text = table.concat(parts)
   ```
   This avoids repeatedly copying an ever-growing prefix; it is not a reason to rewrite one small
   concatenation. See [Lua string construction](https://www.lua.org/notes/ltn009.html).
5. With LuaJIT, investigate repeated trace aborts, side exits and **NYI** operations on the actual hot
   loop. Not every builtin/C function is recorded the same way across versions. Restructure or move
   unsupported work outside the loop only after a profile and `jit.v` show a problem; do not copy an old
   blanket NYI list. See [trace diagnostics](https://github.com/LuaJIT/LuaJIT/blob/v2.1/src/jit/v.lua).

**Gotchas.** LuaJIT, stock Lua and Luau have different optimizers and libraries. LuaJIT settings do
not configure Luau. Table reuse retains references unless cleared, and pools need explicit bounds.

## Python: pygame / pyglet / Arcade

**Profile.** `python -m cProfile -s cumulative game.py` identifies cumulative Python call cost; instrumentation
can distort short calls. See [cProfile](https://docs.python.org/3/library/profile.html).
Use [py-spy](https://github.com/benfred/py-spy) for external sampling, or
[Scalene](https://github.com/plasma-umass/scalene) to distinguish Python/native CPU, allocation and copying
costs. Check support for the Python version/build and OS; none replaces GPU frame timing.

1. Replace Python element-by-element numeric work with **NumPy** operations when the data already fits
   contiguous arrays. Avoid converting lists to arrays and back every frame. Before:
   ```python
   for i in range(len(x)):
       x[i] += dx[i]
   ```
   After, when both are compatible preexisting arrays:
   ```python
   np.add(x, dx, out=x)
   ```
   `out` can reuse storage; dtype, broadcasting and aliasing must preserve semantics. See [ufuncs](https://numpy.org/doc/stable/reference/ufuncs.html).
2. Move a substantial measured loop to **Cython** typed memoryviews, **Numba** nopython compilation, or
   a **Rust** extension. Pass batches, not individual entities across the boundary. Include compilation,
   packaging and marshaling costs; warm JIT-compiled kernels before steady-state timing. See
   [Cython memoryviews](https://cython.readthedocs.io/en/latest/src/userguide/memoryviews.html),
   [Numba performance](https://numba.readthedocs.io/en/latest/user/performance-tips.html), and [PyO3 parallelism](https://pyo3.rs/v0.30.1/parallelism).
3. Cache repeated asset conversions, geometry and derived data until their inputs change. Reuse large
   arrays and avoid accidental copies between Python and native libraries; Scalene's copying metrics
   can establish whether a boundary is the problem. Retained caches need size and lifetime limits.
4. Fix broad collision/query complexity before translating it to another language. A compiled all-pairs
   algorithm still scales badly; preserve the engine's collision semantics when adding an index.
5. Treat interpreter upgrades as measured experiments. **Python 3.13** introduced optional experimental
   free-threaded builds (`--disable-gil`) and an experimental JIT (`--enable-experimental-jit`); neither
   makes an ordinary 3.13 installation automatically parallel/faster. See [3.13 build options](https://docs.python.org/3.13/using/configure.html).
   **Late-2026 status, checked 2026-10-21:** free-threaded Python became officially supported in **3.14**
   but remains an optional build; extension compatibility still matters. See [3.14 changes](https://docs.python.org/3.14/whatsnew/3.14.html).
   **3.15**, released in October 2026, still describes its upgraded JIT as **experimental**. Availability
   and gains depend on the build/workload; do not project benchmark-suite gains onto a game. See
   [3.15 release notes](https://docs.python.org/3.15/whatsnew/3.15.html#upgraded-experimental-jit-compiler).

**Gotchas.** Removing the GIL does not make a windowing/rendering API thread-safe. Ordinary GIL builds
do not parallelize Python bytecode just by adding threads; native code may release it. Keep the engine's
graphics/event loop on its required thread and verify every native dependency before changing builds.

## JavaScript / TypeScript

**Profile.** Use [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/reference)
for task stacks and frame stalls, and [Memory tools](https://developer.chrome.com/docs/devtools/memory-problems)
for allocation/retention. Include warm-up and reproduce on the shipping browser/device. TypeScript types
do not impose a typed runtime representation; see [type erasure](https://www.typescriptlang.org/docs/handbook/2/basic-types.html).

1. Keep hot object layouts and field types stable when profiles implicate property access. Initialize
   fields consistently rather than repeatedly adding/deleting them. V8 **HiddenClasses** and inline
   caches exploit repeated shapes; this is implementation guidance, not a JS specification guarantee.
   See [V8 properties](https://v8.dev/blog/fast-properties).
2. Investigate optimization/deoptimization churn only for a measured CPU hotspot. Polymorphic inputs
   and changing assumptions can invalidate optimized code, but one deoptimization is not proof of a
   frame problem. Avoid outdated syntax bans; see [V8 deoptimization context](https://v8.dev/blog/lazy-unlinking).
3. Reuse transient vectors/results if the allocation timeline shows GC stalls; keep bounded pools and
   clear references/listeners on release. Avoid rebuilding unchanged text/geometry. Long-lived pools
   can increase retained heap, so compare both frame tails and memory; see [memory diagnosis](https://developer.chrome.com/docs/devtools/memory-problems).
4. Use **typed arrays** for dense numeric buffers and bulk engine uploads. They have explicit element
   formats, so check precision, integer conversion and buffer bounds. They are not universally faster
   object replacements; see [typed arrays](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Typed_arrays).
5. Move independent simulation/decoding to **Workers** only when communication is cheaper than the work.
   Transfer an `ArrayBuffer` instead of cloning a large payload where appropriate; transfer detaches it
   from the sender. A typed-array view itself is not the transferable object. See
   [transferable objects](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Transferable_objects).

**Gotchas.** Workers cannot directly mutate DOM state. Measure responsiveness separately from total
throughput. Browser, Node and embedded JS runtimes have different JIT, profiler and API support.

## GDScript

**Profile.** Use Godot's script Profiler to find function/self time and call count; use Visual Profiler
for rendering cost. A slow script caller can actually be waiting inside native engine work. See
[Debugger panels](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/debugger_panel.html).

1. Type operands, arguments and returns in arithmetic-heavy code. Godot 4 can choose optimized opcodes
   when types are known; gains depend on the operations, not annotation count. See [static typing](https://docs.godotengine.org/en/4.4/tutorials/scripting/gdscript/static_typing.html).
2. Resolve stable node paths once with `@onready` references, then use the reference in hot callbacks;
   refresh it if the node is replaced. See [nodes and instances](https://docs.godotengine.org/en/stable/tutorials/scripting/nodes_and_scene_instances.html).
3. Use signals or dirty-state updates for unchanged UI/derived state instead of repeated per-frame
   lookups and rebuilds. Preserve event ordering and disconnect according to object lifetime. See
   [signals](https://docs.godotengine.org/en/stable/getting_started/step_by_step/signals.html).
4. For a proven large compute loop, compare bulk GDExtension/C# code or server APIs as described in
   [engine projects](engine-projects.md); integration cost is justified by measured native/script savings.

**Gotchas.** Typed GDScript is still GDScript, not an automatic C++ translation. Reducing script overhead
will not remove an expensive physics query, too many draws or a GPU bottleneck.

## Rust

**Profile.** Start with `cargo run --release`; optimized code and debug symbols are compatible.
`cargo flamegraph` profiles a release build by default; follow its current platform/linker guidance if
stacks are incomplete. See [cargo-flamegraph](https://github.com/flamegraph-rs/flamegraph).

1. Check **Cargo profiles** before rewriting code: `opt-level`, `lto` and `codegen-units` trade runtime,
   code size and build time. Test a candidate such as the following rather than asserting it always wins:
   ```toml
   [profile.release]
   debug = 1
   lto = "thin"
   codegen-units = 1
   ```
   Release already defaults to optimization level 3; level 3 is not always fastest. Keep the candidate
   only when the game improves. See [Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html).
2. Distinguish debug assertions and integer overflow checks from release behavior. Cargo defaults enable
   both in dev and disable both in release. Use explicit checked/wrapping arithmetic where semantics
   require it; never rely on a debug-only panic for correctness. See [profile defaults](https://doc.rust-lang.org/cargo/reference/profiles.html).
3. Reuse vectors and buffers in hot loops instead of allocating/collecting each frame. `Vec::clear`
   drops elements and retains capacity; cap retained storage after peaks. See [Vec guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html).
4. Avoid unnecessary `clone` of owned data and repeated string formatting; borrow existing data where
   ownership permits. Copies of small values may be cheaper than indirection, so profile actual types.
5. Improve contiguous traversal and query selectivity before adding threads or unsafe code. Scheduling,
   synchronization and cache contention can exceed a small loop's work; respect engine ownership.

**Gotchas.** Iterator chains are not inherently slower than manual loops, and collecting is not always
free. Inspect allocations and optimized profiles rather than replacing idiomatic code mechanically.

## Go

**Profile.** Use CPU/heap **pprof** profiles and **go tool trace** for scheduler, blocking and GC events;
see [Go diagnostics](https://go.dev/doc/diagnostics).
Test three small changes: reuse bounded scratch slices; reduce escaping/per-frame objects where heap
profiles show churn; batch independent work instead of creating a goroutine per tiny update. Preallocation
and lower allocation rate trade retained memory for GC work; see [Go's GC guide](https://go.dev/doc/gc-guide).
**Gotchas.** Goroutines do not make graphics APIs thread-safe. Confirm ownership and measure latency;
do not tune GC frequency before knowing allocation rate and live heap size.

## Zig

**Profile.** Sample an optimized binary with symbols using the native tools in the C/C++ section.
Compare **ReleaseSafe** and **ReleaseFast** for the actual hot path; ReleaseFast disables safety checks,
so this is a correctness trade-off, not a free speed switch. See [Zig build modes](https://ziglang.org/documentation/master/#Build-Mode).
Test three changes: reuse explicitly owned scratch storage; keep hot numeric data contiguous; move
repeated parsing/searches outside the frame loop. Preserve allocator ownership and bounds. Zig's APIs
change between versions, so follow the project's pinned standard library rather than pasting allocator
examples from another release; see [Zig documentation](https://ziglang.org/documentation/).
**Gotchas.** Benchmark build modes with identical inputs; disabling safety does not fix bad complexity.

## Universal hot-path checklist

1. **Algorithmic complexity first.** Replace an O(n²) all-pairs neighbor scan with a spatial hash/grid
   when queries are local. Query every cell intersecting the search radius and perform an exact final
   distance test. Dense occupancy can still approach quadratic behavior; account for moving objects,
   rebuild cost, cell size and deterministic ordering. See [spatial partitioning](https://gameprogrammingpatterns.com/spatial-partition.html).
2. **Per-frame allocation.** Count allocations/bytes at the source, remove avoidable temporaries, and
   compare GC pauses or allocator contention. Bound pools and release obsolete references/resources.
3. **Redundant work every frame.** Cache with explicit invalidation, throttle noncritical tasks, or use
   event-driven updates. Check worst-case response delay and spread periodic work to avoid new spikes.
4. **Batch draw calls and I/O.** Group compatible rendering and bulk data operations where order permits.
   Larger batches can cost memory, weaken culling, or add latency; measure the resulting frame.
5. **Move off the main thread only when allowed.** Transfer independent owned data through supported
   engine job/worker APIs; include synchronization, copying and result-consumption costs in the budget.
6. **Measure after every change.** Repeat the same scene twice, compare frame-time distributions and
   memory, then test correctness. Keep wins beyond noise; revert losses and unexplained complexity.
   See [the baseline/change/compare loop](../../optimize-any-game/SKILL.md).
