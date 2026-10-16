# AwesomeCUA website

The organization homepage is published at **https://awesomecua.github.io/**. The GitHub organization entry point is **https://github.com/AwesomeCUA**.

The website combines a static interactive application with complete HTML resource pages and reading guides. Search, filters, pagination, English/Chinese navigation, source evidence, and downloads use the committed catalog. Unknown resource metadata remains unknown. [Search and AI discovery](search-discovery.md) documents canonical pages, sitemap policy, structured data, and submission receipts.

## Build and preview

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist/site
```

Open http://127.0.0.1:4173/. Source files are in `web/`; the deployable static bundle is in `dist/site/`. The bundle includes the search index, resource HTML/Markdown, guides, and JSONL/SQLite downloads. Discovery pages are configured for the root of `https://awesomecua.github.io/`; changing the origin or deploying under a subdirectory requires updating the canonical URLs and internal paths.

```bash
node --test tests/web.test.mjs
.venv/bin/python -m unittest discover -s tests -v
```

The `AwesomeCUA/awesomecua.github.io` repository contains the published static snapshot and a scheduled GitHub Pages Actions workflow. It checks out the public `reacher-z/Awesome-CUA` source, validates it, rebuilds, updates the static snapshot, and deploys the artifact. Publication runs twice daily and on website-repository pushes. The [update status page](https://awesomecua.github.io/updates/) links to actual scan receipts.

The `AwesomeCUA/.github` repository contains the organization profile. Its links lead to the public homepage and public website repository.

The initial browser QA covered desktop and a 390-pixel mobile viewport, catalog/category/platform intersections, detail evidence and license separation, empty results, Chinese UI, and absence of horizontal mobile overflow. The automated tests cover filter behavior, Unicode queries, deep-link state, sorting, metadata review boundaries, and safe rendering of untrusted text/URLs.
