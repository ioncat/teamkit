# Start messages and launch order

The owner starts with the **Product Manager** session: it is the entry role. It opens the two planning roles, the Business Analyst and the CTO; the CTO opens the delivery roles. Check first whether the Product session has a `start_session` tool (newer Claude Code desktop sessions do; it may be deferred and need loading). If it does, it opens the Business Analyst and the CTO sessions itself with the start messages below, on the owner's word; the CTO then opens the delivery roles the same way, on the owner's word. If not, you (the owner) open each session and paste its one-line start message. Name the session as shown so the others can find it with `ListAgents`.

## Launch order

1. **Product Manager** (name it `Product`). The first session, the one you talk to. It reads the rules and the roadmap, then opens the Business Analyst and the CTO.
<!-- role:analyst -->
2. **Business Analyst** (name it `Analyst`). Opened by the Product Manager: it does the discovery of each request and writes the issues.
<!-- /role -->
3. **CTO** (name it `CTO`). Opened by the Product Manager (or by you) when the first technical question or the first written issue comes. It reads the rules, sets up the tracker labels (`by-<role>`, `reviewed`, `needs-owner`), decides which agents are needed and tells you what to open next.
<!-- role:backend -->
4. **Backend** (and the other delivery roles listed in the table below), opened by the CTO.
<!-- /role -->
<!-- role:qa -->
5. **QA** (name it `QA`), opened by the CTO when the first change with an effect needs the stage (rule 31).
<!-- /role -->
<!-- role:code-reviewer -->
6. **Reviewer** (read-only; opened by the CTO when the first risky change needs a look).
<!-- /role -->

Open them one at a time; each sends the CTO a line "ready".

## Grouping the team in the sidebar (Claude Code desktop)

When the CTO has the sidebar tools (`list_groups`, `create_group`, `move_sessions`):
1. Look for a group named after the product (`list_groups`). Reuse it; create it only if it is missing.
2. Move itself and every session it opens into that group.

Without these tools, the owner groups the sessions by hand: right-click a session in the sidebar.

## Roles are persistent sessions

Each role is ONE long-lived session with the role's name (`Developer`, `Code Reviewer`, ...), not one session per task.
- The CTO sends each new task to the existing role session (`send_message` / `SendMessage`); the task id goes in the message, never in the session title.
- Experience is kept in files as well as in the context: session logs, `.claude/memory/`, and lines in the role addendum (better: tests). That way it survives autocompaction and restarts.
- A new session for a role is opened only when the old one has lost the thread (see "When a session loses its context"). The one exception: for the "logic and flows" lens the CTO opens a fresh Reviewer session per request (`roles/code-reviewer.md`).

## Start messages (paste the whole line)

| Role | Session name | Message |
|---|---|---|
| Product (entry) | `Product` | `Read docs/team/roles/product.md, then docs/delivery/roles/product.md, then docs/team/AGENT_TEAM_RULES.md and CLAUDE.md, and follow them.` |
<!-- role:analyst -->| Business Analyst | `Analyst` | `Read docs/team/roles/analyst.md, then docs/delivery/roles/analyst.md, then docs/team/AGENT_TEAM_RULES.md and CLAUDE.md, and follow them.` |<!-- /role -->
| CTO | `CTO` | `Read docs/team/roles/cto.md, then docs/delivery/roles/cto.md, then docs/team/AGENT_TEAM_RULES.md and CLAUDE.md, and follow them.` |
<!-- role:backend -->| Backend | `Backend` | `Read docs/team/roles/backend.md, then docs/delivery/roles/backend.md, and follow them.` |<!-- /role -->
<!-- role:frontend -->| Frontend | `Frontend` | `Read docs/team/roles/frontend.md, then docs/delivery/roles/frontend.md, and follow them.` |<!-- /role -->
<!-- role:mobile -->| Mobile | `Mobile` | `Read docs/team/roles/mobile.md, then docs/delivery/roles/mobile.md, and follow them.` |<!-- /role -->
<!-- role:mcp -->| MCP | `MCP` | `Read docs/team/roles/mcp.md, then docs/delivery/roles/mcp.md, and follow them.` |<!-- /role -->
<!-- role:qa -->| QA | `QA` | `Read docs/team/roles/qa.md, then docs/delivery/roles/qa.md, and follow them.` |<!-- /role -->
<!-- role:qa-web -->| Web QA | `Web QA` | `Read docs/team/roles/qa-web.md, then docs/delivery/roles/qa-web.md, and follow them.` |<!-- /role -->
<!-- role:code-reviewer -->| Independent Reviewer | `Code Reviewer` | `Read docs/team/roles/code-reviewer.md, then docs/delivery/roles/code-reviewer.md, and follow them.` |<!-- /role -->

## When a session loses its context

After two failed attempts at the same thing, do not stack corrections: write a short brief of what was learned, `/clear`, and restart from it (rule 26).


Paste the same message again, then: "Read the latest file in `.claude/sessions/` and continue." (Not for a "logic and flows" review session: it has no session log; the CTO opens a new one with a new export folder.)

## Waking a sleeping session

The CTO can send a message to an existing session (it arrives as a user turn). It creates a new one only with `start_session`, when it has that tool.
