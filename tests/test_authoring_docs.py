import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scope_review import resolve_exclusions
from site_files import MANAGED_ROOTS

FENCE = re.compile(r"^```(\w+)\n(.*?)^```", re.S | re.M)


def section(path, heading):
    return (ROOT / path).read_text(encoding="utf-8").split(f"\n{heading}\n", 1)[1].split("\n## ", 1)[0]


class ScopeDecisionAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.text = section("docs/scope-review.md", "## Authoring a decision")
        fences = FENCE.findall(self.text)
        self.snippet = next(body for lang, body in fences if lang == "bash")
        self.example = json.loads(next(body for lang, body in fences if lang == "json"))
        self.records = {row["id"]: row for row in map(json.loads, (ROOT / "data/papers.jsonl").read_text(encoding="utf-8").splitlines())}

    def test_snippet_prints_the_example_as_a_draft(self):
        arxiv, script = re.fullmatch(r"python3 - (\S+) <<'PY'\n(.*)PY\n", self.snippet, re.S).groups()
        self.assertEqual("arxiv:" + arxiv, self.example["id"])
        output = subprocess.run([sys.executable, "-", arxiv], input=script, cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(output), {**self.example, "reason": "", "reviewed_at": ""})

    def test_example_matches_the_schema_and_resolves_to_excluded(self):
        import jsonschema
        schema = json.loads((ROOT / "schemas/scope-decision.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate([self.example])
        self.assertEqual([row["status"] for row in resolve_exclusions(self.records, [self.example])], ["excluded"])
        for key in ("reason", "reviewed_at"):
            with self.subTest(key), self.assertRaises(ValueError):
                resolve_exclusions(self.records, [{**self.example, key: ""}])

    def test_rules_name_every_field_the_resolver_checks(self):
        source = (ROOT / "scripts/scope_review.py").read_text(encoding="utf-8")
        resolver = source[source.index("def resolve_exclusions"):source.index("def scope_report")]
        fields = set(re.findall(r"decision(?:\.get\(|\[)'(\w+)'", resolver)) - {"evidence"}
        fields |= {"evidence." + key for key in re.findall(r"evidence(?:\.get\(|\[)'(\w+)'", resolver)}
        self.assertGreaterEqual(fields, {"id", "decision", "basis", "reason", "name", "url", "metadata_fingerprint", "reviewed_at", "evidence.url", "evidence.sha256", "evidence.retrieved_at"})
        rules = self.text.split("rules:\n", 1)[1]
        for field in fields:
            self.assertIn(f"`{field}`", rules)
        for term in ("`data/papers.jsonl`", "curated", "`identifiers.preferred_arxiv`", "`revalidation_pending`", "`data/metadata-updates.jsonl`", "scope-decision.schema.json"):
            self.assertIn(term, rules)


class ManualPublicationDocsTests(unittest.TestCase):
    def setUp(self):
        self.text = section("docs/website.md", "## Manual publication")
        self.script = (ROOT / "scripts/prepare_publication.py").read_text(encoding="utf-8")

    def test_checkouts_match_the_script_defaults_and_repositories(self):
        defaults = dict(re.findall(r"add_argument\('(--[\w-]+)',type=Path,default=ROOT/'([^']+)'\)", self.script))
        repositories = re.search(r"Clone (\S+) and (\S+) into", self.script).groups()
        clones = dict(re.findall(r"^git clone https://github\.com/(\S+)\.git (\S+)$", self.text, re.M))
        self.assertEqual(clones, {repositories[0]: defaults["--site-dir"], repositories[1]: defaults["--profile-dir"]})
        self.assertIn(f"git -C {defaults['--site-dir']} status", self.text)

    def test_every_flag_and_the_build_order_are_documented(self):
        flags = re.findall(r"add_argument\('(--[\w-]+)'", self.script)
        self.assertEqual(len(flags), 4)
        for flag in flags:
            self.assertRegex(self.text, rf"(?m)^\| `{flag}` \|")
        commands = next(body for _, body in FENCE.findall(self.text) if "prepare_publication.py" in body).splitlines()
        self.assertEqual(commands, ["python3 scripts/build_site.py", "python3 scripts/prepare_publication.py"])
        workflow = re.search(r"python (scripts/prepare_publication\.py .*)", (ROOT / "automation/publish.yml").read_text(encoding="utf-8")).group(1)
        self.assertIn(workflow, self.text)

    def test_deletions_and_rewrites_are_called_out(self):
        for root in MANAGED_ROOTS:
            self.assertIn(f"`{root}/`", self.text)
        for phrase in ("previous `data/search-manifest.json`", "`downloads/topics/`", "`.gitignore`", "Rewrites `README.md`", "`profile/README.md`", "never commits, pushes or deploys"):
            self.assertIn(phrase, self.text)
        self.assertIn("(website.md#manual-publication)", (ROOT / "docs/maintenance.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
