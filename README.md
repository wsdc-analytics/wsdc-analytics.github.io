# WSDC Analytics

Data-driven insights about the West Coast Swing competitive scene, published as a static GitHub Pages website.

## Start here

| Door | URL |
|------|-----|
| **Live site** | [wsdc-analytics.github.io](https://wsdc-analytics.github.io/) |
| **Event Growth (EN)** | [event_growth_dashboard_en.html](https://wsdc-analytics.github.io/event_growth_dashboard_en.html) |
| **Event locations data guide** | [docs site](https://zlat1109.github.io/wsdc-data-pipeline/committee/event-locations-guide/) · [GitHub](https://github.com/zlat1109/wsdc-data-pipeline/blob/main/docs/committee/event-locations-guide.md) |
| **Growth payload** | [`static/data/event_growth.json`](static/data/event_growth.json) |

Upstream CSV source of truth: [zlat1109/wsdc-data-pipeline](https://github.com/zlat1109/wsdc-data-pipeline) (`data/location_info.csv`, `data/event_editions.csv`, …). The pipeline feeds this site after each successful export.

## Production Site

- Main: `https://wsdc-analytics.github.io/`
- Homepage source: `index.html`
- Points summary source: `points-summary.html`

## Repository Layout

- Root `*.html` — published pages and language variants.
- `static/data/` — site datasets (`articles.json`, `points_summaries.json`, `event_growth.json`, etc).
- `static/css/`, `static/js/` — reusable frontend assets.
- `api/` — serverless handlers for feedback/reactions.
- `scripts/` — data and support automation scripts.
- `docs/` — operational and architectural guidance.
- `docs/archive/root-notes/` — historical setup / brainstorm notes (not required to run the site).

## Support and Operations

- Baseline audit: [docs/AUDIT_BASELINE_2026-05.md](docs/AUDIT_BASELINE_2026-05.md)
- Support runbook: [docs/SUPPORT_RUNBOOK.md](docs/SUPPORT_RUNBOOK.md)
- Multilingual maintenance: [docs/MULTILINGUAL_MAINTENANCE.md](docs/MULTILINGUAL_MAINTENANCE.md)
- Mini design system: [docs/DESIGN_SYSTEM_MINI.md](docs/DESIGN_SYSTEM_MINI.md)
- Design guideline: [docs/DESIGN_GUIDELINE.md](docs/DESIGN_GUIDELINE.md)
- Design checklist (PR must-pass): [docs/DESIGN_CHECKLIST.md](docs/DESIGN_CHECKLIST.md)
- Design audit inventory: [docs/DESIGN_AUDIT_INVENTORY.md](docs/DESIGN_AUDIT_INVENTORY.md)
- SEO template: [docs/SEO_TEMPLATE.md](docs/SEO_TEMPLATE.md)
- Repository practices: [docs/REPO_PRACTICES.md](docs/REPO_PRACTICES.md)
- Content map: [docs/CONTENT_MAP.md](docs/CONTENT_MAP.md)
- Scripts usage: [scripts/README.md](scripts/README.md)

## Data Source

Primary source is the WSDC registry data and derived analysis datasets maintained in this repository, refreshed from the WSDC data pipeline exports.

## License

Content and analysis © 2025-2026. Data sourced from WSDC database and public WSDC resources.
