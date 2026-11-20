"""End-to-end tests of the generator (python -m unittest discover tools/tests)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
import new_project as gen  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "ci", "GIT_AUTHOR_EMAIL": "ci@example.org",
           "GIT_COMMITTER_NAME": "ci", "GIT_COMMITTER_EMAIL": "ci@example.org"}
BASE = {"name": "Demo", "visibility": "private", "tracker": "linear", "language": "English"}


def generate(tmp, **answers):
    """Run the CLI with an answers file; return the project folder."""
    out = Path(tmp) / "proj"
    answers_file = Path(tmp) / "answers.json"
    answers_file.write_text(json.dumps({**BASE, **answers}))
    env = {**os.environ, **GIT_ENV}
    res = subprocess.run([sys.executable, str(TOOLS / "new_project.py"), "--out", str(out),
                          "--answers", str(answers_file)], capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stdout + res.stderr
    return out


def all_text(out):
    return {p.relative_to(out).as_posix(): p.read_text(encoding="utf-8")
            for p in out.rglob("*") if p.is_file() and ".git" not in p.parts}


class GeneratorTest(unittest.TestCase):
    def assert_clean(self, out):
        for rel, text in all_text(out).items():
            self.assertNotRegex(text, r"<!-- /?(role|depth|stack|kind)", rel)
        for name in ("Demo",):
            self.assertIn(name, (out / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_web_mvp(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="web", stack="react", depth="mvp")
            self.assert_clean(out)
            self.assertTrue((out / "docs/team/roles/frontend.md").exists())
            for gone in ("qa-web", "mobile", "mcp"):
                self.assertFalse((out / f"docs/team/roles/{gone}.md").exists(), gone)
            self.assertFalse((out / "docs/delivery/REVIEW_FINDINGS.md").exists())
            self.assertTrue((out / "docs/delivery/CHANGELOG.md").exists())
            brief = (out / "docs/delivery/PRODUCT_BRIEF.md").read_text(encoding="utf-8")                 # the product brief template: the team's first reference
            self.assertIn("# Product brief: Demo", brief)
            self.assertIn("North Star", brief)
            self.assertIn("PRODUCT_BRIEF.md", (out / "docs/delivery/roles/product.md").read_text(encoding="utf-8"))
            rules = (out / "docs/delivery/AGENT_RULES.md").read_text(encoding="utf-8")
            self.assertIn("Linear", rules)
            self.assertIn("The repository is private.", rules)
            self.assertNotIn("Epics", (out / "docs/delivery/documentation-conventions.md").read_text(encoding="utf-8"))
            meta = json.loads((out / "project.yaml").read_text())
            self.assertEqual((meta["kind"], meta["depth"], meta["template_version"]), ("web", "mvp", (gen.ROOT / "TEMPLATE_VERSION").read_text().strip()))
            self.assertEqual((out / ".claude/work_mode").read_text().strip(), "manual")
            log = subprocess.run(["git", "log", "--oneline"], cwd=out, capture_output=True, text=True)
            self.assertIn("start from TeamKit", log.stdout)


    def test_nothing_of_the_plugin_or_the_workshop_is_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="web", stack="react", depth="mvp")
            for gone in (".claude-plugin", "skills", "LICENSE", "tools"):
                self.assertFalse((out / gone).exists(), gone)
            # the generator makes these two itself; nothing else comes from the template's working folders
            self.assertEqual(sorted(p.name for p in (out / ".scratch").iterdir()), ["README.md"])
            self.assertEqual(sorted(p.name for p in (out / ".claude").iterdir()), ["work_mode"])

    def test_logic_check_is_the_reviewers_lens(self):
        """No separate Logic Checker: the logic and flows check is a lens of the reviewer; old extra_roles answers are accepted and dropped."""
        for extra in ([], ["logic-checker"], ["analyst"]):
            with tempfile.TemporaryDirectory() as tmp:
                out = generate(tmp, kind="web", stack="react", depth="product", extra_roles=extra)
                self.assert_clean(out)
                for gone in ("docs/team/roles/logic-checker.md", "docs/delivery/roles/logic-checker.md", "docs/delivery/LOGIC_FINDINGS.md"):
                    self.assertFalse((out / gone).exists(), gone)
                for f in ("docs/delivery/AGENT_RULES.md", "docs/team/START_PROMPTS.md", "docs/team/AGENT_TEAM_RULES.md"):
                    self.assertNotIn("logic checker", (out / f).read_text(encoding="utf-8").lower(), f)
                self.assertNotIn("logic-checker", json.loads((out / "project.yaml").read_text())["roles"])
                self.assertIn("Logic and flows", (out / "docs/team/roles/code-reviewer.md").read_text(encoding="utf-8"))

    def test_business_analyst_writes_the_tasks_everywhere(self):
        """The Business Analyst is in every preset (research included): it writes the issues, the CTO never does."""
        for answers in ({"kind": "research", "depth": "research", "tracker": "backlog"},
                        {"kind": "web", "stack": "react", "depth": "mvp"},
                        {"kind": "service", "stack": "python", "depth": "product"}):
            with tempfile.TemporaryDirectory() as tmp:
                out = generate(tmp, **answers)
                self.assert_clean(out)
                roles = json.loads((out / "project.yaml").read_text())["roles"]
                self.assertEqual(roles[:3], ["product", "analyst", "cto"], answers)
                brief = (out / "docs/team/roles/analyst.md").read_text(encoding="utf-8")
                self.assertIn("Business Analyst", brief)
                self.assertTrue((out / "docs/delivery/roles/analyst.md").exists())
                prompts = (out / "docs/team/START_PROMPTS.md").read_text(encoding="utf-8")
                self.assertLess(prompts.index("| Business Analyst |"), prompts.index("| CTO |"))
                rules = (out / "docs/team/AGENT_TEAM_RULES.md").read_text(encoding="utf-8")
                self.assertIn("the **Business Analyst** creates issues", rules)

    def test_extra_roles_validated(self):
        with self.assertRaises(SystemExit):
            gen.normalize({**BASE, "kind": "web", "stack": "react", "depth": "mvp", "extra_roles": ["nobody"]})
    def test_mobile_flutter_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="mobile", stack="flutter", depth="product", mcp=False)
            self.assert_clean(out)
            self.assertTrue((out / "docs/team/roles/mobile.md").exists())
            self.assertTrue((out / "docs/delivery/REVIEW_FINDINGS.md").exists())
            self.assertFalse((out / "docs/team/roles/qa-web.md").exists())
            mobile = (out / "docs/team/roles/mobile.md").read_text(encoding="utf-8")
            self.assertIn("flutter analyze", mobile)
            self.assertNotIn("to fill on first use", mobile)
            self.assertIn("Epics", (out / "docs/delivery/documentation-conventions.md").read_text(encoding="utf-8"))

    def test_product_is_the_entry_role_everywhere(self):
        """The Product Manager is in every preset and comes first: the owner talks to it, it opens the Business Analyst and the CTO."""
        for answers in ({"kind": "research", "depth": "research", "tracker": "backlog"},
                        {"kind": "web", "stack": "react", "depth": "mvp"},
                        {"kind": "web", "stack": "react", "depth": "product"}):
            with tempfile.TemporaryDirectory() as tmp:
                out = generate(tmp, **answers)
                roles = json.loads((out / "project.yaml").read_text())["roles"]
                self.assertEqual(roles[0], "product", answers)
                self.assertIn("cto", roles)
                self.assertTrue((out / "docs/team/roles/product.md").exists())
                self.assertTrue((out / "docs/delivery/roles/product.md").exists())
                prompts = (out / "docs/team/START_PROMPTS.md").read_text(encoding="utf-8")
                self.assertIn("| Product (entry) |", prompts)
                self.assertLess(prompts.index("| Product (entry) |"), prompts.index("| CTO |"))
                self.assertIn("Product session first", (out / "README.md").read_text(encoding="utf-8"))

    def test_research_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="research", depth="research", tracker="backlog")
            self.assert_clean(out)
            roles = sorted(p.stem for p in (out / "docs/team/roles").iterdir())
            self.assertEqual(roles, ["analyst", "cto", "product"])
            self.assertFalse((out / "docs/delivery/CHANGELOG.md").exists())
            self.assertTrue((out / "docs/delivery/BACKLOG.md").exists())
            self.assertIn("Research", (out / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_native_both_two_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="mobile", stack="native-both", depth="mvp")
            self.assert_clean(out)
            for n in ("mobile-ios", "mobile-android"):
                self.assertTrue((out / f"docs/team/roles/{n}.md").exists())
                self.assertTrue((out / f"docs/delivery/roles/{n}.md").exists())
            self.assertFalse((out / "docs/team/roles/mobile.md").exists())
            prompts = (out / "docs/team/START_PROMPTS.md").read_text(encoding="utf-8")
            self.assertIn("roles/mobile-ios.md", prompts)
            self.assertIn("roles/mobile-android.md", prompts)

    def test_mcp_role_and_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="service", depth="product")  # mcp defaults to yes
            self.assertTrue((out / "docs/team/roles/mcp.md").exists())
            self.assertIn("by-mcp", (out / "docs/delivery/AGENT_RULES.md").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="research", depth="research", mcp=False)
            self.assertFalse((out / "docs/team/roles/mcp.md").exists())

    def test_qa_role_and_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="service", stack="python", depth="mvp", mcp=False)
            self.assertFalse((out / "docs/team/roles/qa.md").exists())
            self.assertFalse((out / "docs/delivery/STAGE.md").exists())
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="service", stack="python", depth="mvp", mcp=False, stage=True)
            self.assertTrue((out / "docs/team/roles/qa.md").exists())
            self.assertTrue((out / "docs/delivery/roles/qa.md").exists())
            self.assertTrue((out / "docs/delivery/STAGE.md").exists())
            self.assertIn("by-qa", (out / "docs/delivery/AGENT_RULES.md").read_text(encoding="utf-8"))
            self.assertIn("`QA`", (out / "docs/team/START_PROMPTS.md").read_text(encoding="utf-8"))
            self.assertIn("rule 31", (out / "docs/delivery/documentation-conventions.md").read_text(encoding="utf-8"))
            self.assert_clean(out)
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="web", stack="react", depth="product")  # product without a stage: qa-web, no qa
            self.assertFalse((out / "docs/team/roles/qa.md").exists())
            self.assertTrue((out / "docs/team/roles/qa-web.md").exists())
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="web", stack="react", depth="product", stage=True)  # with a stage: qa and its STAGE.md
            self.assertTrue((out / "docs/team/roles/qa.md").exists())
            self.assertTrue((out / "docs/delivery/STAGE.md").exists())
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="service", stack="python", depth="mvp", mcp=False)
            self.assertNotIn("TEAMKIT_BACKLOG", " ".join(str(p) for p in out.rglob("*")))  # TeamKit's own list is never copied
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="research", depth="research", mcp=False, stage=True)  # research never gets a stage role
            self.assertFalse((out / "docs/team/roles/qa.md").exists())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            answers = Path(tmp) / "a.json"
            answers.write_text(json.dumps({**BASE, "kind": "web", "depth": "mvp"}))
            res = subprocess.run([sys.executable, str(TOOLS / "new_project.py"), "--out", str(out),
                                  "--answers", str(answers), "--dry-run"], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("Dry run", res.stdout)
            self.assertFalse(out.exists())

    def test_file_layout_layer_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="service", stack="python", depth="mvp", mcp=False)
            self.assertTrue((out / "docs/team/FILE_LAYOUT.md").exists())
            self.assertTrue((out / "docs/discovery/README.md").exists())
            self.assertTrue((out / ".scratch/README.md").exists())
            ignore = (out / ".gitignore").read_text(encoding="utf-8")
            for path in (".scratch/", ".worktrees/", ".claude/sessions/", ".claude/memory/"):
                self.assertIn(path, ignore)
            tracked = subprocess.run(["git", "ls-files"], cwd=out, capture_output=True, text=True).stdout
            self.assertNotIn(".scratch/", tracked)
            self.assertIn("docs/discovery/README.md", tracked)

    def test_checks_find_no_problems(self):
        for kind, stack, depth in [("web", "any", "product"), ("mobile", "native-both", "product"),
                                   ("data-ml", "any", "mvp"), ("research", "any", "research")]:
            a = gen.normalize({**BASE, "kind": kind, "stack": stack, "depth": depth})
            problems, _ = gen.check(gen.render(a))
            self.assertEqual(problems, [], (kind, depth))


# ---------------------------------------------------------------- adopt: TeamKit into an existing project (nothing that exists may break)

def git(folder, *args):
    res = subprocess.run(["git", *args], cwd=folder, capture_output=True, text=True, encoding="utf-8", env={**os.environ, **GIT_ENV})
    assert res.returncode == 0, res.stdout + res.stderr
    return res.stdout


def make_repo(tmp, files, symlinks=None, commit=True):
    """An existing project: a git repository root with the given files {path: bytes} (and symlinks {path: target}), committed."""
    repo = Path(tmp) / "existing"
    repo.mkdir()
    git(repo, "init", "-b", "master")
    for rel, data in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(data)
    for rel, target in (symlinks or {}).items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, repo / rel)
    if commit and (files or symlinks):
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "existing project")
    return repo


EXISTING = {
    "CLAUDE.md": b"# My own guidelines\r\n\r\nCustom rules, CRLF line ends.\r\n",
    "README.md": "# Existing\n\nUnicode: \u041f\u0440\u0438\u0432\u0456\u0442\n".encode("utf-8"),
    ".gitignore": b"node_modules/\n.env\n",
    "package.json": b'{"name": "mine"}\n',
    ".github/workflows/ci.yml": b"name: ci\r\n",
    "src/app.py": b"print('hello')\n",
}
ANSWERS = {"kind": "service", "stack": "python", "depth": "mvp", "mcp": False}


def run_cli(tmp, repo, *extra, **answers):
    """Run the CLI with --adopt (plus extra flags); return the finished process (not asserted)."""
    answers_file = Path(tmp) / "answers.json"
    answers_file.write_text(json.dumps({**BASE, **ANSWERS, **answers}))
    return subprocess.run([sys.executable, str(TOOLS / "new_project.py"), "--out", str(repo), "--answers", str(answers_file), "--adopt", *extra],
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **GIT_ENV, "GIT_CEILING_DIRECTORIES": str(Path(tmp))})   # git must not find a repository above the temporary folder


def run_undo(tmp, repo):
    return subprocess.run([sys.executable, str(TOOLS / "new_project.py"), "--out", str(repo), "--undo-adopt"], capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **GIT_ENV, "GIT_CEILING_DIRECTORIES": str(Path(tmp))})


def snapshot(repo):
    """Every file (a symlink by its target, never followed) and every folder of the tree, .git excluded."""
    files, dirs = {}, set()
    for root, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for d in dirnames:
            p = Path(root) / d
            (files.__setitem__(p.relative_to(repo).as_posix(), "symlink:" + os.readlink(p)) if p.is_symlink() else dirs.add(p.relative_to(repo).as_posix()))
        for f in filenames:
            p = Path(root) / f
            files[p.relative_to(repo).as_posix()] = "symlink:" + os.readlink(p) if p.is_symlink() else p.read_bytes()
    return files, dirs


def adopted_rendered(**answers):
    return gen.render(gen.normalize({**BASE, **ANSWERS, **answers}))


class AdoptTest(unittest.TestCase):
    def test_existing_files_are_kept_byte_for_byte_and_only_allowlisted_new_files_appear(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            before, before_dirs = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            after, _ = snapshot(repo)
            for rel, data in before.items():
                self.assertEqual(after[rel], data, f"{rel} was changed")            # CLAUDE.md (CRLF), README.md, .gitignore, package.json, CI, the code: byte for byte
            added = set(after) - set(before)
            for rel in added:
                self.assertTrue(gen.adopt_allowed(rel), f"{rel} is outside the allowlist")
            rendered = adopted_rendered()
            expected = {r for r in rendered if gen.adopt_allowed(r) and r not in gen.NEVER_WRITTEN}
            self.assertEqual(added, expected | {gen.SECTION_FILE, gen.MANIFEST})
            for rel in expected:
                self.assertEqual(after[rel].decode("utf-8"), rendered[rel], rel)
            status = git(repo, "status", "--porcelain").splitlines()
            self.assertTrue(status and all(line.startswith("??") for line in status), status)      # only new files: nothing modified, nothing deleted
            self.assertEqual(git(repo, "diff").strip(), "")                                      # `git diff` is empty: no tracked file changed
            for rel in ("CLAUDE.md", "README.md", ".gitignore"):
                self.assertIn(f"= {rel}", res.stdout)
            self.assertIn("git status", res.stdout)
            self.assertIn("NEW BRANCH", res.stdout)                                               # the owner is told to work on a new branch and to look at git status

    def test_the_project_files_that_adopt_never_writes_stay_unwritten_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, {"src/app.py": b"x\n"})
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            after, _ = snapshot(repo)
            for never in ("CLAUDE.md", "README.md", ".gitignore", ".scratch/README.md"):
                self.assertNotIn(never, after, never)
            section = after[gen.SECTION_FILE].decode("utf-8")
            for heading in ("## Team", "## Session memory (mandatory)", "## Documentation", "## Rules by kind and depth"):
                self.assertIn(heading, section)
            self.assertIn("Service:", section)
            self.assertNotIn("<<", section)
            self.assertIn("Not written in adopt mode", res.stdout)
            self.assertIn("create one with at least", res.stdout)                                # no .gitignore: the lines TeamKit needs are named

    def test_the_owners_own_docs_folders_are_kept_byte_for_byte_even_where_a_teamkit_name_collides(self):
        own = {"docs/guide.md": b"my guide\r\n", "docs/team/notes.md": b"team notes\n", "docs/delivery/CHANGELOG.md": b"my own changelog\r\n",
               "docs/delivery/AGENT_RULES.md": b"my own rules\n", "docs/delivery/PRODUCT_BRIEF.md": b"my own brief\r\n", "docs/team/AGENT_TEAM_RULES.md": b"my copy of a TeamKit file\n"}
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, {**EXISTING, **own})
            before, before_dirs = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            after, after_dirs = snapshot(repo)
            for rel in own:
                self.assertEqual(after[rel], before[rel], rel)
                if rel in adopted_rendered():
                    self.assertIn(f"= {rel}", res.stdout)                                       # a collision with a TeamKit file is listed as kept, merge by hand
            self.assertTrue(before_dirs <= after_dirs)
            self.assertIn("docs/team/roles/product.md", after)                                  # the files that did not exist were added around the owner's
            self.assertEqual(git(repo, "diff").strip(), "")

    def test_a_crlf_repository_and_non_ascii_file_names_are_untouched_and_seen_by_the_snapshot(self):
        files = {"\u0434\u043e\u043a.md": b"cyrillic name\r\n", "\u00fc file.txt": b"umlaut\r\n", "docs/\u043d\u043e\u0442\u0430\u0442\u043a\u0438.md": b"notes\r\n", "a b/c d.txt": b"spaces\r\n", **EXISTING}
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, files)
            git(repo, "config", "core.autocrlf", "true")
            hashes = gen.tree_hashes(repo)
            for rel in files:
                self.assertIn(rel, hashes, rel)                                                 # the names are read correctly (UTF-8, NUL-separated), so they are protected too
                self.assertNotEqual(hashes[rel], "not-a-file")
            before, _ = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            after, _ = snapshot(repo)
            for rel, data in before.items():
                self.assertEqual(after[rel], data, rel)

    def test_a_symlink_in_the_tree_is_neither_followed_nor_touched(self):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp, EXISTING, symlinks={"link.txt": "src/app.py", "linkdir": "src", "docs_link": "nowhere-at-all"})
                self._symlink_checks(tmp, repo)
        except OSError as exc:                                                                  # Windows without the privilege to create symlinks
            self.skipTest(f"symlinks are not available: {exc}")

    def _symlink_checks(self, tmp, repo):
        before, _ = snapshot(repo)
        hashes = gen.tree_hashes(repo)
        self.assertEqual(hashes["link.txt"], "symlink:src/app.py")                              # hashed by its target, not by the file behind it
        res = run_cli(tmp, repo)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        after, _ = snapshot(repo)
        for rel in ("link.txt", "linkdir", "docs_link"):
            self.assertEqual(after[rel], before[rel], rel)
        self.assertEqual(os.readlink(repo / "link.txt"), "src/app.py")
        self.assertEqual((repo / "src/app.py").read_bytes(), EXISTING["src/app.py"])

    def test_a_teamkit_path_that_is_a_symlink_is_kept_and_a_symlinked_folder_is_refused(self):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp, {"x.txt": b"x\n"}, symlinks={"project.yaml": "x.txt"})              # a symlink where TeamKit wants a file
                res = run_cli(tmp, repo)
                self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
                self.assertEqual(os.readlink(repo / "project.yaml"), "x.txt")                     # not followed, not replaced
                self.assertEqual((repo / "x.txt").read_bytes(), b"x\n")
                self.assertIn("= project.yaml", res.stdout)
            with tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp, {"elsewhere/keep.txt": b"k\n"}, symlinks={"docs": "elsewhere"})  # a symlinked FOLDER where TeamKit needs docs/
                before, _ = snapshot(repo)
                res = run_cli(tmp, repo)
                self.assertEqual(res.returncode, 1)
                self.assertIn("REFUSED docs is a symlink", res.stdout)
                self.assertEqual(snapshot(repo)[0], before)                                       # nothing written, nothing written THROUGH the link either
                self.assertFalse((repo / "elsewhere/team").exists())
        except OSError as exc:
            self.skipTest(f"symlinks are not available: {exc}")

    def test_a_file_where_a_folder_is_needed_refuses_the_whole_adoption_and_nothing_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, {"docs": b"a FILE named docs\n", "README.md": b"x\n"})
            before = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
            self.assertIn("REFUSED docs is a file", res.stdout)
            self.assertEqual(snapshot(repo), before)                                            # atomic: not even project.yaml or .claude/work_mode (which would have been fine alone)
            dry = run_cli(tmp, repo, "--dry-run")
            self.assertEqual(dry.returncode, 1)
            self.assertEqual(snapshot(repo), before)

    def test_a_dirty_tree_a_non_git_folder_a_subfolder_and_a_missing_folder_are_refused_and_nothing_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            (repo / "src/app.py").write_bytes(b"print('edited')\n")             # a modified tracked file
            before = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("not clean", res.stdout + res.stderr)
            self.assertEqual(snapshot(repo), before)
            (repo / "src/app.py").write_bytes(EXISTING["src/app.py"])
            (repo / "notes.txt").write_text("untracked", encoding="utf-8")        # an untracked file counts too
            self.assertNotEqual(run_cli(tmp, repo).returncode, 0)
            self.assertNotIn("docs/team/roles/product.md", snapshot(repo)[0])
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / "plain"
            plain.mkdir()
            (plain / "a.txt").write_text("x", encoding="utf-8")
            res = run_cli(tmp, plain)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("not a git repository", res.stdout + res.stderr)
            self.assertEqual(sorted(p.name for p in plain.iterdir()), ["a.txt"])
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            res = run_cli(tmp, repo / "src")
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("subfolder", res.stdout + res.stderr)
            res = run_cli(tmp, Path(tmp) / "nowhere")
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("not an existing folder", res.stdout + res.stderr)

    def test_dry_run_prints_the_plan_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            before = snapshot(repo)
            res = run_cli(tmp, repo, "--dry-run")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(snapshot(repo), before)
            self.assertEqual(git(repo, "status", "--porcelain").strip(), "")
            for part in ("New files", "Kept as they are", "Dry run: nothing written", gen.SECTION_FILE, "Blanks left to fill"):
                self.assertIn(part, res.stdout)
            line = next(l for l in res.stdout.splitlines() if "= .gitignore" in l)
            self.assertIn(".claude/sessions/", line)                                           # the lines the project's .gitignore lacks are named
            self.assertNotIn("node_modules/", line)

    def test_no_git_command_that_changes_anything_is_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            head, branches, count = git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--list"), git(repo, "rev-list", "--count", "HEAD")
            index = (repo / ".git" / "index").read_bytes()
            self.assertEqual(run_cli(tmp, repo).returncode, 0)
            self.assertEqual((git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--list"), git(repo, "rev-list", "--count", "HEAD")), (head, branches, count))
            self.assertEqual((repo / ".git" / "index").read_bytes(), index)                     # not even the index was refreshed: nothing was staged, nothing under .git was written

    def test_work_mode_and_project_yaml_are_written_only_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, {**EXISTING, ".claude/work_mode": b"auto\n", "project.yaml": b"name: mine\n"})
            self.assertEqual(run_cli(tmp, repo).returncode, 0)
            self.assertEqual((repo / ".claude/work_mode").read_bytes(), b"auto\n")
            self.assertEqual((repo / "project.yaml").read_bytes(), b"name: mine\n")
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            self.assertEqual(run_cli(tmp, repo).returncode, 0)
            self.assertEqual((repo / ".claude/work_mode").read_text(encoding="utf-8").strip(), "manual")
            self.assertEqual(json.loads((repo / "project.yaml").read_text(encoding="utf-8"))["work_mode"], "manual")

    def test_running_it_twice_in_a_row_writes_nothing_the_second_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            self.assertEqual(run_cli(tmp, repo).returncode, 0)
            mid = snapshot(repo)
            res = run_cli(tmp, repo)                                                            # uncommitted: the tree is not clean, so it is refused
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("not clean", res.stdout + res.stderr)
            self.assertEqual(snapshot(repo), mid)
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "adopt TeamKit")
            res = run_cli(tmp, repo)                                                            # committed: allowed, and there is nothing left to write
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertEqual(snapshot(repo), mid)
            self.assertIn("(0, plus the manifest", res.stdout)
            self.assertIn("Nothing to adopt", res.stdout)

    def test_the_hash_snapshot_undoes_the_run_when_an_existing_file_is_changed_during_it(self):
        """Fault injection: the writer also changes an existing file, deletes another, or drops an unexpected file. The run must fail, remove only what it wrote and restore nothing else."""
        import contextlib
        import io
        from unittest import mock
        real = gen.write_new

        def tamper(kind):
            def wrapper(files, out, created, made_dirs):
                real(files, out, created, made_dirs)
                if gen.MANIFEST in files:
                    return
                if kind == "change":
                    (out / "src/app.py").write_bytes(b"tampered\n")
                elif kind == "delete":
                    (out / "package.json").unlink()
                elif kind == "unexpected":
                    (out / "surprise.txt").write_text("not ours", encoding="utf-8")
            return wrapper

        for kind in ("change", "delete", "unexpected"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp, EXISTING)
                before, before_dirs = snapshot(repo)
                answers = Path(tmp) / "a.json"
                answers.write_text(json.dumps({**BASE, **ANSWERS}))
                buf = io.StringIO()
                with mock.patch.object(gen, "write_new", tamper(kind)), contextlib.redirect_stdout(buf):
                    code = gen.main(["--out", str(repo), "--answers", str(answers), "--adopt"])
                self.assertEqual(code, 1, kind)
                self.assertIn("ERROR", buf.getvalue())
                after, after_dirs = snapshot(repo)
                expected = dict(before)
                if kind == "change":
                    expected["src/app.py"] = b"tampered\n"                                       # nothing else is restored: the tampering stays visible for the owner
                elif kind == "delete":
                    del expected["package.json"]
                elif kind == "unexpected":
                    expected["surprise.txt"] = b"not ours"
                self.assertEqual(after, expected, kind)                                          # every file this run wrote is gone (the manifest was never written)
                self.assertEqual(after_dirs, before_dirs, kind)                                  # and so are the folders it created

    def test_the_manifest_lists_every_created_file_and_the_undo_restores_the_original_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            before, before_dirs = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            after, after_dirs = snapshot(repo)
            manifest = after[gen.MANIFEST].decode("utf-8")
            listed = [l.split(" ")[1] for l in manifest.splitlines() if l.startswith("file ")]
            self.assertEqual(set(listed), set(after) - set(before) - {gen.MANIFEST})           # every created file, nothing else
            self.assertEqual({l[4:] for l in manifest.splitlines() if l.startswith("dir ")}, after_dirs - before_dirs)
            self.assertNotIn(str(repo), manifest)                                               # no absolute path of the machine in a file that may be committed
            self.assertIn("--undo-adopt", res.stdout)                                           # the one command that undoes it is printed
            undo = run_undo(tmp, repo)
            self.assertEqual(undo.returncode, 0, undo.stdout + undo.stderr)
            self.assertEqual(snapshot(repo), (before, before_dirs))                             # the original files, hash for hash, and no folder left behind
            self.assertEqual(git(repo, "status", "--porcelain").strip(), "")
            again = run_undo(tmp, repo)
            self.assertNotEqual(again.returncode, 0)                                            # the manifest is gone: nothing to undo

    def test_the_undo_leaves_alone_a_file_that_was_changed_since_and_refuses_paths_outside_the_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            self.assertEqual(run_cli(tmp, repo).returncode, 0)
            (repo / "docs/team/START_PROMPTS.md").write_text("the owner edited this after the adoption\n", encoding="utf-8")
            manifest = (repo / gen.MANIFEST).read_text(encoding="utf-8")
            (repo / gen.MANIFEST).write_text(manifest + "file src/app.py " + "0" * 64 + "\nfile ../outside.txt " + "0" * 64 + "\nfile .git/config " + "0" * 64 + "\n", encoding="utf-8")
            outside = Path(tmp) / "outside.txt"
            outside.write_text("keep", encoding="utf-8")
            res = run_undo(tmp, repo)
            self.assertEqual(res.returncode, 1)
            self.assertIn("changed since the adoption", res.stdout)
            self.assertIn("not a path adopt mode writes", res.stdout)
            self.assertEqual((repo / "docs/team/START_PROMPTS.md").read_text(encoding="utf-8"), "the owner edited this after the adoption\n")
            self.assertEqual((repo / "src/app.py").read_bytes(), EXISTING["src/app.py"])
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep")
            self.assertTrue((repo / gen.MANIFEST).exists())                                     # kept: undo again after looking
            self.assertFalse((repo / "docs/team/roles").exists() and any((repo / "docs/team/roles").iterdir()))   # the unchanged files are gone

    def test_a_folder_that_is_a_separate_git_repository_is_never_written_into(self):
        """A submodule or nested repository at docs/ (or docs/team/): writing there would change ANOTHER repository."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, {"src/app.py": b"x\n"})
            nested = repo / "docs"
            nested.mkdir()
            git(nested, "init", "-b", "master")
            (nested / "inner.md").write_text("inner\n", encoding="utf-8")
            git(nested, "add", "-A")
            git(nested, "commit", "-m", "inner")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "with an embedded repository")
            before = snapshot(repo)
            inner_before = git(nested, "status", "--porcelain")
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
            self.assertIn("separate git repository", res.stdout)
            self.assertEqual(snapshot(repo), before)
            self.assertEqual(git(nested, "status", "--porcelain"), inner_before)

    def test_a_manifest_of_an_earlier_adoption_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, {**EXISTING, gen.MANIFEST: b"file docs/team/x.md abc\n"})
            before = snapshot(repo)
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 1)
            self.assertIn("of an earlier adoption", res.stdout)
            self.assertEqual(snapshot(repo), before)

    def test_a_directory_junction_or_symlink_pointing_outside_the_repository_is_refused_and_nothing_is_written_there(self):
        """RF-719: `docs` is a junction (Windows) or a symlink to a folder OUTSIDE the repository and git status is clean (the link is ignored): nothing may be written through it."""
        for kind in ("junction", "symlink"):
            with tempfile.TemporaryDirectory() as tmp:
                outside = Path(tmp) / "outside"
                outside.mkdir()
                (outside / "precious.txt").write_text("not yours", encoding="utf-8")
                repo = make_repo(tmp, {"src/app.py": b"x\n", ".gitignore": b"docs\n"})
                try:
                    if kind == "junction":
                        if sys.platform != "win32":
                            continue
                        made = subprocess.run(["cmd", "/c", "mklink", "/J", str(repo / "docs"), str(outside)], capture_output=True, text=True)
                        if made.returncode != 0:
                            self.skipTest("a junction cannot be created here")
                    else:
                        os.symlink(outside, repo / "docs", target_is_directory=True)
                except OSError as exc:
                    self.skipTest(f"links are not available: {exc}")
                self.assertEqual(git(repo, "status", "--porcelain").strip(), "")                # the link is ignored: the tree looks clean
                res = run_cli(tmp, repo)
                self.assertEqual(res.returncode, 1, kind + res.stdout + res.stderr)
                self.assertIn("REFUSED docs is", res.stdout)
                self.assertEqual(sorted(p.name for p in outside.iterdir()), ["precious.txt"], kind)      # nothing was written through the link
                self.assertFalse((repo / ".teamkit-adopt-manifest.txt").exists())

    def test_write_new_rechecks_every_parent_right_before_writing(self):
        """RF-719: a folder that becomes a link AFTER the plan must still be caught at the write."""
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside"
            outside.mkdir()
            repo = make_repo(tmp, {"src/app.py": b"x\n"})
            try:
                os.symlink(outside, repo / "docs", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks are not available: {exc}")
            created, made = [], []
            with self.assertRaises(gen.AdoptError):
                gen.write_new({"docs/team/x.md": "x"}, repo, created, made)
            self.assertEqual(list(outside.iterdir()), [])
            self.assertEqual(created, [])

    def test_ctrl_c_half_way_removes_what_was_written_and_a_killed_run_can_still_be_undone(self):
        """RF-720: KeyboardInterrupt at the 4th file must not leave files without a manifest; and the manifest is written FIRST, so even a run that is killed (no clean-up at all) can be undone."""
        import contextlib
        import io
        from unittest import mock
        real = gen.write_new

        def interrupt(files, out, created, made_dirs):
            if gen.MANIFEST in files:
                return real(files, out, created, made_dirs)
            real(dict(list(files.items())[:3]), out, created, made_dirs)
            raise KeyboardInterrupt()

        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            before = snapshot(repo)
            answers = Path(tmp) / "a.json"
            answers.write_text(json.dumps({**BASE, **ANSWERS}))
            buf = io.StringIO()
            with mock.patch.object(gen, "write_new", interrupt), contextlib.redirect_stdout(buf):
                code = gen.main(["--out", str(repo), "--answers", str(answers), "--adopt"])
            self.assertEqual(code, 130)
            self.assertIn("Interrupted", buf.getvalue())
            self.assertEqual(snapshot(repo), before)                                                  # 3 files, their folders and the manifest are gone
        with tempfile.TemporaryDirectory() as tmp:                                                    # the process is killed: no clean-up runs at all
            repo = make_repo(tmp, EXISTING)
            before = snapshot(repo)
            answers = Path(tmp) / "a.json"
            answers.write_text(json.dumps({**BASE, **ANSWERS}))
            with mock.patch.object(gen, "write_new", interrupt), mock.patch.object(gen, "rollback", lambda *a, **k: []), contextlib.redirect_stdout(io.StringIO()):
                gen.main(["--out", str(repo), "--answers", str(answers), "--adopt"])
            left, _ = snapshot(repo)
            self.assertIn(gen.MANIFEST, left)                                                         # the manifest exists although the run never finished
            self.assertTrue(set(left) - set(before[0]) - {gen.MANIFEST})                              # and so do the files that were written
            undo = run_undo(tmp, repo)
            self.assertEqual(undo.returncode, 0, undo.stdout + undo.stderr)
            self.assertEqual(snapshot(repo), before)                                                  # the undo finds them all: the tree is the original again

    def test_a_write_that_fails_half_way_on_the_second_call_removes_the_manifest_too(self):
        import contextlib
        import io
        from unittest import mock
        real = gen.write_new

        def failing(files, out, created, made_dirs):
            if gen.MANIFEST in files:
                return real(files, out, created, made_dirs)
            real(dict(list(files.items())[:4]), out, created, made_dirs)
            raise OSError("disk full")

        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            before = snapshot(repo)
            answers = Path(tmp) / "a.json"
            answers.write_text(json.dumps({**BASE, **ANSWERS}))
            buf = io.StringIO()
            with mock.patch.object(gen, "write_new", failing), contextlib.redirect_stdout(buf):
                code = gen.main(["--out", str(repo), "--answers", str(answers), "--adopt"])
            self.assertEqual(code, 1)
            self.assertIn("disk full", buf.getvalue())
            self.assertEqual(snapshot(repo), before)

    def test_the_undo_does_not_follow_a_parent_that_was_replaced_by_a_link(self):
        """RF-721: the folder docs/team is replaced by a link to a folder outside the repository that holds a file with the same name and the same bytes: the undo must not delete it."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp, EXISTING)
            self.assertEqual(run_cli(tmp, repo).returncode, 0)
            manifest = (repo / gen.MANIFEST).read_text(encoding="utf-8")
            line = next(l for l in manifest.splitlines() if l.startswith("file docs/team/START_PROMPTS.md "))
            same_bytes = (repo / "docs/team/START_PROMPTS.md").read_bytes()
            outside = Path(tmp) / "outside_team"
            outside.mkdir()
            (outside / "START_PROMPTS.md").write_bytes(same_bytes)
            shutil.rmtree(repo / "docs/team")
            try:
                if sys.platform == "win32":
                    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(repo / "docs/team"), str(outside)], capture_output=True, text=True)
                    if made.returncode != 0:
                        raise OSError("mklink failed")
                else:
                    os.symlink(outside, repo / "docs/team", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"links are not available: {exc}")
            res = run_undo(tmp, repo)
            self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
            self.assertIn("left alone", res.stdout)
            self.assertEqual((outside / "START_PROMPTS.md").read_bytes(), same_bytes)                 # the outside file is still there
            self.assertIn(line.split(" ")[1], res.stdout)

    def test_a_folder_that_differs_only_in_case_is_not_reported_as_unexpected_files(self):
        """RF-722 (case-insensitive file systems): the repository has `Docs/Team/notes.md`; the run writes `docs/team/...`, which git reports as `Docs/team/...`."""
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "Probe"
            probe.mkdir()
            if not (Path(tmp) / "probe").exists():
                self.skipTest("this file system is case-sensitive")
            repo = make_repo(tmp, {"Docs/Team/notes.md": b"mine\n", "src/app.py": b"x\n"})
            res = run_cli(tmp, repo)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertNotIn("unexpected", res.stdout)
            self.assertEqual((repo / "Docs/Team/notes.md").read_bytes(), b"mine\n")
            self.assertEqual(git(repo, "diff").strip(), "")

    def test_the_allowlist(self):
        for ok in ("docs/delivery/PRODUCT_BRIEF.md", "docs/team/x.md", "docs/team/roles/product.md", "docs/delivery/AGENT_RULES.md", "docs/discovery/README.md", ".claude/work_mode", "project.yaml", gen.MANIFEST):
            self.assertTrue(gen.adopt_allowed(ok), ok)
        for bad in (".git/config", ".git/hooks/pre-commit", "CLAUDE.md", "README.md", ".gitignore", "package.json", "pyproject.toml", "Makefile", ".github/workflows/ci.yml",
                    "docs/other/x.md", "docs/README.md", "src/app.py", ".claude/settings.json", ".scratch/README.md", "../docs/team/x.md", "docs/team/../../x", "/etc/passwd",
                    "docs\\team\\x.md", "C:/x", "docs/team//x.md", "", "docs/team/.git/x"):
            self.assertFalse(gen.adopt_allowed(bad), bad)

    def test_everything_adopt_plans_to_write_is_allowlisted_for_every_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind, stack, depth, extra in (("web", "react", "product", {"stage": True}), ("mobile", "native-both", "mvp", {}), ("research", "any", "research", {"tracker": "backlog"})):
                repo = Path(tmp) / f"r-{kind}"
                repo.mkdir()
                git(repo, "init", "-b", "master")
                (repo / "a.txt").write_text("x", encoding="utf-8")
                git(repo, "add", "-A")
                git(repo, "commit", "-m", "c")
                a = gen.normalize({**BASE, "kind": kind, "stack": stack, "depth": depth, **extra})
                new, kept, skipped, refusals = gen.adopt_plan(gen.render(a), repo)
                self.assertEqual(refusals, [])
                self.assertTrue(new and all(gen.adopt_allowed(r) for r in new), [r for r in new if not gen.adopt_allowed(r)])
                self.assertTrue(all(r in gen.NEVER_WRITTEN or not gen.adopt_allowed(r) for r in skipped), skipped)      # what is not written is the project's own file or outside the allowlist
                self.assertTrue({"CLAUDE.md", "README.md", ".gitignore"} <= set(skipped))


class AdoptSkillTextTest(unittest.TestCase):
    """The adopt skill is text an agent follows: its claims about the generator must stay true (RF-724..727)."""

    def setUp(self):
        self.skill = (gen.ROOT / "skills" / "adopt" / "SKILL.md").read_text(encoding="utf-8")

    def test_the_values_the_skill_lists_are_the_generators_values(self):
        for value in gen.KINDS + gen.MOBILE_STACKS + gen.TRACKERS + gen.DEPTHS + gen.DOC_LEVELS + ["public", "private"]:
            self.assertIn(f"`{value}`", self.skill, value)

    def test_early_stages_with_code_are_not_mapped_to_the_research_team_and_there_is_no_invented_adoption_level(self):
        self.assertNotRegex(self.skill, r"idea, experiment, proof of concept: `research`")
        self.assertNotIn("Adoption level", self.skill)
        self.assertIn("ONLY for a repository that has no code", self.skill)
        self.assertIn("a `research` team never has a stage", self.skill.replace("A `research`", "a `research`"))

    def test_the_skill_keeps_secrets_out_of_the_transcript_and_deletes_the_answers_file_at_every_stop(self):
        self.assertIn("Never open the contents", self.skill)
        self.assertIn("git grep -l", self.skill)
        self.assertIn("deleted at every stop", self.skill)
        self.assertIn("`answers:` error", self.skill)
        self.assertIn("only after he has said \"make it\"", self.skill)

    def test_the_answers_keys_the_skill_writes_are_the_ones_the_generator_reads(self):
        for key in ("name", "kind", "stack", "depth", "visibility", "tracker", "language", "docs", "mcp", "stage", "extra_roles", "work_mode"):
            self.assertIn(f"`{key}`", self.skill, key)
        answers = gen.normalize({**BASE, "kind": "service", "stack": "python", "depth": "mvp", "docs": "light", "mcp": False, "stage": True, "extra_roles": [], "work_mode": "manual"})
        self.assertIn("qa", gen.pick_roles(answers))                                                # an MVP with a stage gets the QA role: the stage flag is its own answer
        research = gen.normalize({**BASE, "kind": "service", "stack": "python", "depth": "research", "stage": True})
        self.assertFalse(research["stage"])                                                         # and research drops it, which is why the skill never proposes both
        self.assertNotIn("backend", gen.pick_roles(research))



class OutModeUnchangedTest(unittest.TestCase):
    def test_a_non_empty_out_is_still_refused_without_adopt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            out.mkdir()
            (out / "keep.txt").write_text("x", encoding="utf-8")
            answers = Path(tmp) / "a.json"
            answers.write_text(json.dumps({**BASE, "kind": "web", "depth": "mvp"}))
            res = subprocess.run([sys.executable, str(TOOLS / "new_project.py"), "--out", str(out), "--answers", str(answers)], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("exists and is not empty", res.stdout + res.stderr)
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["keep.txt"])

    def test_an_empty_out_still_gets_the_project_and_the_first_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="web", stack="react", depth="mvp")
            self.assertIn("start from TeamKit", subprocess.run(["git", "log", "--oneline"], cwd=out, capture_output=True, text=True).stdout)


if __name__ == "__main__":
    unittest.main()
