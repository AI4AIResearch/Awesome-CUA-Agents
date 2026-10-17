# Data dictionary

The executable contract is [resource.schema.json](../schemas/resource.schema.json). All text files are UTF-8. JSONL has one resource per line; file ordering is by stable ID.

| Field | Meaning |
| --- | --- |
| `id` | Stable resource identity; prefixes distinguish arXiv, repositories, URLs, components, and publishers |
| `name`, `aliases` | Display name and explicitly reviewed alternative names |
| `kind` | Primary resource type; model families and checkpoints are distinguished by details/relations |
| `url` | Primary landing page; not necessarily a direct binary download |
| `scope` | `core`, `adjacent`, or `relevance_pending` |
| `review_status` | `curated` or `metadata_verified`; candidates live outside the catalog |
| `environments` | Reviewed platform facets; `cross-platform` is not a claim of support for every OS |
| `topics` | Editorial topic facets; empty for unreviewed bibliography entries |
| `summary` | Original concise annotation; null for metadata-only entries |
| `published_at`, `updated_at` | Exact calendar dates where established, otherwise null; a known year/month remains in `details.publication.date_parts` |
| `authors`, `identifiers` | Official bibliographic attribution and IDs |
| `links` | Typed links, starting with a primary or paper link |
| `relations` | Explicit semantic assertions: introduced by, documented by, published by, component of, variant of, etc. |
| `licenses` | Four separate nullable declarations: code, data, weights, document |
| `evidence` | Primary source URL, retrieval time in UTC, response digest, method, supported fields |
| `last_verified_at` | Time of the primary identity/content check; not a promise of current runtime availability |
| `details` | Kind-specific facts, with unknown quantities preserved as null |
| `notes` | Renames, historical context, and material limitations |

Dataset details can include sample count and unit, modalities, languages, download landing page, gated status, and explicitly approximate reported scale. Benchmark details can include task count, metric names, evaluation type, and leaderboard URL. Counts of episodes, actions, screenshots, tasks, and instructions are different units. Models can include `artifact_type: model-checkpoint`; family relations prevent treating every checkpoint as an independent project.

`references.jsonl` is a separate discovery graph. Its `mentions` relation only means a URL was found in the source. `target_in_catalog` distinguishes indexed and unresolved targets. Strong reviewed relations remain inside each resource record and in the SQLite `relations` table.

Source data lives in `editorial.json`, `papers.jsonl`, `publications.jsonl`, `primary-evidence.jsonl`, `enrichment.jsonl`, `candidates.jsonl`, and discovery manifests. `catalog.jsonl`, `coverage.json`, `references.jsonl`, `review-queue.jsonl`, and category Markdown are generated views. The ignored `.cache/` directory is not needed to reproduce an offline build.

`papers.jsonl` remains the arXiv archive. Each `publications.jsonl` observation has `id`, `publication`, `evidence`, and `last_verified_at`, following [publication-observation.schema.json](../schemas/publication-observation.schema.json). An existing arXiv ID receives publication metadata without replacing its original title, authors, dates or version. A new publisher URL identity creates a metadata-only record; relevance approval is still a separate editorial decision. A known publisher or PDF alias resolves to the same resource instead of adding another paper.

`details.publication` retains the publication edition's title, literal authors, type, venue, publisher, DOI, volume/issue/pages and source receipts. `date_parts` is `[year]`, `[year, month]`, `[year, month, day]`, or null. Unknown components are never filled with `01`; event dates are kept separately. `published_at IS NULL` therefore does not necessarily mean the publication year is unknown. Catalogue years use the retained arXiv submission date for arXiv identities, and the publication's recorded precision for publisher-only identities. Undated records sort last; partial dates sort after more precise dates in the same year/month, without asserting an earlier calendar day.

Coverage counts distinguish `bibliographic_records` (all active papers/surveys), `arxiv_active_records`, `non_arxiv_bibliographic_records`, and `publication_metadata_records` (including publication attachments to arXiv). The arXiv archive count remains separate. Per-source `indexed` counts matched discovery identifiers; `indexed_resources` counts distinct canonical resources, so multiple publisher/PDF aliases cannot inflate the catalog's resource total.

The website's `downloads/topics.json` is a derived index of reviewed topic membership, tied to the source catalog SHA-256. Each topic lists canonical resource IDs, counts, bilingual page URLs, and export fingerprints. `resources_with_topics` counts distinct reviewed resources across all topics; individual topic totals overlap and must not be summed. Per-topic JSONL preserves the complete source records, including evidence, license scopes and review state. Shared tags are not reviewed resource relationships. Rebuilds remove obsolete generated topic pages and exports when a topic loses all reviewed members.

Reviewed `documented_by` links connect an implementation or dataset to a paper named by its first-party source. They do not imply a training or evaluation dependency. Resource pages expose both outgoing relations and incoming connected assets. The [connections directory](https://awesomecua.github.io/connections/) and [relationship export](https://awesomecua.github.io/downloads/relationships.json) provide a consolidated view.

The citation exports retain literal source authors, source dates at their known precision, review status, and stable catalog identity. The default arXiv citation keeps its retained preprint version; `--edition publication` explicitly selects the publication's own title/authors/date/venue/DOI. Publisher-only records cite their publication in either mode. Unknown facts are omitted. Publication citation IDs can have an edition suffix while `custom.catalog_id` retains the canonical resource ID. The export manifest records editions, counts and file SHA-256 values, tied to the source catalog SHA-256.

`catalog.py get` returns an exact active record with its stable ID. `--related` adds only source-backed reviewed semantic relations; raw reference mentions are not promoted. A scope-excluded ID returns its applied decision and a nonzero exit code, preserving the boundary between the active catalog and retained archive.
