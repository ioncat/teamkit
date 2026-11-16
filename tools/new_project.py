#!/usr/bin/env python3
"""Create a new project from TeamKit.

Usage:  python tools/new_project.py --out <dir> [--answers answers.json] [--dry-run]

Standard library only. Steps: read answers (interview or JSON file), render the
template into memory (drop roles, cut marked blocks, fill blanks), check the
result, then write it, run `git init` and make the first commit.

Markers (HTML comments, so documents stay readable without the generator):
    <!-- role:NAME -->...<!-- /role -->    kept if the role is in the team
    <!-- depth:LEVEL -->...<!-- /depth --> kept if the depth matches
    <!-- stack:NAME -->...<!-- /stack -->  kept if the stack matches
    <!-- kind:NAME -->...<!-- /kind -->    kept if the kind matches
NAME may be a comma-separated list. Markers may sit on their own lines (block)
or wrap part of a line (inline). Markers of the same type do not nest.
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ["web", "mobile", "service", "data-ml", "research"]
MOBILE_STACKS = ["flutter", "react-native", "native-ios", "native-android", "native-both", "other"]
DEPTHS = ["research", "mvp", "product"]
TRACKERS = ["linear", "github", "backlog"]
DOC_LEVELS = ["light", "standard", "full"]
DEFAULT_DOCS = {"research": "light", "mvp": "standard", "product": "full"}
TRACKER_TEXT = {"linear": "Linear", "github": "GitHub Issues", "backlog": "`docs/delivery/BACKLOG.md`"}
ALL_ROLES = ["cto", "backend", "frontend", "mobile", "mcp", "product", "analyst", "qa", "qa-web", "code-reviewer"]
OPTIONAL_ROLES: list[str] = []  # no optional roles now; a project opts in with the answer "extra_roles"
# extra roles of earlier versions: the logic check (called "analyst" before 0.4.2, "logic-checker" in 0.4.2 drafts) is now the reviewer's
# "logic and flows" lens, and the Business Analyst is in every preset; such answers are accepted and dropped with a note
LEGACY_EXTRA = {"analyst", "logic-checker"}
EXCLUDE_TOP = {".git", ".pytest_cache", "tools", "TEMPLATE_VERSION", "README.md", "QUICKSTART.md", "QUICKSTART.ru.md", "TEAMKIT_CHANGELOG.md",
               # not for a new project: TeamKit's own plugin files, its license, and local working folders
               ".claude-plugin", "skills", "LICENSE", ".scratch", ".claude", ".worktrees"}
EXCLUDE_DIRS = ("docs/knowledge/",)  # knowledge sources for TeamKit itself, not for new projects
EXCLUDE_FILES = {"docs/template-design.md", "docs/SOURCES.md", "docs/ears-ste-decision.md", "docs/agentic-sdlc-v1.md", "docs/agentic-sdlc-draft-v0.md",
                 "docs/agentic-sdlc-sources.md", "docs/agentic-sdlc-critique-main.md", "docs/agentic-sdlc-critique-reviewer.md",
                 "docs/delivery/TEAMKIT_BACKLOG.md"}  # TeamKit's own working list, never copied into a project
IOS_ANDROID = {"mobile-ios": "Mobile iOS", "mobile-android": "Mobile Android"}

MARKER = re.compile(
    r"(?P<lead>^[ \t]*)?<!-- (?P<t>role|depth|stack|kind):(?P<names>[\w,-]+) -->"
    r"(?P<body>.*?)<!-- /(?P=t) -->(?P<trail>[ \t]*\n)?",
    re.S | re.M)
LEFTOVER = re.compile(r"<!-- /?(role|depth|stack|kind)\b")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
PATTERNS = {
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"\+\d[\d\s().-]{7,}\d|\(\d{3}\)\s?\d{3}[- ]?\d{4}|\b\d{3}[- .]\d{3}[- .]\d{4}\b"),
    "absolute path": re.compile(r"\b[A-Za-z]:\\|/Users/\w+|/home/\w+"),
}


# ---------------------------------------------------------------- answers

def ask(prompt, choices=None, default=None):
    """Ask one question on the console; repeat until the answer is valid."""
    hint = f" [{'/'.join(choices)}]" if choices else ""
    dflt = f" (default: {default})" if default else ""
    while True:
        value = input(f"{prompt}{hint}{dflt}: ").strip() or (default or "")
        if value and (not choices or value in choices):
            return value
        print("  Please answer with one of the listed values." if choices else "  An answer is required.")


def interview():
    """Run the interactive interview and return the answers dict."""
    kind = ask("Kind of project", KINDS)
    if kind == "mobile":
        stack = ask("Stack", MOBILE_STACKS)
    elif kind == "research":
        stack = "any"
    else:
        stack = ask("Stack (any text, e.g. 'any')", default="any")
    depth = ask("Depth", DEPTHS)
    mcp_default = "yes" if depth == "product" and kind in ("web", "service") else "no"
    return {
        "name": ask("Project name"), "kind": kind, "stack": stack, "depth": depth,
        "visibility": ask("Repository", ["public", "private"]),
        "tracker": ask("Tracker", TRACKERS),
        "language": ask("Chat language (e.g. English)"),
        "docs": ask("Documentation level", DOC_LEVELS, DEFAULT_DOCS[depth]),
        "mcp": ask("Will users connect their own agents (MCP)?", ["yes", "no"], mcp_default) == "yes",
        "extra_roles": [],
        "stage": ask("Does it push messages, spend tokens or write live data (then it gets a stage and the QA role)?", ["yes", "no"], "yes" if depth == "product" else "no") == "yes",
        "work_mode": "manual",
    }


def normalize(raw):
    """Validate answers (from a file or the interview) and fill defaults."""
    a = dict(raw)
    for key in ("name", "kind", "depth", "visibility", "tracker", "language"):
        if not a.get(key):
            raise SystemExit(f"answers: missing '{key}'")
    for key, choices in (("kind", KINDS), ("depth", DEPTHS), ("tracker", TRACKERS),
                         ("visibility", ["public", "private"])):
        if a[key] not in choices:
            raise SystemExit(f"answers: '{key}' must be one of {choices}")
    a["stack"] = str(a.get("stack") or "any").lower()
    if a["kind"] == "mobile" and a["stack"] not in MOBILE_STACKS:
        raise SystemExit(f"answers: mobile stack must be one of {MOBILE_STACKS}")
    a["docs"] = a.get("docs") or DEFAULT_DOCS[a["depth"]]
    if a["docs"] not in DOC_LEVELS:
        raise SystemExit(f"answers: 'docs' must be one of {DOC_LEVELS}")
    if "mcp" not in a:
        a["mcp"] = a["depth"] == "product" and a["kind"] in ("web", "service")
    a["mcp"] = bool(a["mcp"]) if not isinstance(a["mcp"], str) else a["mcp"] == "yes"
    extra = a.get("extra_roles") or []
    if isinstance(extra, list):
        dropped = [r for r in extra if r in LEGACY_EXTRA]
        if dropped:
            print(f"Note: extra role(s) {dropped} are no longer separate roles: the logic check is the Reviewer's 'logic and flows' lens, "
                  "and the Business Analyst is in every team.")
        extra = [r for r in extra if r not in LEGACY_EXTRA]
    if not isinstance(extra, list) or any(r not in OPTIONAL_ROLES for r in extra):
        raise SystemExit(f"answers: 'extra_roles' must be a list from {OPTIONAL_ROLES}")
    a["extra_roles"] = extra
    stage = a.get("stage", False)
    a["stage"] = stage == "yes" if isinstance(stage, str) else bool(stage)
    if a["stage"] and (a["depth"] == "research" or a["kind"] == "research"):
        print("Note: a research project has no stage and no QA role; the stage answer is ignored.")
        a["stage"] = False
    a["work_mode"] = "manual"
    return a


# ---------------------------------------------------------------- roles and markers

def pick_roles(a):
    """Return the list of roles of the team for the answers (preset by depth and kind). The Product Manager is the entry role of every project and comes first;
    the Business Analyst (discovery and the tasks) is in every preset, research included, because the CTO never writes the issues. QA comes only with a stage."""
    kind, depth = a["kind"], a["depth"]
    if depth == "research" or kind == "research":
        roles = ["product", "analyst", "cto"]
    else:
        ui = {"web": ["frontend"], "mobile": ["mobile"]}.get(kind, [])
        roles = ["product", "analyst", "cto", "backend"] + ui + ["code-reviewer"]
        if a.get("stage"):
            roles.append("qa")  # QA runs the stage (rule 31): only a project with a stage has it
        if depth == "product" and kind == "web":
            roles.append("qa-web")
    if a["mcp"] and "backend" in roles:
        roles.append("mcp")
    roles += [r for r in a.get("extra_roles", []) if r not in roles]
    return roles


def role_variants(a, roles):
    """Map each role to the file names it produces (native-both makes two mobile roles)."""
    out = {r: [r] for r in roles}
    if "mobile" in roles and a["stack"] == "native-both":
        out["mobile"] = list(IOS_ANDROID)
    return out


def context(a, variants):
    """Names that count as true per marker type."""
    roles = set(variants)
    for names in variants.values():
        roles.update(names)
    stack = {a["stack"]}
    if a["stack"] == "native-both":
        stack.add("native")
    elif a["stack"].startswith("native-"):
        stack.add("native")
    return {"role": roles, "depth": {a["depth"]}, "stack": stack, "kind": {a["kind"]}}


def cut(text, ctx):
    """Cut marked blocks: keep the body where the marker matches, drop it otherwise."""
    def repl(m):
        keep = bool(set(m["names"].split(",")) & ctx[m["t"]])
        body = cut(m["body"], ctx) if keep else ""
        if m["lead"] is None or m["trail"] is None:  # marker in the middle of a line
            return body + (m["trail"] or "") if keep else (m["trail"] or "")
        if body.startswith("\n"):  # block form: markers on their own lines
            return body[1:]
        return body + "\n" if keep else ""  # whole line wrapped by a marker pair
    return MARKER.sub(repl, text)


def as_variant(text, name):
    """Rewrite mobile text for one native platform role (mobile-ios or mobile-android)."""
    text = text.replace("mobile.md", f"{name}.md").replace("by-mobile", f"by-{name}")
    text = text.replace("[mobile]", f"[{name}]")
    return re.sub(r"\bMobile\b", IOS_ANDROID[name], text)


def expand_variants(text, names):
    """Repeat every role:mobile block once per platform role (native-both)."""
    pat = re.compile(r"(?P<lead>^[ \t]*)?<!-- role:mobile -->(?P<body>.*?)<!-- /role -->", re.S | re.M)
    def repl(m):
        copies = [f"<!-- role:{n} -->{as_variant(m['body'], n)}<!-- /role -->" for n in names]
        return (m["lead"] or "") + ("\n" if m["lead"] is not None else "").join(copies)
    return pat.sub(repl, text)


# ---------------------------------------------------------------- rendering

def fill_map(a):
    """Exact blanks the answers can fill, longest first."""
    stack = a["stack"] if a["stack"] not in ("", "any") else "any"
    pairs = [
        ("<<Linear / GitHub Issues / BACKLOG.md>>, key <<PRJ>>",
         "`docs/delivery/BACKLOG.md`, no tracker key" if a["tracker"] == "backlog" else f"{TRACKER_TEXT[a['tracker']]}, key <<PRJ>>"),
        ("<<Linear / GitHub Issues / BACKLOG.md>>", TRACKER_TEXT[a["tracker"]]),
        ("<<Project name>>", a["name"]), ("<<project>>", a["name"]),
        ("<<language>>", a["language"]), ("<<repository visibility>>", f"The repository is {a['visibility']}."),
        ("<<YYYY-MM-DD>>", datetime.date.today().isoformat()),
        ("<<kind>>", a["kind"]), ("<<stack>>", stack), ("<<depth>>", a["depth"]),
    ]
    return pairs


STAGE_STUB = """# Stage

