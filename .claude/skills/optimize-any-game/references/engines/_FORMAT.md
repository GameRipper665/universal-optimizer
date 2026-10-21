# Playbook format (for contributors adding or updating a playbook)

Every engine playbook in this folder follows the same shape, so an agent can skim any of them the same way:

```
# <Engine>

**Identify.** files that prove the engine, where config/logs live.

**Where the time usually goes.** the 3-6 bottlenecks this engine is known for (CPU main thread, GC, shader
compile stutter, draw calls, streaming...), and how to confirm each one with a measurement.

## Tier 1: config and launch options (no files added)
Exact file paths, keys/cvars/flags, what each does, the trade-off, and which versions it applies to.

## Tier 2: drop-in community fixes and runtime swaps
Named projects (link), what they fix, how to install, how to remove.

## Tier 3: code-level patches (profile -> patch the hot path)
The profiler that sees inside this engine, the patching route (Harmony, Mixin, UE4SS, native hook...),
and 2-3 patterns that have actually paid off.

## Gotchas
symptom -> cause -> fix.
```

Rules:
- Only write settings, cvars, flags and file paths you verified (official docs, the project's README/source,
  a well-known community guide). Link the source next to the claim. If you could not verify something, leave it
  out or mark it `(unverified)`.
- Say the trade-off of every knob (visual loss, stability risk, more VRAM). No placebo: memory "cleaners",
  "RAM boosters", registry folklore and `EmptyWorkingSet` tricks are called out as useless where relevant.
- Never anything that touches anti-cheat, online clients or DRM. Single-player/offline or servers the user hosts.
- Agent-neutral wording ("the agent"), short sentences, no marketing.
