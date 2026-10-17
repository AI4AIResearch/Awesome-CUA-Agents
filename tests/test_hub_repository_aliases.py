import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog
from repository_identity import attach_repository_aliases, hub_identity, hub_path, repository_aliases, unrecorded_hub_renames

OBJECT = "6616a35f75f203eb75e90f03"
# The catalog record keeps the former path; the Hub API now answers both paths with the new id.
FORMER, CURRENT = "datasets/rootsautomation/ScreenSpot", "datasets/bevaya/ScreenSpot"


def observation(path, current=CURRENT, rid=OBJECT):
    api = lambda p: "https://huggingface.co/api/" + (p if p.startswith("datasets/") else "models/" + p)
    return {"url": api(path), "resolved_url": api(current), "repository_id": rid, "full_name": current.removeprefix("datasets/"),
        "html_url": "https://huggingface.co/" + current, "retrieved_at": "2026-10-17T00:01:00Z", "sha256": "a" * 64}


def declaration(alias=CURRENT, target=FORMER, current=CURRENT):
    return {"alias_id": hub_identity(alias), "target_id": hub_identity(target), "repository_id": OBJECT, "basis": "official_huggingface_repository_id",
        "reviewed_at": "2026-10-17T00:02:00Z", "observations": [observation(alias, current), observation(target, current)]}


def record(path=FORMER):
    return {"id": hub_identity(path), "url": "https://huggingface.co/" + path, "name": "ScreenSpot", "review_status": "curated", "scope": "core",
        "aliases": [], "evidence": [], "details": {"hub_id": CURRENT.removeprefix("datasets/")}}


