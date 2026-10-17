import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "scan.yml"


def block(lines, start):
    indent = len(lines[start]) - len(lines[start].lstrip())
    body = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    return textwrap.dedent("\n".join(body)).strip("\n") + "\n"


def step_script(name):
    lines = WORKFLOW.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"- name: {name}")
    return block(lines, next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "run: |"))


def section(*path):
    lines = WORKFLOW.read_text().splitlines()
    start, end = -1, len(lines)
    for depth, key in enumerate(path):
        prefix = "  " * depth + key + ":"
        start = next(i for i in range(start + 1, end) if lines[i] == prefix or lines[i].startswith(prefix + " "))
        end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) <= 2 * depth), len(lines))
    return lines[start].split(":", 1)[1].strip() or block(lines, start)


class ScanWorkflowTests(unittest.TestCase):
    def test_scan_runs_the_catalog_quality_gate_and_site_build_before_committing(self):
        check = step_script("Check generated data and review boundaries")
        for command in ["python scripts/catalog.py validate", "python scripts/catalog.py build --check",
                        "python -m unittest discover -s tests -v", "node --test tests/web.test.mjs", "python scripts/build_site.py"]:
            self.assertIn(command, check)

    def test_only_the_dispatch_job_can_write_actions(self):
        self.assertEqual(section("permissions"), "{}")
        self.assertEqual(section("jobs", "scan", "permissions"), "contents: write\n")
        self.assertEqual(section("jobs", "scan", "outputs"), "pushed: ${{ steps.commit.outputs.pushed }}\n")
        self.assertEqual(section("jobs", "dispatch_quality", "needs"), "scan")
        self.assertEqual(section("jobs", "dispatch_quality", "if"), "needs.scan.outputs.pushed == 'true'")
        self.assertEqual(section("jobs", "dispatch_quality", "permissions"), "actions: write\n")
        steps = section("jobs", "dispatch_quality", "steps")
        self.assertNotIn("uses:", steps)
        self.assertEqual(steps.count("- name:"), 1)
        self.assertIn("GH_TOKEN: ${{ github.token }}", steps)
        self.assertIn('run: gh workflow run catalog.yml --ref main -R "$GITHUB_REPOSITORY"', steps)
        self.assertEqual(WORKFLOW.read_text().count("actions: write"), 1)


class ScanCommitStepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org", "GIT_COMMITTER_NAME": "t",
                    "GIT_COMMITTER_EMAIL": "t@example.org", "GH_LOG": str(base / "gh.log"), "GITHUB_OUTPUT": str(base / "output")}
        (base / "bin").mkdir()
        gh = base / "bin" / "gh"
        gh.write_text('#!/bin/sh\necho "$@" >> "$GH_LOG"\n')
        gh.chmod(0o755)
        self.env["PATH"] = f"{base / 'bin'}{os.pathsep}{os.environ['PATH']}"
        self.origin, self.work = base / "origin.git", base / "work"
        self.git("init", "-q", "--bare", "-b", "main", str(self.origin), cwd=base)
        self.git("init", "-q", "-b", "main", str(self.work), cwd=base)
        for path, text in {".gitignore": "dist/\n", "data/catalog.jsonl": "{}\n", "docs/papers.md": "# Papers\n",
                           "README.md": "readme\n", "README.zh-CN.md": "readme\n", "scripts/build.py": "pass\n"}.items():
            (self.work / path).parent.mkdir(parents=True, exist_ok=True)
            (self.work / path).write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", "Initial")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "origin", "HEAD:main")
        self.initial = self.origin_head()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.work, env=self.env, check=True, capture_output=True, text=True).stdout

    def origin_head(self):
        return self.git("--git-dir", str(self.origin), "rev-parse", "main").strip()

    def run_step(self):
        result = subprocess.run(["bash", "-e", "-c", step_script("Commit verified scan output")], cwd=self.work,
                                env=self.env, capture_output=True, text=True)
        gh, output = Path(self.env["GH_LOG"]), Path(self.env["GITHUB_OUTPUT"])
        return result, (gh.read_text() if gh.exists() else "") + (output.read_text() if output.exists() else "")

    def test_commits_scan_paths_and_reports_the_push(self):
        (self.work / "data" / "catalog.jsonl").write_text('{"id":"x"}\n')
        (self.work / "dist" / "site").mkdir(parents=True)
        (self.work / "dist" / "site" / "index.html").write_text("ignored build output\n")
        result, effects = self.run_step()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotEqual(self.origin_head(), self.initial)
        self.assertEqual(effects, "pushed=true\n")

    def test_refuses_tracked_change_outside_committed_paths(self):
        (self.work / "data" / "catalog.jsonl").write_text('{"id":"x"}\n')
        (self.work / "scripts" / "build.py").write_text("raise SystemExit\n")
        result, effects = self.run_step()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scripts/build.py", result.stdout)
        self.assertEqual((self.origin_head(), effects), (self.initial, ""))

    def test_refuses_untracked_file_outside_committed_paths(self):
        (self.work / "data" / "catalog.jsonl").write_text('{"id":"x"}\n')
        (self.work / "schemas").mkdir()
        (self.work / "schemas" / "new.schema.json").write_text("{}\n")
        result, effects = self.run_step()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("schemas/new.schema.json", result.stdout)
        self.assertEqual((self.origin_head(), effects), (self.initial, ""))

    def test_unchanged_scan_neither_commits_nor_reports_a_push(self):
        result, effects = self.run_step()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.origin_head(), effects), (self.initial, ""))


if __name__ == "__main__":
    unittest.main()
