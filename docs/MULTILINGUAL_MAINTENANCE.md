# Multilingual Maintenance Guide

## Goal
Reduce repeated manual edits across language variants and prevent drift.

## Variant convention
- Base page: `name.html` (RU or default)
- English: `name_en.html`
- Spanish: `name_es.html`

## Shared blocks policy
Keep these blocks aligned across all variants of one page family:
1. top navigation markup,
2. analytics/tracking snippet,
3. base accessibility attributes (`lang`, skip links, aria labels),
4. footer + source links.

## Edit strategy
1. Make shared structural edits in all variants in one commit.
2. Keep language text changes isolated from structural changes.
3. Run site smoke check after every multi-language update.

## Verification checklist
- Variant set exists for target page family.
- Navigation links and query param language handling are consistent.
- Canonical/OG URLs map to correct variant URL.
- No missing headings/landmarks after edit.
