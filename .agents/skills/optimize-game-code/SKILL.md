---
name: optimize-game-code
description: Make a game run faster by changing its source code, as its developer, in any engine or language - Roblox (Luau scripts in Studio or Rojo), Unity (C#), Unreal (C++/Blueprints), Godot (GDScript/C#), GameMaker (GML), LÖVE (Lua), MonoGame/FNA, Bevy (Rust), libGDX (Java), web games (JS/TS), custom C/C++ engines, Python games. Use when the user has the game's project or scripts and wants better FPS, less lag, less server load, less memory, faster loading, or a profile of what is slow ("my scripts lag", "optimize this game's code", "why is my server heartbeat low", "reduce memory in my experience"). It covers profiling with the engine's own tools, finding the hot path, fixing it, and proving the gain.
---

# Optimize game code

You are the engine programmer on the team. The user owns the source. Your job: find the code that costs the
frame (or the server tick, or the memory), make it cheaper without changing what the game does, and prove it
with the same measurement before and after.

For a shipped game the user only plays, use the **optimize-any-game** skill instead.

## Your tools
- `uo plan <project folder>` names the kind of project and its languages, and points to the guide below.
- The engine's own profiler. It sees inside the frame and is the source of truth: Roblox MicroProfiler and
  Script Profiler, Unity Profiler, Unreal Insights, Godot's profiler, Chrome DevTools, spark/JFR, dotnet-trace,
  Tracy, Superluminal. If a Roblox Studio MCP server is connected, use its profiler, memory and scene tools
  instead of guessing.
- `uo bench` / `uo compare` for frame-time numbers of a running build on Windows (PresentMon).
- The project's own tests, if any. Run them after every change.

## The loop

### 0. Intake
What is slow (client FPS, server tick/heartbeat, load time, memory, network), where (scene, player count,
device), and the target. Read the project's conventions before editing: style, strictness, file layout,
naming. Every edit matches them. Start `OPTLOG.md` in the project: each change, the numbers, keep or revert.

### 1. Make it measurable
- One repeatable scenario: a scene or map, a fixed number of players, bots, or entities, a scripted camera
  path, or a stress script that spawns the heavy case. Write it down so anyone can rerun it.
- Measure on a representative target. Editors and Studio are slower than shipped builds and live servers;
  development builds of engines carry profiling overhead. Compare like with like.
- Baseline: frame or tick time (average, 99th percentile, spikes), memory, and network if relevant. Twice.

### 2. Profile, then read
- Capture the slow moment with the engine profiler. Find the top 3 costs on the thread that bounds the
  frame (main/game thread, render thread, server simulation).
- Read the code behind each one, end to end: who calls it, how often (per frame? per entity per frame?),
  what it allocates, what it waits on.
- Don't optimize code the profiler didn't flag. Clean-looking code that runs once is not the problem.

### 3. Fix the cheapest big thing
In rough order of payoff:
1. **Algorithm.** O(n²) scans become spatial grids or hash lookups; repeated searches become a cache built
   once; linear lookups in hot loops become maps.
2. **Work per frame.** Cache what doesn't change, throttle what doesn't need 60 Hz (AI, pathing, UI text,
   distance checks), move to events instead of polling, spread a big job over frames.
3. **Allocations and garbage.** Reuse tables, arrays, lists and buffers; no closures, string building or LINQ
   in hot paths; pool spawned objects.
4. **Engine object costs.** Fewer instances, nodes or actors; batch draw calls; cheaper collision and physics;
   streaming and LOD; fewer per-object ticking components.
5. **Network.** Send less, less often, and smaller; batch; send unreliably what may drop; never replicate what the
   client can derive.
6. **Parallelism**, only once the above is done and the engine supports it safely (Parallel Luau Actors, Unity
   Jobs/Burst, Godot threads/servers, worker threads). It adds sync cost and bugs.

Keep behaviour identical unless the user agrees to a trade-off (lower AI update rate, shorter view distance).
Keep the diff small and in the project's style.

### 4. Re-measure and verify
Same scenario, same measurement, twice. Keep the change only if it beats noise. Then check the game still
plays the same: run the tests, play the affected feature, watch the logs for new errors.

### 5. Report
Before/after numbers, what changed and why it was slow, any trade-off, and the next hottest item. Leave a
note in the knowledge base (`knowledge/`) for techniques that will help other projects.

## Rules
- **Server authority stays.** Never move validation or game state to the client to save server time, and
  never trust client data you didn't validate.
- **No behaviour changes in disguise.** Lowering an update rate or a radius is a design change: ask first.
- **No placebo.** Micro-optimizations the profiler can't see are noise. Say so instead of doing them.
- **Respect the codebase.** Match its style, keep unrelated code untouched, run its tests.
- **Fix leaks at the source.** Disconnect what you connect, destroy what you create, drop references to dead
  objects. A periodic "cleanup" timer is not a fix.

## References
- `references/roblox-luau.md`: Roblox experiences. MicroProfiler, Script Profiler, memory, native codegen,
  Parallel Luau, streaming, physics, networking, UI, leaks; a short player-side section.
- `references/engine-projects.md`: Unity, Unreal, Godot, GameMaker, LÖVE, MonoGame/FNA, Bevy, libGDX, web
  games.
- `references/languages.md`: C/C++, C#, Java/Kotlin, Lua/LuaJIT/Luau, Python, JS/TS, GDScript, Rust; the
  universal hot-path checklist.
- For shipped games and platform-level settings: the **optimize-any-game** skill.
