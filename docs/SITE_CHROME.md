# Shared site chrome (Evolved C)

## Usage

In page `<head>`:

```html
<link rel="stylesheet" href="static/css/tokens.css">
<link rel="stylesheet" href="static/css/site-chrome.css">
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
| `data-active` | `home` \| `dashboards` \| `points` \| `champions` | Highlights nav pill |
| `data-lang` | `ru` \| `en` \| `es` | Initial language pills |
| `data-fixed` | `true` | Fixed floating bar (homepage **and magazine articles**) |
| `data-brand` | `logo` (default) \| `text` | WSDC logo links home |
| `data-home-href` | URL | Logo → home (default `index.html`) |
| `data-lang-mode` | `callback` \| `navigate` | Per-lang navigation or callback |
| `data-lang-ru/en/es` | URL | Used with `data-lang-mode=navigate` |
| `data-current-dash` | filename | Marks current Dashboards item |

Includes quiet `i` tips for Dashboards, Summary Points, and New Champions (hover/focus). On mobile (≤720px) Dashboards is hidden; Summary Points and New Champions are centered on the second chrome row.

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
