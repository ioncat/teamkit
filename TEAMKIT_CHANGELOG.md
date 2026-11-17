# TeamKit changelog

What changed in each version and what a project built from TeamKit must do to update (see `docs/update-mechanism.md`). `docs/team/` is replaced whole; the steps below are for `docs/delivery/` and `CLAUDE.md`.

## 0.4.3 (2026-11-17, no irreversible action without a backup)

Changed in `docs/team/` (replaced by the update):
- `AGENT_TEAM_RULES.md`: rule 32 added (placed after rule 10): before anything that cannot be undone (deleting or overwriting files, a database write or migration, `git reset --hard` / `checkout --` / `clean` / `rebase`, clearing a folder) a dated copy is made first and its path named in the report; when a copy is impossible (an outward send, a push), the action waits for the owner's word. Rule 10 is one case of it.

Steps for a project: none.

## 0.4.2 (2026-11-16, the Business Analyst writes the tasks)

Changed in `docs/team/` (replaced by the update):
- `roles/analyst.md` is now the **Business Analyst**: discovery of each request (restate it, read what exists read-only, find the edges, keep facts, assumptions and open questions apart, a short discovery note when the request is larger than a few lines) and the issue in the tracker (Origin, Value, user story, Given / When / Then criteria, edge cases, out of scope, dependencies). A persistent session, in every team.
- The separate optional logic-check role is gone (it was the old optional `analyst.md`): its work is a new **"logic and flows" lens of the Reviewer** (`roles/code-reviewer.md`): documents that say how the product behaves (flows, epics, requirements, acceptance criteria) are checked in a fresh Reviewer session in a clean export; its findings go to `REVIEW_FINDINGS.md` (the separate `LOGIC_FINDINGS.md` template is removed).
- `AGENT_TEAM_RULES.md` rule 20: one writer per kind of tracker change (the Analyst creates issues and writes their description; the CTO adds the technical part, labels, states, assigns and closes; the owner's edits win). Rules 21, 24 and 28: the logic check is the Reviewer's lens; rule 24's one exception is a fresh Reviewer session for that lens.
- `roles/cto.md`: no longer writes issues; reads the Analyst's issue, adds the technical part, assigns and starts the agent; routes findings that need work to the Analyst. `roles/product.md`: the Analyst writes the acceptance criteria; the Product Manager gives the meaning, decides and approves them. `roles/qa.md`, `roles/qa-web.md`, `roles/code-reviewer.md` follow the new names.
- `START_PROMPTS.md`: launch order Product Manager, Business Analyst, CTO, then the delivery roles; a Business Analyst row; QA in the launch order. The Product Manager opens the two planning roles (Business Analyst, CTO); the CTO opens the delivery roles (rule 29).
- One route for issues: the Business Analyst is the only agent that creates issues; the CTO never files one, not even a one-line fix (it sends the Analyst one line); Reviewer and QA findings that need work go to the CTO, who passes them to the Analyst (`cto.md`, `code-reviewer.md`, `qa.md`, `REVIEW_FINDINGS.md`).
- Rule 21: executor labels, `reviewed`, and the QA verdict recorded on the issue in a project with a stage; `cto.md` accepts results only with the QA verdict when rule 31 applies.
- Rule 31 applies in a project that has a stage. Generator: QA comes only with a stage (depth product asks with default yes; a research project never has one); `STAGE.md` is generated whenever QA is; TeamKit's own working notes are never copied into a project.
- `roles/product.md`: the Product Manager's core job is written at the top: for every product and request, what problem we solve, for whom (the user), what value the user gets; priorities and acceptance checks are tested against these three. Rule 30 and `product.md` no longer name a status page.
- Role names are written with capitals everywhere (Product Manager, Business Analyst, CTO, Backend, Frontend, Mobile, MCP, QA, Web QA, Reviewer, Delivery Team). README: "builds on ideas from GitHub Spec Kit"; the stage and review principles say when they apply. QUICKSTART (both languages): open the Product Manager first, the stage question and the `stage` key, the minimal team and the launch order.

A project built from an earlier version does this to update (see `docs/update-mechanism.md`):
1. Replace `docs/team/` whole. Add `docs/delivery/roles/analyst.md` (Business Analyst) from the template. If the project had the old optional Analyst (the logic check), delete its addendum, move the rows of its `LOGIC_FINDINGS.md` into `REVIEW_FINDINGS.md` with the lens "Logic and flows", and drop its row from `AGENT_RULES.md` and `START_PROMPTS.md`.
2. In `docs/delivery/AGENT_RULES.md`: a Business Analyst row in the ownership table (the issues, discovery notes); row 20 rewritten (among agents the Business Analyst creates the issues, the CTO adds the technical part, labels, states, assignment and closing; no other agent writes there); in `documentation-conventions.md` the tracker line (who writes what).
3. Open the Business Analyst session with its line from `START_PROMPTS.md`. An existing project may keep the CTO writing issues if the owner decides so; write that in the project addendum.

Changed in the tools: `tools/new_project.py` puts `analyst` (Business Analyst) in every preset, research included; there are no optional roles now, and an answers file with `extra_roles: ["analyst"]` or `["logic-checker"]` from an earlier version is accepted and dropped with a note. `README.md` rewritten short (what it is, why a team, the roles, the flow, five principles, how to start).

## 0.4.1 (2026-11-16, the stage and the QA role)

Changed in `docs/team/` (replaced by the update):
- `roles/qa.md` (new): the QA agent runs the project's stage and passes an issue's acceptance criteria at three levels (backend by HTTP, the app without a window, the app with a window); verdicts PASS, FAIL, PASS-without-window with evidence; windowed runs are announced and need the owner's ok, queued when he cannot. `roles/qa-web.md` stays as the browser-interface specialisation.
- `AGENT_TEAM_RULES.md`: rule 31 appended (a change with a visible, outward, token, setting or migration effect runs on the stage and passes QA before it reaches the owner's live system).
- `FILE_LAYOUT.md`: stage items (`db/stage*`, `logs/stage_outbound.log`, `.env.stage`, `docs/delivery/STAGE.md`, `docs/delivery/qa/`).
- `START_PROMPTS.md`: a QA row.
- `AGENT_TEAM_RULES.md` rule 11 and `roles/qa.md`: the stage is started and stopped by the agents that use it (QA, the backend); the live system's services stay the owner's; real model calls on the stage and windowed runs still need his word.

A project built from an earlier version does this to update (see `docs/update-mechanism.md`):
1. Replace `docs/team/` whole. If the project pushes messages, spends tokens or writes live data: add `docs/delivery/roles/qa.md` from the template, a QA row and a `by-qa` label mention in `docs/delivery/AGENT_RULES.md`, and write `docs/delivery/STAGE.md` (start, data copy, replaced channels, start guard, fixtures) with the Backend agent. The owner approves the stage launcher once.
2. Add the gate line to `docs/delivery/documentation-conventions.md` (session end checklist, item 2).
3. Open the QA session with its line from `docs/team/START_PROMPTS.md` when the stage runs.

Changed in the tools: `tools/new_project.py` has the new role `qa`, the answer `stage` (true or false; default no, asked at the interview) and generates `docs/delivery/STAGE.md` and `docs/delivery/qa/README.md` for a project with a stage; depth `product` includes `qa` by default. `/teamkit:init` asks the new question.

## 0.4.0 (2026-11-16, the Product Manager is the entry role)

Changed in `docs/team/` (replaced by the update):
- `roles/product.md` rewritten: the Product Manager is the FIRST session the owner talks to; it decides product questions, brings the owner's decisions as the rule 5 table and calls the CTO for the technical part.
- `roles/cto.md`: the CTO is called by the Product Manager, decides the technical part and which agents to activate, starts them, reports to the Product Manager; talks to the owner directly only when he opens its session or a decision is his by nature.
- `AGENT_TEAM_RULES.md`: rule 29 (the Product Manager is the entry role) and rule 30 (agreements reach the CTO in one line) appended; the roles line names the Product Manager.
- `START_PROMPTS.md`: launch order starts with Product, then CTO (opened by Product on the owner's word); the Product row is always present.

Generator and plugin: every preset now includes the Product Manager as the FIRST role (before it was an option at depth `product`); `/teamkit:init` interviews as the Product Manager and, at the end, calls the CTO; README and QUICKSTART say "open the Product session first". A test pins the product role in every preset and its first place.

Not in this version (still planned): the isolation hook with name normalisation and a group refresh script; the rule "reading is free".

Steps for a project built from an earlier version:
- Replace `docs/team/`. In `docs/delivery/AGENT_RULES.md` row 1-3 add the `Product` session name; if the project has no product role file in `docs/delivery/roles/`, copy the template's `roles/product.md` addendum and fill what it owns.
- Open a `Product` session and give it its start line; from now on the owner's requests go to it first.

## 0.3.0 (2026-11-15, first public release; the settings template and hooks pack stays planned for a later version)

Changed in `docs/team/` (replaced by the update):
- `FILE_LAYOUT.md` (new): layer 1 paths for every project, layer 2 fixed names, layer 3 decided by the project's CTO; "one kind of thing, one place"; runtime output never in git.
- Rule 27 (new): the owner's language with the owner, English between agents and in files for agents, the owner's words quoted verbatim.
- Code Reviewer: talks to the CTO in English; asks for an end hash when a range ends in `HEAD`.
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
  - "keep roles persistent" and "a bouncing handout is rewritten" in CTO;
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
