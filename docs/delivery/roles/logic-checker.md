<!-- role:logic-checker -->
# Role addendum: Logic Checker (<<project>>)

> Role brief: `../../team/roles/logic-checker.md`. Rules: `../../team/AGENT_TEAM_RULES.md`. Project specifics: [`../AGENT_RULES.md`](../AGENT_RULES.md).

- Findings register: `docs/delivery/LOGIC_FINDINGS.md`. The Logic Checker works in an export folder with no repository and writes new rows to `LOGIC_FINDINGS.new.md`; the CTO appends them to the committed register and commits. First-pass ids are date-based (`YYYYMMDD-n`).
- Documents this role checks here: <<the flow document, epics, requirements, acceptance criteria: their paths>>.
- The briefing pack the CTO builds (the export folder) is an **allowlist, not the full tree**: the code, a schema dump, `GLOSSARY.md` (or the project's vocabulary file), `docs/team/`, this addendum, the committed artifact, the files the card names, counts supplied by the CTO, and (on a re-check only) the committed register. Not in the pack: `.claude/`, `.scratch/`, gitignored files, session logs, memory notes, earlier findings (second pass only).
- The standing checklist in this project's words: <<the failure and retry rules, the stale-result rule, what is per user, the outward actions that need a confirmation, the silent-degradation rule>>.
- Labels (rule 21): the Logic Checker does not execute issues, so there is no `by-logic-checker`; a passed check is recorded with `reviewed` when the CTO treats it as an independent review.
- Never read personal files or user profiles.
<!-- /role -->
