# WSDC Analytics Brief (meeting draft)

Draft HTML slides for the WSDC analytics-committee conversation on **Points Registry limits, coverage, and data quality**.

## Status

- **Not linked** from homepage, articles index, or site chrome.
- `noindex, nofollow` on both decks.
- Shareable by direct URL after the usual GitHub Pages deploy of this repo.
- Safe to remove later if the materials should not stay public.

## Files

| File | Purpose |
|------|---------|
| [slides_ru.html](slides_ru.html) | RU working draft (review / rehearsal) |
| [slides_en.html](slides_en.html) | EN adaptation for the call |
| [examples/](examples/) | Screenshots of location/name mess for the DQ slide |

## Share URLs (after deploy to `main`)

- RU: https://wsdc-analytics.github.io/meetings/2026-wsdc-analytics-brief/slides_ru.html
- EN: https://wsdc-analytics.github.io/meetings/2026-wsdc-analytics-brief/slides_en.html

Local preview: open the HTML files in a browser (tokens load from `../../static/css/tokens.css`).

## Navigation

Keyboard: `←` `→` `Space` · click left/right edges of the stage · `#N` deep-link to slide N.

Core path first; **Appendix** slides follow for optional depth.

## Fact notes (as of 2026-08-27)

- Competitor ID only after a point: Registry Event Rules **2026.1B §3.2.2c**.
- Event reporting already includes **list of all competitors registered** in WSDC J&J: **§2.3**. Public Points Registry still exposes scored histories, not that list.
- Scandinavian Open location empty on all **993** local result rows in the current extract.
- Name/series examples checked against `event_aliases.json` and `event_splits_latest.json`.

## Out of scope for this folder

- Publishing into site navigation / CONTENT_MAP as a product page.
- Sharing private pipeline / internal DB schema.
