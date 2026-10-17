# Contributing

Contributions should improve coverage or trustworthiness. A small correction with primary evidence is valuable.

1. Search `data/catalog.jsonl` and `data/candidates.jsonl` for existing IDs, aliases, and mirrors. [Editorial input](docs/editorial-input.md#resource-id) shows how a URL maps to its ID.
2. Add an editorial proposal to `data/editorial.json` with `name`, `kind`, the primary `url`, `environments`, `topics`, a concise original `summary`, `verify_terms`, and `editorial_reviewed: false`. [Editorial input](docs/editorial-input.md) documents every key, its default, and its effect on the published record.
3. Run `python3 scripts/catalog.py verify` and inspect the actual primary source. HTTP status or keyword presence is not enough. Check scope, current naming, and the exact asset being described.
4. After review, set `editorial_reviewed: true` and copy `reviewed_sha256` from the matching receipt in `data/primary-evidence.jsonl`. Record the UTC review time in `reviewed_at`; it is informational and only orders the README's recently reviewed list. Keep unresolved proposals unapproved with a `review_note`.
5. Run `enrich`, `build`, `validate`, the test suite, and `build --check` as described in [maintenance](docs/maintenance.md).
6. Submit the source changes and generated views together. Explain the evidence, any uncertain facts, and whether the resource is core or adjacent.

Do not directly edit generated catalog/category files. Do not copy upstream abstracts, READMEs, datasets, or model weights into this repository. Do not infer dataset/model licensing from the code license. Preserve unknowns as null, with count units and evaluation settings stated when facts are available.

New discovery sources belong in `data/sources.json`. Identify the exact document and scope; prefer complementary sources over mirrors. Do not promote a list entry to a curated record without a first-party check. Report broken links, missing resources, and incorrect merges through the issue template.
