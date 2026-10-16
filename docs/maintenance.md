# Maintenance

Ordinary builds are offline and deterministic. Live discovery is opt-in and reads public sources only. No paid API, model inference, login, or private data is required.

```bash
# Re-fetch the declared discovery documents and update provenance.
python3 scripts/catalog.py discover --refresh

# Fetch missing arXiv identities. Requests are batched and spaced.
python3 scripts/catalog.py harvest

# Run the recorded title-query strategy, paginated to the reported total.
python3 scripts/catalog.py search-arxiv

# Refresh first-party evidence for editorial proposals.
python3 scripts/catalog.py verify --refresh
python3 scripts/catalog.py enrich

# Review changed snapshots before updating editorial approval digests.
python3 scripts/catalog.py build
.venv/bin/python scripts/catalog.py validate
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/catalog.py build --check
```

`--limit` bounds a harvest or search. Search manifests explicitly report incomplete pagination. Successful responses are cached; failed requests are recorded separately and never overwrite the last successful response. A failed refresh remains a failure in the latest run manifest. Re-running without `--refresh` can reuse an older successful cache response, retaining its original retrieval timestamp.

Every editorial entry binds to a `reviewed_sha256`. If an upstream page changes, rerun the editorial review, fix names/taxonomy/notes as needed, and copy the new digest and retrieval time only after inspection. A changed or unresolved entry remains in the review queue until this is done. HTTP success and keyword matching do not grant editorial approval.

The GitHub workflow validates committed data, tests ingestion safeguards, checks generated-view consistency, and exports build artifacts. It does not autonomously curate new records. No unattended source refresh has been enabled in this repository.

For each expansion, prioritize sources or resource kinds with known gaps rather than a raw-count target. Track primary metadata coverage separately from editorial review, protocol completeness, license completeness, and executable reproduction. Keep removed/renamed resources explainable; do not silently substitute a different project with the same name.
