@AGENTS.md

## Claude Code specifics
- Installed as a plugin, the skill is `/universal-optimizer:optimize-any-game` and a SessionStart hook puts
  `uo` and `um` on PATH. In a clone, `.claude/settings.json` adds the same hook and `.claude/skills` is a
  copy of `skills/`.
- Install universal-modder's plugin too for its `reverse-engineering`, `mod-any-game` and
  `share-field-notes` skills, which the code-level tier and the field notes use.
