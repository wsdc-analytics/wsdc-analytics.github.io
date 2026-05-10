# WSDC Analytics Baseline Audit (2026-05)

## Scope
- Repository: `wsdc-analytics.github.io`
- Production site: `https://wsdc-analytics.github.io/`
- Priority focus: UX/design + maintainable support workflow

## Current System Snapshot
- Static site with root-level `*.html` pages and data-backed rendering from `static/data/*.json`.
- Data preparation and maintenance scripts are split between repo root and `scripts/`.
- GitHub Pages deployment is configured via `.github/workflows/pages.yml`.
- API handlers (`api/contact.js`, `api/reactions.js`) support feedback and reactions flows.

## Key Technical Risks
1. Large amount of root-level files (html/csv/py/assets) increases accidental-change risk.
2. Duplicate UI logic exists across pages and language variants.
3. `index.html`/`points-summary.html` rely on large inline style/script blocks.
4. No mandatory data integrity checks before deploy.
5. No site smoke checks in CI for critical paths (`index`, `points-summary`, `sitemap`, `articles.json`).

## Key UX/Design Risks
1. Inconsistent interaction patterns between homepage and secondary pages.
2. Limited shared design primitives (tokens/components) reused across pages.
3. Accessibility implementation is uneven (aria labels and explicit landmark clarity vary by page).
4. Mobile behavior requires explicit regression checks for top navigation + cards + search.

## Baseline Controls (starting point)
- Core pages for regression checks:
  - `index.html`
  - `points-summary.html`
  - `overview_2025_en.html`
  - `events_2025_en.html`
- Core data contracts:
  - `static/data/articles.json`
  - `static/data/points_summaries.json`
- Deploy-critical files:
  - `.github/workflows/pages.yml`
  - `sitemap.xml`
  - `robots.txt`

## Success Metrics for This Improvement Cycle
- Homepage and points-summary UI use shared design tokens.
- Baseline accessibility checks pass for key controls and landmarks.
- CI blocks deploy on invalid JSON structure or missing critical pages/assets.
- Support runbook allows routine data/content update without ad-hoc steps.
