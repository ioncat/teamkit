"""End-to-end tests of the generator (python -m unittest discover tools/tests)."""
import json
import os
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

    def test_logic_checker_is_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = generate(tmp, kind="web", stack="react", depth="product")
            self.assert_clean(out)
            for gone in ("docs/team/roles/logic-checker.md", "docs/delivery/roles/logic-checker.md", "docs/delivery/LOGIC_FINDINGS.md"):
                self.assertFalse((out / gone).exists(), gone)
            self.assertNotIn("logic checker", (out / "docs/delivery/AGENT_RULES.md").read_text(encoding="utf-8").lower())
        for extra in (["logic-checker"], ["analyst"]):  # "analyst" is the pre-0.4.2 name of the check
            with tempfile.TemporaryDirectory() as tmp:
                out = generate(tmp, kind="web", stack="react", depth="product", extra_roles=extra)
                self.assert_clean(out)
                for kept in ("docs/team/roles/logic-checker.md", "docs/delivery/roles/logic-checker.md", "docs/delivery/LOGIC_FINDINGS.md"):
                    self.assertTrue((out / kept).exists(), kept)
                self.assertIn("roles/logic-checker.md", (out / "docs/delivery/AGENT_RULES.md").read_text(encoding="utf-8"))
                self.assertIn("`Logic Checker`", (out / "docs/team/START_PROMPTS.md").read_text(encoding="utf-8"))
                self.assertIn("logic-checker", json.loads((out / "project.yaml").read_text())["roles"])

    def test_business_analyst_writes_the_tasks_everywhere(self):
        """The business analyst is in every preset (research included): it writes the issues, the CTO no longer does."""
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
                self.assertIn("the **business analyst** creates issues", rules)

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
        """The product agent is in every preset and comes first: the owner talks to it, it calls the CTO."""
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
            out = generate(tmp, kind="web", stack="react", depth="product")  # product: qa and qa-web
            self.assertTrue((out / "docs/team/roles/qa.md").exists())
            self.assertTrue((out / "docs/team/roles/qa-web.md").exists())
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


if __name__ == "__main__":
    unittest.main()
