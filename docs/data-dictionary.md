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
| `published_at`, `updated_at` | Bibliographic dates where established, otherwise null |
| `authors`, `identifiers` | Official bibliographic attribution and IDs |
| `links` | Typed links, starting with a primary or paper link |
| `relations` | Explicit semantic assertions: introduced by, published by, component of, variant of, etc. |
| `licenses` | Four separate nullable declarations: code, data, weights, document |
| `evidence` | Primary source URL, retrieval time in UTC, response digest, method, supported fields |
| `last_verified_at` | Time of the primary identity/content check; not a promise of current runtime availability |
| `details` | Kind-specific facts, with unknown quantities preserved as null |
| `notes` | Renames, historical context, and material limitations |

Dataset details can include sample count and unit, modalities, languages, download landing page, gated status, and explicitly approximate reported scale. Benchmark details can include task count, metric names, evaluation type, and leaderboard URL. Counts of episodes, actions, screenshots, tasks, and instructions are different units. Models can include `artifact_type: model-checkpoint`; family relations prevent treating every checkpoint as an independent project.

`references.jsonl` is a separate discovery graph. Its `mentions` relation only means a URL was found in the source. `target_in_catalog` distinguishes indexed and unresolved targets. Strong reviewed relations remain inside each resource record and in the SQLite `relations` table.

Source data lives in `editorial.json`, `papers.jsonl`, `primary-evidence.jsonl`, `enrichment.jsonl`, `candidates.jsonl`, and discovery manifests. `catalog.jsonl`, `coverage.json`, `references.jsonl`, `review-queue.jsonl`, and category Markdown are generated views. The ignored `.cache/` directory is not needed to reproduce an offline build.
