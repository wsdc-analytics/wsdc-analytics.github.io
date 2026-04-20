# Scripts

## sync_telegraph_to_site.py

Syncs event data (bracket numbers `[N]` and markers 🟡/🟢) from Telegraph "Full Info" pages into `static/data/points_summaries.json`.

**Usage**

```bash
# From repo root (wsdc-analytics-repo)
python3 scripts/sync_telegraph_to_site.py URL1 [URL2 ...]

# Example
python3 scripts/sync_telegraph_to_site.py "https://telegra.ph/Warsaw-Halloween-Swing---Full-Info-11-08-4"

# Dry run (no file write)
python3 scripts/sync_telegraph_to_site.py --dry-run URL1 URL2

# Custom JSON path
python3 scripts/sync_telegraph_to_site.py --json path/to/points_summaries.json URL1
```

**Options**

- `--json PATH` — path to `points_summaries.json` (default: `static/data/points_summaries.json` relative to repo root).
- `--dry-run` — fetch and match only; do not write JSON.
- `--slug SLUG` — (repeat per URL) match event by slug if same name appears in multiple summaries.
- `--post-date DD-MM-YYYY` — (repeat per URL) match by summary `post_date` for disambiguation.

**Flow**

1. Load `points_summaries.json` once.
2. For each URL: fetch page via `api.telegra.ph/getPage/<path>`, parse event name/dates and divisions/places, find event in JSON by normalized name + dates (or by `--slug` / `--post-date`), replace only `leader` / `follower` / `leaders` / `followers` with Telegraph strings.
3. Save JSON once after all URLs.

**After running**

Commit and push the updated JSON to the site:

```bash
git add static/data/points_summaries.json
git commit -m "Points summary: sync brackets and markers from Telegraph (N events)"
git push
```
