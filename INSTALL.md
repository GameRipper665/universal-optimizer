# Installing universal-optimizer (instructions for AI agents)

**You are an AI coding agent and the user sent you this repository so you'd install it for yourself.** Do the
steps below from start to finish without asking about each one, except where it says *ask*. When you're done,
tell the user what you installed, where, and how to undo it.

Repository: `https://github.com/GameRipper665/universal-optimizer` (call it `REPO` below).

## 1. Prerequisites
- **git.** Required. If it's missing, stop and tell the user how to install it for their OS.
- **uv** ([docs.astral.sh/uv](https://docs.astral.sh/uv/)). It installs the `uo` CLI and its Python. If it's
  missing, install it with the official installer and tell the user you did:
  - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

  Then open a new shell, or add uv's bin folder to PATH for this session, so `uv` resolves.

## 2. Install the `uo` CLI (and `um`, which it depends on)
```bash
uv tool install --force --with-executables-from universal-modder "git+REPO"
```
This puts `uo` (this toolkit) and `um` ([universal-modder](https://github.com/rehan-remade/universal-modder),
for backups, window control and engine scans) on PATH. If uv warns that its tool bin folder isn't on PATH, run
`uv tool update-shell` and tell the user to open a new terminal. Check it with `uo --help`.

## 3. Register the skills with yourself
Find the section for the agent you are. If several apply, do the first one that matches.

**Claude Code**
```bash
claude plugin marketplace add GameRipper665/universal-optimizer
claude plugin install universal-optimizer@universal-optimizer
claude plugin marketplace add rehan-remade/universal-modder
claude plugin install universal-modder@universal-modder
```
universal-modder is the companion that the code-level tier uses (reverse-engineering and modding routes). Tell
the user to restart Claude Code so the skills load.

**Grok Build.** Grok reads Claude Code plugins, so if Claude Code is installed too, do the Claude Code steps.
Otherwise clone the repo as a Grok plugin:
```bash
git clone REPO ~/.grok/plugins/universal-optimizer
```
Then tell the user to open `/plugins` and enable it if it isn't already, and to check with `/skills` that
`optimize-any-game` and `optimize-game-code` are listed. For one session only, Grok can also load it with
`--plugin-dir <path to a clone>`.

**Antigravity (Google)**
```bash
agy plugin install REPO
```
This installs the skills (the repo root has the `plugin.json` Antigravity expects). If `agy` isn't available
(IDE or App only), copy `skills/optimize-any-game` and `skills/optimize-game-code` from a clone into
`~/.gemini/config/skills/` instead.

**Codex**
```bash
codex plugin marketplace add GameRipper665/universal-optimizer
codex plugin add universal-optimizer@universal-optimizer
```

**Cursor, GitHub Copilot, OpenCode, or any other agent.** Clone the repo to `~/.universal-optimizer/repo` (or
`git -C ~/.universal-optimizer/repo pull` if it's already there). Then copy `skills/optimize-any-game` and
`skills/optimize-game-code` into the folder your agent loads skills from:
- your agent's documented user-level skills folder (look it up rather than guessing);
- `~/.agents/skills/`: a shared user-level folder that Grok Build and several other Agent Skills readers scan;
- `~/.claude/skills/`: Claude Code.

If your agent has no skills support, tell the user to open their agent inside the clone instead: the repo's
`AGENTS.md` (and `CLAUDE.md`) gives any agent the same instructions.

## 4. Frame-time capture (Windows, optional; *ask* first)
`uo bench` needs Intel's PresentMon console app for frame times. Ask the user if they want it. If yes, download
the console exe from the latest release (the asset named `PresentMon-<version>-x64.exe`, not the `.msi`) into
`~/.universal-optimizer/tools/`. `uo` looks there automatically.
```bash
gh release download --repo GameTechDev/PresentMon --pattern "PresentMon-*-x64.exe" --dir ~/.universal-optimizer/tools
```
Without `gh`, take the asset URL from `https://api.github.com/repos/GameTechDev/PresentMon/releases/latest`.
Tell the user that capturing needs an elevated (administrator) terminal. On Linux/Steam Deck, MangoHud does the
same job (see `uo bench --help`).

## 5. Verify, then report
- `uo --help`, `uo plan --help` and `um --help` all work.
- The two skills are visible to you (`/skills`, a plugin list, or the files in your skills folder).
- Report in a few lines: what was installed (the uv tool, the plugin or skills and where they live, PresentMon
  if chosen), whether a restart is needed, and how to try it, e.g. *"My game stutters, find out why"* or
  *"Profile my Roblox scripts"*.
- Uninstall: `uv tool uninstall universal-optimizer`, then remove the plugin with the agent's own plugin
  manager, or delete the copied skill folders and `~/.universal-optimizer`.

## Rules while installing
- Don't install anything into game folders, edit the registry, change drivers, or run anything as administrator
  during installation. Those changes happen later, per game, only with the user's OK.
- Don't change or remove other plugins, skills or MCP servers the user already has.
- If a step fails, say which one and why. Don't report success for a step that didn't run.
