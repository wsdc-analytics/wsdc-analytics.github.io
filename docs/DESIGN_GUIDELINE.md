# WSDC Analytics — Design Guideline (Evolved C)

Source of truth for UI architecture on the static site.  
Charts/maps/visual encodings may vary by analysis; **chrome, layout, controls, and typography must not**.

Companion docs:

- Short checklist: [`DESIGN_CHECKLIST.md`](DESIGN_CHECKLIST.md)
- Inventory: [`DESIGN_AUDIT_INVENTORY.md`](DESIGN_AUDIT_INVENTORY.md)
- Chrome API: [`SITE_CHROME.md`](SITE_CHROME.md)
- Mini index: [`DESIGN_SYSTEM_MINI.md`](DESIGN_SYSTEM_MINI.md)

---

## 1. Design principles

1. **Preserve Evolved C** — quiet surfaces, strong type hierarchy, restrained accent blue; no purple-glass AI defaults.
2. **One shell, many canvases** — every navigable page shares chrome + tokens; page body is a tool canvas or a reading column.
3. **Same job → same control** — search, filters, primary actions, info tips, and pills look and sit consistently.
4. **Desktop and mobile are equal** — mobile gets dedicated stacking, not a shrunk desktop toolbar.
5. **Tokens over hex** — new colors/spacing come from `static/css/tokens.css` (`--wsdc-*`).

---

## 2. Page types

| Type | Examples | Chrome | CSS stack |
|------|----------|--------|-----------|
| **Product tool** | home, Points, Champions, Calendar, dashboards, rankings, dancer-profile | Required | `tokens` + `site-chrome` + `ui-primitives` + page CSS |
| **Tableau / viz shell** | `dashboard`, `navigator`, `rankings`, `dancer-profile`, `city-clouds`, secondary-role host | Required | above + `dashboard-shell.css` (token remap + viz layout) |
| **Magazine article** | `article_*`, overview/geo/events/dancers 2025, rules, `events/*/article_*` | Required (usually `data-fixed`) | above + `article-shell.css` **after** inline styles |
| **Embeddable** | `interactive_*`, forecast/risk cards (iframe) | **Forbidden** | `tokens` + `ui-primitives` + page CSS only |

Out of alignment scope (but new work must still follow this guideline): `draft_*`, `source_draft_*`, `_rebuild/`, `wsdc-article/`.

---

## 3. Design tokens

File: [`static/css/tokens.css`](../static/css/tokens.css)

### Color

| Token | Role |
|-------|------|
| `--wsdc-color-text-strong` | Headings, brand emphasis |
| `--wsdc-color-text` | Body |
| `--wsdc-color-text-muted` | Secondary / captions |
| `--wsdc-color-surface` | Page / chrome background |
| `--wsdc-color-surface-soft` | Soft panels |
| `--wsdc-color-border` | Default borders |
| `--wsdc-color-brand` | Primary ink / dark controls |
| `--wsdc-color-brand-accent` | Links, focus, info accents |
| `--wsdc-shadow-card` | Elevation (use sparingly; magazine often flat) |

### Spacing / radius / type / layout (extended)

Use scale tokens (see file): `--wsdc-space-*`, `--wsdc-radius-*`, `--wsdc-font-*`, `--wsdc-width-reading`, `--wsdc-width-tool`, `--wsdc-focus-ring`.

Do **not** add one-off hex for text/border/surface on new UI. Legacy page locals must remap to `--wsdc-*` (article-shell already does for magazine).

---

## 4. Shared chrome

- Mount: `<div data-site-chrome …>` per [`SITE_CHROME.md`](SITE_CHROME.md).
- Always load `site-chrome.css` + `site-chrome.js` with the same cache-bust query when bumping chrome.
- Fixed chrome pages: `data-fixed="true"` + `wsdc-chrome-page-pad` on the main container.
- Back link: `<a class="wsdc-back" data-wsdc-back href="index.html">` (no literal ← in text).
- Lang: RU / EN / ES pills via chrome; keep structural parity across language files.

### Mobile chrome (≤720px)

Follow existing chrome CSS: Dashboards hidden; Points + Champions equal width; Calendar centered on its row. Do not invent a third mobile nav pattern.

---

## 5. Layout shells

### Reading column (magazine)

