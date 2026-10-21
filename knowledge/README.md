# Knowledge base

Field notes from optimization runs, written by agents for the next agent. One note per game (or project type)
and technique: what limited it, what moved the numbers, what didn't, and the gotchas. Search before starting:

```bash
grep -ril "<game or engine>" knowledge/notes
```

## Writing a note
1. Copy `TEMPLATE.md` to `notes/<game-or-topic>-<short-title>.md` (lower case, hyphens).
2. Fill the frontmatter. `kind` is `shipped` (a game the user plays), `project` (source the user develops) or
   `platform` (emulator, console, cloud, mobile).
3. Numbers come from `uo compare` (or the engine profiler for projects), same scene, at least two runs per side.
   Include the hardware: a fix that helps a 4-core laptop can do nothing on a desktop.
4. Name what didn't work too. A measured dead end saves the next agent an hour.
5. No game files, decompiled code, private project code, keys, or anything that identifies the user's own
   private projects. Describe techniques, not someone's codebase.
6. `uv run --with pytest pytest -q tests` checks the frontmatter. Open a PR only with the user's OK.
