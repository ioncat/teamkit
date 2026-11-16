# File layout

The skeleton every TeamKit project shares. Layer 1 is the same everywhere. Layer 2 gives fixed names to folders a project may need. Layer 3 is the project's own; its CTO decides it and writes it down.

Two rules hold over all layers:
1. **One kind of thing, one place.** The backlog, the changelog, a role's scratch files each live at the path below and nowhere else. A second copy or a second place is a defect.
2. **What a running program creates never goes into git.** Runtime data, generated output, logs and local databases are gitignored. A project with such folders adds a guard test that fails when one of them is tracked.

## Layer 1: every project, same paths

| Path | Holds | In git |
|---|---|---|
| `CLAUDE.md` | the project's main guidelines | yes, unless the project decides otherwise (then say so in `README.md`) |
| `README.md` | what the project is, how to start | yes |
| `.teamkit-version` | the TeamKit version the project was built from or last updated to | yes |
| `docs/team/` | TeamKit rules and role briefs; never edited in a project, replaced whole on update | yes |
| `docs/delivery/` | `AGENT_RULES.md`, `roles/`, `CHANGELOG.md`; `BACKLOG.md` when the tracker is a file; `Epics/` at depth product; `REVIEW_FINDINGS.md` when kept | yes |
| `docs/discovery/` | ideas and designs not yet committed to | yes |
| `.claude/sessions/` | session logs (rule 18) | no |
| `.claude/memory/` | project memory | no |
| `.claude/work_mode` | `auto` or `manual` | no |
| `.scratch/<role>/` | temporary files of each role: drafts, reports, run logs, one-off scripts | no |
| `.worktrees/` | git worktrees of agents | no |
| `db/stage*` | the stage's copy of the database (made from the live one, which is opened read-only); only in a project with a stage | no |
| `logs/stage_outbound.log` | what the stage would have sent or spent (its outward channels write here) | no |
| `.env.stage` | the stage's settings; carries no secret | no |
| `docs/delivery/STAGE.md` | how to start and stop the stage, refresh the snapshot, add a fixture | yes |
| `docs/delivery/qa/` | QA scenario files, one per feature | yes |

## Layer 2: fixed names, used when needed

The CTO decides whether a project needs one of these. When it does, it uses this name.

| Path | Holds | In git |
|---|---|---|
| `docs/project/` | reference: architecture, API, history, former guidelines | yes |
| `docs/knowledge/` | knowledge taken from outside sources, one folder per source | yes |
| `research/` | the owner's own research, not product work | project decides |
| `data/` | data the running program creates or reads at run time | no |
| `tests/` | tests | yes |
| `scripts/` | service scripts (maintenance, one-off migrations kept for history) | yes |

## Layer 3: the project's own

The code layout for the stack and any special folders (for example `sources/` with site profiles in a scraper). The CTO writes it in two places on the first day and keeps them current:
- the "Project structure" tree in `CLAUDE.md`;
- the file ownership table in `docs/delivery/AGENT_RULES.md`.

A layer 3 folder never reuses a layer 1 or layer 2 name for something else.

## Existing projects

A project that predates this file is not reshuffled at once. Each TeamKit update lists the paths that differ (`TEAMKIT_CHANGELOG.md`, "Manual steps"); the CTO moves them in one commit, with the owner's word when the move touches runtime data.