- Prefer `--wsdc-width-reading` (~700–800px content) inside a wider page pad.
- Section titles: quiet weight; no thick colored rails (article-shell).
- Body copy: justified without hyphenation (article-shell).

### Tool canvas (product)

- Prefer `--wsdc-width-tool` (~860–980px) or full chrome max (`1200px`) for dense tools.
- Page header pattern: title + one subtitle + optional actions row (`.wsdc-page-header`).
- Full-bleed Tableau hosts: use [`dashboard-shell.css`](../static/css/dashboard-shell.css) instead of copying dead header/dropdown CSS; keep chrome + `wsdc-back` only.

### Spacing

- Page horizontal pad: ≥12–16px; section vertical rhythm from `--wsdc-space-6` / `--wsdc-space-8`.
- Control clusters: gap `--wsdc-space-2` / `--wsdc-space-3` (8–12px).

---

## 6. Controls (UI primitives)

File: [`static/css/ui-primitives.css`](../static/css/ui-primitives.css)

| Class | Use |
|-------|-----|
| `.wsdc-btn` + `--primary` / `--secondary` / `--ghost` | Actions |
| `.wsdc-pill` | Status / kind chips |
| `.wsdc-field` | Text inputs / search |
| `.wsdc-filter-bar` | Horizontal filter/toolbar row (stacks on mobile) |
| `.wsdc-info-btn` | Circular «i» tips (match chrome accent behavior) |
| `.wsdc-page-header` | Title + subtitle block |
| `.wsdc-dd` (+ `__btn` / `__value` / `__menu`, `.is-open`) | Compact pill filter dropdown (Calendar, Champions); width via `--wsdc-dd-width` or `.wsdc-dd--auto` |
| `.wsdc-dd--field` + `select.wsdc-select` + `static/js/wsdc-select.js` | Form/chart filters: enhance native `<select>` into the same white anchored menu (no OS black popup) |

Rules:

- Primary action: one per obvious region; secondary for alternatives; ghost for tertiary.
- Min tap target on mobile: ~44px height for icon buttons (info, clear).
- Focus: visible `--wsdc-focus-ring`; never `outline: none` without a replacement.
- Do not relocate the same control to a different structural slot across sibling tools without updating this guideline.
- **Do not ship native `<select>` popups** for in-scope product/magazine/embed UI — they render as OS menus (often dark, detached). Use `.wsdc-dd` or mark `<select class="wsdc-select">` and load `wsdc-select.js`.

---

## 7. Typography

- **UI / body:** DM Sans, fallback Inter / system.
- **Avoid** introducing Manrope or new display faces on product/magazine pages.
- Weights: 400 body, 500/600 UI, 700 sparingly for titles.
- Material Symbols allowed for Calendar map UI only; don’t use as general icon system elsewhere without documenting.

---

## 8. Responsive

Breakpoints in use (document when adding):

- **720px** — chrome mobile layout  
- **700px** — Calendar L2 stack  
- **640px** — Points / tools field stacking  

Patterns:

- Filter bars → column stack; full-width fields.
- No horizontal page overflow; tables scroll inside a wrapper.
- Info tips: viewport-aware (chrome already ports bubbles on mobile).

---

## 9. Accessibility baseline

- Every icon-only control: `aria-label`.
- Skip link on major pages.
- Landmarks: `header` / `main` / `footer` where applicable.
- Keyboard: custom toggles need `aria-expanded` + Enter/Space.
- Honor `prefers-reduced-motion` (tokens already zero out motion).

---

## 10. Charts & visualizations

Allowed to differ: series colors, chart library, mark types, map styling.  
Must still share: page chrome (if navigable), fonts, button/filter chrome around the viz, spacing to page edges.

---

## 11. Languages

- Ship EN/RU/ES structural parity for in-scope pages.
- Same chrome `data-active`, same shell classes, same control order.
- Do not leave a language file without chrome/tokens when siblings have them.

---

## 12. Implementation order for new pages

1. Copy chrome mount + CSS/JS links from a sibling of the same page type.  
2. Link `tokens.css` + `ui-primitives.css`.  
3. Tableau/viz host: also link `dashboard-shell.css`.  
4. Magazine: link `article-shell.css` **last** among CSS.  
5. Use primitives for buttons/fields/pills; page CSS only for unique layout.  
5. Run [`DESIGN_CHECKLIST.md`](DESIGN_CHECKLIST.md) before PR.
