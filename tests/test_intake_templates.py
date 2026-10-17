from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORMS = ROOT / ".github/ISSUE_TEMPLATE"


class IntakeTemplateTests(unittest.TestCase):
    def test_issue_forms_set_title_and_existing_label(self):
        # Labels must already exist in the repository; GitHub silently drops unknown ones.
        known = {"area:data", "bug"}
        for path in sorted(set(FORMS.glob("*.yml")) - {FORMS / "config.yml"}):
            text = path.read_text()
            self.assertRegex(text, r'(?m)^title: "\[\w+\] "$', path.name)
            labels = re.search(r"(?m)^labels: \[(.*)\]$", text)
            self.assertIsNotNone(labels, path.name)
            self.assertLessEqual({l.strip(' "') for l in labels.group(1).split(",")}, known, path.name)

    def test_resource_form_asks_for_request_type(self):
        text = (FORMS / "resource.yml").read_text()
        intent = re.search(r"- type: dropdown\n    id: intent\n(.*?)\n  - type:", text, re.S)
        self.assertIsNotNone(intent)
        self.assertEqual(re.findall(r"(?m)^        - (.+)$", intent.group(1)), ["New resource", "Missing asset", "Correction"])
        self.assertIn("    validations:\n      required: true", intent.group(1))
        self.assertIn("candidates.jsonl", text)

    def test_chooser_has_no_blank_issues_and_https_contact_links(self):
        text = (FORMS / "config.yml").read_text()
        self.assertIn("blank_issues_enabled: false", text)
        self.assertTrue((FORMS / "bug.yml").exists())
        urls = re.findall(r"url: (\S+)", text)
        self.assertTrue(urls)
        self.assertTrue(all(u.startswith("https://") for u in urls))

    def test_pull_request_checklist_runs_every_ci_check(self):
        checklist = (ROOT / ".github/pull_request_template.md").read_text()
        runs = re.findall(r"(?m)^ +run: (python (?!-m pip).*|node .*)$", (ROOT / ".github/workflows/catalog.yml").read_text())
        self.assertGreaterEqual(len(runs), 5)
        for command in runs:
            self.assertIn(re.sub(r"^python ", "python3 ", command).removesuffix(" -v"), checklist)
        self.assertIn("reviewed_sha256", checklist)


if __name__ == "__main__":
    unittest.main()
