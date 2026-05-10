# Mini Design System (Static Site)

## Design tokens
Source of truth: `static/css/tokens.css`

Core tokens:
- text: `--wsdc-color-text-strong`, `--wsdc-color-text`, `--wsdc-color-text-muted`
- surface: `--wsdc-color-surface`, `--wsdc-color-surface-soft`
- border: `--wsdc-color-border`
- brand: `--wsdc-color-brand`, `--wsdc-color-brand-accent`
- elevation: `--wsdc-shadow-card`

## Component primitives
Use these shared patterns across pages:
1. **Top navigation bar** with visible active language state.
2. **Card list item** with hover/focus affordance.
3. **Search field** with label and clear focus ring.
4. **Expandable blocks** (`aria-expanded` + keyboard toggle).

## Accessibility baseline
- Every interactive icon/button gets `aria-label`.
- Skip link for each major page.
- Use semantic landmarks (`header`, `main`, `footer`).
- Preserve keyboard support for custom controls.
