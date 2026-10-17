# Search and SQL

Run commands from the repository root. Search is literal, case-insensitive, AND across words. It covers names, original summaries, aliases, authors, and curated topics. Default output is limited to 20 matches; use `--limit 0` for all matches.

```bash
python3 scripts/catalog.py search "GUI grounding" --limit 10
python3 scripts/catalog.py search --kind dataset --environment android
python3 scripts/catalog.py search --kind benchmark --topic safety-security
python3 scripts/catalog.py search --kind product --status curated --json
python3 scripts/catalog.py search "reinforcement" --kind paper --json
```

Environment and topic filters refer to reviewed facets. Bibliography entries with unreviewed taxonomy use `unspecified` and will not appear in an Android filter merely because the title mentions Android. Search the title when investigating those entries.

```bash
python3 scripts/catalog.py build
sqlite3 dist/catalog.sqlite
```

```sql
-- Curated Android datasets.
SELECT r.name, r.url
FROM resources r
JOIN facets f ON f.resource_id = r.id
WHERE r.kind = 'dataset' AND r.review_status = 'curated'
  AND f.facet = 'environments' AND f.value = 'android'
ORDER BY r.name;

-- FTS5 title/description/author search.
SELECT r.name, r.kind, r.review_status, r.url
FROM resource_search s JOIN resources r ON r.id = s.id
WHERE resource_search MATCH 'grounding'
LIMIT 20;

-- Dataset licenses explicitly declared in publisher metadata.
SELECT name, json_extract(record_json, '$.licenses.data.declared') AS declaration
FROM resources
WHERE kind = 'dataset'
  AND json_type(record_json, '$.licenses.data') = 'object';

-- Offerings linked to selected publishers/brands.
SELECT publisher.name AS publisher, offering.name AS offering, offering.kind
FROM relations rel
JOIN resources offering ON offering.id = rel.source_id
JOIN resources publisher ON publisher.id = rel.target_id
WHERE rel.relation = 'published_by'
ORDER BY publisher.name, offering.name;
```

SQLite uses `resources`, `facets`, `relations`, and `resource_search`. The full record is retained in `resources.record_json`. FTS5 syntax differs from the CLI's literal search. Model variant and publisher counts must not be described as counts of independent projects.

## Agent and RAG access

Clone the complete source catalog with `git clone https://github.com/reacher-z/Awesome-CUA.git`. [AGENTS.md](../AGENTS.md) contains executable local-search examples and a citation-preserving retrieval workflow.

```sh
python3 scripts/export_rag.py --output dist/rag-documents.jsonl
python3 scripts/export_rag.py --include-metadata --output dist/rag-all-records.jsonl
```

The default includes reviewed resources; `--include-metadata` includes every active record with its review state intact. Each row contains `id`, `text`, and `metadata`. Keep citation URLs, evidence, dates, recorded arXiv versions, licenses, and `record_sha256` alongside embeddings. Use IDs for upserts and reconcile removed IDs against the full snapshot and scope ledger. The public [RAG manifest](https://awesomecua.github.io/downloads/rag-manifest.json) gives file counts and SHA-256 fingerprints. Embeddings and upstream paper full text are not part of the export.
