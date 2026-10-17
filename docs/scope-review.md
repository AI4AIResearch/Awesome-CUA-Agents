# Scope review and retained bibliography

The active catalog focuses on computer-use agents and directly relevant foundations. Broad discovery queries can also retrieve work in unrelated areas such as physical quantum computing or reservoir hardware. Bibliographic verification alone does not establish CUA relevance.

## Explicit decisions

`data/exclusions.json` is an authored list of primary-abstract scope reviews. Each entry records the paper identity, original title and URL, reason, review time, metadata fingerprint, and primary response receipt. No keyword rule automatically excludes a paper.

`data/exclusion-status.json` is generated during the offline build. A decision applies only while its metadata fingerprint and retained evidence match and no upstream metadata change is queued. Otherwise the record remains visible as metadata-only and the decision is queued for revalidation. A curated inclusion or a dependency from a retained relationship must be reconciled before an exclusion can take effect.

## Preserving provenance

- `data/papers.jsonl` retains ingested arXiv metadata, including excluded records. It is an archive of input snapshots, not the current editorial catalog.
- `data/catalog.jsonl`, SQLite search, and the interactive catalog omit applied exclusions.
- Previous resource URLs remain available as scope explanations with `noindex,follow`; their Markdown companions are updated too.
- The website exposes the scope ledger and raw metadata archive as separate downloads. Active-catalog counts, archive counts, exclusions, and unresolved candidates have different meanings.

A decision concerns the catalog's scope, not the quality of the underlying research. It can be corrected by updating or removing the authored decision in a source-backed commit; Git history retains the previous decision. If an upstream metadata proposal triggered revalidation, reconcile that proposal before renewing the decision.

## Checks

`schemas/scope-decision.schema.json` defines the authored input. `scripts/scope_review.py` resolves decisions and guards against source drift, silent removal of curated entries, and broken retained relationships. Tests cover preservation of the archive, revalidation, explicit-only decisions, coverage counts, and non-indexed explanation pages.

```bash
python3 scripts/catalog.py build
python3 scripts/catalog.py validate
python3 -m unittest discover -s tests -p 'test_scope_review.py' -v
```
