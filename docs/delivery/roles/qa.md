# Role addendum: QA agent (<<project>>)

> Role brief: `../../team/roles/qa.md`. Rules: `../../team/AGENT_TEAM_RULES.md`. Project specifics: [`../AGENT_RULES.md`](../AGENT_RULES.md).

- The stage: its start command (the owner's launcher script), its address and port: <<>> (QA starts and stops it itself; never the live system).
- What the stage replaces: the database copy <<file>>, the outward log <<file>>, the stand-in for the paid service <<what>>, recorded fixtures <<folder>>.
- How the snapshot is refreshed: <<command>> (only with the owner's yes).
- Scenario folder: `docs/delivery/qa/` (one file per feature; create on first use).
- Windowed runs: the tool <<name>>; whether a minimised window still works: <<unknown until tried>>.
