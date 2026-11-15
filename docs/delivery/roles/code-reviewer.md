# Role addendum: Independent Reviewer (<<project>>)

> Role brief: `../../team/roles/code-reviewer.md`. Rules: `../../team/AGENT_TEAM_RULES.md`. Project specifics: [`../AGENT_RULES.md`](../AGENT_RULES.md).

- Lenses used here: code and security (default); others on request (see the role brief).
<!-- depth:product -->
- Findings register: `docs/delivery/REVIEW_FINDINGS.md`; commit only that file, through a temporary index.
<!-- /depth -->
<!-- depth:mvp -->
- No findings register at this depth: report findings to the CTO, who keeps what matters in the tracker.
<!-- /depth -->
- Tests on a clean export: <<command>>.
- Security focus here: <<endpoints that take outside input, network sends, SQL from input, subprocess calls, file paths from input, personal data>>.
- Never read personal files or user profiles.
