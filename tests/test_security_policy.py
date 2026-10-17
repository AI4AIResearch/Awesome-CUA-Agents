from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_pages import CLONE_COMMAND


class SecurityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = (ROOT / "SECURITY.md").read_text()

    def test_reports_go_to_private_vulnerability_reporting(self):
        repo = CLONE_COMMAND.split()[-1].removesuffix(".git")
        self.assertIn(repo + "/security/advisories/new", self.policy)
        for heading in ("## Scope", "## Reporting a vulnerability", "## What to include", "## What to expect"):
            self.assertIn(heading, self.policy)

    def test_scope_names_only_existing_paths(self):
        paths = [p for p in re.findall(r"`([\w./-]+)`", self.policy) if "/" in p or "." in p]
        self.assertIn("automation/publish.yml", paths)
        for path in paths:
            self.assertTrue((ROOT / path).exists(), path)

    def test_contributing_points_reporters_to_the_policy(self):
        self.assertIn("[SECURITY.md](SECURITY.md)", (ROOT / "CONTRIBUTING.md").read_text())


if __name__ == "__main__":
    unittest.main()
