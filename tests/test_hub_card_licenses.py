import contextlib
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog


class CardLicenseTests(unittest.TestCase):
    def test_reads_scalar_quoted_commented_and_list_forms(self):
        cases = {
            "---\nlicense: mit\n---\nCard": "mit",
            "---\r\npretty_name: DroidCall\r\nlicense: apache-2.0\r\n---\r\nCard": "apache-2.0",
            "---\nlicense: mit                                    # update if needed\n---\nCard": "mit",
            "---\nlicense: \"cc-by-4.0\"\n---\nCard": "cc-by-4.0",
            "---\nlicense: 'other'\n---\nCard": "other",
            "---\nlicense: [mit, cc-by-4.0]\n---\nCard": ["mit", "cc-by-4.0"],
            "---\nlicense:\n- mit\n- cc-by-nc-4.0\ntags:\n- agent\n---\nCard": ["mit", "cc-by-nc-4.0"],
            "---\nlicense:\n  - apache-2.0  # weights\n---\nCard": ["apache-2.0"],
        }
        for card, expected in cases.items():
            with self.subTest(card=card):
                self.assertEqual(catalog.card_license(card), expected)

    def test_ignores_prose_nested_keys_and_unparseable_values(self):
        for card in ("# Card\nlicense: mit", "---\nlicense:\n---\nCard", "---\nlicense: see the LICENSE file\n---", "---\nfoo:\n  license: mit\n---",
                     "---\nlicense: []\n---", "---\nlicense: [mit, see below]\n---", "---\ntags:\n- mit\n---\nlicense: mit"):
            with self.subTest(card=card):
                self.assertIsNone(catalog.card_license(card))


class HubCardSlotTests(unittest.TestCase):
    def enrich(self, kind, url, card):
        primary = url + "/raw/main/README.md"
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(catalog, "DATA", Path(directory)):
            catalog.write_json(Path(directory) / "editorial.json", [{"url": url, "kind": kind, "name": "Example"}])
            catalog.write_jsonl(Path(directory) / "primary-evidence.jsonl", [{"id": catalog.canonical(url)[0], "url": primary, "content_matched": True,
                "sha256": hashlib.sha256(card).hexdigest(), "retrieved_at": "2026-10-17T00:00:00Z"}])
            with mock.patch.object(catalog, "cached_body", side_effect={primary: card}.get), \
                    mock.patch.object(catalog, "fetch", side_effect=AssertionError("Unexpected network request")), contextlib.redirect_stdout(io.StringIO()):
                catalog.enrich(types.SimpleNamespace(refresh=False))
            row, = catalog.read_jsonl(Path(directory) / "enrichment.jsonl")
        return {slot: value["declared"] for slot, value in row["licenses"].items()}, row["evidence"]

    def test_benchmark_hosted_as_a_hub_dataset_fills_the_data_slot(self):
        licenses, evidence = self.enrich("benchmark", "https://huggingface.co/datasets/example/bench", b"---\nlicense: mit\n---\nBenchmark card")
        self.assertEqual(licenses, {"data": "mit"})
        self.assertEqual([(e["method"], e["supports"]) for e in evidence], [("huggingface_card", ["licenses.data"])])

    def test_crlf_and_commented_cards_are_read(self):
        self.assertEqual(self.enrich("dataset", "https://huggingface.co/datasets/example/data", b"---\r\nlicense: apache-2.0\r\n---\r\nCard")[0], {"data": "apache-2.0"})
        self.assertEqual(self.enrich("model", "https://huggingface.co/example/model", b"---\nlicense: mit    # update if needed\n---\nCard")[0], {"weights": "mit"})

    def test_model_repository_card_fills_weights_only_for_a_model(self):
        for kind in ("framework", "infrastructure", "benchmark"):
            with self.subTest(kind=kind):
                self.assertEqual(self.enrich(kind, "https://huggingface.co/example/repo", b"---\nlicense: mit\n---\nCard"), ({}, []))


class DeclaredLicenseRecordTests(unittest.TestCase):
    def test_card_declarations_fill_their_slots(self):
        records = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "catalog.jsonl")}
        expected = {"url:3b6dfd52f98bfe76bc7f": ("data", "mit"), "url:d5140d438466c1e1348a": ("data", "mit"),
            "url:ae8f5208eea9e7f1f606": ("data", "apache-2.0"), "url:3932d69c6b6f9b2a7ba8": ("weights", "mit")}
        for rid, (slot, declared) in expected.items():
            with self.subTest(rid):
                record = records[rid]
                license_info = record["licenses"][slot]
                self.assertEqual(license_info["declared"], declared)
                self.assertTrue(license_info["url"].endswith("/raw/main/README.md"))
                self.assertTrue(any(ev["url"] == license_info["url"] and "licenses." + slot in ev["supports"] for ev in record["evidence"]))


if __name__ == "__main__":
    unittest.main()
