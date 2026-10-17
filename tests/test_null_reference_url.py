import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from specifications import validate_profiles, counts_html, resource_profile_html
from search_pages import resource_markdown

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return copy.deepcopy(next(row for row in map(json.loads, (ROOT / "data/catalog.jsonl").read_text().splitlines()) if row["id"] == "github:xlang-ai/osworld"))


class NullReferenceUrlTests(unittest.TestCase):
    def test_null_reference_url_is_rejected_like_the_schema(self):
        import jsonschema
        validator = jsonschema.Draft202012Validator(json.loads((ROOT / "schemas/resource.schema.json").read_text()))
        row = fixture()
        self.assertEqual(validate_profiles(row), [])
        self.assertEqual(list(validator.iter_errors(row)), [])
        row["details"]["benchmark_protocol"]["counts"][0]["reference_url"] = None
        self.assertIn("benchmark_protocol count has an invalid readable source link", validate_profiles(row))
        self.assertTrue(list(validator.iter_errors(row)))

    def test_renderers_fall_back_to_evidence_url(self):
        row = fixture()
        count = row["details"]["benchmark_protocol"]["counts"][0]
        for value in [None, ""]:
            with self.subTest(reference_url=value):
                count["reference_url"] = value
                html = counts_html(row["details"]["benchmark_protocol"])
                self.assertNotIn('href="None"', html)
                self.assertNotIn('href=""', html)
                self.assertIn(f'href="{count["evidence_url"]}"', html)
                self.assertNotIn('href="None"', resource_profile_html(row))
                markdown = resource_markdown(row)
                self.assertNotIn("source: None", markdown)
                self.assertIn(f'source: {count["evidence_url"]})', markdown)
        count["reference_url"] = "https://arxiv.org/abs/2404.07972"
        self.assertIn('href="https://arxiv.org/abs/2404.07972"', counts_html(row["details"]["benchmark_protocol"]))
        self.assertIn("source: https://arxiv.org/abs/2404.07972)", resource_markdown(row))


if __name__ == "__main__":
    unittest.main()
