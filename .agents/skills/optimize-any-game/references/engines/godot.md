# Godot (3 / 4)

**Identify.** Look for an adjacent `.pck` or a pack embedded in the executable.
Confirm the Godot version from the engine startup header or the pack inspection, rather than guessing from
the art style. The companion [Godot routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/godot.md)
cover identification, GDRE, and loader choices. C# builds need a separate managed-code investigation;
GDScript changes do not optimize arbitrary C# hot paths.

On Windows, the default `user://` directory is `%APPDATA%\Godot\app_userdata\<ProjectName>\`.
With `application/config/use_custom_user_dir`, it can instead be `%APPDATA%\<ProjectName>\` or
`%APPDATA%\<custom_user_dir_name>\`. See the [data-path reference](https://docs.godotengine.org/en/4.3/tutorials/io/data_paths.html).
Do not confuse this save/user-data location with the executable directory used for the ordinary override file.
For a standard export, the default file log is `user://logs/godot.log`, configurable through
[`debug/file_logging/log_path`](https://docs.godotengine.org/en/4.4/classes/class_projectsettings.html#class-projectsettings-property-debug-file-logging-log-path).

Only optimize owned offline/single-player games or explicitly supported user-hosted servers.
Do not touch online clients, anti-cheat, DRM, or encrypted/protected assets.
Record the game build, engine version, renderer, save/scene, and benchmark route before changes.

**Where the time usually goes.** Confirm each suspected cause:

- GDScript/main-thread work: compare function self time, total time, and call counts in a compatible debug
  session or recovered project. [Godot profiler](https://docs.godotengine.org/en/4.3/tutorials/scripting/debug/the_profiler.html).
- Physics: compare physics time with script time and collision/object counts. Many physics callbacks or
  catch-up steps can hurt even when graphics settings make little difference.
  [Engine timing controls](https://docs.godotengine.org/en/4.3/classes/class_engine.html).
- GPU work: lower resolution or effects for a diagnostic run and observe frame times.
  A heavy 3D renderer is not necessarily the bottleneck in a 2D simulation.
  [General optimization guidance](https://docs.godotengine.org/en/4.3/tutorials/performance/general_optimization.html).
- Resource/pipeline loading: compare first visits with warm revisits and record disk activity.
  Caches can change repeated-run performance; separate loading hitches from persistent CPU work.
- Node/resource churn: inspect recurring creation, searches, and retained objects. A repeated scene-tree
  search or unbounded cache is a code issue; an FPS cap does not remove it.
  [CPU optimization guidance](https://docs.godotengine.org/en/4.3/tutorials/performance/cpu_optimization.html).

Use [PresentMon](https://github.com/GameTechDev/PresentMon) for external Windows frame durations when the
shipped build lacks internal instrumentation. It does not identify a specific GDScript function.
Keep first-launch and warmed-up measurements separate and remove profiling overhead for final runs.

## Tier 1: config and launch options (no files added)

Use launch arguments or edit an existing `override.cfg` here. If none exists, the small config-only addition
is described in Tier 2. Preserve its original contents and launch arguments for exact rollback.
Change one control at a time and restart for startup settings.

### override.cfg behavior in shipped exports

Godot 3.5 and 4.3 document `override.cfg` beside the exported project binary, in project-settings format:
[3.5 ProjectSettings](https://docs.godotengine.org/en/3.5/classes/class_projectsettings.html),
[4.3 ProjectSettings](https://docs.godotengine.org/en/4.3/classes/class_projectsettings.html).
This works with a standard shipped export; a recovered editable project is not required.

The [4.3 source](https://github.com/godotengine/godot/blob/4.3/core/config/project_settings.cpp)
loads project settings from the pack, then override files. With an explicitly selected main pack it checks
that pack's directory; with an automatically discovered pack it checks the executable directory as well
as `res://override.cfg`. Do not assume the current working directory is the location.
Feature-tagged settings can outrank an untagged override; mirror the relevant platform feature tag.
Game code can also change the effective runtime property after startup.

The [4.6 settings reference](https://docs.godotengine.org/en/4.6/classes/class_projectsettings.html#class-projectsettings-property-application-config-disable-project-settings-override)
documents `application/config/disable_project_settings_override`, which can disable override loading and
related CLI controls. This is a version-specific restriction, not a reason to promise every Godot 3/4
binary accepts arbitrary external settings. Do not bypass a developer-disabled override path.

### Renderer selection: use the export's available drivers

Check the actual executable's `--help`; custom exports may omit drivers. The
[4.3 CLI reference](https://docs.godotengine.org/en/4.3/tutorials/editor/command_line_tutorial.html)
marks `--rendering-driver` and `--rendering-method` as available in release export templates.
Unknown arguments can silently do nothing, so verify the startup header after a change.

- `--rendering-driver vulkan`: a Godot 4 RenderingDevice backend when compiled in.
- `--rendering-driver d3d12`: a Windows backend documented in
  [Godot 4.3](https://docs.godotengine.org/en/4.3/classes/class_projectsettings.html#class-projectsettings-property-rendering-rendering-device-driver-windows).
  Do not prescribe it to every 4.0–4.2 export. Compare driver stability and frame pacing rather than
  assuming one API is faster. A startup flag cannot supply an omitted driver.
- `--rendering-driver opengl3`: pairs with Compatibility; it is not another driver for Forward+.
- `--rendering-method forward_plus`: the richer Godot 4 renderer, with a higher feature/cost envelope.
- `--rendering-method mobile`: a simpler RenderingDevice renderer. Some Forward+ features are unavailable.
- `--rendering-method gl_compatibility`: the OpenGL Compatibility renderer. It can help older hardware but
  changes feature availability and may break effects/material assumptions.
  Names and constraints: [rendering methods/drivers](https://docs.godotengine.org/en/4.4/classes/class_projectsettings.html#class-projectsettings-property-rendering-renderer-rendering-method).

Example Compatibility experiment, only if the exported binary lists support:

```text
Game.exe --rendering-method gl_compatibility --rendering-driver opengl3
```

For Godot 3.5 the corresponding family is `--video-driver GLES2` or `--video-driver GLES3`, not the 4.x
flags above. See the [3.5 CLI reference](https://docs.godotengine.org/en/3.5/tutorials/editor/command_line_tutorial.html).
GLES2 can lose rendering features; compare image correctness as well as performance.
Do not replace the game's engine executable just to gain a driver from another version.

### Physics, VSync, and FPS keys

Use these **versioned names**, not an interchangeable 3/4 config snippet:

| Purpose | Godot 3.5 key | Godot 4.3 key |
| --- | --- | --- |
| Physics rate | `physics/common/physics_fps` | `physics/common/physics_ticks_per_second` |
| Render FPS cap | `debug/settings/fps/force_fps` | `application/run/max_fps` |
| Main-window VSync | `display/window/vsync/use_vsync` | `display/window/vsync/vsync_mode` |

Sources: [3.5 startup implementation](https://github.com/godotengine/godot/blob/3.5/main/main.cpp),
[3.5 settings](https://docs.godotengine.org/en/3.5/classes/class_projectsettings.html),
[4.3 settings](https://docs.godotengine.org/en/4.3/classes/class_projectsettings.html).
Godot 3's `force_fps` name is a render cap here, not offline fixed-time video capture.
For these caps, `0` means unlimited by that cap; VSync or game code can still limit rendering.
Choose a sustainable cap to reduce CPU/GPU load at the expense of maximum FPS and update latency.

Godot 3 uses a VSync boolean. Godot 4 uses the DisplayServer enum: `0` disabled, `1` enabled,
`2` adaptive, `3` mailbox. Support/fallback differs by driver; adaptive/mailbox are not universal upgrades.
VSync avoids tearing but changes presentation latency; disabling it can increase load and tearing.
See [VSyncMode](https://docs.godotengine.org/en/4.3/classes/class_displayserver.html#enum-displayserver-vsyncmode).

Physics defaults to 60 ticks per second in the cited versions. Reducing it may lower CPU cost but changes
collision accuracy, callbacks, damping, controls, and gameplay feel. It is not a graphics-only tweak.
Do not lower it unless the user accepts a simulation change and the game's behavior has been tested.
Godot 4's `physics/common/max_physics_steps_per_frame` limits catch-up work; reducing it can make
simulation fall behind real time. See
[Engine timing/physics documentation](https://docs.godotengine.org/en/4.3/classes/class_engine.html).
Prefer optimizing measured collision/script work before altering simulation timing.

### Threading settings are not automatic script parallelism

Godot 3.5 uses `rendering/threads/thread_model`; Godot 4.3 uses
`rendering/driver/threads/thread_model`. Both references show default `1`.
The [3.5 reference](https://docs.godotengine.org/en/3.5/classes/class_projectsettings.html#class-projectsettings-property-rendering-threads-thread-model)
warns rendering-thread synchronization can increase jitter. The
[4.3 reference](https://docs.godotengine.org/en/4.3/classes/class_projectsettings.html#class-projectsettings-property-rendering-driver-threads-thread-model)
labels its threading setting experimental with known crashes around particles/window resizing.
Keep defaults unless a game-specific tested change exists; do not blindly force a separate render thread.

Godot 4.3 exposes `physics/2d/run_on_separate_thread` and `physics/3d/run_on_separate_thread`.
They change physics-server scheduling, not the thread safety of arbitrary scene-tree access.
Concurrent work can add synchronization costs or expose unsafe assumptions; keep defaults without evidence.
Follow [thread-safe APIs](https://docs.godotengine.org/en/4.3/tutorials/performance/thread_safe_apis.html),
which warns that scene-tree operations are not generally safe from worker threads.

## Tier 2: drop-in community fixes and runtime swaps

There is no engine-wide Godot performance DLL to install as a default step.
Use the game's maintained mod ecosystem and the companion
[Godot Mod Loader/PCK routes](https://github.com/rehan-remade/universal-modder/blob/main/skills/mod-any-game/references/engines/godot.md).
A loader adds access; it does not speed up the game by itself.

If the ordinary export accepts external overrides and no file exists, create only the needed settings.
For example, this **Godot 4 cap experiment** adds `override.cfg` beside the executable:

```ini
[application]
run/max_fps=60
```

The section plus key reconstructs `application/run/max_fps`; the value caps rendering at 60, trading peak
FPS for lower load. Delete this newly created file to revert; restore an existing file instead of deleting it.
See [ProjectSettings override syntax](https://docs.godotengine.org/en/4.3/classes/class_projectsettings.html).
If startup/runtime readback does not confirm the setting, remove it instead of accumulating more overrides.

For a game-specific performance pack, verify engine minor version, mod-loader version, changed resource
paths, and the original project's stated behavior. Install/remove it through the same loader.
Keep a copied save and added-file manifest. Avoid whole-game repacks or replacement executables.
Do not silently remove visual assets or change physics while describing the result as equivalent behavior.

## Tier 3: code-level patches (profile -> patch the hot path)

### Profiling a shipped game

The [Godot profiler](https://docs.godotengine.org/en/4.3/tutorials/scripting/debug/the_profiler.html)
shows frame/physics/script timings and per-function cost. Start it only for diagnosis; collection adds overhead.
In a compatible debug export or recovered project, compare function self time with inclusive time and call count.
An Editor measurement is a guide to the hot path; confirm the result in the actual export.

The [4.3 CLI documentation](https://docs.godotengine.org/en/4.3/tutorials/editor/command_line_tutorial.html)
lists `--profiling` and `--remote-debug <uri>` even for release templates.
That does not guarantee full script instrumentation: the
[4.3 GDScript profiler implementation](https://github.com/godotengine/godot/blob/4.3/modules/gdscript/gdscript.cpp)
guards profiling work with `DEBUG_ENABLED`. A normal release export can accept the flag without producing
the function data needed. Use an authorized compatible debug/recovered project or narrow custom timings.
Connect a debugger only to a local session under the user's control; do not expose a debug listener publicly.

Use external frame times and OS CPU/I/O sampling if internal profiling is unavailable.
Native stack detail depends on symbols. A frame-time spike alone cannot distinguish script work, GPU work,
and resource loading; compare the same trigger with the suspected behavior isolated.

### Recover, patch, overlay

[GDRE Tools](https://github.com/GDRETools/gdsdecomp) can inspect/recover supported PCKs or embedded exports,
decompile GDScript, and recover project resources. Use it only on unprotected owned content.
Follow the companion's recovery and PCK-overlay route; do not repeat loader setup here.
Match the original engine/resource format and inspect the recovered scene/script relationships.

Godot supports later resource packs replacing earlier resources at matching `res://` paths, through
`ProjectSettings.load_resource_pack(...)`. See
[packs, patches, and mods](https://docs.godotengine.org/en/4.3/tutorials/export/exporting_pcks.html).
An extra `.pck` beside the game is **not automatically loaded**. The existing loader or an authorized
bootstrap must mount it before the affected resources/scripts are first loaded.
Replacing an already-instantiated script does not automatically migrate its objects or reset cached resources.
Package only the changed resources and minimal bootstrap; do not redistribute the recovered game.
Remove the overlay and restore bootstrap settings to roll back.

### Patch patterns

1. **Cache stable node lookups.** Replace repeated per-frame `get_node()` traversals with an `@onready`
   reference in Godot 4, or `onready` in Godot 3. Rebind after the relevant node/scene is replaced;
   release references and disconnect signals on teardown.
   Godot's [style guide](https://docs.godotengine.org/en/4.3/tutorials/scripting/gdscript/gdscript_styleguide.html)
   explicitly uses onready variables for caching dependencies.
2. **Use types in the measured loop.** In modern Godot 4, known operand/argument types permit optimized
   opcodes; see [typed GDScript](https://docs.godotengine.org/en/4.4/tutorials/scripting/gdscript/static_typing.html).
   Preserve nullability and dynamic interfaces rather than adding incorrect casts.
   Godot 3.5's [typing guide](https://docs.godotengine.org/en/3.5/tutorials/scripting/gdscript/static_typing.html)
   describes performance optimization as future work. Do not promise a 3.x speedup merely by adding types.
3. **Stop redundant work.** Update a cosmetic label when its value changes, reuse bounded temporary arrays,
   or disable an unnecessary processing callback while the object is inactive.
   Preserve physics/input/gameplay events and restore behavior when reactivated.
   These are profile-driven applications of [Godot's CPU optimization guidance](https://docs.godotengine.org/en/4.3/tutorials/performance/cpu_optimization.html),
   not proof that every loop or allocation is expensive.

Measure the changed method and exported frame times. Test scene reloads, resource lifetime, and a long run.
Keep each patch individually removable; caches must not retain old scenes or grow without bounds.

## Gotchas

- Override has no effect -> wrong directory, feature-tag precedence, runtime reassignment, or disabled
  override loading -> verify the effective property and restore the file; do not bypass restrictions.
- Renderer switch starts but effects disappear -> feature mismatch -> restore the original method/driver.
- Higher render FPS but slower/incorrect simulation -> physics rate/catch-up was changed -> restore timing.
- Blank script profile from release -> instrumentation compiled out -> use compatible debug instrumentation;
  adding another CLI flag cannot restore code absent from the binary.
- Overlay changes nothing -> never mounted, wrong resource path, or resources loaded too early -> inspect
  the loader's mount order and exact exported paths before changing more scripts.
- RAM cleaner lowers reported residency -> it does not remove script/physics work -> remove it.
  [`EmptyWorkingSet`](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-emptyworkingset)
  trims pages, not game allocations. Memory boosters and registry folklore are not engine optimizations.
