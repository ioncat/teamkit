---
name: help
description: Tell the owner what TeamKit can do and when to use each command (init, adopt, update, help), plus the generator's flags and where the quickstart is. Read-only.
disable-model-invocation: true
---

# TeamKit: what can I do here? (read-only)

You change no file and run no command. Answer in the language the owner writes in (the text below is English; translate it). Keep it short: one line per command and one example each, then the flags, then where to read more. Do not add anything else.

## Commands

| Command | Use it when | Example |
|---|---|---|
| `/teamkit:init` | You start a **new project**: an agent (the Product Manager) interviews you, then you get a ready project folder and the list of sessions to open. | Open an empty folder in Claude Code and run `/teamkit:init` |
| `/teamkit:adopt` | You already have a **project in git** and want a team of agents in it. Product first: the Product Manager reads the project and agrees the stage, the goal and the North Star with you (no goal, no adoption), then the CTO checks the technology in the light of that goal; only then are new files added. Nothing that exists is changed; work on a branch you can throw away. | In the project folder, on a clean tree, run `/teamkit:adopt` |
| `/teamkit:update` | A project built from TeamKit should get the **newer TeamKit rules**. It compares versions and lists what must change; it changes nothing. | In the project folder run `/teamkit:update` |
| `/teamkit:help` | You want this list again. | `/teamkit:help` |

## The generator (the same thing without Claude Code)

`python tools/new_project.py --out <folder> [flags]`

| Flag | Meaning |
|---|---|
| `--out <folder>` | The project folder: new (empty or absent); with `--adopt`, the existing project (the root of a git repository). |
| `--adopt` | Existing project: add TeamKit without changing anything that exists (clean git tree needed; only new files; a manifest and an undo). |
| `--answers <file.json>` | Take the answers from a JSON file instead of asking questions. |
| `--dry-run` | Print the plan and write nothing. Use it first, always. |
| `--undo-adopt` | Remove exactly the files a previous `--adopt` created (read from `.teamkit-adopt-manifest.txt`). |

Examples: `python tools/new_project.py --out ../my-app --dry-run` (a new project, plan only); `python tools/new_project.py --out . --adopt --dry-run` (the existing project in this folder, plan only).

## Where to read more

How to install TeamKit (four ways: the plugin from GitHub, the plugin from a local folder, the generator directly, a manual copy; with the update and uninstall commands): the section "Ways to install" in `README.md` and `QUICKSTART.md`. `QUICKSTART.md` in the TeamKit folder: a new project, and the section "Existing project". The rules every agent follows: `docs/team/AGENT_TEAM_RULES.md` in a project built from TeamKit. The version history: `TEAMKIT_CHANGELOG.md`.