The stage is a second instance of the project, started from the branch under test, with a copy of the data and every outward channel replaced (rule 31). Nothing reaches the owner's live system before a change has passed QA here.

Fill in (the CTO writes this with the backend agent):

- Start and stop: <<launcher script, address, port>> (the live system's services are started only with the owner's launcher; the stage is started and stopped by QA and the backend).
- Data: the copy is made from the live data opened read-only: <<snapshot command>>. Keep it out of git (`db/stage*`).
- Outward channels replaced: messages, pushes and mail write to `logs/stage_outbound.log`; paid services are replaced by <<stand-in>>; a real call only on the owner's word, per run.
- Start guard: the stage refuses to start on the live data file, on the live port, or with a secret present (`.env.stage` carries none).
- Fixtures for anything read from outside: <<folder>>.
"""


def readme(a, roles):
    """A short project README that replaces the template's."""
    names = ", ".join(roles)
    return (f"# {a['name']}\n\nKind: {a['kind']}. Stack: {a['stack']}. Depth: {a['depth']}. "
            f"Tracker: {TRACKER_TEXT[a['tracker']]}.\n\n"
            "Built by a team of agent sessions under one owner. Start with `CLAUDE.md`, then "
            "`docs/team/START_PROMPTS.md` (open the Product session first: it is the entry role and calls the CTO).\n\n"
            f"Roles: {names}.\n\nFill the remaining blanks (search for the double angle brackets).\n")


