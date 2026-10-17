from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


EVIDENCE = "https://example.org/agent/readme"
LICENSE = {"basis": "publisher model/dataset card", "declared": "apache-2.0", "retrieved_at": "2026-10-16T11:11:53Z", "url": "https://huggingface.co/datasets/example/android-taps"}


def row(rid, name, kind, environments=("web",), topics=(), relations=(), **fields):
    return {"id": rid, "name": name, "kind": kind, "url": "https://example.org/" + rid.split(":", 1)[1], "review_status": "curated", "scope": "core",
        "published_at": None, "summary": None, "aliases": [], "authors": [], "environments": list(environments), "topics": list(topics), "relations": list(relations),
        "licenses": {"code": None, "data": None, "document": None, "weights": None}, **fields}


ROWS = [
    row("url:android-taps", "Android Taps", "dataset", environments=["android", "ios"], topics=["mobile", "navigation"], summary="Screen grounding traces from phones.",
        licenses={"code": None, "data": LICENSE, "document": None, "weights": None}),
    row("url:web-clicks", "Web Clicks", "dataset", topics=["web-navigation"]),
    row("organization:example-labs", "Example Labs", "company"),
    row("url:example-agent", "Example Agent", "product", environments=["desktop"], relations=[
        {"type": "published_by", "target_id": "organization:example-labs", "evidence_url": EVIDENCE},
        {"type": "uses", "target_id": "url:android-taps", "evidence_url": EVIDENCE}]),
]


def guide_statements():
    text = (catalog.ROOT / "docs/query-guide.md").read_text()
    sql = "\n".join(re.findall(r"^```sql\n(.*?)^```", text, re.M | re.S))
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


class SqliteExportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "catalog.sqlite"
        build.write_sqlite(ROWS, path)
        self.con = sqlite3.connect(path)
        self.addCleanup(self.con.close)

    def test_documented_tables_exist(self):
        tables = {name for (name,) in self.con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertLessEqual({"resources", "facets", "relations", "resource_search"}, tables)

    def test_facets_hold_each_environment_and_topic(self):
        self.assertEqual(self.con.execute("SELECT resource_id, facet, value FROM facets ORDER BY resource_id, facet, value").fetchall(), [
            ("organization:example-labs", "environments", "web"),
            ("url:android-taps", "environments", "android"),
            ("url:android-taps", "environments", "ios"),
            ("url:android-taps", "topics", "mobile"),
            ("url:android-taps", "topics", "navigation"),
            ("url:example-agent", "environments", "desktop"),
            ("url:web-clicks", "environments", "web"),
            ("url:web-clicks", "topics", "web-navigation"),
        ])

    def test_relations_keep_type_target_and_evidence(self):
        self.assertEqual(self.con.execute("SELECT source_id, relation, target_id, evidence_url FROM relations ORDER BY source_id, relation, target_id").fetchall(), [
            ("url:example-agent", "published_by", "organization:example-labs", EVIDENCE),
            ("url:example-agent", "uses", "url:android-taps", EVIDENCE),
        ])

    def test_query_guide_sql_runs_and_returns_rows(self):
        statements = guide_statements()
        self.assertTrue(statements, "docs/query-guide.md has no ```sql block")
        for statement in statements:
            with self.subTest(statement=statement.splitlines()[0]):
                self.assertTrue(self.con.execute(statement).fetchall())

    def test_documented_queries_select_only_matching_fixture_rows(self):
        # Web Clicks is a curated dataset outside Android without a data license, and the agent also has a non-publisher relation.
        results = [self.con.execute(statement).fetchall() for statement in guide_statements()]
        for expected in [("Android Taps", "https://example.org/android-taps"), ("Android Taps", "dataset", "curated", "https://example.org/android-taps"),
                ("Android Taps", "apache-2.0"), ("Example Labs", "Example Agent", "product")]:
            with self.subTest(expected=expected):
                self.assertIn([expected], results)


if __name__ == "__main__":
    unittest.main()
