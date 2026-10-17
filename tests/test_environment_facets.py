from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build
from catalog import read_jsonl

DESKTOP_OS = {"windows", "macos", "linux"}


def record(environments, topics=()):
    return {"id": "url:fixture", "url": "https://example.org/fixture", "name": "Fixture", "kind": "benchmark", "review_status": "curated",
        "environments": list(environments), "topics": list(topics), "summary": "A fixture.", "aliases": [], "authors": [], "identifiers": {}}


def facet_errors(environments, topics=()):
    return [error.split(": ", 1)[1] for error in build.validate_records([record(environments, topics)]) if "environment" in error]


class EnvironmentFacetTests(unittest.TestCase):
    def test_desktop_operating_systems_are_listed_with_desktop(self):
        for environments in (["windows"], ["linux", "web"], ["cross-platform", "macos", "windows"]):
            with self.subTest(environments=environments):
                self.assertEqual(facet_errors(environments), ["windows, macos or linux environment without desktop"])
        for environments in (["desktop"], ["desktop", "windows"], ["web", "desktop", "linux", "android", "cross-platform"]):
            with self.subTest(environments=environments):
                self.assertEqual(facet_errors(environments), [])

    def test_unspecified_stands_alone(self):
        self.assertEqual(facet_errors(["unspecified", "android"]), ["unspecified environment combined with platform facets"])
        self.assertEqual(facet_errors(["unspecified"]), [])

    def test_navigation_topics_match_their_platforms(self):
        self.assertEqual(facet_errors(["android"], ["web-navigation"]), ["web-navigation topic without a web or cross-platform environment"])
        self.assertEqual(facet_errors(["unspecified"], ["web-navigation"]), ["web-navigation topic without a web or cross-platform environment"])
        self.assertEqual(facet_errors(["desktop", "windows"], ["mobile-navigation"]), ["mobile-navigation topic with only desktop environments"])
        for environments, topic in [(["android", "web"], "web-navigation"), (["cross-platform"], "web-navigation"), (["android"], "mobile-navigation"),
                                    (["unspecified"], "mobile-navigation"), (["web"], "mobile-navigation"), (["desktop", "linux", "harmonyos"], "mobile-navigation")]:
            with self.subTest(environments=environments, topic=topic):
                self.assertEqual(facet_errors(environments, [topic]), [])

    def test_catalog_follows_the_facet_hierarchy(self):
        curated = [row for row in read_jsonl(ROOT / "data" / "catalog.jsonl") if row["review_status"] == "curated"]
        self.assertEqual([row["id"] for row in curated if set(row["environments"]) & DESKTOP_OS and "desktop" not in row["environments"]], [])
        self.assertEqual([row["id"] for row in curated if "unspecified" in row["environments"] and len(row["environments"]) > 1], [])


if __name__ == "__main__":
    unittest.main()
