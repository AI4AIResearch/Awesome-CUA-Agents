# Scope and methodology

The unit of the catalog is a **resource**. A research paper, dataset release, model checkpoint, repository, product, and publisher entity have distinct identities even when they belong to the same project. Totals must always be accompanied by kind and review-state breakdowns.

## Inclusion boundary

Core resources concern agents that observe and interact with graphical interfaces, web pages, desktop applications, or mobile devices. Hybrid GUI/code/API interaction is included when computer interaction is material to the work. GUI grounding, screen understanding, training data, evaluation, execution environments, and safety research are in scope.

Supporting automation libraries and workflow recording tools may be marked `adjacent`. Generic coding assistants, LLM frameworks, RPA vendors, and crawlers are not automatically core CUA resources. Discovery can contain such items; discovery is not inclusion.

## Discovery and authority

1. Community collections and survey repositories supply candidate identifiers. They are credited, but do not establish the correctness of a resource's claims.
2. A separate, timestamped arXiv title query supplies primary-source candidates. Its exact expression, cutoff, pagination, and reported population are saved.
3. arXiv's API supplies bibliographic facts. Full abstracts and papers are not copied into the catalog.
4. Editorial resources use official repositories, publisher documentation, and model/dataset cards. A reachable page or name match alone is insufficient for curation.
5. Editorial decisions are AI-assisted, not an assertion of independent human peer review. The reviewed content digest is recorded. A changed snapshot cannot inherit approval merely because its URL still works.

## Identity and deduplication

- arXiv PDF, abstract, HTML, versioned URLs, and Hugging Face paper mirrors map to one version-independent arXiv ID.
- GitHub repository spelling/case, `.git`, and repository-file links fold to a repository ID for discovery.
- Explicit `component:` IDs distinguish reviewed assets inside a monorepo.
- `organization:` IDs distinguish publisher/brand entities from their offerings; these do not assert legal incorporation or ownership.
- Other URLs lose fragments and common tracking parameters. Similar titles are not automatically merged.
- Redirects, project renames, dataset mirrors, and model variants require continued editorial entity resolution. Source coverage is conservative and does not assume that similar names are equivalent.
- When an author explicitly identifies an accidental duplicate submission, `identifiers.preferred_arxiv` records the preferred identifier with primary evidence. The duplicate stays accessible as bibliographic provenance and cannot be promoted as another curated paper. Similar titles alone do not establish this relationship.

## Explicit scope review

`data/exclusions.json` records individually reviewed, out-of-scope bibliographic snapshots. These are relevance decisions based on primary abstracts, not assessments of research quality. Keywords never create an exclusion automatically. Each decision binds to the reviewed metadata fingerprint and a primary evidence receipt; changed ingested metadata, missing evidence, or a queued upstream metadata change reopens the decision and leaves the record visible as pending review.

The raw arXiv archive retains every ingested record. Applied exclusions are absent from the active catalog, search, and SQLite export, but their previous resource URLs remain accessible as `noindex` scope explanations. The generated `data/exclusion-status.json` separates applied decisions from revalidation requests. Discovery counts distinguish indexed, excluded, and unresolved identifiers.

Curated inclusion cannot conflict with an exclusion, and scope changes cannot silently break retained relationships. Correct a decision through a source-backed edit to the ledger; version control preserves its history. The input contract is `schemas/scope-decision.schema.json`.

## Evidence and unknowns

Every published record has a primary URL, retrieval timestamp, SHA-256 of the fetched response, and the fields supported by that evidence. Upstream raw responses stay in an ignored local cache; committed receipts retain attribution and fingerprints. A digest verifies identity when the response is available; it does **not** guarantee that a mutable upstream URL can recreate an old snapshot.

Some dataset cards contain only licensing metadata. For these entries, Hub metadata establishes identity and licensing while an inspected project README supports the description and scope. Editorial inputs retain these as `additional_evidence` with separate content hashes and field scopes. Refreshing either required source with changed or unavailable content revokes the verification match until another review.

`published_at` is the original arXiv publication date where available. Retrieval dates never substitute for release dates. Unknown dates, size, licenses, and pricing are null. A hub size category can refer to packaged files, so it is not interpreted as a sample count. Publisher claims and independent measurements are not interchangeable.

License declarations are scoped to code, data, weights, or documents. Repository LICENSE headers never establish permissions for weights or embedded third-party data. No blanket permissive license is inferred from public availability.

`mentions` edges record references found in a primary README/card. They do not establish training, evaluation, derivation, partnership, or endorsement. Stronger relations are explicit editorial assertions with evidence.

When a paper documents an implementation that is not cited back by the repository, an editorial `reviewed_relations` entry may cite the paper's retained evidence receipt. Its evidence URL must exist in the resource's evidence list. This does not imply that current code reproduces the paper's results.

## Coverage denominator

The coverage ledger measures how many normalized identifiers from each successfully fetched source snapshot have a catalog record. A source may include incidental or out-of-scope links. Multiple sources overlap; their counts cannot be summed into a unique field size. Failed refreshes are shown as failures; previous successful local cache data are not presented as a fresh successful fetch.

The arXiv title-query population is also bounded. It misses papers with different terminology and work on other publication platforms. Neither list-union coverage nor title-query recall proves global completeness. Regional/language-specific products, closed data, unpublished systems, and detailed benchmark protocols remain active curation gaps.

## Performance comparisons

This release does not publish a unified leaderboard. A future score observation must include model/checkpoint, benchmark/version, split, metric, action/step budget, evaluator, run date, evidence, and whether it is publisher-reported or independently reproduced. Without that context, results must not be ranked together.
