import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import summary_lint
from summary_lint import summary_issues

CLEAN = "Execution-based evaluation of agents performing tasks in real desktop environments."


class SummaryLintTests(unittest.TestCase):
    def test_clean_summary_has_no_issues(self):
        self.assertEqual(summary_issues(CLEAN), [])
        self.assertEqual(summary_issues(CLEAN + "  "), [])

    def test_length_budget_is_220_characters(self):
        self.assertEqual(summary_issues("x" * 219 + "."), [])
        self.assertEqual(summary_issues("x" * 220 + "."), ["221 characters, over 220"])

    def test_terminal_period_is_required(self):
        for text in ["Benchmark for agents in SaaS applications", "Benchmark for agents in SaaS applications!", "Benchmark (web)", "Benchmark…"]:
            with self.subTest(text):
                self.assertEqual(summary_issues(text), ["no terminal period"])

    def test_superlatives_are_reported_once_each(self):
        self.assertEqual(summary_issues("A revolutionary agent with state-of-the-art and State of the art results."),
            ['superlative "revolutionary"', 'superlative "state-of-the-art"', 'superlative "State of the art"'])
        self.assertEqual(summary_issues("The best agent, best on every benchmark."), ['superlative "best"'])
        self.assertEqual(summary_issues("Best results on OSWorld."), ['superlative "Best"'])

    def test_technique_names_are_not_superlatives(self):
        for text in ["Applies best-first search to web agents.", "Selects actions with best-of-N sampling.", "Measures the bestiary of GUI tasks."]:
            with self.subTest(text):
                self.assertEqual(summary_issues(text), [])

    def test_lint_lists_curated_records_with_reasons_and_never_fails(self):
        rows = [{"id": "github:a/clean", "review_status": "curated", "summary": CLEAN},
            {"id": "github:a/long", "review_status": "curated", "summary": "A revolutionary " + "y" * 220},
            {"id": "arxiv:2404.07972", "review_status": "metadata_verified", "summary": None},
            {"id": "arxiv:2404.00001", "review_status": "metadata_verified", "summary": "Best results"}]
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(summary_lint, "DATA", Path(directory)):
            catalog.write_jsonl(Path(directory) / "catalog.jsonl", rows)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = catalog.main(["lint"])
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue().splitlines(), [
            'github:a/long: 236 characters, over 220; no terminal period; superlative "revolutionary"',
            "Summary style: 1 of 2 curated summaries flagged. This report is advisory and never fails."])


if __name__ == "__main__":
    unittest.main()
