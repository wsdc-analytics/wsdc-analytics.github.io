# Event portraits

Long-form portraits of individual WSDC events (Skill JJ points registry).

## Status

Drafts under `events/` are **not** linked from the homepage or `static/data/articles.json` until ready to publish.

## Naming

`NNN-<region-or-state>-<event-slug>/`

Example: `001-arizona-4th-of-july/` — Arizona is the state; the event is Phoenix 4th of July / 4th of July Convention.

## Hero (locked)

Shared underlay for every event portrait:

- **File:** [`assets/hero_underlay.png`](assets/hero_underlay.png)
- **Do not replace** without an explicit series-wide decision.

Stack (bottom → top), same brightness family as other article heroes (`#2d3748` wash ≈ 0.5):

1. blurred event asset from the event site (`assets/hero_fullwidth.png` or logo)
2. locked ChatGPT underlay (`../assets/hero_underlay.png`, screen + opacity)
3. slate wash (`#2d3748`)
4. title / subtitle text

## Pilot

- [`001-arizona-4th-of-july/draft_ru.html`](001-arizona-4th-of-july/draft_ru.html)
