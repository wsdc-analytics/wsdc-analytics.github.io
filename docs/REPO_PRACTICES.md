# Repository Practices

This repository is the single source of truth for:
- production website content (articles, charts, pages),
- data and scripts used to compute article metrics,
- backend/static data used by frontend pages.

## Scope

Keep in Git:
- article pages (`*.html`) and chart pages,
- reusable scripts used for analysis and publication,
- reusable datasets required to reproduce published numbers,
- API/static data that powers the website.

Do not keep in Git:
- virtual environments,
- Python caches (`__pycache__`, `*.pyc`),
- temporary extracts and one-off local debug files,
- secrets (`.env` and similar).

## Data Update Policy (weekly sources)

- Store current reusable source datasets in the repository.
- Keep reproducible transformation scripts in the repository.
- Avoid committing local temporary intermediates.
- If a dataset grows toward GitHub limits, split old snapshots to external storage/release artifacts and keep only the active baseline in this repository.

## Branch and Commit Policy

- `main` remains deployable.
- Use focused commits with clear scope (article update, data refresh, script fix).
- Before push:
  - `git status` reviewed,
  - only intended files staged,
  - no accidental mass deletions.
