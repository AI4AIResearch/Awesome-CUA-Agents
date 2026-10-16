# AwesomeCUA website

The organization homepage is published at **https://awesomecua.github.io/**. The GitHub organization entry point is **https://github.com/AwesomeCUA**.

The website is a static application: no API keys, account system, paid backend, or analytics. It uses the committed catalog and coverage ledger. Search, filters, pagination, English/Chinese navigation, shareable resource links, evidence details, and downloads work in the browser. Unknown resource metadata remains unknown in the site.

## Build and preview

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist/site
```

Open http://127.0.0.1:4173/. Source files are in `web/`; the deployable static bundle is in `dist/site/`. The bundle includes a compact search index, full resource records, and JSONL/SQLite downloads. It can also be hosted under a subdirectory because application assets use relative URLs.

```bash
node --test tests/web.test.mjs
.venv/bin/python -m unittest discover -s tests -v
```

The `AwesomeCUA/awesomecua.github.io` repository contains the published static snapshot, its own README, contribution issue form, and a `.nojekyll` marker. GitHub Pages serves the `main` branch root. Refresh that repository with a newly verified `dist/site/` build when catalog data changes. The original catalog repository keeps its existing visibility.

The `AwesomeCUA/.github` repository contains the organization profile. Its links lead to the public homepage and public website repository.

The initial browser QA covered desktop and a 390-pixel mobile viewport, catalog/category/platform intersections, detail evidence and license separation, empty results, Chinese UI, and absence of horizontal mobile overflow. The automated tests cover filter behavior, Unicode queries, deep-link state, sorting, metadata review boundaries, and safe rendering of untrusted text/URLs.
