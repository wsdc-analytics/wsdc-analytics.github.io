# Content Map

This map helps find reusable components quickly for article updates.

## Website Pages

- Root-level `*.html` files are primary published pages and article entries.
- Language variants typically follow:
  - RU: `name.html`
  - EN: `name_en.html`
  - ES: `name_es.html`

## Interactive Charts

- Chart pages are standalone HTML files embedded via iframe in article pages.
- Reuse pattern:
  - article page controls chart language via `?lang=ru|en|es`,
  - chart page reads the language parameter and applies labels/translations.

## Data and Backend-like Site Data

- Static website data lives in `static/data/` (for example `articles.json`, `reactions.json`).
- Rule documents and reference files live in `static/rules/`.
- API endpoints and handlers live under `api/`.

## Analysis Scripts and Datasets

- Python scripts in repository root and `scripts/` are used for:
  - data extraction,
  - calculations,
  - article-ready aggregations,
  - publication support.
- CSV and JSON datasets in repository root are working datasets used in weekly updates.

## Reuse Workflow

1. Identify the target article page and language variants.
2. Locate chart iframes used by that article.
3. Locate scripts/datasets that produced the current metrics.
4. Refresh dataset, rerun relevant scripts, update article/chart/static data.
5. Validate all language variants and publish.
