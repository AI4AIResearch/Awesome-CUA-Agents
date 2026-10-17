import copy
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


def records():
    # A reviewed repository whose relation targets a paper in the same fixture.
    rows = {r["id"]: r for r in catalog.read_jsonl(catalog.DATA / "catalog.jsonl")}
    repository = copy.deepcopy(rows["github:xlang-ai/osworld"])
    repository["relations"] = repository["relations"][:1]
    return repository, copy.deepcopy(rows[repository["relations"][0]["target_id"]])


class DuplicateRelationTests(unittest.TestCase):
    def test_fixture_is_valid_without_duplicates(self):
        self.assertEqual(build.validate_records(list(records())), [])

    def test_duplicate_relation_is_reported(self):
        repository, target = records()
        repository["relations"].append(copy.deepcopy(repository["relations"][0]))
        errors = build.validate_records([repository, target])
        self.assertIn(f"github:xlang-ai/osworld: duplicate relation {repository['relations'][0]['type']} {target['id']}", errors)

    def test_same_target_with_different_types_is_allowed(self):
        repository, target = records()
        relation = repository["relations"][0]
        repository["relations"].append({**relation, "type": "uses" if relation["type"] != "uses" else "evaluates"})
        self.assertEqual(build.validate_records([repository, target]), [])

    def test_schema_rejects_repeated_relation(self):
        import jsonschema
        repository, _ = records()
        repository["relations"].append(copy.deepcopy(repository["relations"][0]))
        validator = jsonschema.Draft202012Validator(catalog.read_json(catalog.ROOT / "schemas/resource.schema.json"))
        self.assertTrue(any(error.validator == "uniqueItems" for error in validator.iter_errors(repository)))

    def test_failed_sqlite_write_leaves_no_temporary_files(self):
        repository, target = records()
        repository["relations"].append(copy.deepcopy(repository["relations"][0]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.sqlite"
            with self.assertRaises(sqlite3.IntegrityError):
                build.write_sqlite([repository, target], path)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_failed_sqlite_write_keeps_previous_export(self):
        repository, target = records()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.sqlite"
            build.write_sqlite([repository, target], path)
            repository["relations"].append(copy.deepcopy(repository["relations"][0]))
            with self.assertRaises(sqlite3.IntegrityError):
                build.write_sqlite([repository, target], path)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ["catalog.sqlite"])
            con = sqlite3.connect(path)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM relations").fetchone()[0], 1)
            con.close()


if __name__ == "__main__":
    unittest.main()
