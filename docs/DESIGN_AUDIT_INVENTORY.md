# Design Audit Inventory — WSDC Analytics

**As of:** 2026-08-26 (wave C/D closeout)  
**Perimeter:** live product + magazine + interactive tools; all EN/RU/ES.  
**Out:** `events/_rebuild/`, `wsdc-article/`, `draft_*` / `source_draft_*`.  
**Aesthetic target:** preserve Evolved C; unify patterns (light polish only).

## Method

- Static scan of in-scope HTML (chrome/tokens/shell/CSS links, max-width, fonts).
- Cross-page comparison of product tools vs magazine shell vs embeddables.
- Mobile notes from media queries (≤640 / ≤700 / ≤720) and `SITE_CHROME.md`.

Severity: **P0** broken/missing shared shell · **P1** visible control/layout drift · **P2** token/typography inconsistency · **P3** polish.

---

## Pattern findings (grouped) — status after waves

### P0 — Missing shared chrome / tokens

| Page | Status |
|------|--------|
| Embeddables | Tokens + primitives wired; chrome **forbidden** (iframe). Locals remapped to `--wsdc-*`. |
| `dancers_2025_ru.html` | Redirect stub to RU canonical — not a shell gap. |

### P1 — Control / layout drift

| Finding | Status |
|---------|--------|
| Content max-width zoo | Named tokens `--wsdc-width-reading` / `--wsdc-width-tool` / `--wsdc-width-chrome` in guideline |
| Button / pill radii | Shared `.wsdc-btn` / `.wsdc-pill`; Points / Champions / Calendar apply primitives |
| Filter / search toolbars | `.wsdc-filter-bar` + field/info on Points, Champions, Calendar |
| Info «i» buttons | `.wsdc-info-btn` on core tools |
| Section headers | `.wsdc-page-header` on core tools; magazine via article-shell |
| Tableau host dead CSS | Removed; shared `dashboard-shell.css` |

### P2 — Typography / color tokens

| Finding | Status |
|---------|--------|
| Dual token systems | Remapped on core tools, dashboard hosts, embeds; magazine via article-shell |
| Font stacks | DM Sans / Inter; Manrope cleared from in-scope pages |
| Google Fonts | Product/magazine load DM Sans + Inter |

### P3 — Polish

- Tool-specific breakpoints (640/700) remain documented as acceptable.
- Calendar/Champions filter dropdowns share `.wsdc-dd` (page CSS only sets `--wsdc-dd-width`).

---

## Page matrix (summary)

### Wave A — Home

| Page | Chrome | Tokens | Notes |
|------|--------|--------|-------|
| `index.html` | yes | yes + primitives | Locals → `--wsdc-*`. Good chrome reference. |

### Wave B — Core tools

| Page | Chrome | Tokens | Notes |
|------|--------|--------|-------|
| `points-summary.html` | yes | remapped | Header + filter-bar + field + info primitives |
| `champion-news.html` | yes | remapped | Header + filter-bar + field/info + shared `.wsdc-dd` |
| `events-calendar.html` | yes | yes | Filter-bar; Clear/search/info + shared `.wsdc-dd`; Leaflet/Material stay tool-local |

### Wave C — Dashboards / tools

| Page | Chrome | Shell | Notes |
|------|--------|-------|-------|
| `dashboard.html`, `navigator.html`, `rankings.html`, `dancer-profile.html`, `city-clouds.html` | yes | `dashboard-shell.css` | Dead local header/dropdown CSS removed |
| `secondary_role_distribution_dashboard_en.html` | yes | dashboard-shell | Pills via `.wsdc-pill` |
| `interactive_*`, forecast/risk cards | no | tokens + primitives + embed-shell | Locals → `--wsdc-*` |

### Wave D — Magazine

| Family | Chrome | Tokens | Article-shell | Notes |
|--------|--------|--------|---------------|-------|
| `article_*` × langs | yes | yes | yes + primitives | Reference |
| `dancers_2025*` / `overview_*` / `geo_*` / `events_2025*` | yes | yes | yes | RU redirect stub OK |
| `rules_*` | yes | yes | yes | OK |
| `events/*/article_*.html` (published) | yes | yes | yes | OK |

---

## Good references (canon)

1. Magazine: tokens + chrome + article-shell + `wsdc-chrome-page-pad` + `wsdc-back`
2. Points / Champions: `.wsdc-page-header` + `.wsdc-filter-bar` + field/info + `.wsdc-dd`
3. Tableau host: chrome + `dashboard-shell.css` only (no duplicate nav CSS)
4. Embed: `wsdc-embed-shell` + tokens + primitives, no chrome

---

## Open P0/P1 before closeout

- [x] Clarify `dancers_2025_ru.html` redirect
- [x] Ship `ui-primitives.css` + wire in-scope pages
- [x] Extend `tokens.css`
- [x] Align embeddables (tokens, no chrome)
- [x] Home / Points / Champions / Calendar primitives + token remap
- [x] Tableau hosts → `dashboard-shell.css`; strip dead CSS
- [x] Secondary-role host pills + shell
- [x] Embed `:root` → `--wsdc-*`
- [x] Docs: guideline / checklist / mini / inventory updated for dashboard-shell
- [x] Extract Calendar/Champions pill dropdowns to shared `.wsdc-dd`

**Open P0/P1/P3 deferred:** none.
