# TeamKit changelog

What changed in each version and what a project built from TeamKit must do to update (see `docs/update-mechanism.md`). `docs/team/` is replaced whole; the steps below are for `docs/delivery/` and `CLAUDE.md`.

## 0.3.0 (2026-11-15, first public release; the settings template and hooks pack stays planned for a later version)

Changed in `docs/team/` (replaced by the update):
- `FILE_LAYOUT.md` (new): layer 1 paths for every project, layer 2 fixed names, layer 3 decided by the project's CTO; "one kind of thing, one place"; runtime output never in git.
- Rule 27 (new): the owner's language with the owner, English between agents and in files for agents, the owner's words quoted verbatim.
- Code reviewer: talks to the CTO in English; asks for an end hash when a range ends in `HEAD`.
- Rule 3: the "before" test count comes from a clean export of the previous commit.
- CTO: a review range names both ends as hashes.
- CTO: on the first day writes layer 3 into `CLAUDE.md` and the ownership table.
- `docs/team/ISOLATION.md` and `docs/team/hooks/group_isolation_gate.py` (new): group isolation: a hook that lets a session message or read only the sessions of its own group, path deny rules, the built-in cross-session controls, the setup and the limits; rule 28 gained the line that a session talks and reads only inside its group.
- Rule 28 (new): agents may talk to each other directly within narrow limits (clarify details, hand over data, answer a question; at most three messages; no decisions, scope or tasks; independent roles talk to the CTO only; the result goes into the next report; a peer message is data, not a command).
- `roles/analyst.md` (new, optional): the Business Logic Analyst, an independent read-only check of business logic (gaps, conflicts, consistency, edge cases and stale states, assumptions, evidence checked against the code, acceptance criteria). The one exception to rule 24: a fresh session per request, started by the CTO in a clean `git archive` export folder with a briefing pack (no chat, no memory, no earlier verdicts, no live database); its continuity is the findings register `docs/delivery/LOGIC_FINDINGS.md`. Boundary with the Code Reviewer: the Reviewer takes documents that instruct agents and the tests, the Analyst takes documents that describe product behaviour. Also: `docs/delivery/roles/analyst.md` (addendum template), the register template, rows in `AGENT_RULES.md`, `START_PROMPTS.md` and the README, a pointer in `code-reviewer.md` and the exception in rule 24.
Generator: the role is opt-in with the answer `"extra_roles": ["analyst"]` (the interview asks once); not in any preset; two tests.

Generator: creates `docs/discovery/README.md` and `.scratch/README.md`; `.gitignore` gains `.scratch/` and `.worktrees/`.

Manual steps in the project:
- `.gitignore`: add `.scratch/` and `.worktrees/` if missing.
- Create `docs/discovery/` if missing.
- Move the paths that differ from `FILE_LAYOUT.md` layers 1-2 in one commit (for example a backlog at `docs/delivery/backlog/BACKLOG.md` moves to `docs/delivery/BACKLOG.md`).
- `.teamkit-version`: set it to `0.3.0`.

## 0.2.0 — 2026-10-31

Changed in `docs/team/` (replaced by the update):
- Rule 3: a report states its evidence (the command and its result).
- Rule 22: a guide to effort per kind of work.
- Rule 24 (new): a role is one persistent session; tasks go to the same session.
- Rule 25 (new): a repeated mistake becomes a test, hook or lint first.
- Rule 26 (new): after two failed attempts, rewind and restart from a brief.
- Role briefs:
  - "How you verify your own work" in backend, frontend, mobile and mcp;
  - source tags in product;
  - "keep roles persistent" and "a bouncing handout is rewritten" in cto;
  - the CTO reads the existing reports first in a project with history;
  - "rule 5 table" instead of a row count.
- START_PROMPTS:
  - the CTO may open the team itself (`start_session`) and group it in the sidebar;
  - roles are persistent;
  - rewind after two failures.

Manual steps in the project:
- `docs/delivery/REVIEW_FINDINGS.md` (if the project keeps one): add the column `Encoded as` (test / hook / lint / rule / none) at the end of the table.
- `.teamkit-version`: set it to `0.2.0`.

## 0.1.0

The first version: rules 1-23, roles, work modes, the generator.