class HubRepositoryAliasTests(unittest.TestCase):
    def test_hub_ids_are_the_catalog_ids_of_each_spelling(self):
        for path in (FORMER, CURRENT, "microsoft/Fara-7b", "microsoft/Fara-7B", "microsoft/fara-7b"):
            with self.subTest(path):
                self.assertEqual(hub_identity(hub_path("https://huggingface.co/" + path)), catalog.canonical("https://huggingface.co/" + path)[0])
        self.assertEqual(hub_path("https://huggingface.co/api/models/microsoft/Fara-7B", api=True), "microsoft/Fara-7B")
        self.assertEqual(hub_path("https://huggingface.co/api/datasets/bevaya/ScreenSpot", api=True), CURRENT)

    def test_non_repository_hub_urls_are_rejected(self):
        for url in ("http://huggingface.co/a/b", "https://hf.co/a/b", "https://huggingface.co/a/b/tree/main", "https://huggingface.co/a/b?x=1",
                    "https://huggingface.co/spaces/a/b", "https://huggingface.co/datasets/a", "https://huggingface.co/a/b/", "https://huggingface.co/a/..",
                    "https://huggingface.co/api/a/b", " https://huggingface.co/a/b"):
            with self.subTest(url):
                with self.assertRaises(ValueError):
                    hub_path(url)
        with self.assertRaises(ValueError):
            hub_path("https://huggingface.co/api/spaces/a/b", api=True)

    def test_paired_observations_resolve_the_other_name_to_the_existing_record(self):
        item = declaration()
        self.assertEqual(repository_aliases([item], [record()]), {item["alias_id"]: item["target_id"]})
        result = attach_repository_aliases([record()], [item])[0]
        self.assertEqual(result["aliases"], [item["alias_id"], "bevaya/ScreenSpot", "https://huggingface.co/" + CURRENT])
        self.assertEqual({(e["url"], e["method"], tuple(e["supports"])) for e in result["evidence"]},
            {(o["url"], "huggingface_repository_identity", ("aliases",)) for o in item["observations"]})

    def test_several_spellings_may_point_at_one_record(self):
        rid = lambda path: hub_identity(path)
        items = [declaration("microsoft/Fara-7B", "microsoft/Fara-7b", "microsoft/Fara-7B"), declaration("microsoft/fara-7b", "microsoft/Fara-7b", "microsoft/Fara-7B")]
        self.assertEqual(repository_aliases(items, [record("microsoft/Fara-7b")]), {rid("microsoft/Fara-7B"): rid("microsoft/Fara-7b"), rid("microsoft/fara-7b"): rid("microsoft/Fara-7b")})

    def test_mismatched_or_incomplete_evidence_is_rejected(self):
        mutations = {
            "different object": lambda item: item["observations"][0].update(repository_id="0" * 24),
            "numeric object": lambda item: item.update(repository_id=101),
            "different current name": lambda item: item["observations"][0].update(full_name="other/ScreenSpot", html_url="https://huggingface.co/datasets/other/ScreenSpot"),
            "html page of another repository": lambda item: item["observations"][0].update(html_url="https://huggingface.co/datasets/other/ScreenSpot"),
            "redirect to another repository": lambda item: item["observations"][1].update(resolved_url="https://huggingface.co/api/datasets/other/ScreenSpot"),
            "model page for a dataset": lambda item: item["observations"][0].update(html_url="https://huggingface.co/bevaya/ScreenSpot"),
            "uncovered alias": lambda item: item["observations"][0].update(url="https://huggingface.co/api/datasets/other/ScreenSpot"),
            "GitHub identifiers": lambda item: item.update(alias_id="github:bevaya/screenspot"),
            "GitHub basis": lambda item: item.update(basis="official_github_repository_id"),
            "uppercase identifier": lambda item: item.update(alias_id=item["alias_id"].upper()),
        }
        for label, mutate in mutations.items():
            with self.subTest(label):
                item = declaration()
                mutate(item)
                with self.assertRaises(ValueError):
                    repository_aliases([item])
        with self.assertRaises(ValueError):
            repository_aliases([declaration()], [record(CURRENT)])
        with self.assertRaises(ValueError):
            repository_aliases([declaration()], [record(), record(CURRENT)])

    def test_validate_lists_hub_renames_without_a_recorded_alias(self):
        self.assertEqual(unrecorded_hub_renames([record()], {}), [(hub_identity(FORMER), FORMER, CURRENT)])
        self.assertEqual(unrecorded_hub_renames([record()], repository_aliases([declaration()])), [])
        self.assertEqual(unrecorded_hub_renames([{**record(CURRENT), "details": {"hub_id": "bevaya/ScreenSpot"}}], {}), [])

    def test_published_schema_accepts_hub_declarations_and_keeps_github_shapes_apart(self):
        import jsonschema
        validator = jsonschema.Draft202012Validator(catalog.read_json(ROOT / "schemas/repository-alias.schema.json"))
        self.assertEqual(list(validator.iter_errors([declaration()])), [])
        self.assertTrue(list(validator.iter_errors([{**declaration(), "basis": "official_github_repository_id"}])))
        self.assertTrue(list(validator.iter_errors([{**declaration(), "repository_id": 101}])))
        self.assertEqual(list(validator.iter_errors(catalog.read_json(catalog.DATA / "repository-aliases.json"))), [])

    def test_committed_hub_renames_resolve_to_their_records(self):
        rows = catalog.read_jsonl(catalog.DATA / "catalog.jsonl")
        aliases = repository_aliases(catalog.read_json(catalog.DATA / "repository-aliases.json"), rows)
        self.assertEqual(unrecorded_hub_renames(rows, aliases), [])
        expected = {"url:f4bcd696942ee04dcc42": "url:7abb418096432f56c685", "url:a6db151f939a6748ff76": "url:f976dec3d1c5e0bedbd7",
            "url:d416331cdf9730afd6b9": "url:a4da77ee63f879cc8e63", "url:4338ec0f1a67bdb6a139": "url:a4da77ee63f879cc8e63",
            "url:5f4cb613bda51b45d9c7": "url:611df37e5f3caa6befd7", "url:8c792416d297293422cf": "url:4a0b1692589594745a3c"}
        for alias, target in expected.items():
            with self.subTest(alias):
                self.assertEqual(aliases[alias], target)
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(catalog.main(["get", alias, "--json"]), 0)
                self.assertEqual(json.loads(out.getvalue())["id"], target)
        queued = {row["id"] for row in catalog.read_jsonl(catalog.DATA / "review-queue.jsonl")}
        self.assertNotIn("url:8c792416d297293422cf", queued)



class UnrecordedRenameRobustnessTests(unittest.TestCase):
    def test_non_hub_url_with_hub_id_is_skipped(self):
        record = {"id": "github:a/b", "review_status": "curated", "url": "https://github.com/a/b", "details": {"hub_id": "a/b"}}
        self.assertEqual(unrecorded_hub_renames([record], {}), [])


if __name__ == "__main__":
    unittest.main()
