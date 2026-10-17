import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import build


class JsonlLineErrorTests(unittest.TestCase):
    def write(self, directory, text):
        path = Path(directory) / "catalog.jsonl"
        path.write_text(text)
        return path

    def test_malformed_line_names_file_line_and_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, '{"id": "a"}\n\n{"id": "b"}\n{"id": "c", "name": "Trailing comma example",}\n')
            with self.assertRaises(ValueError) as raised:
                catalog.read_jsonl(path)
        self.assertEqual(str(raised.exception), f"{path}:4: Illegal trailing comma before end of object (column 45)")
        self.assertIsInstance(raised.exception.__cause__, json.JSONDecodeError)

    def test_valid_blank_and_missing_files_still_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, '{"id": "a"}\n  \n{"id": "b"}\n')
            self.assertEqual(catalog.read_jsonl(path), [{"id": "a"}, {"id": "b"}])
            self.assertEqual(catalog.read_jsonl(Path(directory) / "missing.jsonl"), [])

    def test_validate_reports_the_catalog_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, '{"id": "a"}\n{"id": "b"\n')
            with mock.patch.object(build, "DATA", Path(directory)), self.assertRaisesRegex(ValueError, "^" + re.escape(str(path)) + r":2: Expecting ',' delimiter \(column 11\)$"):
                build.validate(types.SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
