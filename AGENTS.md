# universal-optimizer

A game-optimization toolkit for AI coding agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot, OpenCode and
anything that reads `AGENTS.md`). When someone opens an agent here, they almost always want a game to **run
faster or smoother**, measured: a game they play (PC, emulated, console/mobile/cloud settings) or a game they
develop (its source or scripts, in any engine or language, Roblox included). It is a companion to
[universal-modder](https://github.com/rehan-remade/universal-modder): `uo` depends on it for engine detection,
backups and window control, and code-level fixes use its modding routes.

## Start here
0. **If the user just sent you this repo to install it**, follow `INSTALL.md` and stop there.
1. **Pick the skill:** the user has the game's source or scripts → `skills/optimize-game-code/SKILL.md`;
   otherwise → `skills/optimize-any-game/SKILL.md`. `uo plan <name or folder>` tells you which.
2. **Follow its loop:** intake → recon (`uo plan`) → lab
   (backups) → baseline (`uo bench` twice) → find the bottleneck → change one thing, measure, keep or revert →
   verify → report.
3. **Search prior art first:** `knowledge/notes`, `um kb search "<game>"`, PCGamingWiki, community fixes.
4. **At the end, share what you learned** as a note in `knowledge/notes` (from `knowledge/TEMPLATE.md`),
   and open a PR only once your human agrees.

## Tools
- **`bin/uo`** (Python CLI, sets itself up with `uv`; `bin\uo.cmd` on Windows). Put `bin` on PATH. Every
  group has `--help`:
  - `plan`: engine, graphics APIs, 32-bit/LAA, shipped upscalers, installed wrappers, anti-cheat, emulators,
    CPU → levers; for a source folder, the project kind, languages and code guide; `uo plan roblox` for the
    Roblox client
  - `bench`: frame times via PresentMon (needs an elevated shell), 1%/0.1% lows, stutters, GPU-vs-CPU bound,
    CPU, busiest thread, memory → JSON; `--from-csv` loads PresentMon/CapFrameX/MangoHud captures
  - `compare`: before/after table, changes under 3% marked as noise
  - `proc`: priority and CPU affinity of a running game
- **`bin/um`** runs universal-modder's CLI from the same environment (`um backup`, `um win`, `um kb`, `um scan`).

## Rules (full list in the skill's Hard rules)
- Online games with anti-cheat: in-game settings, official launch options, documented config, driver/OS
  settings only. No wrappers, injection or patched files. Never bypass anti-cheat or DRM.
- Back up every file before changing or adding it (`um backup`), and log the restore path in `OPTLOG.md`.
- One change at a time, measured twice; revert anything that doesn't beat noise.
- No placebo tweaks (RAM cleaners, working-set trimming, registry packs). No hardware tuning unless asked.
- Ask before installing into the game folder, editing the registry/driver profiles, or changing a running
  game's priority/affinity.

## Working on the toolkit itself
- Python 3.10+, deps `psutil` and `universal-modder`. One module per CLI group in `uo/`, each with
  `register(sub)` and a docstring that doubles as `--help`.
- Tests: `uv run --with pytest pytest -q tests`.
- Knowledge notes in `knowledge/notes/*.md` need the frontmatter in `knowledge/TEMPLATE.md` (a test checks it).
- Skills live in `skills/` and are copied to `.agents/skills` and `.claude/skills`; a test fails while the
  copies differ.
- Playbooks follow `skills/optimize-any-game/references/engines/_FORMAT.md`: verified claims with links,
  trade-offs, no placebo.
