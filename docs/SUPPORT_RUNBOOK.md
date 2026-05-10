# WSDC Analytics Support Runbook

## Purpose
Single operational flow for routine support: update source data, validate, and publish safely.

## 1) Pre-flight
1. Pull latest `main`.
2. Confirm clean tree:
   - `git status -sb`
3. Confirm critical files exist:
   - `index.html`
   - `points-summary.html`
   - `static/data/articles.json`
   - `static/data/points_summaries.json`

## 2) Data update
Use only durable scripts in `scripts/` for data refresh.

Typical points summary refresh:
```bash
python3 scripts/sync_telegraph_to_site.py "<TELEGRAPH_URL_1>" "<TELEGRAPH_URL_2>"
```

## 3) Local validation
Run validation scripts before commit:
```bash
python3 scripts/validate_site_data.py
python3 scripts/smoke_check_site_files.py
```

## 4) Visual smoke check (manual)
Open and verify:
- `index.html` (cards, language switcher, search)
- `points-summary.html` (expand/collapse, search, mobile behavior)
- one article page in EN and ES variants

## 5) Commit policy
- Commit only files related to one change scope.
- Prefer messages by intent:
  - `ux: improve homepage navigation accessibility`
  - `data: refresh points summaries for week NN`
  - `ci: add site smoke checks`

## 6) Release checklist
- `git status -sb` shows only intentional files.
- Validation scripts pass.
- No accidental deletions in root.
- Push to `main` triggers Pages workflow.

## 7) Incident recovery
If production shows critical regression:
1. Identify last known good commit.
2. Revert only faulty commit(s).
3. Re-run validation scripts.
4. Push revert and verify Pages deploy result.
