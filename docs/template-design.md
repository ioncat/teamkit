# Template design: one generator, three axes

Status: draft v1 (2026-10-26). Owner: CTO of the template. The generator script is `tools/new_project.py` (Python, standard library only, Windows and Linux).

## Goal and value

Create a new project from this template in about a minute with the rules that fit its kind and depth, so that nobody fills the same blanks by hand, forgets a required one, or inherits roles and rules the project does not need. Value: speed and consistency for every new project, and a template that can be upgraded in the projects already made from it.

## The three axes (the interview)

| Axis | Choices | What it changes |
|---|---|---|
| **Kind** | web app; mobile app; service / API; data and ML; research (no code) | which roles exist, which checks the Reviewer and QA run |
| **Stack** (asked after the kind, optional) | web: any / React / Vue / server-rendered; mobile: Flutter / React Native / native iOS / native Android / both native; service: any; other: free text | stack blocks inside the role briefs; one Mobile role or two (native iOS and native Android are two sessions: `mobile-ios`, `mobile-android`) |
| **Depth** | Research (find out, no release); MVP (small and fast); Product (full discipline) | how strict the rules are, how much documentation is kept |

Other answers: will users connect their own agents (MCP; adds the optional `mcp` role, default yes for Product depth with web or service, no for research), project name, repository public or private, tracker (Linear, GitHub Issues, a `BACKLOG.md` file), chat language, documentation level (defaults from the depth: light, standard, full), default work mode (`manual`).

## Presets (starting values, tuned after the first real projects)

| | Research | MVP | Product |
|---|---|---|---|
| Roles | CTO, product | CTO, backend (and the UI role of the kind), Reviewer on risky changes | all roles of the kind, independent Reviewer always |
| MCP role (optional) | no | if users connect their own agents | if users connect their own agents (default yes for web and service) |
| Review | none | risky changes only (data, security, money, outward calls) | every change before a push |
| Documentation | notes only | README, changelog | changelog, review register, issue format with `Origin` and `Value`, smoke plan |
| Tracker discipline | a list | issues with `Origin` and `Value` | full issue format, labels, board |

Kind adds: **web** gets the Web QA role (browser smoke plan); **mobile** gets the Mobile role(s) with checks for screen sizes, orientation, keyboard, offline, permissions, themes and the owner's confirmation on an emulator or simulator; **service** gets contract and load checks; **data and ML** gets reproducibility and data-handling rules (no personal data in the repository, fixtures synthetic); **research** drops code roles.

Native mobile (iOS Swift, Android Kotlin): the role brief states the generic checks (build, unit and UI tests, simulator or emulator, store requirements) and marks the stack-specific commands as `<<to fill on first use>>`. The template does not invent tooling details that have not been tried on a real project.

## How the generator works

1. Read answers (interactive, or `--answers project.yaml` so an agent can run it).
2. Copy the template, remove the roles the preset does not include (files, table rows, start messages).
3. Cut the marked blocks: `<!-- role:mobile -->...<!-- /role -->`, `<!-- depth:product -->...<!-- /depth -->`, `<!-- stack:flutter -->...<!-- /stack -->`.
4. Fill the `<<...>>` blanks from the answers; leave the ones only the project can answer and list them at the end.
5. Write `project.yaml` (the answers and the template version) and `.claude/work_mode`; `git init` and the first commit.
6. Check: no `<<` left that the answers could fill, no personal data, links between the documents resolve. `--dry-run` prints the plan and writes nothing.

## Upgrade (later)

`project.yaml` keeps the template version. A later `--upgrade` compares the project's rule files with the new template and shows a diff to accept file by file; it never overwrites the project addenda (`docs/delivery/`).

## Open questions

Decided simply in v1: the documentation level is recorded in `project.yaml` but the cuts follow the depth only. The template README and the quickstarts are not copied into the new project; it gets a short generated README. The Reviewer stays a role at MVP depth (a session opened for risky changes), not a CTO checklist. Marker pairs of the same type do not nest. Answers are a JSON file (no YAML reader). Role briefs outside the marked blocks may still mention roles the project dropped.

Whether the generator also creates the remote repository (needs the owner's word and a token: out of scope for v1). Where research projects keep their findings. Whether MVP keeps the Reviewer as a session or as a checklist run by the CTO.
