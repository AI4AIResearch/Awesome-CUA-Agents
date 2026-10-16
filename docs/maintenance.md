# Maintenance

Ordinary builds are offline and deterministic. Public-source discovery is scheduled twice a day and can also be run manually. No paid API, model inference, login, or private data is required for discovery.

The source workflow runs at **08:17 and 20:17 America/Los_Angeles**. Website publication runs at **08:47 and 20:47** in the same timezone. GitHub can delay or drop scheduled jobs under load; [the status page](https://awesomecua.github.io/updates/) records actual completed runs and links to their logs. Both workflows can be dispatched manually for recovery.

```bash
python3 scripts/scan.py
```

One scan refreshes the discovery documents and Hugging Face paper searches, queries recent arXiv titles, verifies missing paper identities, rebuilds the catalog, and validates it. New rows remain metadata-only or candidates. A changed existing paper title/author/date is recorded in `data/metadata-updates.jsonl` for review instead of overwriting the reviewed snapshot. Partial source failures are recorded explicitly; a failed build or validation prevents publication.

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

`.github/workflows/scan.yml` performs discovery and commits validated metadata using its own repository-scoped `GITHUB_TOKEN`. The public site's `publish.yml` independently checks out this public source, validates and builds it, updates the website snapshot, and deploys through the GitHub Pages Actions API. No cross-repository personal access token is required. The publication workflow source is maintained in `automation/publish.yml`; install workflow changes explicitly with `prepare_publication.py --install-workflow` during authorized maintenance.

`data/scan-status.json` records the latest completed attempt; `data/scan-history.jsonl` retains the most recent 180 receipts. Workflow failures before a valid receipt are visible in GitHub Actions and its uploaded evidence artifact. Review the run timestamps, not just the presence of a status file.

After a successful website deployment, the publication workflow notifies IndexNow of changed pages and preserves accepted fingerprints and submission receipts in the website repository's `.indexnow/` directory. Unchanged pages are not resubmitted. HTTP 202 and failures do not advance fingerprints, so a later publication retries the pending changes. See [search discovery](search-discovery.md) for manual use and the distinction between submission and indexing.

For each expansion, prioritize sources or resource kinds with known gaps rather than a raw-count target. Track primary metadata coverage separately from editorial review, protocol completeness, license completeness, and executable reproduction. Keep removed/renamed resources explainable; do not silently substitute a different project with the same name.