def render(a, template=ROOT):
    """Render the template into {relative path: text}. Nothing is written."""
    roles = pick_roles(a)
    variants = role_variants(a, roles)
    ctx = context(a, variants)
    fills = fill_map(a)
    files = {}
    for path in sorted(template.rglob("*")):
        rel = path.relative_to(template).as_posix()
        if not path.is_file() or rel.split("/")[0] in EXCLUDE_TOP or rel in EXCLUDE_FILES or rel.startswith(EXCLUDE_DIRS):
            continue
        m = re.match(r"docs/(team|delivery)/roles/([\w-]+)\.md$", rel)
        if m and m[2] not in roles:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "mobile" in variants and len(variants["mobile"]) > 1:
            text = expand_variants(text, variants["mobile"])
        for name, value in fills:
            text = text.replace(name, value)
        text = cut(text, ctx)
        if m and m[2] == "mobile" and len(variants["mobile"]) > 1:
            for n in variants["mobile"]:
                files[rel.replace("mobile.md", f"{n}.md")] = as_variant(text, n)
        elif text.strip():
            files[rel] = text
    files["README.md"] = readme(a, [n for r in roles for n in variants[r]])
    if a["tracker"] == "backlog":
        files["docs/delivery/BACKLOG.md"] = "# Backlog\n\nOpen tasks, one per line: `Origin:` first, then `Value:`.\n"
    if "qa" in roles:
        files["docs/delivery/STAGE.md"] = STAGE_STUB
        files["docs/delivery/qa/README.md"] = "# QA scenarios" + chr(10) * 2 + "One file per feature: the steps, the expected result, the level (backend by HTTP, app without a window, app with a window). Written by the QA role." + chr(10)
    files["project.yaml"] = json.dumps(
        {**a, "template_version": (ROOT / "TEMPLATE_VERSION").read_text().strip(),
         "roles": [n for r in roles for n in variants[r]]}, indent=2) + "\n"
    files[".claude/work_mode"] = a["work_mode"] + "\n"
    # layer 1 of docs/team/FILE_LAYOUT.md: folders that exist from day one
    files["docs/discovery/README.md"] = "# Discovery\n\nIdeas and designs not yet committed to. One file per topic.\n"
    files[".scratch/README.md"] = "Temporary files of each role, one folder per role (`.scratch/<role>/`). Gitignored.\n"
    return files


