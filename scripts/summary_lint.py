"""Advisory style report for curated summaries; its findings never fail a build or CI run."""
from __future__ import annotations

import re

from catalog import DATA, read_jsonl

SUMMARY_LIMIT = 220
SUPERLATIVES = ("state-of-the-art", "best", "revolutionary")
# Inside a longer hyphenated term, such as best-first search or best-of-N sampling, a listed word names a technique, not a claim.
SUPERLATIVE_RE = re.compile("|".join(r"(?<![\w-])" + word.replace("-", "[- ]") + r"(?![\w-])" for word in SUPERLATIVES), re.I)


def summary_issues(summary):
    issues = []
    if len(summary) > SUMMARY_LIMIT:
        issues.append(f"{len(summary)} characters, over {SUMMARY_LIMIT}")
    if not summary.rstrip().endswith("."):
        issues.append("no terminal period")
    issues += [f'superlative "{word}"' for word in dict.fromkeys(match.group(0) for match in SUPERLATIVE_RE.finditer(summary))]
    return issues


def lint(args):
    rows = [r for r in read_jsonl(DATA / "catalog.jsonl") if r.get("review_status") == "curated" and isinstance(r.get("summary"), str)]
    flagged = 0
    for row in rows:
        if issues := summary_issues(row["summary"]):
            flagged += 1
            print(f"{row['id']}: " + "; ".join(issues))
    print(f"Summary style: {flagged} of {len(rows)} curated summaries flagged. This report is advisory and never fails.")
    return 0
