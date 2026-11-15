# Group isolation (rule 28): keep sessions inside their own project group

**Why.** Every session on the machine can see and message every other one, and session names collide across projects (several `Code Reviewer`, `CTO`, `Backend`). A rule in a text file does not stop a mix-up; a hook run by the harness does. This page is the setup. Verified live on Windows on 2026-11-05 (a blocked message to a foreign session, a blocked read of a foreign session, an allowed read of an own-group session, a denied file read in another project's folder; no restart of the session was needed).

## Layers (use all four; they are cheap)

1. **Unique names.** Prefix every session title with the project (`CA Reviewer`, `YT Reviewer`). It removes the wrong-addressee mistake; it is not a barrier.
2. **A PreToolUse hook** (`hooks/group_isolation_gate.py`). A call that names another session (`SendMessage`, and the `mcp__ccd_session_mgmt__*` tools that take a `session_id`) passes only when the target is in the group's allowlist `.claude/group_sessions.json` (`{"ids": [...], "names": [...]}`; ids are session ids, names are display names that are unique on the machine, lower case; a name given as `Name [ref]` passes when the name or the ref is listed). The search over all transcripts has no single target and is blocked. A broadcast (`*`) is blocked. A subagent id of the session passes. On any error of its own the hook lets the call through (fail open), so a broken hook cannot lock a session. It writes one line per checked call (tool, argument names, target, verdict, never the message text) to `.claude/group_gate.log`.
3. **Path deny rules** in `permissions.deny`, one per foreign project folder, gitignore syntax with `//` for an absolute path and the drive letter in lower case, for example `Read(//e/My files/0 My_Dev/my_prj/other-project/**)`. `Read` deny also blocks Edit and Write on the path and the Bash file commands that name it (`cat`, `sed`, redirections).
4. **Built-in controls** (documented, per session, not per target): `crossSessionInbound` = `accept` / `hold` / `refuse` (a stricter project value wins over user and managed values); `permissions.deny` with `SendMessage` and `ListAgents` removes messaging for the whole session, subagents included; `isolatePeerMachines: true` asks before a message to a session on another machine. They cannot allow the own group and block the others, which is why the hook exists.

## Setup (once per project)

1. Copy `hooks/group_isolation_gate.py` to `scripts/` or `.claude/hooks/` of the project.
2. Create `.claude/group_sessions.json` (gitignore it): the ids and unique names of the group's sessions. The ids come from the session list (the sidebar group is the source of truth). Add a new session to the file when it joins the group.
3. In `.claude/settings.local.json` (the local file is not tracked) add the hook and the denies:

```json
{
  "hooks": { "PreToolUse": [ { "matcher": "SendMessage|mcp__ccd_session_mgmt__.*",
    "hooks": [ { "type": "command", "command": "python \"<project root>/scripts/group_isolation_gate.py\"" } ] } ] },
  "permissions": { "deny": [ "Read(//<drive letter>/<path of a foreign project>/**)" ] }
}
```
   The matcher is a regular expression (it contains `|`, `.` and `*`); a bare `mcp__server` matches nothing in a hook. The hook gets `CLAUDE_PROJECT_DIR` from the harness and finds the allowlist there.
4. Test, one call each: a message to a foreign session (must be blocked and the reason shown), a read of an own-group session (must pass), a file read in a foreign folder (must be refused). Check `.claude/group_gate.log`.

## The CTO exception

The CTOs of different projects may message each other (rule 28). In `.claude/group_sessions.json`: `"cto_sessions": [<the hook's `session_id` of this group's CTO session>]` and `"cto_peers": {"ids": [...], "names": [...]}`. The hook passes a message to a listed peer only when the caller's `session_id` is in `cto_sessions`, so no other session of the group can use it, and only as a message (a read of the peer's session stays blocked). Find the CTO's `session_id` in `.claude/group_gate.log` after one allowed call.

## What was learned about the payloads

`SendMessage` carries the target in `to` (and `recipient`, with `recipient_kind`) and the text in `message` (and `content`, `summary`, `type`); the MCP `send_message` carries `session_id` and `message`. The hook checks every target field. **Windows:** the harness sends the payload as UTF-8 but a Python text stdin decodes it as cp1252, so every emoji in a session title arrives garbled and a name with an emoji never matches the allowlist; the script therefore reads the raw bytes and decodes UTF-8 (found live on 2026-11-05: a message to an allowed session was blocked until this was fixed).

## Limits (not 100%)

- It controls the tools named above. A subprocess that opens a file (Python, Node) or a Bash command that is not a plain file command is not covered by the path deny (Bash rules are textual). True isolation needs a separate OS account or a container.
- It protects the sessions of the project that has it. A session of another project without the hook can still message in; it needs its own hook, or the receiver sets `crossSessionInbound`.
- The allowlist is maintained by hand. A new session that is not in it cannot be reached until the CTO adds it.
- Names can collide; prefer ids and prefixed names.
