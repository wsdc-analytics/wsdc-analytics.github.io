# Mini Design System (Static Site)

> **Full canon:** [`DESIGN_GUIDELINE.md`](DESIGN_GUIDELINE.md) · **PR checklist:** [`DESIGN_CHECKLIST.md`](DESIGN_CHECKLIST.md) · **Audit:** [`DESIGN_AUDIT_INVENTORY.md`](DESIGN_AUDIT_INVENTORY.md)

## Design tokens

Source of truth: `static/css/tokens.css` (`--wsdc-*` colors, spacing, radii, widths, focus).

## Shared chrome (Evolved C)

Source: `static/css/site-chrome.css` + `static/js/site-chrome.js`  
Usage: [`SITE_CHROME.md`](SITE_CHROME.md)

Mount with `<div data-site-chrome …>` — brand · Dashboards · Summary Points · New Champions · Events Calendar · quiet contact · RU/EN/ES.

## UI primitives

Source: `static/css/ui-primitives.css`  
Buttons, pills, fields, filter bar, info button, page header — see guideline §6.

## Dashboard / Tableau shell

`static/css/dashboard-shell.css` — legacy token remap + viz viewport layout for full-bleed dashboard hosts.

## Magazine

`static/css/article-shell.css` after page inline styles. Quiet remaps of legacy locals onto Evolved C tokens.

## Page types (quick)

| Type | Chrome? |
|------|---------|
| Product / magazine | Required |
| iframe embeddable (`interactive_*`, forecast cards) | Forbidden — tokens + primitives only |

## Accessibility baseline

- Every interactive icon/button gets `aria-label`.
- Skip link for each major page.
- Semantic landmarks (`header`, `main`, `footer`).
- Keyboard support for custom controls.
