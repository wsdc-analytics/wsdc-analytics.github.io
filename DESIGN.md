---
name: WSDC Analytics
description: Evolved C — quiet analytics chrome for WCS competitive insights
colors:
  text-strong: "#0b1221"
  text: "#1f2937"
  text-muted: "#4b5563"
  border: "#d1d5db"
  surface: "#ffffff"
  surface-soft: "#f8fafc"
  brand: "#111827"
  brand-accent: "#2563eb"
  danger: "#b91c1c"
  success: "#15803d"
typography:
  body:
    fontFamily: "DM Sans, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: "DM Sans, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.25
  caption:
    fontFamily: "DM Sans, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  pill: "999px"
spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  5: "20px"
  6: "24px"
  8: "32px"
  10: "40px"
  12: "48px"
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  button-accent:
    backgroundColor: "{colors.brand-accent}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "40px"
  pill:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: "6px 12px"
    height: "32px"
---

# Design System

Canonical source for agents. Human-maintained detail lives in `docs/DESIGN_GUIDELINE.md` and `static/css/tokens.css`. Prefer `--wsdc-*` CSS variables in code over hard-coded hex.

## Overview

**Evolved C**: quiet surfaces, strong type hierarchy, restrained accent blue. One shared chrome shell; page bodies are either tool canvases or magazine reading columns. No purple-glass AI aesthetics, no nested card-in-card decoration, no new display fonts.

## Colors

| Role | Token / hex |
|------|-------------|
| Strong text / headings | `--wsdc-color-text-strong` `#0b1221` |
| Body | `--wsdc-color-text` `#1f2937` |
| Muted | `--wsdc-color-text-muted` `#4b5563` |
| Border | `--wsdc-color-border` `#d1d5db` |
| Surface | `--wsdc-color-surface` `#ffffff` |
| Soft panel | `--wsdc-color-surface-soft` `#f8fafc` |
| Brand ink | `--wsdc-color-brand` `#111827` |
| Accent (links, focus) | `--wsdc-color-brand-accent` `#2563eb` |

Do not invent one-off hex for text/border/surface on new UI. Remap legacy locals via `article-shell.css` / tokens.

## Typography

Primary stack: **DM Sans** (Inter only as fallback). Scale from tokens: xs 12 → sm 13 → md 15 → lg 18 → xl 24. Weights 400 / 500 / 600 / 700. Preserve clear heading vs body step (≥1.25×). Do not introduce Manrope or other display faces without an explicit redesign brief.

## Layout

- Chrome max width: `--wsdc-width-chrome` 1200px
- Tool canvas: `--wsdc-width-tool` 860px
- Magazine reading column: `--wsdc-width-reading` 760px
- Fixed chrome pages: `data-fixed="true"` + `wsdc-chrome-page-pad`
- Mobile ≤720px: dedicated chrome stacking (not shrunk desktop toolbar)

Page types: product tool / Tableau shell / magazine / embeddable — see `docs/DESIGN_GUIDELINE.md` §2.

## Elevation & Depth

Use `--wsdc-shadow-card` sparingly. Magazine pages often stay flat. Prefer border + soft surface over layered glass.

## Shapes

Radii: sm 6 / md 8 / lg 10 / pill 999. Controls height 40px (sm 32); tap target min 44px. Focus: `--wsdc-focus-ring` accent outline with offset.

## Components

- **Chrome**: `data-site-chrome` + `site-chrome.css` / `site-chrome.js` (required on navigable pages; forbidden on iframe embeddables)
- **Primitives**: `ui-primitives.css` — buttons, pills, fields, filter bar, info button, page header, `.wsdc-dd` dropdowns (native `<select>` popups not canon)
- **Magazine**: load `article-shell.css` after page inline styles
- **Dashboard shell**: `dashboard-shell.css` for viz hosts
- Back link: `<a class="wsdc-back" data-wsdc-back href="index.html">`

## Do's and Don'ts

**Do**
- Follow `docs/DESIGN_CHECKLIST.md` before PR
- Keep EN/RU/ES structural parity
- Use tokens and `.wsdc-*` primitives
- Add `aria-label` on icon-only controls; skip links; landmarks

**Don't**
- Purple gradients, nested cards, Inter-as-brand, pill-button spam
- Site chrome inside iframe embeddables
- Rewrite copy for “style” alone
- Ship without mobile stacking for toolbars/filters
