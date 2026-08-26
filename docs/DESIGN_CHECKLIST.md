# Design Checklist — WSDC Analytics

Must-pass before merging a new or edited **navigable** page, magazine article, or **new draft**.  
Full rules: [`DESIGN_GUIDELINE.md`](DESIGN_GUIDELINE.md).

## Page type

- [ ] Identified as **product tool**, **magazine**, or **embeddable** (iframe child)

## Shared shell (product + magazine only)

- [ ] `tokens.css` linked
- [ ] `site-chrome.css` + `site-chrome.js` linked
- [ ] `ui-primitives.css` linked
- [ ] Tableau/viz host ⇒ `dashboard-shell.css` linked (no leftover local header chrome CSS)
- [ ] `<div data-site-chrome …>` present with correct `data-active` / `data-lang`
- [ ] Fixed chrome ⇒ `data-fixed="true"` + `wsdc-chrome-page-pad` on main container
- [ ] Magazine ⇒ `article-shell.css` loaded **after** inline `<style>`

## Embeddables only

- [ ] **No** floating `data-site-chrome`
- [ ] `tokens.css` + `ui-primitives.css` linked
- [ ] Safe padding when opened top-level

## Layout & controls

- [ ] Reading column vs tool width uses guideline tokens (not a new magic max-width)
- [ ] Buttons/pills/fields/info/dropdowns use `.wsdc-*` primitives (or documented exception)
- [ ] Filter dropdowns use `.wsdc-dd` / `select.wsdc-select` (no native OS popup menus)
- [ ] Filter/search/actions sit in a consistent toolbar region
- [ ] One clear primary action per region

## Typography & color

- [ ] No new hex for text/border/surface — use `--wsdc-*`
- [ ] DM Sans / Inter (no new display font)
- [ ] Focus ring visible on interactive controls

## Responsive

- [ ] Checked ~375px and ~768px widths: no overflow, controls usable
- [ ] Toolbars stack on small screens (mobile-aware, not shrunk desktop)

## Languages

- [ ] EN/RU/ES siblings share the same shell/classes/control order (when page is multilingual)

## A11y

- [ ] Icon-only controls have `aria-label`
- [ ] Custom expanders: `aria-expanded` + keyboard
- [ ] Skip link on major pages (product/magazine)
