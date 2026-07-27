# Event portraits

Long-form portraits of individual WSDC events (Skill JJ points registry).

## Writing rules

Series editorial guide (conclusion-first sections, charts after insight, Summary as synthesis):  
→ workspace docs: `projects/wsdc/docs/events/EVENT_ARTICLE_SERIES_WRITING.md`  
(also mirrored below if present in this repo: `EVENT_ARTICLE_SERIES_WRITING.md`)

## Status

Drafts under `events/` are **not** linked from the homepage or `static/data/articles.json` until ready to publish.

**Published:** [`001-arizona-4th-of-july/`](001-arizona-4th-of-july/) (RU/EN/ES) — on homepage and in `articles.json` since 2026-07-22.

**On site, not on homepage yet:** [`002-uk-wcs-championships/`](002-uk-wcs-championships/) (RU/EN/ES production articles; not in `articles.json`).

## Naming

`NNN-<region-or-state>-<event-slug>/`

Examples:
- `001-arizona-4th-of-july/` — Arizona is the state; the event is Phoenix 4th of July / 4th of July Convention.
- `002-uk-wcs-championships/` — UK is the country; the event is UK WCS Championships (London).

## Hero (locked)

Shared underlay for every event portrait:

- **File:** [`assets/hero_underlay.png`](assets/hero_underlay.png)
- **Do not replace** without an explicit series-wide decision.

Stack (bottom → top), same brightness family as other article heroes (`#2d3748` wash ≈ 0.5):

1. full event asset from the event site (`contain`, slightly scaled down so the whole graphic is visible)
2. locked ChatGPT underlay (`../assets/hero_underlay.png`, screen mix) as the series retouch layer
3. slate wash (`#2d3748` gradient) for title readability
4. title / subtitle text

## Pilot

- [`001-arizona-4th-of-july/article_ru.html`](001-arizona-4th-of-july/article_ru.html) · [`article_en.html`](001-arizona-4th-of-july/article_en.html) · [`article_es.html`](001-arizona-4th-of-july/article_es.html)
- Rebuild from `source_draft_ru.html` + `i18n.json`: `python3 scripts/build_arizona_event_articles.py`
- `draft_ru.html` redirects to `article_ru.html` (old URL)
- **Published** on homepage (`static/data/articles.json`) since 2026-07-22

## UK WCS Championships (002)

- [`002-uk-wcs-championships/article_ru.html`](002-uk-wcs-championships/article_ru.html) · [`article_en.html`](002-uk-wcs-championships/article_en.html) · [`article_es.html`](002-uk-wcs-championships/article_es.html)
- Rebuild from `source_draft_ru.html` + `i18n.json`: `python3 scripts/build_uk_event_articles.py`
- `draft_ru.html` redirects to `article_ru.html`
- **Not on homepage** until approved (`articles.json` unchanged)
