from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github/workflows").glob("*.yml")) + [ROOT / "automation/publish.yml"]
PIN = re.compile(r"uses: ([\w.-]+/[\w./-]+)@(\S+)(?: # (\S+))?")


def pins(path):
    return PIN.findall(path.read_text())


class ActionPinTests(unittest.TestCase):
    def test_actions_are_pinned_to_a_commit_named_by_its_exact_tag(self):
        for path in WORKFLOWS:
            self.assertTrue(pins(path), path.name)
            for action, ref, tag in pins(path):
                with self.subTest(workflow=path.name, action=action):
                    self.assertRegex(ref, r"^[0-9a-f]{40}$")
                    self.assertRegex(tag, r"^v\d+\.\d+\.\d+$")

    def test_publish_workflow_shares_pins_with_the_watched_workflows(self):
        # Dependabot's grouped bump covers both directories; a hand edit to one workflow must be copied to the others.
        found = {}
        for path in WORKFLOWS:
            for action, ref, tag in pins(path):
                found.setdefault(action, set()).add((ref, tag))
        for action, refs in found.items():
            self.assertEqual(len(refs), 1, f"{action}: {sorted(refs)}")

    def test_dependabot_updates_actions_in_one_group_and_python_requirements(self):
        updates = {block.split("\n", 1)[0].strip(): block for block in (ROOT / ".github/dependabot.yml").read_text().split("- package-ecosystem:")[1:]}
        self.assertEqual(sorted(updates), ["github-actions", "pip"])
        for block in updates.values():
            self.assertIn("interval: weekly", block)
        self.assertIn('directories: ["/", "/automation"]\n', updates["github-actions"])
        self.assertIn("directory: /\n", updates["pip"])
        self.assertRegex(updates["github-actions"], r'groups:\n +[\w-]+:\n +patterns: \["\*"\]')
        self.assertTrue((ROOT / "requirements-dev.txt").exists())


if __name__ == "__main__":
    unittest.main()
