# TeamKit: a project start kit for a team of Claude Code agents

**New here? Read [`QUICKSTART.md`](QUICKSTART.md) (15 minutes).**

Copy this folder as the root of a new project. It gives you the working rules, the role briefs and the project addenda of a team of agent sessions (product as the entry role, CTO, backend, frontend, mobile, MCP, independent reviewer, web QA) so you can start a full development team in a few steps.

## What is inside

| Path | What it is |
|---|---|
| `CLAUDE.md` | Project instructions with blanks to fill (stack, commands, critical rules) |
| `docs/team/AGENT_TEAM_RULES.md` | Common rules for every agent (reports, talking to the owner, commits, data, safety, quality). Do not edit per project; add to the addendum instead |
| `docs/team/roles/` | One startup brief per role: CTO, backend, frontend, mobile, mcp (optional: agent interface for users' own agents), product, code-reviewer (independent reviewer with lenses), analyst (independent check of business logic: process, flow, requirements), qa (runs the stage and passes an issue's criteria before it reaches the owner's live system), qa-web |
| `docs/team/FILE_LAYOUT.md` | The folder skeleton: fixed paths for every project, fixed names for optional folders, the project's own part decided by its CTO |
| `docs/team/WORK_MODES.md` | Two modes: `auto` (agents work almost alone) and `manual` (the owner works) |
| `docs/team/START_PROMPTS.md` | The one-line start message for each role and the launch order |
| `docs/delivery/AGENT_RULES.md` | The project addendum: fill in tracker, file ownership, project specifics by rule number |
| `docs/delivery/roles/` | Per-role project addenda (short, to fill) |
| `docs/delivery/documentation-conventions.md` | Where tasks, changelog and epics live |
| `docs/delivery/CHANGELOG.md`, `REVIEW_FINDINGS.md` | Empty, with headers |
| `.claude/sessions/` | Session logs (gitignored) |
| `docs/discovery/`, `.scratch/` | Ideas and designs; temporary files per role (gitignored) |

## Use it as a Claude Code plugin (prototype)

Install it once, then start a project from any empty folder:

```bash
claude plugin marketplace add ioncat/teamkit
claude plugin install teamkit@teamkit
```

In Claude Code, open an empty folder and run `/teamkit:init`. Claude acts as the product agent of the new project (the entry role; it calls the CTO for technical matters): it interviews you one question at a time, writes the project files with the generator below, then fills the blanks with you. `/teamkit:update` (read-only for now) tells you what a project built by an older TeamKit needs to catch up. The generator needs Python 3.10 or newer. To try it without installing, run `claude --plugin-dir <this folder>`.

## Generator

`python tools/new_project.py --out <folder>` asks for the kind, stack and depth of the project and builds a folder with only the roles and rules that fit (see `docs/template-design.md` and the quickstart). The steps below are the manual way.

## Start in six steps

1. Copy the folder, `git init`, fill the blanks marked `<<...>>` (search for `<<`).
2. Decide the tracker (an issue board such as Linear, or a `docs/delivery/BACKLOG.md`) and write it into `docs/delivery/AGENT_RULES.md`, row 20.
3. Fill `CLAUDE.md` (stack, commands, critical rules, no-personal-data rule if the repo is public).
4. Fill the file ownership table in `docs/delivery/AGENT_RULES.md`: which role owns which folders.
5. Open the Product session first and give it its start message from `docs/team/START_PROMPTS.md`: it is the entry role, you talk to it. When a question has a technical part it calls the CTO, which reads the rules, creates the tracker labels and decides which sessions to open.
6. Open the other sessions one by one (each with its start message). The CTO cannot create full sessions itself unless it has a `start_session` tool; you open them, it manages them.

## Roles you can drop

Not every project needs every role. A project without a UI drops frontend and qa-web; a project that pushes messages, spends tokens or writes live data adds a stage and the qa role (rule 31); a small one can start with CTO, backend and reviewer. Add a role by copying `roles/backend.md`, changing the "who you are" and the first action, and adding a row to the ownership table.

## Hygiene

No personal data, secrets or real names in tracked files. Fixtures are synthetic. Add a guard test in the first week (`tests/test_no_personal_data.py` in your own style).

## Sources

The documents TeamKit is built on (methodology, standards, Claude Code practice), with what each one gave: [`docs/SOURCES.md`](docs/SOURCES.md).
