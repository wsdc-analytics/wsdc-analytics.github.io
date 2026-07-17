# Mini Design System (Static Site)

## Design tokens
Source of truth: `static/css/tokens.css`

Core tokens:
- text: `--wsdc-color-text-strong`, `--wsdc-color-text`, `--wsdc-color-text-muted`
- surface: `--wsdc-color-surface`, `--wsdc-color-surface-soft`
- border: `--wsdc-color-border`
- brand: `--wsdc-color-brand`, `--wsdc-color-brand-accent`
- elevation: `--wsdc-shadow-card`

## Shared chrome (Evolved C)
Source of truth: `static/css/site-chrome.css` + `static/js/site-chrome.js`  
Usage notes: `docs/SITE_CHROME.md`

Mount with `<div data-site-chrome …>` — brand · Dashboards · Summary Points · quiet contact · RU/EN/ES.

## Component primitives
Use these shared patterns across pages:
1. **Top navigation bar** via shared chrome (active language state on pills).
2. **Card list item** with hover/focus affordance (homepage uses divider list).
3. **Search field** with label and clear focus ring (secondary on Points Summary).
4. **Expandable blocks** (`aria-expanded` + keyboard toggle).
5. **Magazine article shell** via `static/css/article-shell.css` (quiet Evolved C remaps; keep content/structure).

## Accessibility baseline
- Every interactive icon/button gets `aria-label`.
- Skip link for each major page.
- Use semantic landmarks (`header`, `main`, `footer`).
- Preserve keyboard support for custom controls.
