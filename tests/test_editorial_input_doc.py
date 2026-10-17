import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog import ENVIRONMENTS, KINDS, canonical

DOC = ROOT / "docs" / "editorial-input.md"


def documented_fields(text):
    return [m.group(1) for m in re.finditer(r"^\| `(\w+)` \|", text, re.M)]


class EditorialInputDocTests(unittest.TestCase):
    def setUp(self):
        self.text = DOC.read_text()
        self.fields = documented_fields(self.text)

    def test_every_editorial_key_is_documented_once(self):
        used = {key for row in json.loads((ROOT / "data" / "editorial.json").read_text()) for key in row}
        self.assertEqual(len(self.fields), len(set(self.fields)))
        self.assertEqual(sorted(used - set(self.fields)), [])
        source = (ROOT / "scripts" / "build.py").read_text() + (ROOT / "scripts" / "catalog.py").read_text()
        stale = [key for key in self.fields if key not in used and f'"{key}"' not in source and f"'{key}'" not in source]
        self.assertEqual(stale, [])

    def test_examples_are_valid_editorial_entries(self):
        examples = [json.loads(block) for block in re.findall(r"^```json\n(.*?)^```", self.text, re.S | re.M)]
        self.assertEqual(len(examples), 3)
        for example in examples:
            with self.subTest(example["name"]):
                self.assertEqual(sorted(set(example) - set(self.fields)), [])
                self.assertLessEqual({"name", "kind", "url", "environments", "topics", "summary", "editorial_reviewed"}, set(example))
                self.assertIn(example["kind"], KINDS)
                self.assertLessEqual(set(example["environments"]), ENVIRONMENTS)
                self.assertIsNotNone(canonical(example["url"]))
        self.assertEqual(canonical(examples[0]["url"])[0], "github:xlang-ai/osworld")
        self.assertTrue(canonical(examples[1]["url"])[0].startswith("url:"))
        self.assertTrue(examples[2]["id"].startswith("component:"))

    def test_documented_id_command_prints_the_documented_id(self):
        command, expected = re.search(r"^(python3 -c .*)\n# (\S+)$", self.text, re.M).groups()
        argv = shlex.split(command)
        self.assertEqual(argv[:2], ["python3", "-c"])
        output = subprocess.run([sys.executable, *argv[1:]], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(output, expected)

    def test_contributing_uses_the_real_keys_and_links_the_contract(self):
        contributing = (ROOT / "CONTRIBUTING.md").read_text()
        for key in ["`environments`", "`verify_terms`", "`reviewed_sha256`", "`reviewed_at`", "(docs/editorial-input.md)"]:
            self.assertIn(key, contributing)
        self.assertIn("informational", self.text[self.text.index("| `reviewed_at`"):].splitlines()[0].lower())


if __name__ == "__main__":
    unittest.main()
