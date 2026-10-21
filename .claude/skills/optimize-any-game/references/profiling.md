# Finding the bottleneck

Optimize what limits the frame, nothing else. A faster GPU setting does nothing for a game stuck on one CPU
thread, and a code patch on a function that takes 0.2 ms of a 30 ms frame is wasted work.

## 1. The first read: `uo bench`

`uo bench <exe> -o run.json` gives, per run:
- **avg FPS, 1% low, 0.1% low, p99 frame time, stutters/min.** Lows and stutters are what the player feels.
  Two runs with the same average can feel completely different.
- **`bound`** from PresentMon's `MsGPUBusy` / `MsBetweenPresents`:
  - `GPU`: the GPU is busy for ~90%+ of each frame. GPU-side levers only: resolution, upscaler, the heavy
    settings (shadows, volumetrics, ray tracing, reflections, AO), GPU cvars.
  - `CPU/engine`: the GPU waits. CPU-side levers: simulation load, draw calls, view distance, API
    translation, engine fixes, code patches. Lowering resolution barely helps; check that it doesn't.
  - `mixed`: both are close; it changes with the scene. Measure the worst scene.
- **`busiest_thread_pct`**: CPU time of the busiest thread over the run. Near 100% means one thread (main,
  game or render thread) is the wall, which is the normal case for older and simulation-heavy games. More
  cores won't help; less work on that thread will.
- **Working set and private bytes.** Private bytes are what the process committed; working set is what is in
  RAM right now. Private bytes that climb across a long run is a leak or an unbounded cache.

A quick confirmation that needs no tools: drop the resolution to the minimum (or the render scale to 50%).
If FPS barely moves, the game is CPU/engine-bound in that scene.

## 2. Stutter: what kind

| Pattern | Cause | How to confirm |
|---|---|---|
| Hitches the first time an effect, area or enemy appears; a second pass is smooth | shader / PSO compilation | run the scene twice: the second run's stutters/min drops sharply |
| Hitches while moving through the world, every run | asset streaming (disk, decompression, VRAM overflow) | GPU dedicated memory near the card's limit in Task Manager; disk reads spike in Resource Monitor; lower texture quality helps |
| Regular hitches every few seconds, standing still | garbage collection (Unity/Mono, .NET, JVM, Lua) or a periodic system (autosave, AI tick) | the engine's GC log or profiler; spark/JFR for Java; the period is regular |
| Frame times alternate fast/slow, average looks fine | pacing: no cap, VSync/VRR mismatch, a frame-rate-tied loop | a frame cap just under the 1% lows smooths it |
| Hitches line up with an overlay, capture or background task | outside the game | close it and remeasure |

## 3. Profilers, by what they can see

### Any Windows process, no source: Windows Performance Recorder / Analyzer
Built into Windows 10/11 (`wpr`); the analyzer (WPA) comes with the Windows Performance Toolkit (Windows
ADK) or the Microsoft Store.
```powershell
wpr -start CPU -start GPU -filemode      # elevated shell; then play the bad scene for 10-20 s
wpr -stop trace.etl
```
Open `trace.etl` in WPA: *CPU Usage (Sampled)* grouped by Process → Thread → Stack shows which thread is
hot and which functions inside it. Load symbols where they exist (Microsoft's symbol server covers Windows
and driver DLLs; games usually ship none, so you see `module!offset` and map hot offsets in Ghidra/IDA).
*GPU Utilization* and *Generic Events / DXGI present* line up frames with CPU work. `wpr -profiles` lists
other built-in profiles (DiskIO, FileIO, Heap, VirtualAllocation, DotNET).

Other samplers that read the same data with less friction: Superluminal (paid, excellent with symbols),
Intel VTune (free), AMD uProf (free), and Very Sleepy (free, simple).

### Engine and runtime profilers
| Runtime | Profiler | Notes |
|---|---|---|
| Unity | the Unity Profiler needs a Development build; for shipped games use a sampler plus Harmony timing patches | see `engines/unity.md` |
| Unreal | `stat unit`, `stat fps`, `stat gpu`, `stat game` from the console (UUU or UE4SS unlocks it); Unreal Insights needs a build with tracing | see `engines/unreal.md` |
| Java (Minecraft, JVM games) | spark (`/spark profiler`), JDK Flight Recorder + Mission Control, async-profiler | see `engines/java.md` |
| .NET Core / .NET 5+ (tModLoader...) | `dotnet-trace`, `dotnet-counters`, PerfView, dotTrace | see `engines/dotnet-xna.md` |
| .NET Framework / Mono | PerfView (Framework), dotTrace; Mono: sampling + Harmony stopwatch patches | |
| Lua / scripted | the engine's own profiler or a Lua hook profiler | see `engines/scripted.md` |
| Browser engines (Electron, NW.js) | Chrome DevTools Performance panel (`--remote-debugging-port`) | see `engines/scripted.md` |
| GPU work | the vendor tools: NVIDIA Nsight Graphics, AMD Radeon GPU Profiler, Intel GPA, PIX (D3D12), RenderDoc (per-frame inspection, not timing) | single-player only: they inject |

### Memory
- **Task Manager → Details** with the *Commit size* column (private bytes) and *GPU dedicated memory*
  (VRAM). VRAM at the card's limit is a stutter cause; RAM rarely is unless it is truly full.
- **Sysinternals VMMap** (one process: private, heap, image, mapped) and **RAMMap** (the whole machine).
- Managed runtimes: their heap tools (spark `heapsummary`, `dotnet-gcdump`, JFR's allocation profiling).
- A 32-bit process dies near 2 GB of address space (4 GB with Large Address Aware): watch *Commit size* as
  it approaches the cap before a crash.

## 4. From a hot spot to a fix

1. Confirm it's on the critical thread (the busiest one, the one the frame waits for). A hot function on a
   worker thread that finishes early changes nothing.
2. Find out why it is hot: called too often (per frame per entity), doing too much per call (O(n^2) scans,
   string building, reflection, allocations), or waiting (locks, `Sleep`, sync reads, busy-wait limiters).
3. Pick the cheapest correct fix: cache the result, do it every N frames, use a spatial lookup, move it off
   the main thread only if the engine allows it, delete the work if nobody uses its result.
4. Patch through the game's modding route and remeasure the same scene. If the frame time doesn't move,
   the profile misled you: revert and look again.
