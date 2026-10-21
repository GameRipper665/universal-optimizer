# Roblox / Luau: developer optimization

For an experience the user develops, with its place open in Studio or source available through Rojo. Edit the source of truth, preserve behavior, and keep only measured
improvements. This is not a client tweak pack. Sources checked 2026-10-21; recheck platform availability and rolling features against current Creator Hub docs.

## 1. Measure first

Record the place revision, device, graphics level, frame cap, player count, camera route, workload, and capture duration. Warm assets once, then take two baseline runs and two runs
after each change. Measure cold joins separately. Compare frame-time distributions and spikes, server step time, script CPU, memory growth, and traffic; average FPS alone hides
stalls. Log the change, numbers, trade-off, and rollback. A result inside baseline variation is noise, not a win.

Use the [MicroProfiler](https://create.roblox.com/docs/performance-optimization/microprofiler) to distinguish script, physics, rendering, and other engine work. The overview
documents **Ctrl+F6** on desktop/Studio; the [walkthrough](https://create.roblox.com/docs/performance-optimization/microprofiler/use-microprofiler) documents **Ctrl+Alt+F6**. Try
the shortcut for the installed build; do not diagnose a broken profiler from that discrepancy. For a server capture, join with edit permissions, open Developer Console, select
**MicroProfiler > Server**, and use **Begin server recording**. A client capture does not measure server execution. Save comparable dumps. Wrap a measured, non-yielding hot
section with paired [`debug.profilebegin("label")` / `debug.profileend()`](https://create.roblox.com/docs/reference/engine/libraries/debug). Keep labels stable and make every exit
close the scope; instrumentation also has overhead.

The Developer Console [Script Profiler](https://create.roblox.com/docs/studio/optimization/scriptprofiler) records client or server script CPU, including function calls and engine
API access. Select the correct environment and export the capture. Waiting threads are not CPU work: a slow data load can be absent from this profile. Use the same sampling
settings before and after; avoid interpreting profiler overhead as a game regression.

In Developer Console **Memory**, compare Client and Server separately. Verified category names include `CoreMemory`, `PlaceMemory`, `PlaceScriptMemory`, `Instances`, `Signals`,
`LuaHeap`, `Script`, `PhysicsCollision`, `PhysicsParts`, `GraphicsMeshParts`, `GraphicsTexture`, `Gui`, and `Animation`. The [memory
guide](https://create.roblox.com/docs/studio/optimization/memory-usage) also documents **LuauHeap** snapshots, allocation graphs, and paths retaining unparented instances. Compare
snapshots after repeated spawn/despawn, join/leave, or open/close cycles. Heap size is not total engine, texture, or process memory.

For memory by script, use `PlaceScriptMemory` and Studio [Scene Analysis](https://create.roblox.com/docs/performance-optimization/scene-analysis), including its script-memory,
unparented-instance, instance-composition, and triangle-composition views. Programmatic tooling exists through
[`SceneAnalysisService:GetScriptMemoryAsync()`](https://create.roblox.com/docs/reference/engine/classes/SceneAnalysisService).

The [`Stats` service](https://create.roblox.com/docs/reference/engine/classes/Stats) exposes `InstanceCount`, `GetTotalMemoryUsageMb()`, `GetMemoryUsageMbForTag()`, `DataSendKbps`,
`DataReceiveKbps`, `PhysicsSendKbps`, and `PhysicsReceiveKbps`. These describe the local client or server being observed; server traffic aggregates clients. The network rates are
documented as **kilobytes/second**, despite the property spelling. If `MemoryTrackingEnabled` is false, per-tag reads return zero; that is not proof of zero usage. Console
`PhysicsParts` is not an enum member: the corresponding [`Enum.DeveloperMemoryTag`](https://create.roblox.com/docs/reference/engine/enums/DeveloperMemoryTag) name is `BaseParts`.
Use Performance Stats/debug network stats for replication and ping. Developer Console's [Network tab](https://create.roblox.com/docs/studio/developer-console#network) reports web
calls, including HTTP and data-store requests; it is not a per-RemoteEvent bandwidth report.

A Studio MCP may expose `capture_micro_profiler`, `capture_script_profiler`, `get_memory_breakdown`, and `get_scene_analysis`, or equivalent tools. Discover its schema, select the
correct Studio session and client/server scope, and prefer captures over guessing. Tool names and availability depend on the MCP implementation; the [MicroProfiler
documentation](https://create.roblox.com/docs/performance-optimization/microprofiler) confirms MCP integration.

Keep server size fixed. In an authorized test session, a deterministic Studio bot/stress harness can spawn the same NPC count, repeat actions, and clean up afterward. NPC bots
reproduce simulation load, not real client replication. [Solo Test/Play Solo](https://create.roblox.com/docs/studio/testing-modes) has client and server simulations but one player;
**Server & Clients** tests replication among multiple clients; **Team Test** lets collaborators join one test. Local clients compete for one computer's resources. Studio adds
editor overhead and is often slower than the live client; verify on target hardware in a published test place. Roblox explicitly warns that [Studio performance stats are
skewed](https://create.roblox.com/docs/performance-optimization/identify). Do not start tests, inject stress scripts, or edit client code without authorization for that work.

## 2. Luau script performance

### Native compilation and parallel work

[`--!native` and `@native`](https://create.roblox.com/docs/luau/native-code-gen) opt a script or individual function into native code generation. The current official guide
documents **server-side scripts**. A supported Studio machine is not evidence that every live client platform runs creator scripts natively; live-client rollout and its
supported-platform matrix are **(unverified)** here. Do not promise client gains. Target measured numeric/table/buffer computation, not code dominated by engine calls, rendering,
network waits, or algorithmic waste. Compilation costs startup time and native-code memory, with an overall code-size limit. Prefer `@native` on a hot function, then confirm
`<native>` in Script Profiler; breakpoints can disable it. Use `--!strict` for checking and accurate parameter types for specialization, especially `Vector3`. Strict checking alone
does not enable native compilation or guarantee faster bytecode.

For a profiled server math kernel, compare the same typed function with and without `@native`:

```luau
--!strict

@native
local function SquaredDistance(a: Vector3, b: Vector3): number
    local delta = a - b
    return delta:Dot(delta)
end
```

[`Vector3`](https://create.roblox.com/docs/reference/engine/datatypes/Vector3) uses Luau's optimized vector math; the [`vector`
library](https://create.roblox.com/docs/reference/engine/libraries/vector) also exists. Prefer these over allocating `{x, y, z}` tables. Arithmetic still costs time; avoid repeated
normalizations or magnitudes in inner loops. A squared-distance comparison avoids a square root when only a range check is needed.

[Parallel Luau](https://create.roblox.com/docs/scripting/multithreading) distributes independent computation across `Actor` boundaries on server or client. Scripts under one Actor
still execute serially relative to each other. Enter a parallel phase with `task.desynchronize()` or `RBXScriptSignal:ConnectParallel()`; use `task.synchronize()` before operations
requiring serial access. Check each API's thread-safety annotation, including property writes. Separate Actors, copied messages, scheduling, and synchronization have costs. Batch
substantial independent work; do not create an Actor per tiny operation. `task.spawn()` by itself does not provide multicore execution.
[`SharedTable`](https://create.roblox.com/docs/reference/engine/datatypes/SharedTable) shares supported data across Actors without ordinary table-message copying. It restricts
value types and requires coordination; a multi-step read/modify/write is not automatically atomic. Benchmark the whole pipeline, including serial apply time.

### Look up once; invalidate deliberately

Cache service references and stable instance references outside hot callbacks. `FindFirstChild()` searches and `WaitForChild()` can yield; neither belongs in a repeated lookup
chain when the dependency is already known. [`Instance` lookup methods](https://create.roblox.com/docs/reference/engine/classes/Instance) remain useful during initialization or
when handling actual hierarchy changes. This example assumes a stable server-owned `Arena.Center`.

Before:

```luau
--!strict

local function GetCenter(): Vector3
    local center = workspace:WaitForChild("Arena"):WaitForChild("Center")
    assert(center:IsA("BasePart"))
    return center.Position
end
```

After:

```luau
--!strict

local arena = workspace:WaitForChild("Arena")
local center = arena:WaitForChild("Center")
assert(center:IsA("BasePart"))

local function GetCenter(): Vector3
    return center.Position
end
```

Rebind when the map is replaced; a retained reference to an old part is both a correctness bug and memory cost. On streaming clients, objects can leave and return. Do not turn a
one-time cache into an assumption that streamed content always exists. Likewise, avoid `GetChildren()`/`GetDescendants()` every frame: their result arrays and full scans are work.
Maintain a small registry through hierarchy/tag events, with removal and teardown handling.

### Allocate less where profiles show churn

Reuse private scratch tables with [`table.clear()`](https://create.roblox.com/docs/reference/engine/libraries/table), which preserves capacity; `table.create(n)` preallocates array
space, not arbitrary dictionary capacity. Do not clear a table another task still uses, or retain a huge peak-sized pool forever. Reuse saves allocations at the cost of retained
capacity and stricter ownership. Avoid constructing captured closures in a hot loop when one reusable function works, but do not assume every closure allocates: Luau can cache some
closures. Build long strings as fragments with `table.concat()` instead of repeatedly growing a string. For actual binary data, the [`buffer`
library](https://create.roblox.com/docs/reference/engine/libraries/buffer) provides compact mutable storage; its APIs use byte offsets. Buffers passed through Roblox APIs are
copied, not shared across Actors. Custom binary formats add schema, bounds-checking, and decoding costs; measure against a simple table.

Luau resolves global chains such as `math.abs` through imports and specializes many builtins with fastcalls. `local abs = math.abs` is no longer a required speed trick; direct
calls already get these optimizations. Aliases can still be stylistic. Avoid environment mutation through `getfenv`/`setfenv` or `loadstring` that defeats import optimization. See
[Luau compiler performance](https://luau.org/performance/) and the [`math` API](https://create.roblox.com/docs/reference/engine/libraries/math); benchmark the actual workload.

### Do less per frame

Choose [`RunService` events](https://create.roblox.com/docs/reference/engine/classes/RunService) for semantics: `PreSimulation` adjusts inputs before physics; `PostSimulation`
observes/adjusts its result; `Heartbeat` follows physics for general work. `PreRender` is client-only and blocks rendering; it supersedes `RenderStepped` for new work. Use it
sparingly for camera/presentation changes. Changing event names alone does not remove computation.

Before, a noncritical refresh runs every frame:

```luau
--!strict

local RunService = game:GetService("RunService")

local function StartRefresh(refresh: () -> ()): RBXScriptConnection
    return RunService.Heartbeat:Connect(function(_deltaTime: number): ()
        refresh()
    end)
end
```

After, the caller accepts up to roughly 100 ms of staleness:

```luau
--!strict

local RunService = game:GetService("RunService")

local function StartRefresh(refresh: () -> ()): RBXScriptConnection
    local elapsed = 0
    return RunService.Heartbeat:Connect(function(deltaTime: number): ()
        elapsed += deltaTime
        if elapsed < 0.1 then
            return
        end

        elapsed %= 0.1
        refresh()
    end)
end
```

The owner must disconnect the returned connection. This skips missed refreshes rather than causing catch-up bursts; do not use it as a fixed-step gameplay integrator. For many
objects, process a bounded slice each frame and preserve a cursor; throttling one enormous scan merely creates less frequent enormous stalls.
[`task.wait()`](https://create.roblox.com/docs/scripting/scheduler) replaces legacy `wait()` and resumes on an eligible Heartbeat after the duration; timing is not exact.
`task.defer()` runs after the current resume point, potentially within the same frame. It neither makes work parallel nor guarantees a next-frame budget break.

## 3. Memory leaks

[`Instance:Destroy()`](https://create.roblox.com/docs/reference/engine/classes/Instance#Destroy) destroys children and disconnects signals belonging to that instance. It does
**not** disconnect a `RunService` or `Players` subscription whose callback captures the instance. `Parent = nil` is temporary unparenting, not disposal. Destroy owned objects,
disconnect external subscriptions, cancel pending work, and remove retained references.

Before, a long-lived service callback keeps a departed Player reachable:

```luau
--!strict

local RunService = game:GetService("RunService")

local function TrackPlayer(player: Player): ()
    RunService.Heartbeat:Connect(function(_deltaTime: number): ()
        player:SetAttribute("Tracked", true)
    end)
end
```

After, use one idempotent cleanup owner per player; the callback below is intentionally unchanged to isolate cleanup:

```luau
--!strict

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local connections: {[Player]: RBXScriptConnection} = {}

local function StopTracking(player: Player): ()
    local connection = connections[player]
    if connection then
        connection:Disconnect()
        connections[player] = nil
    end
end

local function TrackPlayer(player: Player): ()
    StopTracking(player)
    connections[player] = RunService.Heartbeat:Connect(function(_deltaTime: number): ()
        player:SetAttribute("Tracked", true)
    end)
end

Players.PlayerRemoving:Connect(StopTracking)
```

These are lifecycle fragments: call `TrackPlayer` from the existing join handler. The after version assumes a server-lifetime owner; a shorter-lived component must also disconnect
its `PlayerRemoving` connection and stop all tracked players. In production, set an unchanged attribute once rather than every frame.
[`Players.PlayerRemoving`](https://create.roblox.com/docs/reference/engine/classes/Players#PlayerRemoving) is also the cleanup point for player-keyed caches, queues, and session
state. Type annotations do not remove references.

Use the project's existing Maid/Trove/Janitor-style cleanup owner rather than adding three libraries. These are community ownership patterns, not engine services: register
connections, instances, tasks, and cleanup functions, and invoke cleanup on normal completion, cancellation, destruction, and player departure. Closures, delayed tasks, and module
tables can retain an entire dead hierarchy. Inspect retaining paths rather than periodically forcing collection or trimming process memory.

[Weak tables](https://create.roblox.com/docs/luau/metatables#use-weak-tables) use `__mode = "k"`, `"v"`, or `"kv"`. The omitted side remains strong; weak values do not fix strong
Player keys. Collection timing is nondeterministic. For Instances, the weak reference is to the Luau wrapper: losing it does not destroy the engine object, and an engine object
remaining alive does not guarantee its weak entry remains. Never use weak tables as lifecycle notifications or a substitute for explicit cleanup; avoid values/closures that
strongly retain their weak keys.

With [`CollectionService`](https://create.roblox.com/docs/reference/engine/classes/CollectionService), initialize existing tags via `GetTagged()`, handle `GetInstanceAddedSignal()`
and `GetInstanceRemovedSignal()`, and release per-instance resources on removal. Disconnect the service listeners when their owner ends; make setup idempotent.
[`Debris:AddItem(instance, lifetime)`](https://create.roblox.com/docs/reference/engine/classes/Debris) schedules destruction without yielding. Its queue has a 1,000-item cap, so
lifetime is a maximum, not an exact timer. It does not clear your tables, stop external connections, or replace immediate cancellation cleanup.

## 4. Engine-side costs a developer controls

Set [`Workspace.StreamingEnabled`](https://create.roblox.com/docs/workspace/streaming) in Studio, not a runtime script. Streaming reduces client residency/join work; it does not
unload the server's world. Tune `StreamingMinRadius` and `StreamingTargetRadius` in Studio: a larger high-priority/minimum region costs memory and bandwidth; a smaller target can
increase pop-in. Keep target greater than minimum and test traversal speed, teleports, interactions, and replication dependencies. Target radius is not a hard eviction boundary.
[`Model.ModelStreamingMode`](https://create.roblox.com/docs/reference/engine/classes/Model#ModelStreamingMode) supports `Atomic`, `Persistent`, and `PersistentPerPlayer`: atomic
models arrive as units; persistent content stays resident. Large atomic models create loading bursts; widespread persistence defeats memory savings. Reserve persistence for genuine
requirements. Streaming clients must tolerate absent/replaced instances and clean their registries.

Reduce unnecessary parts/instances and visible mesh/union triangles; part count alone does not predict draw calls. Use [Scene
Analysis](https://create.roblox.com/docs/performance-optimization/scene-analysis) to check actual instance, triangle, and draw-call composition. A single highly detailed union can
cost more than several simple objects. [`CollisionFidelity`](https://create.roblox.com/docs/reference/engine/enums/CollisionFidelity) `Box` or `Hull` can replace expensive
`PreciseConvexDecomposition` where simplified collisions are acceptable; verify doors, slopes, projectiles, and traversal. Visual mesh triangles and collision geometry are separate
budgets. [`RenderFidelity`](https://create.roblox.com/docs/reference/engine/enums/RenderFidelity) `Automatic`/`Performance` can reduce distant mesh detail compared with `Precise`;
the trade-off is visible simplification.

For decorative [`BasePart`s](https://create.roblox.com/docs/reference/engine/classes/BasePart), disable `CanCollide`, `CanTouch`, or `CanQuery` only when gameplay permits.
`CanCollide = false` alone still allows touch events; `CanQuery = false` takes effect when collision is disabled and removes the part from spatial queries. Anchor static geometry;
anchoring moving mechanisms changes behavior. Selective `CastShadow = false` can help complex scenes but removes shadows and can cause artifacts. Confirm a GPU/shadow bottleneck
before applying it.

Old guides compare `Enum.Technology.Voxel`, `ShadowMap`, and `Future`, but [`Lighting.Technology` is
deprecated](https://create.roblox.com/docs/reference/engine/classes/Lighting#Technology). Use current [global lighting
controls](https://create.roblox.com/docs/environment/lighting): `LightingStyle` (`Soft`/`Realistic`) and `PrioritizeLightingQuality`. The latter trades lighting/shading quality
against view distance as quality scales down. Recheck appearance on target devices; a style name is not a guaranteed FPS gain. Reduce overlapping translucent surfaces and effects
when overdraw is measured; the trade-off is visual density.

To reduce [Humanoid computation](https://create.roblox.com/docs/performance-optimization/improve#humanoids) on static animated NPCs, an
[`AnimationController`](https://create.roblox.com/docs/reference/engine/classes/AnimationController) with an `Animator` can replace a `Humanoid` when its movement/state machinery
is unnecessary. Movement, health, and state behavior then need another owner; do not strip Humanoids from functioning characters as a blanket optimization. Reduce unnecessary
constraints and let inactive assemblies [sleep](https://create.roblox.com/docs/physics/sleep-system); repeated force/transform changes can keep them awake.
[`SetNetworkOwner(player)`](https://create.roblox.com/docs/physics/network-ownership) distributes eligible unanchored physics from the server and improves local responsiveness, but
grants that client control of the simulation. `SetNetworkOwner(nil)` keeps server ownership at a server CPU/latency cost; validate gameplay outcomes either way. Inspect
[`workspace:GetPhysicsThrottling()`](https://create.roblox.com/docs/reference/engine/classes/Workspace#GetPhysicsThrottling) when physics slows under load. Reduce active mechanisms
instead of disabling throttling as an FPS tweak. [`Workspace.PhysicsSteppingMethod`](https://create.roblox.com/docs/reference/engine/classes/Workspace#PhysicsSteppingMethod) with
`Enum.PhysicsSteppingMethod.Adaptive` can reduce work versus fixed stepping; test stability and fast collisions.

## 5. Networking

Measure frequency * payload * recipients, including automatic instance/property replication. Send changed, relevant state to the clients that need it; avoid broadcasting huge
tables or rebuilding replicated hierarchies. [`RemoteEvent`](https://create.roblox.com/docs/reference/engine/classes/RemoteEvent) batching reduces call overhead, but oversized
bursts add latency and deserialization spikes. Bound both batch size and update frequency.

Before, one server message per visual marker:

```luau
--!strict

local function SendMarkers(remote: RemoteEvent, player: Player, positions: {Vector3}): ()
    for _, position in positions do
        remote:FireClient(player, position)
    end
end
```

After, a bounded snapshot batch; the receiving handler must now consume arrays:

```luau
--!strict

local function SendMarkers(remote: RemoteEvent, player: Player, positions: {Vector3}): ()
    local batch: {Vector3} = table.create(32)
    for _, position in positions do
        batch[#batch + 1] = position
        if #batch == 32 then
            remote:FireClient(player, batch)
            table.clear(batch)
        end
    end

    if #batch > 0 then
        remote:FireClient(player, batch)
    end
end
```

Thirty-two is an illustrative application bound, not a Roblox limit. This batches one refresh without waiting to fill a batch; schedule refreshes separately. If thousands remain,
spread or cull them rather than emitting all chunks in one frame. Clearing is safe after this non-yielding remote serialization; never do that with a custom asynchronous sender
that retains the table. Change both ends of the protocol only within authorized scope.

[`UnreliableRemoteEvent`](https://create.roblox.com/docs/reference/engine/classes/UnreliableRemoteEvent) suits disposable cosmetic/continuously refreshed state: messages can be
lost or reordered, and payloads above 1,000 bytes are dropped. Use sequence numbers when stale updates matter. Keep purchases, inventory, and authoritative outcomes reliable; an
unreliable remote is not a drop-in replacement for every event. Server-set [attributes](https://create.roblox.com/docs/studio/properties#instance-attributes) on replicated
instances are convenient observable state, but still replicate. Use attributes for persistent small state and targeted remotes for explicit messages/audiences; replacing one with
the other is not automatically a bandwidth win. Never depend on an attribute/property change arriving before a related remote; include necessary message state. At every
[client/server boundary](https://create.roblox.com/docs/scripting/security/client-server-boundary), validate types, table/string sizes, finite numbers, instance ownership/location,
permissions, cooldowns, and rate limits. Never trust client damage, money, target eligibility, or claimed physics outcomes. Batching also requires a per-batch entry cap and a
per-entry validation budget. Use `Stats` replication rates and ping from section 1; use Console Network for data-store/HTTP failures, not a purported RemoteEvent trace.

## 6. UI

Write UI properties when displayed state changes, rather than every frame. A [`ScreenGui`](https://create.roblox.com/docs/reference/engine/classes/ScreenGui) caches appearance
until descendants or properties change. Separate frequently changing UI from static UI when profiling supports it; avoid a ScreenGui per row, but do not merge everything into one
invalidation-heavy root either. [`ResetOnSpawn`](https://create.roblox.com/docs/reference/engine/classes/LayerCollector#ResetOnSpawn) controls respawn recreation. `false` preserves
a ScreenGui that is a direct child of StarterGui; it also preserves its state and subscriptions, so reconnecting on every spawn can duplicate work.

Cache text measurements by text/font/size/width and invalidate when those inputs change.
[`TextService:GetTextBoundsAsync()`](https://create.roblox.com/docs/reference/engine/classes/TextService#GetTextBoundsAsync) takes `GetTextBoundsParams` and can yield while fonts
load; handle failures and do not call it inside render work. [`ViewportFrame`](https://create.roblox.com/docs/reference/engine/classes/ViewportFrame) renders another 3D scene:
measure model/camera animation and instance costs; use static thumbnails or a few reused previews for large lists. Virtualize scrolling lists by keeping visible rows plus a small
margin and recycling them. This trades simpler layout code for bounded instance counts; hiding thousands of existing rows does not remove their memory. Avoid rebuilding
[`UIGradient`](https://create.roblox.com/docs/reference/engine/classes/UIGradient) color/transparency sequences repeatedly; animate offset/rotation when equivalent. In large lists,
compare simpler styling, and avoid tweening text [`UIStroke.Thickness`](https://create.roblox.com/docs/reference/engine/classes/UIStroke#Thickness), which can render/cache many
glyph sizes. Keep changes only when measured UI time improves without readability loss.

## 7. Data stores and startup

Distinguish replicating instances from fetching their mesh/texture/audio content. [`ReplicatedStorage`](https://create.roblox.com/docs/reference/engine/classes/ReplicatedStorage)
contents replicate to clients; keep server-only templates/state in server containers. Streaming does not apply to ReplicatedStorage.
[`ReplicatedFirst`](https://create.roblox.com/docs/reference/engine/classes/ReplicatedFirst) replicates first: keep it small and self-contained for early loading UI, rather than
putting the game's asset library there. Measure time to first interaction and time to required assets, not just time until the loading screen disappears.
[`ContentProvider:PreloadAsync()`](https://create.roblox.com/docs/reference/engine/classes/ContentProvider#PreloadAsync) can prevent first-use pop-in for selected assets but delays
startup if overused. Preload the loading screen, essential UI, and starting-area assets; loading the entire Workspace defeats that purpose. Permit skipping where safe.
`RequestQueueSize` fluctuates and is not a reliable loading progress/completion denominator.

Check [`DataStoreService:GetRequestBudgetForRequestType(requestType)`](https://create.roblox.com/docs/reference/engine/classes/DataStoreService#GetRequestBudgetForRequestType)
before scheduling optional requests. It accepts `Enum.DataStoreRequestType`; a positive budget is not a reservation or proof that a hot key will avoid throttling. Use protected
calls, bounded retries with backoff/jitter, and coalesced/staggered saves. Keep session data in memory rather than fetching it every frame or UI refresh. Respect per-key and
experience/server [data-store limits](https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits). Do not benchmark against production player data. Longer
save intervals reduce traffic but increase the unsaved window; preserve session locking, shutdown handling, and failure recovery rather than silently dropping writes.

## 8. Player side, briefly

A player cannot rewrite someone else's server/scripts. The practical in-game levers are Graphics Quality (lower detail for less GPU work) and [Maximum Frame
Rate](https://devforum.roblox.com/t/introducing-the-maximum-framerate-setting/2995965) where offered (a higher cap permits more frames but cannot create CPU/GPU capacity and can
increase power use). Roblox's [Hyperion anti-tamper](https://devforum.roblox.com/t/roblox-should-start-banning-cheaters-theyre-already-detecting/3040956/9) protects the client: no
injection, DLLs, or memory edits as optimization. Since September 2025, [`ClientAppSettings.json` overrides use Roblox's official
allowlist](https://devforum.roblox.com/t/allowlist-for-local-client-configuration-via-fast-flags/3966569). Non-listed flags are ignored; the list can change without notice. Treat
bulk "FFlag FPS packs" as mostly placebo: unlisted entries do nothing, and any listed change still needs measurement. The announcement exempts Studio.

## 9. Gotchas

| Symptom | Likely cause to verify | Fix / trade-off |
|---|---|---|
| Good average FPS, periodic hitches | One large scan, allocations, replication, or asset fetch | Capture the spike; bound work, reuse scratch space, or preload only the required assets. |
| Every player lags at once | Server script/physics time or replication backlog | Profile the server at fixed population; a client graphics change cannot remove server work. |
| Memory rises after every respawn/menu cycle | Captured instances, duplicated listeners, retained rows | Compare heap/Scene Analysis snapshots; clean ownership and verify growth plateaus. |
| Cached part exists but gameplay stopped updating | Map replacement or client stream-out | Invalidate/rebind references and remove stale registry entries. |
| Native annotation gives no win | API-bound code, compilation limit, breakpoint, unsupported context | Confirm `<native>` and compare function CPU; remove it if costs exceed gains. |
| Parallel version is slower | Tiny jobs, copying, synchronization, serial apply bottleneck | Batch substantial independent work or return to a simpler serial implementation. |
| Physics slows while scripts look cheap | Too many awake mechanisms or excessive solver work | Inspect throttling/physics captures; simplify constraints/collisions and preserve needed accuracy. |
| Lower triangles but no FPS gain | Another bottleneck, overdraw, shadows, or draw calls | Compare CPU/GPU captures; optimize the limiting task rather than the count alone. |
| Long join despite a custom loading screen | Excess replication/preload or blocked initialization | Reduce join content; measure first interaction and missing-dependency waits. |
| Network tab looks quiet but remotes lag | Network tab measures web calls, not replication | Inspect Stats traffic, ping, server step time, and MicroProfiler network captures. |
| Batched effects arrive late or disappear | Giant burst, unreliable loss, or payload limit | Bound/cull batches, include freshness information, and keep critical state reliable. |
| Local test improves but live devices do not | Studio overhead, different quality/cap, or workload | Repeat the same route on target clients and record the actual test conditions. |
