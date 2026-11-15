# Agentic SDLC template: v1 (after critique)

**Status:** v1 for the owner, 2026-10-28. Built from `agentic-sdlc-draft-v0.md` (CTO), `agentic-sdlc-critique-reviewer.md`, `agentic-sdlc-critique-main.md` and `agentic-sdlc-sources.md` (specdriven.ai, Agentic Development Lifecycle, Spec Kit). Open decisions for the owner are in section 9.
**Goal:** agents work as a team and autonomously as experts in their roles; what is built is fixed in a spec before code.
**Scope (owner, 2026-10-28): this is for FUTURE projects built from TeamKit. It does not change existing projects: nothing there is rewritten or reorganised because of this document.**

---

## 1. Principles (what changed from v0)

1. **Handoffs are files, not messages.** A message only points to a file. Files survive compaction and paused agent-to-agent messages; chat does not. (v0, confirmed by both critics, same rule in ADLC.)
2. **The spec is examples, not prose.** A spec is a ≤10-line intent note plus acceptance criteria written as **examples** (input or action → expected result), each with an id and a `check by`. Examples become failing tests first. (Reviewer's alternative A + Main's AC rules.)
3. **Nobody grades their own homework.** The session that writes the intent does not write the plan; the plan and the examples are reviewed by the reviewer **before** code; the test writer is not the code writer on the spec lane; code is done only when the tests and the spec are unchanged by the code writer. (Both critics + ADLC.)
4. **Lane and autonomy follow risk, not hours or roles.** (Main 5.3, reviewer B.)
5. **The owner's attention is the scarcest resource.** He approves a one-page spec, decides only failed gates, and runs only the `owner` checks. He never reads a plan or code to approve. (Main 4, reviewer B.)
6. **Light files, grown from mistakes.** One file per role; skills and actions are added only after the same mistake repeats. (Reviewer 5; replaces v0's six layers and three files per role.)

## 2. Two lanes, chosen by risk

| Spec lane (any one is enough) | Fix lane |
|---|---|
| touches live data, prompts, multi-user behaviour, a screen whose **behaviour** changes, a seam between two agents, money or anything irreversible | everything else, however long; a layout or wording change of a screen stays here, with an `owner` check |

Promotion rule: a fix-lane change that needs a **second review round** sends the next change of its kind to the spec lane. The CTO marks the lane on the issue.

## 3. Spec lane, step by step

| Step | Who (role hat) | Given | Hands back (file) | Done when |
|---|---|---|---|---|
| 1 Shape | Product hat (Main, fresh session) with the owner | the owner's words or voice note | `spec.md`: restatement card, intent note, 3–7 examples with ids (happy, failure, **must-not**), `check by` each, out of scope, `Multi-user:`, assumptions ledger | owner approved the restatement; ≤5 questions asked, each with a recommended default; nothing unsettled was invented |
| 2 Plan | CTO | `spec.md` | the Linear issue: approach, seams touched, impact list (dependents: compatible / breaking / behaviour change), gates (multi-user, live data, prompt review, owner UI check) | every gate passed or justified |
| 3 Pre-code review | reviewer | spec + plan | findings in the register | every finding answered |
| 4 Tests | test hat: a fresh session, never the implementer and never the reviewer | the examples | failing tests named by example id; UI examples as widget tests where possible | tests fail against empty stand-ins; the mutation gate ("each program removed is noticed") only for rule and seam code |
| 5 Build | implementer role | spec, plan, tests | code + commits naming the example ids; screenshots for `screenshot`/`owner` examples | tests pass; tests and spec unchanged by the implementer, except through accepted proposals |
| 6 Review | reviewer | code + tests | findings | every finding answered by a change or a reason |
| 7 Accept | owner | the **done table** | his yes per `owner` example | recorded with date |

Mid-task discovery: the implementer may add `AC-n (proposed by <role>, RF-x)` inline; the spec writer accepts or rejects it; work continues against the proposal meanwhile. The same path holds for a wrong test: the implementer proposes the change, the test hat accepts or rejects it. (Reviewer.)

Impact is a line in the plan, not a stage; the owner sees it only when something is **breaking**. Recorded acceptance only for `owner` examples. The reviewer does steps 3 and 6 for every feature: watch it as a possible bottleneck in the pilot.

Bug = spec first: an owner-found defect becomes a new or sharpened example, then the fix. (Main 5.2.)

## 4. Fix lane

The Linear issue is the whole spec: Origin, Value, `Multi-user:`, 1–3 examples with `check by`. Build → review → done. No pre-code review.

## 5. The done table (resolves "verification.md: keep or drop")

Not written by hand. A script builds it from the spec's examples, the test names (by example id), the review register and the owner's recorded checks: example → evidence → result. The same script is the **drift check**: an example with no test or evidence, or a behaviour change with no example id, fails it. (Reviewer 4, Main 5.1; column named "result", owner's rule.)

## 6. Seams: contract first

Where two agents meet (backend ↔ Flutter, judge brief ↔ quote check), the producer owns a schema; consumer fixtures are generated from it; both sides test against it. Most of this week's Medium findings sat on seams. (Reviewer C.)

## 7. Roles

One file per role, in the ADLC shape: **questions it answers, access it needs, what it refuses, what it produces, the outside check it does not control**, plus a checklist of past findings (each line names its finding id). Skills (best-practice packs with sources) and actions (TeamKit format) are added only after a mistake repeats twice. The role brief replaces long prose.

## 8. Mechanics

- **One worktree and branch per agent; the shared tree stays on master.** Enforced by a hook that refuses a commit on another agent's branch. (Today's incident.)
- **Ledger of debts with teeth:** the multi-user watchlist becomes a ledger. Each row names its area as a list of files, an owner role and a due date. An overdue open debt blocks promotion of that area to a release (not every push); the push that pays the debt is always allowed.
- **Owner decision queue** (the existing page) carries every question; `[NEEDS CLARIFICATION]` lines become cards.
- From Spec Kit we take three ideas, not its commands: example ids, `[NEEDS CLARIFICATION]`, gates before code. The plan and tasks live in the Linear issue, not in extra files.

## 9. Decisions for the owner

1. **DECIDED (owner, 2026-10-28): by work mode.** In `auto` an agent does a reversible action on its own recommendation (the card shows it as done and revertable); in `manual` it waits for the owner. Irreversible actions always wait. Written into `team/WORK_MODES.md`. Original question: **Reversible decisions proceed after N hours?** Reviewer's alternative B: a reversible item goes ahead on the agent's recommendation after N hours unless you object; irreversible items (live data, push, model spend, deleting) always wait for your yes. This changes your rule "no action without an explicit yes". Options: [1] adopt with N = 4 working hours; [2] keep "always wait"; [3] adopt only for UI wording and docs (the reviewer's suggestion if you adopt it at all).
1b. **DECIDED (owner, 2026-10-28): EARS and STE-lite accepted** as analysed in `ears-ste-decision.md`. EARS: required form for the failure and must-not examples of spec-lane features; happy-path examples may stay free. STE-lite: the five style lines for every agent instruction of a new project from day one (imperative; one instruction per sentence; warning before the action; no should/may/try; one term per concept from GLOSSARY.md; a one-line "Why:" where an edge case needs it). Strict STE stays off. Existing projects are not changed. Kept or dropped after the pilot by the success and kill criteria in that file.
2. **Pilot feature.** (Owner: moved to the first new project built from the template.) Run one real feature through the spec lane and measure owner minutes, rework after "done" and review rounds. Candidate: a feature with live data, a screen and two agents.
3. **Where it lives.** TeamKit only, for future projects. existing projects are not changed by it (owner, 2026-10-28).
