# Design Audit Inventory — WSDC Analytics

**As of:** 2026-08-26  
**Perimeter:** live product + magazine + interactive tools; all EN/RU/ES.  
**Out:** `events/_rebuild/`, `wsdc-article/`, `draft_*` / `source_draft_*`.  
**Aesthetic target:** preserve Evolved C; unify patterns (light polish only).

## Method

- Static scan of 52 in-scope HTML files (chrome/tokens/shell/CSS links, max-width, fonts).
- Cross-page comparison of product tools (home, Points, Champions, Calendar) vs magazine shell vs embeddables.
- Mobile notes from existing media queries (≤640 / ≤700 / ≤720) and `SITE_CHROME.md` mobile chrome rules.

Severity: **P0** broken/missing shared shell · **P1** visible control/layout drift · **P2** token/typography inconsistency · **P3** polish.

---

## Pattern findings (grouped)

### P0 — Missing shared chrome / tokens

| Page | Issue |
|------|--------|
| Embeddables (see below) | No chrome/tokens historically — now wired to tokens + primitives; chrome remains **forbidden** (iframe) |

**Note:** `dancers_2025_ru.html` is a **redirect stub** to `dancers_2025.html` (RU canonical). Not a missing-shell bug.

**Embeddable tools** (iframe children; parent article owns chrome):

- `interactive_*.html` (5)
- `forecast_*_card.html`, `risk1_role_balance_card.html`

**Canon:** embeddables use tokens + UI primitives + shared type; **do not** mount floating site chrome.

### P1 — Control / layout drift

1. **Content max-width zoo:** magazine often `700`–`980`; Points `860`; chrome wrap `1200`; misc `560`/`780`/`820`. Reading column vs tool canvas not named in tokens.
2. **Button / pill radii:** `4px`, `6px`, `8px`, `999px`, `var(--radius)` — no shared button primitive classes on product pages.
3. **Filter / search toolbars:** Points Summary search+info pattern differs from Calendar filter row and Champions controls (spacing, info-button size, focus).
4. **Info «i» buttons:** chrome tips use blue accent; some page-local info buttons diverge in size/hit area (mobile tap).
5. **Section headers:** magazine remapped via `article-shell.css`; product tools use one-off `.page-header` / `.subtitle` recipes.

### P2 — Typography / color tokens

1. **Dual token systems:** pages define local `--color-primary`, `--text-*`, `--bg-*` while also loading `--wsdc-*` from `tokens.css`. Article-shell remaps locals → Evolved C; product pages often keep parallel locals that drift (e.g. home `--border-color: #e5e7eb` vs token `#d1d5db`).
2. **Font stacks:** mostly DM Sans + Inter; some magazine/event pages pull **Manrope**; Material Symbols on calendar. Canon face = DM Sans / Inter.
3. **Google Fonts load:** 49/52 pages; embeddables often inherit or skip — inconsistent FOUT/FOIT.

### P3 — Polish / lang parity

1. `dancers_2025_ru.html` structural lag (P0 above) is the main lang parity break.
2. Event series articles (Arizona, UK) aligned to chrome+shell; good reference for magazine.
3. Mobile chrome (≤720): documented in `SITE_CHROME.md`; product pages add extra breakpoints at 640/700 — acceptable if documented as tool-specific, but spacing tokens should still match.

---

## Page matrix (summary)

### Wave A — Home

| Page | Chrome | Tokens | Shell | Notes |
|------|--------|--------|-------|-------|
| `index.html` | yes | yes | n/a | Local `:root` duplicates tokens (P2). Fixed chrome + `wsdc-chrome-page-pad`. **Good chrome reference.** |

### Wave B — Core tools

| Page | Chrome | Tokens | Notes |
|------|--------|--------|-------|
| `points-summary.html` | yes | yes | Search/info pattern strong; max-width 860; local radius vars (P1/P2). |
| `champion-news.html` | yes | yes | Similar product shell to Points. |
| `events-calendar.html` | yes | yes | Heavy page CSS; Leaflet; Material icons; filters differ from Points (P1). |

### Wave C — Dashboards / tools

| Page | Chrome | Tokens | Notes |
|------|--------|--------|-------|
| `dashboard.html`, `navigator.html`, `rankings.html`, `dancer-profile.html`, `city-clouds.html`, `secondary_role_distribution_dashboard_en.html` | yes | yes | Tool canvases; align chrome pad + control primitives. |
| `interactive_*`, forecast/risk cards | no | no | Embed shell (tokens+primitives only). |

### Wave D — Magazine

| Family | Chrome | Tokens | Article-shell | Notes |
|--------|--------|--------|---------------|-------|
| `article_*` (3yr, division, secondary) × langs | yes | yes | yes | Strong reference. |
| `dancers_2025*` | yes | yes | yes | RU file redirects to `dancers_2025.html`. |
| `rules_catalog*`, `rules_evolution_2025*` | yes | yes | yes | OK. |
| `events/*/article_*.html` (published) | yes | yes | yes | Good. |

---

## Good vs bad examples (for canon discussion)

**Good**

1. Magazine page with tokens + site-chrome + article-shell + `wsdc-chrome-page-pad` + `wsdc-back`.
2. Points Summary: quiet chrome, clear search field + info affordance.
3. Shared chrome mobile stacking (≤720) per `SITE_CHROME.md`.

**Bad / drift**

1. `dancers_2025_ru.html` was flagged initially — confirmed **redirect** to RU canonical `dancers_2025.html`.
2. Home inline `:root` shadow/border values fighting `tokens.css` — remapped to `--wsdc-*`.
3. Calendar filters vs Points search — shared `wsdc-filter-bar` / page-header / info primitives applied on core tools.

---

## Recommended canon directions (input to guideline)

1. **Single token source:** `--wsdc-*` only; page locals remap via article-shell or thin page adapters — do not invent new hex for text/border/surface.
2. **Spacing scale + content widths:** tool canvas vs reading column named tokens.
3. **UI primitives:** `.wsdc-btn`, `.wsdc-btn--primary|secondary|ghost`, `.wsdc-pill`, `.wsdc-field`, `.wsdc-filter-bar`, `.wsdc-info-btn`, `.wsdc-page-header`.
4. **Chrome mandatory** on navigable product + magazine pages; **forbidden** on iframe embeddables.
5. **Type:** DM Sans + Inter; Manrope deprecated for new work.
6. **Desktop + mobile equal priority;** mobile-aware stacking (don’t force desktop toolbars onto ≤720).

---

## Open P0/P1 before closeout

- [x] Clarify `dancers_2025_ru.html` redirect (not a shell gap)
- [x] Ship `ui-primitives.css` + wire core tools / magazine / embeds
- [x] Extend `tokens.css` with spacing/width/radius/focus
- [x] Align embeddables to tokens (no chrome)
- [x] Reduce home local token duplication (remap to `--wsdc-*`)
- [x] Points / Champions / Calendar headers + filter primitives  
