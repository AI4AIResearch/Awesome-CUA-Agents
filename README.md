# Awesome Computer-Use Agents

**A source-backed data catalog for computer-use, GUI, browser, and mobile agents.**

[Website](https://awesomecua.github.io/) · [GitHub organization](https://github.com/AwesomeCUA) · [简体中文](README.zh-CN.md) · [Coverage ledger](docs/coverage.md) · [Contribute](CONTRIBUTING.md)

The goal is comprehensive coverage of public research and industry resources, with provenance that can be inspected. Papers, models, training data, evaluation environments, frameworks, infrastructure, products, and publishers belong in the same searchable catalog.

**Global completeness is a goal, not a verified claim.** We publish the source populations, review states, and remaining gaps. Bibliographic metadata verification is different from reviewing a resource's relevance or quality.

<!-- STATS:START -->

**2,025 resource records** · **501 curated** · **1,764 arXiv records** · **29 discovery documents**

Evidence through `2026-10-16T11:15:55Z`. 1,524 records have bibliographic verification only; 727 discovered identifiers remain unindexed. Counts overlap as explained below.

<!-- STATS:END -->

## Explore

| Research and training | Engineering and industry |
| --- | --- |
| [Research bibliography](docs/papers.md) | [Agents](docs/agents.md) |
| [Surveys](docs/surveys.md) | [Frameworks](docs/frameworks.md) |
| [Datasets](docs/datasets.md) | [Infrastructure](docs/infrastructures.md) |
| [Benchmarks](docs/benchmarks.md) | [Tools](docs/tools.md) |
| [Models and checkpoint releases](docs/models.md) | [Products](docs/products.md) · [Publishers and brands](docs/companies.md) |

Coverage spans web, desktop, Android, iOS, Windows, macOS, Linux, and cross-platform work. Topics include grounding, screen understanding, planning, memory, long-horizon workflows, reinforcement learning, data generation, safety, robustness, and evaluation. Environment facets overlap; framework support is not assumed from a model's benchmark results.

## Use the data

Browse the [interactive website](https://awesomecua.github.io/) to search and filter all resources, inspect source evidence, switch between English and Chinese, or download the complete catalog. [Website development and publishing](docs/website.md).

[Reviewed research](https://awesomecua.github.io/papers/) · [Computer-use agent guides](https://awesomecua.github.io/guides/) · [Static resource directory](https://awesomecua.github.io/catalog/) · [Search and AI discovery](docs/search-discovery.md)

- **[Catalog JSONL](data/catalog.jsonl):** one resource per line, with stable IDs, typed fields, provenance, scoped licenses, and review status.
- **[Reference graph](data/references.jsonl):** outbound references from primary sources. `mentions` does not mean `trained_on` or `evaluated_on`.
- **[Discovery registry](data/sources.json)** and **[candidates](data/candidates.jsonl):** source snapshots and where each identifier was found.
- **[Review queue](data/review-queue.jsonl):** unresolved evidence, unindexed discoveries, and proposals requiring editorial work.
- **[JSON Schema](schemas/resource.schema.json)** and **[coverage JSON](data/coverage.json):** machine-checkable contracts and coverage accounting.

```bash
# Python 3.11+. Search and export require only the standard library.
python3 scripts/catalog.py search "grounding" --kind model
python3 scripts/catalog.py search --kind dataset --environment android
python3 scripts/catalog.py search --kind product --status curated --json
python3 scripts/catalog.py build
# Creates dist/catalog.sqlite and dist/catalog.json, with no network calls.
```

Use SQLite to join resources, environment/topic facets, and reviewed relations. See [query examples](docs/query-guide.md). `data/catalog.jsonl` is committed; SQLite and JSON array exports are reproducible local build products.

## What “verified” means

| State | What has been checked | What has not been established |
| --- | --- | --- |
| `curated` | AI-assisted editorial review against a first-party source snapshot, with name, scope, summary, and taxonomy | Independent reproduction, universal availability, or endorsement |
| `metadata_verified` | Bibliographic identity, title, authors, and dates returned by arXiv | Topic relevance, methodology, findings, or inclusion in the core field |
| `candidate` | A normalized URL or identifier was discovered | Inclusion, correctness, or availability; excluded from the published catalog |

Counts refer to **resources**, not unique projects. A paper, repository, dataset release, model checkpoint, product, and publisher can be separate related resources. Model families and individual checkpoints are explicitly linked where reviewed.

Code, data, weights, and document licenses are separate. Missing values are `null`. Dataset archive counts are not converted into training-example counts. Scores from different benchmark versions, splits, action budgets, or evaluators are not combined into a ranking.

## Maintain and verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/catalog.py validate
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/catalog.py build --check
```

Network discovery and verification are explicit commands; ordinary builds are offline. Changed primary snapshots require another editorial review before publication. [Maintenance guide](docs/maintenance.md) · [Methodology](docs/methodology.md) · [Data dictionary](docs/data-dictionary.md)

## Acknowledgments and reuse

The [source registry](data/sources.json) credits the community collections and surveys used for discovery. The catalog obtains authoritative bibliographic metadata from arXiv and checks selected assets against publisher repositories, documentation, and model/dataset cards. Upstream READMEs, papers, model weights, and datasets are not redistributed here.

Original repository code and annotations use the [MIT license](LICENSE). Linked resources retain their own terms; this repository does not relicense them.
