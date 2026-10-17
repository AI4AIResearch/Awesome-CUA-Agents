import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
# An ASCII locale with locale coercion and UTF-8 mode disabled: every implicit text encoding is ASCII.
ASCII_ENV = {**{k: v for k, v in os.environ.items() if not k.startswith(("LC_", "PYTHON")) and k != "LANG"},
    "LC_ALL": "C", "LANG": "C", "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0"}


def run(*args):
    return subprocess.run([sys.executable, "-X", "utf8=0", "-X", "warn_default_encoding", *args], cwd=ROOT, env=ASCII_ENV, capture_output=True, check=False)


class AsciiLocaleTests(unittest.TestCase):
    def assertClean(self, result):
        stderr = result.stderr.decode("utf-8", "replace")
        self.assertEqual(result.returncode, 0, stderr)
        self.assertNotIn("EncodingWarning", stderr)

    def test_environment_really_uses_an_ascii_locale(self):
        result = run("-c", "import locale, sys; print(locale.getencoding(), sys.flags.utf8_mode)")
        self.assertClean(result)
        self.assertEqual(result.stdout.decode().split()[1], "0")
        self.assertNotIn("utf", result.stdout.decode().casefold())

    def test_search_reads_the_utf8_catalog_and_prints_utf8(self):
        result = run("scripts/catalog.py", "search", "osworld", "--limit", "1")
        self.assertClean(result)
        self.assertIn(" · ", result.stdout.decode("utf-8"))
        result = run("scripts/catalog.py", "search", "osworld", "--limit", "1", "--json")
        self.assertClean(result)
        self.assertEqual(json.loads(result.stdout.decode("utf-8"))["returned"], 1)

    def test_generated_views_match_under_an_ascii_locale(self):
        self.assertClean(run("scripts/catalog.py", "build", "--check"))

    def test_helpers_round_trip_non_ascii_text(self):
        name = "Agent \u00b7 \u667a\u80fd\u4f53 \u2265"
        with tempfile.TemporaryDirectory() as directory:
            # ascii() keeps the child's source ASCII; non-ASCII argv would be decoded with the ASCII locale.
            code = (f"import sys; sys.path.insert(0, 'scripts'); from pathlib import Path; import catalog; d, name = Path(sys.argv[1]), {ascii(name)}; "
                "catalog.write_json(d / 'a.json', {'name': name}); catalog.write_jsonl(d / 'a.jsonl', [{'id': 'x', 'name': name}]); "
                "print(catalog.read_json(d / 'a.json')['name'] == name == catalog.read_jsonl(d / 'a.jsonl')[0]['name'])")
            result = run("-c", code, directory)
            self.assertClean(result)
            self.assertEqual(result.stdout.decode().strip(), "True")
            self.assertEqual(json.loads((Path(directory) / "a.json").read_bytes().decode("utf-8")), {"name": name})
            self.assertEqual(json.loads((Path(directory) / "a.jsonl").read_bytes().decode("utf-8")), {"id": "x", "name": name})


class ExplicitEncodingTests(unittest.TestCase):
    def test_script_text_io_names_its_encoding(self):
        implicit = []
        for path in sorted((ROOT / "scripts").glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call) or any(k.arg == "encoding" for k in node.keywords):
                    continue
                method = isinstance(node.func, ast.Attribute)
                if method and getattr(node.func.value, "id", "") == "os":
                    continue  # os.open returns a file descriptor and takes no encoding.
                name = node.func.attr if method else getattr(node.func, "id", "")
                # Path.open(mode) takes the mode first; the builtin open(file, mode) second.
                position = 0 if method else 1
                mode = node.args[position] if len(node.args) > position else next((k.value for k in node.keywords if k.arg == "mode"), None)
                binary = isinstance(mode, ast.Constant) and "b" in str(mode.value)
                if name in {"read_text", "write_text"} or name == "open" and not binary:
                    implicit.append(f"{path.name}:{node.lineno}")
        self.assertEqual(implicit, [])

if __name__ == "__main__":
    unittest.main()
