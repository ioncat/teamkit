# Claude Code Guidelines — <<Project name>>

**Project:** <<one-line description>>
**Version:** 1.0 (<<YYYY-MM-DD>>)
**Status:** <<idea / in progress / MVP / production>>
**Kind / stack / depth:** <<kind>> / <<stack>> / <<depth>>

---

## Project overview

**What:** <<one sentence>>
**Why:** <<the problem it solves>>
**Current goal:** <<what the team works toward now>>

## Technology stack

| Layer | Technology |
|---|---|
| Language | <<>> |
| Framework | <<>> |
| Storage | <<>> |
| Tests | <<>> |
| Client / UI | <<>> |

## Project structure

<<Short tree of the main folders (layer 3 of `docs/team/FILE_LAYOUT.md`; layers 1-2 are fixed there). Say which folder belongs to which role; the table is in `docs/delivery/AGENT_RULES.md`.>>

## Rules by kind and depth

<!-- kind:web -->
- Web: a browser smoke plan covers every screen and function before a release.
<!-- /kind -->
<!-- kind:mobile -->
- Mobile: check screen sizes, orientation, keyboard overlap, offline, permissions and themes; the owner confirms visual changes on an emulator or simulator.
<!-- /kind -->
<!-- kind:service -->
- Service: contract tests for every endpoint and a load check before a release.
<!-- /kind -->
<!-- kind:data-ml -->
- Data and ML: runs are reproducible (pinned data versions and seeds); fixtures are synthetic; no personal data in the repository.
<!-- /kind -->
<!-- kind:research -->
- Research: findings are written to `docs/discovery/`; there is no release and no code role.
<!-- /kind -->
<!-- depth:research -->
- Depth Research: find out, do not release; notes only, no review.
<!-- /depth -->
<!-- depth:mvp -->
- Depth MVP: small and fast; only risky changes (data, security, money, outward calls) are reviewed.
<!-- /depth -->
<!-- depth:product -->
- Depth Product: every change is reviewed before a push; the review register and the smoke plan are kept.
<!-- /depth -->

## Team

This project is built by a team of agent sessions under one owner (the human). Read, once at session start:
1. `docs/team/AGENT_TEAM_RULES.md` (common rules),
2. your role brief in `docs/team/roles/`,
3. the project addendum `docs/delivery/AGENT_RULES.md` and `docs/delivery/roles/<your role>.md`.

Work mode (auto or manual) and who pushes: `docs/team/WORK_MODES.md`.

## Session memory (mandatory)

- Session logs: `.claude/sessions/YYYY-MM-DD-short-description.md` (gitignored). On start read the latest; on end write Done, Decisions, Next, Commits.
- Project memory: `.claude/memory/` (gitignored).

## Documentation

Open tasks live in the tracker named in `docs/delivery/AGENT_RULES.md`; delivered work in `docs/delivery/CHANGELOG.md`. Follow `docs/delivery/documentation-conventions.md`.

## Common commands

| Command | Purpose |
|---|---|
| <<test command>> | Run all tests |
| <<run command>> | Start the app |

## Critical rules

<<Project-specific always/never rules. Keep this list short and enforce what you can with tests.>>
- No personal data, secrets or real names in tracked files; fixtures are synthetic.
- Tests grow cumulatively: each chunk adds tests, never removes them.
- A live database is never touched by tests (rule 19).

**Last updated:** <<YYYY-MM-DD>>
