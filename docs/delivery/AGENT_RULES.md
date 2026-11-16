# Agent rules: project addendum

> The common rules for every agent session are in [`../team/AGENT_TEAM_RULES.md`](../team/AGENT_TEAM_RULES.md). This page holds only what is specific to this project; rule numbers are the same as in the common file. Role addenda: [`roles/`](roles/). Work modes and who pushes: [`../team/WORK_MODES.md`](../team/WORK_MODES.md).

## Project specifics, by rule

| Rule | In this project |
|---|---|
| 1-3 Reports | The entry session is named `Product` (the owner talks to it first); the CTO session is named `CTO` and is called by Product. The owner's panel: <<none / a page / a file>> |
| 4-5 Talking to the owner | Chat language: <<language>>. The first row of the question table carries the tracker id. Product or user-journey questions go first to <<the Product Manager, if any>>; the owner gets only what is his by nature (pushes, live data writes, restarts, changes to team rules, the decisions marked as his) |
| 6-7 Commits | The working tree is shared by all sessions. Use a temporary index (`GIT_INDEX_FILE`) when the shared index holds other people's staged changes |
| 9 File ownership | See the table below |
<!-- kind:web,mobile,service,data-ml -->| 10 Database | The live DB is <<path>>; backups go to <<path>>; a migration is an idempotent startup step; a live write waits for the owner's word |<!-- /kind -->
| 11 Services | Run through <<command/script>>; restarts follow `../team/WORK_MODES.md` |
| 12 Personal data | <<repository visibility>> <<What counts as personal data here?>> Guard tests: <<names>> |
| 14 Quality gates | Tests: <<command>>; static analysis: <<command>>; other gates: <<>> |
| 15 Docs | `CHANGELOG.md` and the tracker issue closed by the CTO, per `documentation-conventions.md` |
<!-- kind:web,mobile -->| 16 UI | <<How the owner confirms a visual change; is there a browser preview?>> |<!-- /kind -->
<!-- kind:web,mobile,service,data-ml -->| 19 Tests and the live DB | A fixture sets the DB path to a throwaway file for every test: <<file>> |<!-- /kind -->
| 20 Task tracker | The board is <<Linear / GitHub Issues / BACKLOG.md>>, key <<PRJ>>. Among agents, the Business Analyst creates the issues and writes their description; the CTO adds the technical part, labels, states, assignment and closing (rule 20); no other agent writes there. Each handout carries an issue id; name it in your report and commit message. Issue format: `Origin:` first (who asked, when, in what words); user-facing issues use User story + Given/When/Then + edge cases + out of scope + dependencies; technical ones the short form Every issue also carries a `Value:` line right after `Origin:` (what gets better and for whom); an issue without it is not handed out. |
| 21 Labels | <!-- role:backend -->`by-backend`, <!-- /role --><!-- role:frontend -->`by-frontend`, <!-- /role --><!-- role:mobile -->`by-mobile`, <!-- /role --><!-- role:mcp -->`by-mcp`, <!-- /role --><!-- role:product -->`by-product`, <!-- /role -->`by-cto`, <!-- role:qa,qa-web -->`by-qa`, <!-- /role --><!-- role:code-reviewer -->`reviewed`, <!-- /role -->`needs-owner` |
| 18 Session log | `.claude/sessions/YYYY-MM-DD-short-description.md` (gitignored) |

## File ownership (rule 9)

| Owner | Files |
|---|---|
<!-- role:backend -->| Backend | <<folders and their tests>> |<!-- /role -->
<!-- role:frontend -->| Frontend | <<folders and their tests>> |<!-- /role -->
<!-- role:mobile -->| Mobile | <<mobile app folders and their tests>> |<!-- /role -->
<!-- role:mcp -->| MCP | <<agent interface folder>> (for example `mcp_server/`) and its tests |<!-- /role -->
<!-- role:product -->| Product | <<glossary, roadmap, discovery notes, user-visible texts, prompts if any>> |<!-- /role -->
| CTO | `docs/delivery/AGENT_RULES.md`, `docs/delivery/roles/`, the owner's panel |
<!-- role:code-reviewer -->
<!-- depth:product -->| Reviewer | `docs/delivery/REVIEW_FINDINGS.md` (the findings register); read-only otherwise |<!-- /depth -->
<!-- depth:mvp -->| Reviewer | read-only; findings go to the CTO in the report |<!-- /depth -->
<!-- /role -->
<!-- role:qa -->| QA | `docs/delivery/qa/` (scenario files) and its own test harness folder; read-only otherwise |<!-- /role -->
<!-- role:qa-web -->| Web QA | the smoke plan in `docs/delivery/`; read-only otherwise |<!-- /role -->
<!-- role:analyst -->| Business Analyst | the issues in the tracker (creates them and writes their description, rule 20), discovery notes in `docs/discovery/`; read-only otherwise |<!-- /role -->
<!-- depth:mvp,product -->| Shared, each for its own entries | `docs/delivery/CHANGELOG.md` |<!-- /depth -->

## Role addenda

- [CTO](roles/cto.md)
<!-- role:backend -->- [backend](roles/backend.md)<!-- /role -->
<!-- role:frontend -->- [frontend](roles/frontend.md)<!-- /role -->
<!-- role:mobile -->- [mobile](roles/mobile.md)<!-- /role -->
<!-- role:mcp -->- [mcp](roles/mcp.md)<!-- /role -->
<!-- role:product -->- [product](roles/product.md)<!-- /role -->
<!-- role:qa -->- [qa](roles/qa.md)<!-- /role -->
<!-- role:qa-web -->- [qa-web](roles/qa-web.md)<!-- /role -->
<!-- role:code-reviewer -->- [code-reviewer](roles/code-reviewer.md)<!-- /role -->
<!-- role:analyst -->- [Analyst](roles/analyst.md)<!-- /role -->
