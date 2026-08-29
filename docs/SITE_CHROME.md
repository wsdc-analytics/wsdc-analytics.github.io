# Shared site chrome (Evolved C)

Full design canon: [`DESIGN_GUIDELINE.md`](DESIGN_GUIDELINE.md) · checklist: [`DESIGN_CHECKLIST.md`](DESIGN_CHECKLIST.md).

## Usage

In page `<head>`:

```html
<link rel="stylesheet" href="static/css/tokens.css">
<link rel="stylesheet" href="static/css/ui-primitives.css">
<link rel="stylesheet" href="static/css/site-chrome.css">
<!-- Tableau / full-bleed viz hosts also: static/css/dashboard-shell.css -->
```

Before `</body>`:

```html
<script src="static/js/site-chrome.js" defer></script>
```

Mount point:

```html
<div
  data-site-chrome
  data-active="points"
  data-lang="en"
  data-home-href="index.html"
></div>
```

### Attributes

| Attribute | Values | Notes |
| --- | --- | --- |
| `data-active` | `home` \| `dashboards` \| `points` \| `champions` \| `calendar` \| `articles` \| `qa` | Highlights nav pill; `qa` lights the chat icon |
| `data-qa-board` | board slug | Optional override for Q&A deep-link (e.g. `articles` on magazine pages) |
| `data-lang` | `ru` \| `en` \| `es` | Initial language pills |
| `data-fixed` | `true` | Fixed floating bar (homepage **and magazine articles**) |
| `data-brand` | `logo` (default) \| `text` | WSDC logo links home |
| `data-home-href` | URL | Logo → home (default `index.html`) |
| `data-path-prefix` | path | Prefix for tool + Q&A hrefs from nested pages |
| `data-lang-mode` | `callback` \| `navigate` | Per-lang navigation or callback |
| `data-lang-ru/en/es` | URL | Used with `data-lang-mode=navigate` |
| `data-current-dash` | filename | Marks current Dashboards item |

### Q&A Hub entry

A chat-style icon sits **left of the Contacts envelope**. It is not a primary section pill. Click navigates to:

`qa.html?lang=<lang>#board/<slug>`

| Page context | Board slug |
| --- | --- |
| `champions` | `new-champions` |
| `points` | `summary-points` |
| `calendar` | `calendar` |
| `dashboards` | `dashboards` |
| `articles` / `data-qa-board="articles"` | `articles` |
| `home` / unknown / `qa` | `other` |

See [`QA_HUB.md`](QA_HUB.md).

Includes quiet `i` tips for Dashboards, Summary Points, New Champions, and Events Calendar (hover/focus on desktop; tap-to-toggle on mobile with viewport-fixed bubbles so they are not clipped by the chrome bar). Open/hover/focus uses the blue accent border+glyph (no separate outline), matching page search info buttons. On mobile (≤720px) Dashboards is hidden; row 2 is Summary Points + New Champions at equal width, and Events Calendar sits centered alone on row 3. Top row: logo \| Q&A chat + envelope + language pills.

### Back to home

Production-style link (arrow via CSS `::before`). Place in the article hero or under chrome:

```html
<a class="wsdc-back is-on-hero" href="index.html" data-wsdc-back id="backLink">Back to home</a>
```

- `data-wsdc-back` — label + `index.html?lang=…` synced by `site-chrome.js`
- `is-on-hero` — light text on photo headers; omit on light pages (dashboards, Points Summary)
- Do not put `←` in the text node; CSS draws it

### Homepage hook

```js
window.WsdcChrome.onLangChange = function (lang) {
  setLanguage(lang);
};
```

Add `wsdc-chrome-page-pad` when using `data-fixed="true"` (homepage and magazine articles).

```html
<div
  data-site-chrome
  data-fixed="true"
  data-active="home"
  data-lang="en"
  data-home-href="index.html"
></div>
<div class="wsdc-chrome-page-pad magazine-container">
  …
</div>
```
