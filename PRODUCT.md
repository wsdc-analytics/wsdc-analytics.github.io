# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: West Coast Swing competitive dancers, event organizers, and analysts who need registry-backed stats, rankings, event context, and research articles.

Secondary: casual WCS community readers browsing published magazine-style articles (EN / RU / ES).

## Product Purpose

WSDC Analytics publishes data-driven insights about the West Coast Swing competitive scene as a static GitHub Pages site. Success means trustworthy metrics and readable analysis that help dancers and organizers understand events, points, geography, and trends.

## Positioning

Independent analytics site based on WSDC registry data and derived datasets — **not** an official WSDC resource (disclosed in site chrome). Combines interactive tools (points, champions, calendars, dashboards) with long-form multilingual articles.

## Operating Context

- Production: https://wsdc-analytics.github.io/
- Content workflows: HTML pages + `static/data/*.json`, automation under `scripts/`, ops docs under `docs/`
- Languages: EN / RU / ES with structural parity across siblings
- Design canon already documented: `docs/DESIGN_GUIDELINE.md`, `docs/DESIGN_SYSTEM_MINI.md`, `docs/DESIGN_CHECKLIST.md`

## Capabilities and Constraints

- Static HTML/CSS/JS site (GitHub Pages); serverless handlers under `api/` for feedback/reactions
- Shared Evolved C chrome (`data-site-chrome`) on navigable product/magazine pages; forbidden on iframe embeddables
- Design tokens: `static/css/tokens.css` (`--wsdc-*`); primitives: `static/css/ui-primitives.css`
- Do not invent WSDC facts, rankings, or testimonials; use repository datasets and cited sources
- Open: which surfaces to redesign first under Impeccable (homepage vs article shell vs dashboards) — decide per task

## Brand Commitments

- Name: **WSDC Analytics**
- Visual identity: **Evolved C** — quiet surfaces, strong type hierarchy, restrained accent blue; no purple-glass AI defaults; no new display fonts (e.g. Manrope)
- Disclaimer: site is based on official WSDC information but is not an official WSDC resource

## Evidence on Hand

- Live site and root HTML pages (`index.html`, article/tool pages)
- Design docs: `docs/DESIGN_*.md`, `docs/SITE_CHROME.md`
- CSS: `static/css/tokens.css`, `site-chrome.css`, `ui-primitives.css`, `article-shell.css`, `dashboard-shell.css`
- Datasets: `static/data/`
- Absence: do not fabricate competitor quotes, official WSDC endorsement, or unverified stats

## Product Principles

1. Accuracy over spectacle — every claim needs data or an explicit source.
2. One shell, many canvases — shared chrome/tokens; page body is tool or reading column.
3. Multilingual parity — EN/RU/ES siblings stay structurally aligned.
4. Desktop and mobile are equal — dedicated stacking, not shrunk desktop toolbars.
5. Preserve Evolved C when refining; redesign only with an explicit replacement brief.

## Accessibility & Inclusion

Baseline from design guideline: `aria-label` on icon controls, skip links, semantic landmarks, keyboard support for custom controls, `prefers-reduced-motion` respected in tokens.
