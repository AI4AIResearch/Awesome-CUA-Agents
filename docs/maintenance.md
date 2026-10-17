# Maintenance

Ordinary builds are offline and deterministic. Public-source discovery is scheduled twice a day and can also be run manually. No paid API, model inference, login, or private data is required for discovery.

The source workflow runs at **08:17 and 20:17 America/Los_Angeles**. Website publication runs at **08:47 and 20:47** in the same timezone. GitHub can delay or drop scheduled jobs under load; [the status page](https://awesomecua.github.io/updates/) records actual completed runs and links to their logs. Both workflows can be dispatched manually for recovery.

```bash
python3 scripts/scan.py
```

One scan attempts to refresh all 44 discovery documents and the Hugging Face paper searches, obtains a recent arXiv query result, verifies missing paper identities, rebuilds the catalog, and validates it. New rows remain metadata-only or candidates. Existing-paper changes are proposed for review instead of overwriting retained metadata. Partial source failures are recorded explicitly; a failed build or validation prevents publication.

The committed `data/paper-discovery-queries.json` registry defines 32 Hugging Face hybrid searches, each with an 80-result window. The topics include desktop and mobile platforms, professional software, grounding, data, learning, memory, safety, accessibility, and Chinese-language discovery. Both daily scans run the registry. `data/paper-discovery-status.json` records the current pass, each query's receipt, successful/failed/deferred states, unique identifiers, and new candidate contributions. Ranked windows and their overlaps do not establish complete coverage. Per-query new counts depend on query order; the pass total is deduplicated.

Successful query results replace only that query's current candidate occurrences. Failures or malformed responses retain prior occurrences without borrowing an old success for the current scan. A completed query is persisted before the next request. On HTTP 429, remaining queries for that provider are explicitly deferred. arXiv harvest also stops after a 429; a rate-limited recent query defers the same scan's harvest. Unresolved candidates remain queued for later verification.

Sources can declare `parser: huggingface_models` for a public publisher index on the official Hub API. This requires an author and a limit of at most 100 entries. Model IDs are converted into candidate URLs; namespace membership does not establish GUI relevance, release completeness, licensing, or a separate model entity. Invalid response shapes and unexpected publishers fail the source pass without erasing earlier occurrences.

The scheduled arXiv query uses a 14-day first-submission window ending at the current UTC midnight, with a configured limit of 500 results. Its query, time bounds, reported population, pagination receipts, and completeness are recorded in `data/recent-paper-search.json`. It discovers recent submissions; it does not refresh revisions of every historical paper. Targeted maintenance through the other ingestion commands is separate from this coverage claim.

A complete successful recent query can be reused by later scans in the same UTC day. Reuse requires the same query and bounds, matching unique and reported counts, no warnings, and successful page receipts with valid hashes and retrieval times in that UTC day. A genuine zero-result Atom feed is eligible. Failed requests, malformed feeds, changing pagination totals, partial results, and capped incomplete searches are not eligible and can be retried on a later scan. The scan phase reports `cache_used` and the original `source_retrieved_at` when reused.

UTC-day reuse is the repository's cache policy, following the API's recommendation to cache identical queries within a daily publication cycle. The official date-query syntax uses GMT. [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html) Both scheduled workflow runs continue, and discovery documents and Hugging Face searches still refresh on each run even when the recent arXiv query is reused.

The discovery registry includes first-party release pages as well as research collections. Refreshing a release page can discover newly linked code, data, or checkpoints, but does not approve those assets or rewrite their reviewed specifications. Announced releases such as CarryOn and GraceBench remain in the editorial queue until the recorded release gap is resolved and reviewed.

```bash
# Re-fetch the declared discovery documents and update provenance.
python3 scripts/catalog.py discover --refresh

# Fetch missing arXiv identities. Requests are batched and spaced.
python3 scripts/catalog.py harvest

# Run the recorded title query; inspect its manifest for pagination completeness.
python3 scripts/catalog.py search-arxiv

# Refresh first-party evidence for editorial proposals.
python3 scripts/catalog.py verify --refresh
python3 scripts/catalog.py enrich

# Review changed snapshots before updating editorial approval digests.
python3 scripts/catalog.py build

# Run the same checks as CI, in order; see "Maintain and verify" in the README.
.venv/bin/python scripts/catalog.py validate
.venv/bin/python scripts/catalog.py build --check
.venv/bin/python -m unittest discover -s tests -v
node --test tests/web.test.mjs
.venv/bin/python scripts/build_site.py
```

`--limit` bounds a harvest or search. Search manifests explicitly report incomplete pagination. Successful responses are cached; failed requests are recorded separately and never overwrite the last successful response. A failed refresh remains a failure in the latest run manifest. Re-running without `--refresh` can reuse an older successful cache response, retaining its original retrieval timestamp.

`enrich` reads each primary-evidence body from the local `.cache/http/` and uses it only when its SHA-256 equals the recorded receipt. A missing or different body (a fresh clone, another machine, or receipts pulled from CI) leaves that record's previous enrichment untouched and is reported as `STALE`; run `verify` on the same machine first. A LICENSE request that fails with anything other than 404 keeps the previously recorded code license.

`harvest`, `search-arxiv`, and the scheduled recent search all use the same revision-proposal path for known IDs, including manual `--refresh` calls. Comparisons cover title, authors, publication/update dates, Atom version, exact submission/update timestamps, and the normalized abstract digest. A changed date-only field is not required: a new version or abstract can be detected within the same day. The retained archive row and its original receipt stay in place until a source-backed decision reconciles the proposal.

Inspect `data/metadata-updates.jsonl` before accepting new metadata. `metadata_change_pending` identifies a confirmed field difference; `metadata_revalidation_pending` identifies an observation whose missing, incomplete, or unsupported baseline prevents a confident comparison. A proposal may also carry an uncertainty reason alongside confirmed differences. Review its `changes`, `observed_snapshot`, source evidence, and first/last observation times. Accepting revised bibliographic facts does not itself approve an old editorial summary for the new paper version. Reconcile editorial and scope decisions against the evidence actually reviewed.

The snapshot schema and field meanings are documented in [methodology](methodology.md#paper-versions-and-revision-proposals). For older rows, recover a baseline from the original response cache with the offline backfill tool:

```bash
# Validate the complete archive and report a plan without changing files.
python3 scripts/backfill_arxiv_snapshots.py

# Apply only after the original-receipt validation succeeds.
python3 scripts/backfill_arxiv_snapshots.py --write
```

The completed migration recovered snapshots for 1,764 retained records. The tool makes no network requests. It checks every original `arxiv_api` receipt's SHA-256, requires one matching entry per paper, checks retained title/authors/dates, and requires multiple receipts to agree. Missing or conflicting evidence blocks the whole write. Existing snapshots must match the original evidence; they are never replaced with a new baseline. A write adds the snapshot and its evidence-support label, preserves record order and existing facts, and atomically replaces the file only if the input has not changed during validation. Repeating the tool on an already completed archive is a no-op.

Every editorial entry binds to a `reviewed_sha256`. If an upstream page changes, rerun the editorial review, fix names/taxonomy/notes as needed, and copy the new digest and record the review time in `reviewed_at` only after inspection. [Editorial input](editorial-input.md) documents every key of an editorial entry. A changed or unresolved entry remains in the review queue until this is done. HTTP success and keyword matching do not grant editorial approval.

`.github/workflows/scan.yml` performs discovery and commits validated metadata using its own repository-scoped `GITHUB_TOKEN`. Before committing, it runs the same validation, tests and website build as Catalog quality and refuses to commit if any tracked or untracked change falls outside the committed paths. A push made with `GITHUB_TOKEN` starts no `push` workflow, so a separate `dispatch_quality` job then dispatches Catalog quality on the new `main` commit. Only that job, which checks out nothing, has `actions: write`; the scan job has only `contents: write`. The public site's `publish.yml` independently checks out this public source, validates and builds it, updates the website snapshot, and deploys through the GitHub Pages Actions API. No cross-repository personal access token is required. The publication workflow source is maintained in `automation/publish.yml`; install workflow changes explicitly with `prepare_publication.py --install-workflow` during authorized maintenance.

`data/scan-status.json` records the latest completed attempt; `data/scan-history.jsonl` retains the most recent 180 receipts. Workflow failures before a valid receipt are visible in GitHub Actions and its uploaded evidence artifact. Review the run timestamps, not just the presence of a status file.

After a successful website deployment, the publication workflow notifies IndexNow of changed pages and preserves accepted fingerprints and submission receipts in the website repository's `.indexnow/` directory. Unchanged pages are not resubmitted. HTTP 202 and failures do not advance fingerprints, so a later publication retries the pending changes. See [search discovery](search-discovery.md) for manual use and the distinction between submission and indexing.

For each expansion, prioritize sources or resource kinds with known gaps rather than a raw-count target. Track primary metadata coverage separately from editorial review, protocol completeness, license completeness, and executable reproduction. Keep removed/renamed resources explainable; do not silently substitute a different project with the same name.

Review scope exclusions in `data/exclusion-status.json`. An upstream-change proposal prevents an old exclusion from continuing silently; reconcile the metadata proposal and renew or remove the scope decision after source review. `arxiv_archive_records` counts retained arXiv ingestion records, while `bibliographic_records` counts all active papers and surveys, including publisher-only identities. `arxiv_active_records` is the active arXiv subset. The exclusion ledger and archive are published separately from the active catalog.

Reviewed license decisions can override machine extraction through `reviewed_licenses` on an editorial input. Each scope retains a value (including null for an unresolved conflict), a reason, and evidence URLs bound to retained receipts that explicitly support that license scope. The public record keeps the reason and sources in `details.license_review`. A model-hosting namespace does not imply that an environment archive contains model weights.

Discovery occurrences preserve `receipt_id` and the source URL, SHA-256 and retrieval time in `evidence`; a later failed source run cannot erase that provenance or masquerade as a successful refresh. Backfilling older occurrences requires a matching retained successful receipt. HTTP 429 deferral is scoped to the provider host; unrelated sources can continue. A successful response that yields fewer than half of a source's retained candidates, including an empty body, is recorded as a failed `suspicious shrink` run and keeps the earlier occurrences. After confirming the upstream change, apply it with `python3 scripts/catalog.py discover --refresh --accept-shrink <source-id>`.
