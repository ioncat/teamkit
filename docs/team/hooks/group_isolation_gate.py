"""Claude Code PreToolUse hook: keep agent sessions inside their own group (rule 28, the isolation layer).

Wiring (local settings file, not tracked): a PreToolUse hook whose matcher covers the session-messaging and session-reading tools
(`SendMessage`, `mcp__ccd_session_mgmt__.*`) and runs `python <repo>/scripts/group_isolation_gate.py`.

Behaviour: a call that names ANOTHER session (a message, a read of its transcript, an export, a stop) passes only when the target is
in this group's allowlist (`.claude/group_sessions.json`: `{"ids": [...], "names": [...]}`, ids are session ids, names are exact
display names that are unique on the machine). Everything else is blocked with exit 2 and a reason on stderr, which Claude Code hands
to the model. A search over ALL transcripts has no single target, so it is blocked outright.

Never blocks because of its own error: a missing or unreadable config, a payload it does not understand, any exception: the call passes
(fail open), so a broken hook cannot lock the session. The allowlist file is the single place to edit; no session ids live in the code.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# the project root: the harness sets CLAUDE_PROJECT_DIR for hook commands; otherwise the folder above this script
_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent)
_CONFIG = _ROOT / ".claude" / "group_sessions.json"
_LOG = _ROOT / ".claude" / "group_gate.log"  # one line per checked call: tool, argument names, target, verdict (never the message text)

# tool name -> the arguments that name the target session (SendMessage has two spellings: `to` and `recipient`)
_TARGET_ARG = {
    "SendMessage": ("to", "recipient"),
    "mcp__ccd_session_mgmt__send_message": ("session_id",),
    "mcp__ccd_session_mgmt__get_session": ("session_id",),
    "mcp__ccd_session_mgmt__list_events": ("session_id",),
    "mcp__ccd_session_mgmt__export_transcript": ("session_id",),
    "mcp__ccd_session_mgmt__stop_session": ("session_id",),
    "mcp__ccd_session_mgmt__archive_session": ("session_id",),
    "mcp__ccd_session_mgmt__unarchive_session": ("session_id",),
    "mcp__ccd_session_mgmt__delete_session": ("session_id",),
    "mcp__ccd_session_mgmt__clear_session": ("session_id",),
    "mcp__ccd_session_mgmt__detach_session": ("session_id",),
}
_NO_TARGET_BLOCKED = {"mcp__ccd_session_mgmt__search_session_transcripts"}
# a subagent started by this session is addressed by its own agent id; those are not other groups' sessions
_SUBAGENT_ID = re.compile(r"^a[0-9a-f]{16}$")


def _load_config() -> dict | None:
    try:
        data = json.loads(_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    peers = data.get("cto_peers") if isinstance(data.get("cto_peers"), dict) else {}
    return {"ids": {str(x).lower() for x in data.get("ids", [])},
            "names": {str(x).strip().lower() for x in data.get("names", [])},
            # the CTOs of other groups, reachable ONLY by a message from this group's CTO session (rule 28)
            "cto_sessions": {str(x).lower() for x in data.get("cto_sessions", [])},
            "cto_peer_ids": {str(x).lower() for x in peers.get("ids", [])},
            "cto_peer_names": {str(x).strip().lower() for x in peers.get("names", [])}}


_SEND_TOOLS = {"SendMessage", "mcp__ccd_session_mgmt__send_message"}


def _is_cto_peer(target: str, cfg: dict) -> bool:
    t = target.strip().lower()
    if t in cfg.get("cto_peer_ids", set()) or t in cfg.get("cto_peer_names", set()):
        return True
    # "Name [ref]" as ListAgents prints it: the bare name or the ref of a listed peer
    m = re.match(r"^(.*?)\s*\[([0-9a-f]{4,})\]$", t)
    return bool(m and (m.group(1).strip() in cfg.get("cto_peer_names", set())
                       or any(i.endswith(m.group(2)) or i.startswith(m.group(2)) for i in cfg.get("cto_peer_ids", set()))))


def _allowed(target: str, cfg: dict) -> bool:
    t = target.strip().lower()
    if not t or _SUBAGENT_ID.match(t):
        return True
    if t in cfg["ids"] or t in cfg["names"]:
        return True
    # "Name [ref]" as ListAgents prints it: allowed when the bare name or the ref is allowed
    m = re.match(r"^(.*?)\s*\[([0-9a-f]{4,})\]$", t)
    if m and (m.group(1).strip() in cfg["names"] or any(i.endswith(m.group(2)) or i.startswith(m.group(2)) for i in cfg["ids"])):
        return True
    return False


def decide(payload: dict, cfg: dict) -> str | None:
    """Return a reason string when the call must be blocked, else None."""
    tool = str(payload.get("tool_name", ""))
    args = payload.get("tool_input") or {}
    if tool in _NO_TARGET_BLOCKED:
        return (f"{tool} searches the transcripts of every session, including other groups'. "
                "Ask the owner to run it by hand, or read your own group's sessions one by one.")
    fields = _TARGET_ARG.get(tool)
    if fields is None or not isinstance(args, dict):
        return None
    for target in (args.get(f) for f in fields):
        if not isinstance(target, str):
            continue
        if target.strip() == "*":
            return _blocked(target)
        if _allowed(target, cfg):
            continue
        # the one cross-group exception: this group's CTO may message another group's CTO (a message only, never a read)
        if (tool in _SEND_TOOLS and str(payload.get("session_id", "")).lower() in cfg.get("cto_sessions", set())
                and _is_cto_peer(target, cfg)):
            continue
        return _blocked(target)
    return None


def _blocked(target: str) -> str:
    return (f"Blocked: '{target}' is not in this group's allowlist (.claude/group_sessions.json). Agents talk only inside their own group "
            "(rule 28). If the session belongs to this group, ask the CTO to add it; if it belongs to another project, route it through the owner.")


def _log(payload: dict, reason: str | None) -> None:
    try:
        args = payload.get("tool_input") or {}
        target = next((args[a] for a in ("to", "recipient", "session_id") if isinstance(args.get(a), str)), "")
        line = json.dumps({"tool": payload.get("tool_name"), "arg_names": sorted(args) if isinstance(args, dict) else [],
                           "target": target, "agent": payload.get("agent_id"), "session": payload.get("session_id"), "verdict": "block" if reason else "pass"})
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main() -> int:
    try:
        # the harness sends UTF-8; on Windows the default text stdin decodes it as cp1252 and every emoji in a session name arrives garbled
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
        cfg = _load_config()
        if cfg is None:
            return 0  # no config: fail open
        reason = decide(payload, cfg)
        _log(payload, reason)
    except Exception:  # never fail the tool call because of the hook itself
        return 0
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
