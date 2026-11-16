# EARS and ASD-STE100: should the agentic SDLC adopt them?

**Status:** analysis for the owner, 2026-10-28. Inputs: the Reviewer (critic seat), Main (prompt owner, PdM), Flutter (implementer). Backend's answer pending; added when it comes.

## What was asked

EARS (Easy Approach to Requirements Syntax): spec examples in five templates (The system shall… / When… / While… / If…, then… / Where…).
ASD-STE100 Simplified Technical English: a controlled language for all agent instructions (one meaning per word, ≤20-word procedural sentences, imperative, one instruction per sentence, warnings before the action).

## Where the agents agree (3 of 3)

| | EARS | STE |
|---|---|---|
| Better work? | **Yes, for behaviour.** "If <unwanted>, then…" and "While <state>…" force the cases we kept missing: RF-383 (title AND a hard content hit), RF-395 (a quote piece not in the text), RF-389 (panel stays open on a folder change). | **Little.** No finding in the review register came from an ambiguous instruction; they came from missing cases and seams. CV problems were content, not syntax. |
| Maintenance | Near zero: five templates, a script can lint them. | High: needs a project dictionary (fit, blocker, archetype are not STE words), a linter that does not exist, and it erodes with every agent edit. |
| Owner's effort | None, if agents write it: Main turns his voice note into EARS, he confirms the restatement in his own language. | None to read; he must never write it. |
| Human↔agent | Harmless. | Harmful in prompts: bare commands strip the short reasons that help the model judge edge cases; a mass rewrite voids the H14 regression baselines. |
| Fit with layout / quality | Does not fit layout or "reads natural"; those stay a picture plus numbers, or an owner check. | Conflicts with PROMPT_EDITING_RULES (say it once; positive wording; bans go to mechanical lists). |

## SWOT

| Strengths | Weaknesses |
|---|---|
| EARS makes the missing failure and must-not cases visible before code; it maps 1:1 to tests and to Main's three AC kinds; cheap to lint. | EARS says nothing about layout or subjective quality; STE has no working checker and needs its own dictionary. |
| **Opportunities** | **Threats** |
| EARS examples become the drift check's ids; a spec-lane pilot can measure it. A light agent-text style (imperative, one instruction per sentence) makes role files easier to check. | Ritual: "shall" everywhere, ACs that pass the template but test the wrong thing ("the system shall work properly"). A mass STE rewrite of prompts loses nuance and regresses CV quality. Enforcement only local, so both drift. |

**The strongest argument against (Reviewer):** our failures come from what was never written, not from how it was written. A controlled language polishes the sentences we have; it adds none of the missing ones. EARS is the exception because its templates *ask* for the missing case.

## Recommendation (consensus)

1. **EARS: adopt narrowly.** Required form for the failure and must-not examples of spec-lane features; happy-path examples may stay free form. Not for layout (picture + numbers) or quality ("owner" check). A script lints the example lines.
2. **STE: do not adopt the standard.** Take five lines as an "agent-text style" for role files, actions and team rules, applied to new or edited lines only: imperative; one instruction per sentence; warning before the action; no should/may/try; one term per concept (from GLOSSARY.md), and keep a one-line "Why:" where an edge case needs it. **prompts/ excluded** (PROMPT_EDITING_RULES already govern them). No mass rewrite, no word cap, no dictionary.
   **Owner's clarification (2026-10-28): STE is meant for FUTURE projects, not for existing ones.** That removes the rewrite and regression objections. Updated: the template for new projects writes its agent instructions in **STE-lite from day 1** (the five style lines + the project's GLOSSARY as its dictionary); strict STE (20-word cap, full dictionary) stays optional, off by default. Measure on the first new project: fewer instruction rewrites than an existing project had? If not, strict mode is never turned on. Still open: a style checker is needed, or it decays. Existing projects: no STE; only the five style lines in their prompt review checklist for new or edited lines.
3. **The owner never writes either.** He speaks freely; agents produce the controlled text; he confirms a restatement.

## How to decide without "it's a cool idea"

- **Pre-mortem** (done above): imagine it failed in six months and name why; design against those reasons.
- **Success and kill criteria, set now:**
  - Success (the pilot + the next 2 spec-lane features): at least half of the missing-case findings are caught at the pre-code review instead of after code; owner minutes per feature not higher than today.
  - Kill: specs get longer with no fewer post-code findings, or the owner has to read EARS to approve.
- **Reversible pilot, not a rule:** one feature, then decide. Rules are added to the template only after the pilot passes.
- **Base rate check:** compare with the last 3 comparable features (title verdict: 4 review rounds, 5 findings, 2 Medium).
- **A dissenting seat:** the Reviewer keeps the critic role for the pilot's review.
