# Sources

The documents TeamKit is built on: its ideological and methodological foundation. Like a reference list at the end of a paper, each entry says what it gave TeamKit and where that shows up.

**Rule:** when a new source changes TeamKit, add it here in the same commit. Videos and talks are not listed; only documents (sites, specifications, articles, standards, books).

## Methodology

| # | Source | What TeamKit took from it | Where in TeamKit |
|---|---|---|---|
| 1 | **specdriven.ai**, Spec-Driven Development: phases, checkpoints, tenets. https://specdriven.ai | The spec comes before code; a change after merge starts with a spec revision; tasks sized for one PR | `docs/agentic-sdlc-v1.md` (spec lane) |
| 2 | **GitHub Spec Kit**: constitution → specify → clarify → plan → tasks → analyze → implement. https://github.com/github/spec-kit ; method: https://github.com/github/spec-kit/blob/main/spec-driven.md | Requirement ids, `[NEEDS CLARIFICATION]` markers, gates checked against the constitution before code | `docs/agentic-sdlc-v1.md` |
| 3 | **B. Böckeler, "Understanding Spec-Driven Development: Kiro, spec-kit, and Tessl"**, martinfowler.com, 2025. https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html | Three levels: spec-first, spec-anchored, spec-as-source; the risk of specs going stale | methodology discussion, v2 |
| 4 | **Thoughtworks Technology Radar: Spec-driven development.** https://www.thoughtworks.com/radar/techniques/spec-driven-development | An independent assessment of SDD's maturity (Assess) | methodology discussion |
| 5 | **Agentic Development Lifecycle (ADLC)**, agenticdevelopment.ai, and **agentroles.ai** | A stage is a role plus inputs, outputs, done-when and rationale. A role is defined by its questions, access, what it refuses, what it produces and an outside check. Handoff = a named artifact. Test before code, by another role. Impact step, ledger of debts | `docs/agentic-sdlc-v1.md`, the role briefs `docs/team/roles/` |

## Requirements and language standards

| # | Source | What TeamKit took from it | Where in TeamKit |
|---|---|---|---|
| 6 | **EARS, Easy Approach to Requirements Syntax.** A. Mavin, P. Wilkinson, A. Harwood, M. Novak, IEEE International Requirements Engineering Conference (RE'09), 2009. https://alistairmavin.com/ears/ | The five templates (ubiquitous / When / While / If…then / Where); the required form for failure and must-not examples | `docs/ears-ste-decision.md` |
| 7 | **ASD-STE100, Simplified Technical English** (ASD specification). https://www.asd-ste100.org/ | STE-lite: imperative; one instruction per sentence; a warning before the action; no should/may/try; one term per concept | `docs/ears-ste-decision.md`, the style of agent instructions |

## Claude Code practice

| # | Source | What TeamKit took from it | Where in TeamKit |
|---|---|---|---|
| 8 | **Anthropic, Claude Code documentation.** https://docs.claude.com/en/docs/claude-code | The mechanics TeamKit builds on: CLAUDE.md, settings and permissions, hooks, subagents, skills, worktrees, sessions | the whole kit |
| 9 | **howborisusesclaudecode.com**, a fan-made catalog (not affiliated with Anthropic) of tips by Boris Cherny and the Claude Code team. https://howborisusesclaudecode.com/ | Self-verification; a repeated mistake becomes a check in code; rewind instead of stacking corrections; effort per task; source tags; the next packs: settings, hooks, worktrees, skills | rules 3, 22, 25, 26; the role briefs; the role briefs' source tags |

## Considered, not adopted

| # | Source | Why it is listed |
|---|---|---|
| 10 | **BMAD Method.** https://github.com/bmad-code-org/bmad-method ; https://docs.bmad-method.org/ | Compared with SDD on 2026-10-31. Not adopted as a whole: it assumes one human driving one agent, keeps its own tracker and changes fast between versions. Its upstream planning chain (PRD → epic → story) is a candidate for the discovery handoff |

## Our own decisions

TeamKit also carries the owner's decisions and the lessons of the first team that used it: work modes, owner gates, the independent Reviewer, file ownership, persistent roles. They are recorded with dates in `docs/team/AGENT_TEAM_RULES.md` (the "Why:" lines), `docs/agentic-sdlc-v1.md` §9 and `TEAMKIT_CHANGELOG.md`.
