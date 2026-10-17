import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog import KINDS

DOC = ROOT / "docs" / "data-dictionary.md"
ROW = re.compile(r"^\| `(\w+)` \| ([^|]+) \| (.+) \| ([^|]+) \|$", re.M)


class DetailsDictionaryTests(unittest.TestCase):
    def setUp(self):
        self.text = DOC.read_text(encoding="utf-8")
        self.section = self.text.split("\n## Kind-specific details\n", 1)[1].split("\n## ", 1)[0]
        self.rows = {m[1]: ({k.strip() for k in m[2].split(",")}, m[3], m[4]) for m in ROW.finditer(self.section)}
        self.source = {name: (ROOT / "scripts" / name).read_text(encoding="utf-8") for name in ("build.py", "catalog.py")}

    def test_every_catalog_details_key_is_documented_once_with_its_kinds(self):
        self.assertEqual(len(ROW.findall(self.section)), len(self.rows))
        used = {}
        for line in (ROOT / "data" / "catalog.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            for key in row.get("details") or {}:
                used.setdefault(key, set()).add(row["kind"])
        self.assertEqual(sorted(set(used) - set(self.rows)), [])
        for key, kinds in used.items():
            with self.subTest(key):
                self.assertLessEqual(kinds, self.rows[key][0])
        for key, (kinds, _, _) in self.rows.items():
            with self.subTest(key):
                self.assertLessEqual(kinds, KINDS)
        source = "".join(self.source.values())
        stale = [key for key in self.rows if key not in used and f'"{key}"' not in source and f"'{key}'" not in source]
        self.assertEqual(stale, [])

    def test_origins_match_build_and_enrich(self):
        self.assertEqual({key for key, row in self.rows.items() if "placeholder" in row[2].lower()}, set())
        hub = re.search(r'result\["details"\] = \{(.*?)\}\n', self.source["catalog.py"], re.S).group(1)
        hub_keys = set(re.findall(r'"(\w+)": ', hub))
        self.assertIn("hub_id", hub_keys)
        self.assertEqual({key for key, row in self.rows.items() if "Hub API" in row[2]}, hub_keys)
        self.assertIn('result["details"]["dataverse"]', self.source["catalog.py"])
        self.assertEqual(self.rows["dataverse"][2], "Dataverse API")
        self.assertEqual(self.rows["license_review"][2], "License review")

    def test_legacy_flat_fields_defer_to_profile_counts(self):
        paragraph = next(p for p in self.section.split("\n\n") if p.startswith("The flat "))
        for key in ("sample_count", "task_count"):
            self.assertIn(f"`{key}`", paragraph)
        self.assertIn("legacy editorial fields", paragraph)
        self.assertIn("no null or empty placeholders", paragraph)
        self.assertIn("authoritative quantities are the `counts` in `dataset_profile` and `benchmark_protocol`", paragraph)

    def test_structured_details_link_their_detailed_docs(self):
        self.assertIn("[kind-specific details](#kind-specific-details)", self.text.split("| `details` |", 1)[1].splitlines()[0])
        for key in ("dataset_profile", "benchmark_protocol"):
            self.assertIn("(specifications.md)", self.rows[key][1])
        self.assertIn("(methodology.md#paper-versions-and-revision-proposals)", self.rows["arxiv_snapshot"][1])
        self.assertIn("\n## Paper versions and revision proposals\n", (ROOT / "docs" / "methodology.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