# ---------------------------------------------------------------- checks

def check(files):
    """Return (problems, remaining blanks) for the rendered files."""
    problems, blanks = [], []
    for rel, text in files.items():
        if LEFTOVER.search(text):
            problems.append(f"{rel}: marker comment left")
        for kind, pat in PATTERNS.items():
            if rel != "project.yaml" and pat.search(text):
                problems.append(f"{rel}: looks like personal data ({kind})")
        blanks += [f"{rel}: {ln.strip()[:80]}" for ln in text.splitlines() if "<<" in ln]
        if rel.endswith(".md"):
            for target in LINK.findall(text):
                if re.match(r"[a-z]+:|#", target):
                    continue
                dest = (Path(rel).parent / target.split("#")[0]).as_posix()
                dest = re.sub(r"[^/]+/\.\./", "", dest)
                if dest and dest not in files and not any(f.startswith(dest.rstrip("/") + "/") for f in files):
                    problems.append(f"{rel}: broken link {target}")
    return problems, blanks


# ---------------------------------------------------------------- output

def write(files, out):
    """Write the rendered files under out."""
    for rel, text in files.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8", newline="\n")


def git_start(out):
    """git init and the first commit; returns a status line."""
    def run(*args):
        return subprocess.run(["git", *args], cwd=out, capture_output=True, text=True)
    if run("init", "-b", "master").returncode != 0:
        return "git init failed; run it yourself"
    run("add", "-A")
    done = run("commit", "-m", "chore: start from TeamKit")
    return "first commit made" if done.returncode == 0 else "git identity not set: commit not made (git add is done)"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Create a project from TeamKit")
    ap.add_argument("--out", required=True, help="new project folder (must be empty or absent)")
    ap.add_argument("--answers", help="JSON file with the answers (no interview)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    raw = json.loads(Path(args.answers).read_text(encoding="utf-8")) if args.answers else interview()
    a = normalize(raw)
    files = render(a)
    problems, blanks = check(files)
    roles = pick_roles(a)
    print(f"Plan: {a['kind']} / {a['stack']} / {a['depth']}; roles: {', '.join(roles)}; {len(files)} files")
    print(f"Dropped roles: {', '.join(r for r in ALL_ROLES if r not in roles) or 'none'}")
    for p in problems:
        print(f"PROBLEM {p}")
    print(f"Blanks left to fill: {len(blanks)}")
    for b in blanks:
        print(f"  {b}")
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0
    if problems:
        print("Not written: fix the template first.")
        return 1
    write(files, out)
    print(git_start(out))
    print(f"\nNext: open Claude Code in {out}, name the session Product and paste the Product row of "
          "docs/team/START_PROMPTS.md. Then fill the blanks listed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
