#!/usr/bin/env python3
"""Create a new project from TeamKit.

Usage:  python tools/new_project.py --out <dir> [--answers answers.json] [--dry-run]
        python tools/new_project.py --out <existing project> --adopt [--answers answers.json] [--dry-run]

Standard library only. Steps: read answers (interview or JSON file), render the
template into memory (drop roles, cut marked blocks, fill blanks), check the
result, then write it, run `git init` and make the first commit.

--adopt brings TeamKit into an EXISTING project: the folder must be a git
repository with a clean working tree (so the adoption is one reviewable diff).
Nothing is overwritten or deleted, no git command changes anything (no init, no
branch, no commit): only the files that do not exist yet are written; a TeamKit
file that already exists is listed as "kept, merge by hand"; an existing
CLAUDE.md is left as it is and the TeamKit section for it goes to
docs/team/CLAUDE_TEAMKIT_SECTION.md.

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
import hashlib
import json
import os
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


# ---------------------------------------------------------------- adopt (an existing project)
#
# The guarantees, in the order they are enforced (the owner's rule: adopting must break NOTHING in an existing repository):
#   1. Plan first, write later: every refusal is found before the first byte is written; one refusal means nothing is written.
#   2. Only an allowlist of paths is ever written (ADOPT_ALLOWED); never under .git, never CLAUDE.md, README.md, .gitignore, build files, CI, or any path that already exists.
#   3. A file is created exclusively (it never replaces anything), never through a symlink, never under an existing FILE.
#   4. A hash snapshot of every file of the repository is taken before and after; if any pre-existing file changed or went missing, or anything unexpected appeared, the files this run
#      wrote are removed again (nothing else is touched) and the run fails.
#   5. A manifest lists every created file (with its hash) and every created folder; `--undo-adopt` removes exactly those, and only those that are unchanged.

SECTION_FILE = "docs/team/CLAUDE_TEAMKIT_SECTION.md"
SECTION_HEADINGS = ("Rules by kind and depth", "Team", "Session memory (mandatory)", "Documentation")
MANIFEST = ".teamkit-adopt-manifest.txt"
ADOPT_ALLOWED_PREFIXES = ("docs/team/", "docs/delivery/")
ADOPT_ALLOWED_FILES = frozenset({"docs/discovery/README.md", "docs/delivery/PRODUCT_BRIEF.md", ".claude/work_mode", "project.yaml", MANIFEST})
NEVER_WRITTEN = ("CLAUDE.md", "README.md", ".gitignore")       # in adopt mode these are the project's: listed (kept), never written, even when absent


class AdoptError(Exception):
    """The adoption was stopped (a refusal, a failed check). Carries the message for the owner."""


def safe_rel(rel):
    """A relative POSIX path that stays inside the repository and is not under .git."""
    parts = rel.split("/")
    return bool(rel) and not (".git" in parts or ".." in parts or "" in parts or rel.startswith("/") or "\\" in rel or ":" in parts[0])


def adopt_allowed(rel):
    """Whether adopt mode may write this relative path at all."""
    return safe_rel(rel) and (rel in ADOPT_ALLOWED_FILES or rel.startswith(ADOPT_ALLOWED_PREFIXES))


def git_out(folder, *args):
    """Run a READ-ONLY git command in folder (`--no-optional-locks`: not even the index is refreshed); return (exit code, stdout)."""
    done = subprocess.run(["git", "--no-optional-locks", *args], cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="surrogateescape")
    return done.returncode, done.stdout


def adopt_refusal(out):
    """Why `out` cannot be adopted, or None. It must be the root of a git repository with a clean working tree, untracked files included (ignored ones do not count)."""
    if not out.is_dir():
        return f"{out} is not an existing folder: --adopt is for a project that already exists (without --adopt the folder must be new or empty)"
    code, top = git_out(out, "rev-parse", "--show-toplevel")
    if code != 0:
        return f"{out} is not a git repository: put the project under git first (git init and a first commit), then adopt, so that the adoption is one reviewable diff"
    if Path(top.strip()).resolve() != out.resolve():
        return f"{out} is a subfolder of the repository {top.strip()}: adopt from the repository root"
    code, status = git_out(out, "status", "--porcelain")
    if code != 0 or status.strip():
        return (f"the working tree of {out} is not clean ({len([l for l in status.splitlines() if l.strip()])} change(s)): commit or stash them first, "
                "so that the adoption is the only change; git status shows them")
    return None


def claude_section(claude_md):
    """The TeamKit part of a rendered CLAUDE.md: the sections an existing CLAUDE.md does not have (rules by kind and depth, team, session memory, documentation) and the generic critical rules."""
    parts = re.split(r"(?m)^(?=## )", claude_md)
    keep = [p.rstrip() for p in parts if p.startswith("## ") and p[3:].split("\n", 1)[0].strip() in SECTION_HEADINGS]
    crit = [ln for p in parts if p.startswith("## Critical rules") for ln in p.splitlines() if ln.startswith("- ") and "<<" not in ln]
    text = ("# TeamKit section for CLAUDE.md\n\nTeamKit never writes or changes the project's `CLAUDE.md` in adopt mode. Merge the sections below into it by hand, keeping your own text "
            "(if the project has no `CLAUDE.md` yet, start one from this file); the paths point to the files TeamKit has just added. Then delete this file.\n\n")
    text += "\n\n".join(keep)
    if crit:
        text += "\n\n## Critical rules (add to your own list)\n\n" + "\n".join(crit)
    return text + "\n"


def adopt_plan(files, out):
    """Plan the whole adoption BEFORE anything is written. Returns (new, kept, skipped, refusals):
    new      {path: text}  files that will be created: allowlisted, and nothing stands at the path (a symlink, even a broken one, counts as standing there);
    kept     [path]        paths that already exist (or that adopt mode never writes and exist): left exactly as they are, to merge by hand;
    skipped  [path]        rendered files that adopt mode does not write at all (outside the allowlist, or the project's own CLAUDE.md / README.md / .gitignore that do not exist yet);
    refusals [text]        reasons the adoption cannot go on (a FILE where a folder is needed, a symlinked folder): ONE of them and nothing is written."""
    files = dict(files)
    if "CLAUDE.md" in files:
        files[SECTION_FILE] = claude_section(files["CLAUDE.md"])         # always: the project's CLAUDE.md is never touched, whether it exists or not
    new, kept, skipped, refusals = {}, [], [], []
    for rel, text in files.items():
        dest = out / rel
        if rel in NEVER_WRITTEN or not adopt_allowed(rel):
            (kept if os.path.lexists(dest) else skipped).append(rel)
            continue
        blocked = False
        for p in dest.parents:                                            # the folders between the repository root and the file
            if p == out or out not in p.parents:
                continue
            if os.path.lexists(p) and (p.is_symlink() or not p.is_dir() or redirected(out, p)):
                what = "a file" if (not p.is_dir() and not p.is_symlink()) else "a symlink or junction (or resolves to another place)"
                refusals.append(f"{p.relative_to(out).as_posix()} is {what}, not a plain folder: {rel} cannot be created under it (nothing is written; move it away or adopt by hand)")
                blocked = True
                break
            if os.path.lexists(p / ".git"):
                refusals.append(f"{p.relative_to(out).as_posix()} is a separate git repository (a submodule or a nested repository): {rel} cannot be created inside it (nothing is written)")
                blocked = True
                break
        if blocked:
            continue
        if os.path.lexists(dest):
            kept.append(rel)
        else:
            new[rel] = text
    if new and os.path.lexists(out / MANIFEST):
        refusals.append(f"{MANIFEST} of an earlier adoption is already here: undo that one first (--undo-adopt) or remove the manifest, so that this run's manifest cannot overwrite it")
    return new, kept, skipped, sorted(set(refusals))


def kept_hint(rel, text, out):
    """What the owner has to merge by hand for a kept file: for .gitignore the lines TeamKit needs and the project's file lacks."""
    if rel == ".gitignore" and (out / rel).is_file():
        have = {ln.strip() for ln in (out / rel).read_text(encoding="utf-8", errors="replace").splitlines()}
        missing = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#") and ln.strip() not in have]
        if missing:
            return "add these lines: " + ", ".join(missing)
    return ""


def _is_junction(p):
    """A Windows directory junction (Python 3.12+: Path.is_junction; 3.12 also has os.path.isjunction). On older Pythons only the real-location check in `redirected` catches it."""
    f = getattr(p, "is_junction", None)
    if f:
        return bool(f())
    f = getattr(os.path, "isjunction", None)
    return bool(f and f(p))


def redirected(out, p):
    """True when the EXISTING path p (under out) is not where its path says: a symlink, a junction, or anything whose real location differs from real(out)/<its relative path> (compared without
    case on Windows, where a folder may differ only in case). A write or a delete through such a path would land somewhere else, possibly outside the repository."""
    if p.is_symlink() or _is_junction(p):
        return True
    expected = os.path.join(os.path.realpath(out), *p.relative_to(out).parts)
    return os.path.normcase(os.path.realpath(p)) != os.path.normcase(expected)


def inside_real(out, p):
    """Whether the real location of p is inside the real location of out."""
    real_out, real_p = os.path.normcase(os.path.realpath(out)), os.path.normcase(os.path.realpath(p))
    try:
        return os.path.commonpath([real_out, real_p]) == real_out
    except ValueError:                                                   # another drive
        return False


def ancestors(out, dest):
    """The folders between the repository root and dest, top first (the root itself excluded)."""
    return [q for q in reversed(dest.parents) if q != out and out in q.parents]


def fold(rel):
    """A path as the snapshot comparison sees it: case-insensitive where the file system is (Windows, macOS), so a folder that differs only in case is the same folder."""
    return rel.casefold() if sys.platform in ("win32", "darwin") else rel


def sha_of(path):
    """Hash of a file's bytes; a symlink is hashed by what it points to and NEVER followed."""
    if path.is_symlink():
        return "symlink:" + os.readlink(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hashes(repo):
    """{path: hash} of every file of the repository that git knows (tracked, or untracked and not ignored), `.git` excluded. A symlink is hashed by its target, never followed; a path that is
    not a regular file (a submodule folder) is recorded as such; an unreadable file as unreadable."""
    code, listing = git_out(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if code != 0:
        raise AdoptError("git could not list the files of the repository: the snapshot cannot be taken, nothing is written")
    snap = {}
    for rel in filter(None, listing.split("\0")):
        p = repo / rel
        try:
            snap[rel] = sha_of(p) if (p.is_symlink() or p.is_file()) else "not-a-file"
        except OSError:
            snap[rel] = "unreadable"
    return snap


def write_new(files, out, created, made_dirs):
    """Create each file under out EXCLUSIVELY (`open(..., "x")`: an existing file is never replaced, even by a race). `created` and `made_dirs` are filled as it goes, so that a failure half way
    still tells the caller exactly what to remove."""
    for rel, text in files.items():
        dest = out / rel
        if not adopt_allowed(rel):
            raise AdoptError(f"{rel} is not a path adopt mode writes")
        for p in ancestors(out, dest):                                     # re-checked right before EVERY write: a folder turned into a link or junction after the plan is caught here
            if os.path.lexists(p) and (not p.is_dir() or redirected(out, p)):
                raise AdoptError(f"{p.relative_to(out).as_posix()} is a file, a symlink or a junction, or resolves to another place: {rel} is not written")
        for d in [p for p in ancestors(out, dest) if not os.path.lexists(p)]:
            d.mkdir()
            made_dirs.append(d.relative_to(out).as_posix())
        for p in ancestors(out, dest):
            if redirected(out, p) or not inside_real(out, p):
                raise AdoptError(f"{p.relative_to(out).as_posix()} resolves outside the repository: {rel} is not written")
        with open(dest, "x", encoding="utf-8", newline="\n") as f:
            created.append(rel)                                          # recorded first: if the write fails, the empty file is removed by the rollback
            f.write(text)
        if not inside_real(out, dest) or redirected(out, dest):
            raise AdoptError(f"{rel} landed outside the repository or somewhere else than its path says: removed again")


def rollback(out, created, made_dirs):
    """Remove what THIS run created and nothing else: each created regular file (never a symlink, never a folder tree), then the folders it made, deepest first, only if they are empty."""
    problems = []
    for rel in reversed(created):
        p = out / rel
        try:
            if os.path.lexists(p) and p.is_file() and not p.is_symlink():
                p.unlink()
        except OSError as exc:
            problems.append(f"{rel}: {exc}")
    for rel in sorted(set(made_dirs), key=lambda r: -r.count("/")):
        try:
            (out / rel).rmdir()
        except OSError:
            pass                                                         # not empty or already gone: not ours to force
    return problems


def planned_dirs(files, out):
    """The folders the run will have to make (parents first), so the manifest can name them before the first file is written."""
    dirs = []
    for rel in files:
        for p in ancestors(out, out / rel):
            r = p.relative_to(out).as_posix()
            if not os.path.lexists(p) and r not in dirs:
                dirs.append(r)
    return dirs


def manifest_text(files, dirs):
    """The manifest, written BEFORE the first file: every file the run is about to create (with the hash of the text it will hold) and every folder it will make. If the run is killed half way, the
    undo still knows what to look for (a listed file that does not exist is skipped)."""
    lines = ["# TeamKit adopt manifest: every file and folder the adopt run creates, nothing else.",
             "# Undo: python <TeamKit>/tools/new_project.py --out . --undo-adopt   (removes exactly these, only the files that are unchanged)"]
    lines += [f"dir {d}" for d in dirs]
    lines += [f"file {rel} {hashlib.sha256(text.encode('utf-8')).hexdigest()}" for rel, text in files.items()]
    return "\n".join(lines) + "\n"


def blanks_of(files):
    return [f"{rel}: {ln.strip()[:80]}" for rel, text in files.items() for ln in text.splitlines() if "<<" in ln]


def apply_adoption(new, out):
    """Write the manifest, then the new files, with every guarantee; returns (created paths, made folders). On ANY failure, including Ctrl-C, the files this run wrote and the folders it made are removed
    again (nothing else is touched or restored); an AdoptError says why, an interrupt is re-raised after the clean-up."""
    before = tree_hashes(out)
    created, made_dirs = [], []
    try:
        write_new({MANIFEST: manifest_text(new, planned_dirs(new, out))}, out, created, made_dirs)       # first: so that an undo always knows what this run was about to create
        write_new(new, out, created, made_dirs)
    except BaseException as exc:
        problems = rollback(out, created, made_dirs)
        if isinstance(exc, (OSError, AdoptError)):
            raise AdoptError(f"writing stopped ({exc}); the files this run wrote were removed again, nothing else was touched" + (f"; could not remove: {problems}" if problems else ""))
        raise
    try:
        after = tree_hashes(out)
    except BaseException:
        rollback(out, created, made_dirs)
        raise
    before_n = {fold(rel): h for rel, h in before.items()}
    after_n = {fold(rel): h for rel, h in after.items()}
    created_n = {fold(rel) for rel in created}
    changed = [rel for rel, h in before_n.items() if after_n.get(rel) != h]
    unexpected = [rel for rel in after_n if rel not in before_n and rel not in created_n]
    if changed or unexpected:
        problems = rollback(out, created, made_dirs)
        detail = "; ".join([f"changed or missing: {changed[:10]}"] * bool(changed) + [f"unexpected new: {unexpected[:10]}"] * bool(unexpected))
        raise AdoptError(f"a file that existed before the run was changed, or something unexpected appeared ({detail}). The files this run wrote were removed again; "
                         "nothing else was touched or restored: look at git status and git diff before you go on" + (f"; could not remove: {problems}" if problems else ""))
    return created, made_dirs


def undo_adoption(out):
    """The undo of `--adopt`: remove exactly the files listed in the manifest (only when they are unchanged since, never a symlink, never outside the allowlist), then the folders it made if they
    are empty, then the manifest. Returns (removed, left_alone)."""
    manifest = out / MANIFEST
    if not manifest.is_file() or manifest.is_symlink():
        raise AdoptError(f"{MANIFEST} not found in {out}: there is nothing to undo here")
    removed, left, dirs = [], [], []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.startswith("dir "):
            dirs.append(line[4:].strip())
        elif line.startswith("file "):
            rel, _, digest = line[5:].rpartition(" ")
            p = out / rel
            if not adopt_allowed(rel) or rel == MANIFEST:
                left.append(f"{rel} (not a path adopt mode writes: left alone)")
            elif not os.path.lexists(p):
                continue
            elif any(redirected(out, q) for q in ancestors(out, p) if os.path.lexists(q)) or not inside_real(out, p):
                left.append(f"{rel} (a folder on its path is a symlink or junction, or resolves elsewhere: left alone)")
            elif p.is_symlink() or not p.is_file():
                left.append(f"{rel} (not a regular file now: left alone)")
            elif sha_of(p) != digest:
                left.append(f"{rel} (changed since the adoption: left alone)")
            else:
                p.unlink()
                removed.append(rel)
    for rel in sorted(set(dirs), key=lambda r: -r.count("/")):
        q = out / rel
        if safe_rel(rel) and os.path.lexists(q) and not redirected(out, q) and not any(redirected(out, x) for x in ancestors(out, q) if os.path.lexists(x)):
            try:
                (out / rel).rmdir()                                      # rmdir only ever removes an EMPTY folder
            except OSError:
                pass
    if not left:
        manifest.unlink()
    return removed, left


def adopt(a, files, problems, roles, out, dry_run):
    """The adopt run: plan, print the plan (new files, kept files, not written, the CLAUDE.md section), and, unless it is a dry run, write with every guarantee. Never a git command that changes
    anything. Returns the exit code."""
    new, kept, skipped, refusals = adopt_plan(files, out)
    print(f"Plan (adopt into {out}): {a['kind']} / {a['stack']} / {a['depth']}; roles: {', '.join(roles)}")
    print(f"Dropped roles: {', '.join(r for r in ALL_ROLES if r not in roles) or 'none'}")
    for p in problems:
        print(f"PROBLEM {p}")
    for r in refusals:
        print(f"REFUSED {r}")
    print(f"\nNew files, written only because nothing stands there yet ({len(new)}, plus the manifest {MANIFEST}):")
    for rel in new:
        print(f"  + {rel}")
    print(f"\nKept as they are, merge by hand ({len(kept)}):")
    for rel in kept:
        hint = kept_hint(rel, files.get(rel, ""), out)
        print(f"  = {rel}" + (f"   ({hint})" if hint else ""))
    if not kept:
        print("  (none)")
    if skipped:
        print(f"\nNot written in adopt mode ({len(skipped)}): {', '.join(skipped)}")
        if ".gitignore" in skipped:
            lines = [ln for ln in files.get(".gitignore", "").splitlines() if ln.strip() and not ln.startswith("#")]
            print(f"  the project has no .gitignore: create one with at least: {', '.join(lines[:8])}")
    if SECTION_FILE in new:
        print(f"\nCLAUDE.md is never written or changed in adopt mode: the TeamKit section for it is {SECTION_FILE}; merge it into the project's CLAUDE.md (or start one from it) by hand.")
    blanks = blanks_of(new)
    print(f"\nBlanks left to fill in the new files: {len(blanks)}")
    for b in blanks:
        print(f"  {b}")
    if refusals:
        print("\nNothing written: fix the REFUSED line(s) first." if not dry_run else "\nDry run: nothing written (and a real run would be refused, see above).")
        return 1
    if dry_run:
        print("\nDry run: nothing written. Run it on a NEW BRANCH (git switch -c chore/adopt-teamkit), then look at git status: it shows only new files.")
        return 0
    if problems:
        print("Not written: fix the template first.")
        return 1
    if not new:
        print("\nNothing to adopt: every file TeamKit would add already exists. Nothing written.")
        return 0
    try:
        created, _dirs = apply_adoption(new, out)
    except AdoptError as exc:
        print(f"\nERROR: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted: the files this run wrote were removed again; nothing else was touched.")
        return 130
    print(f"\nWritten: {len(created) - 1} new file(s) and the manifest {MANIFEST}; {len(kept)} existing path(s) left exactly as they were. No git command was run that changes anything: "
          "no init, no branch, no commit.")
    print("Check it now: `git status` must show ONLY new files (all marked ??, nothing modified, nothing deleted); `git diff` must be empty. Work on a NEW BRANCH "
          "(git switch -c chore/adopt-teamkit) and commit the adoption yourself after looking.")
    print(f'To undo exactly this run: python "{Path(__file__).resolve()}" --out "{out.resolve()}" --undo-adopt')
    print("Then merge the CLAUDE.md section and the kept files by hand, fill the file ownership table in docs/delivery/AGENT_RULES.md from the real folders, and open the Product Manager "
          "session (the Product row of docs/team/START_PROMPTS.md). Start in manual mode with the minimal roles.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Create a project from TeamKit, or adopt TeamKit into an existing project")
    ap.add_argument("--out", required=True, help="the project folder: new (empty or absent); with --adopt or --undo-adopt: the existing project, a git repository root")
    ap.add_argument("--answers", help="JSON file with the answers (no interview)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    ap.add_argument("--adopt", action="store_true",
                    help="add TeamKit to an EXISTING git project without changing anything that exists (clean tree needed; writes only new files, lists a manifest and the undo)")
    ap.add_argument("--undo-adopt", action="store_true", help="remove exactly the files a previous --adopt created (read from .teamkit-adopt-manifest.txt); changed files are left alone")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if args.undo_adopt:
        try:
            removed, left = undo_adoption(out)
        except AdoptError as exc:
            raise SystemExit(str(exc))
        print(f"Removed {len(removed)} file(s) created by the adoption.")
        for item in left:
            print(f"LEFT ALONE: {item}")
        print("Done: the tree is as it was before the adoption." if not left else f"{len(left)} file(s) left; the manifest stays so that you can undo again after you looked at them.")
        return 1 if left else 0
    if args.adopt:
        reason = adopt_refusal(out)
        if reason:
            raise SystemExit(reason)
    elif out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty (to bring TeamKit into an existing project use --adopt)")
    raw = json.loads(Path(args.answers).read_text(encoding="utf-8")) if args.answers else interview()
    a = normalize(raw)
    files = render(a)
    problems, blanks = check(files)
    roles = pick_roles(a)
    if args.adopt:
        return adopt(a, files, problems, roles, out, args.dry_run)
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
