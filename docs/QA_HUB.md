# Q&A / Community Hub

Hub at [`qa.html`](../qa.html): boards, threads, chronological replies. No accounts (display name + optional email). Posts publish immediately; spam is hidden after the fact.

**Language model:** UI is en/ru/es (`?lang=` + chrome); **threads are not split by language** — one shared stream. Placeholders follow the page language.

UI follows Evolved C (`tokens` + `ui-primitives` + site chrome). Chrome has a **chat icon** (left of Contacts) that deep-links to a board from page context — not a primary nav section.

Article feedback forms were replaced by the shared engage block ([`static/js/article-engage.js`](../static/js/article-engage.js)): 👍/👎 + CTA into this hub.

## Boards

| Slug | Title | Chrome `data-active` / context |
|------|--------|--------------------------------|
| `articles` | Articles | articles / `data-qa-board="articles"` |
| `dashboards` | Dashboards | `dashboards` |
| `summary-points` | Summary Points | `points` |
| `new-champions` | New Champions | `champions` |
| `calendar` | Calendar | `calendar` |
| `other` | Other | `home` / unknown / hub itself |

Hash routes: `#board/<slug>`, `#thread/<uuid>`.

Compose defaults to the current board (changeable). From articles: `qa.html?lang=…&page_url=…&title=…#board/articles` prefills related page / title.

## Backend

Schema lives as `qa_*` tables on Supabase project `tougqwxmahkwnaculiju`.

- Migration: [`supabase/migrations/20260826_qa_hub_schema.sql`](../supabase/migrations/20260826_qa_hub_schema.sql)
- Tables: `qa_boards`, `qa_threads`, `qa_posts`
- RLS: public **SELECT** where `not is_hidden`; public **INSERT** with length checks; no public UPDATE/DELETE

Client config (anon key is publishable): [`static/js/qa-config.js`](../static/js/qa-config.js).

i18n dictionary: [`static/js/qa-i18n.js`](../static/js/qa-i18n.js).

## Moderation & Telegram (Vercel)

| Endpoint | Role |
|----------|------|
| `POST /api/qa-mod` | Hide / unhide / pin / unpin / **delete** / **move** (board_slug); `stats`; `list_threads` |
| `POST /api/qa-notify` | Telegram alert after a **fresh** insert |

Env vars: same as before (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `QA_ADMIN_SECRET`, Telegram). See checklist below.

CORS for mod/notify is restricted to `https://wsdc-analytics.github.io` (plus local static previews).

### Env variables — where each value comes from

#### `SUPABASE_URL`

1. Open [Supabase Dashboard](https://supabase.com/dashboard) → project **`tougqwxmahkwnaculiju`**.
2. **Project Settings → API**.
3. Copy **Project URL**.

#### `SUPABASE_SERVICE_ROLE_KEY`

Same page → **`service_role`**. Never commit; Vercel only.

#### `QA_ADMIN_SECRET`

Generate a long random string; set in Vercel; unlock in hub Moderator panel (`localStorage` `qa_admin_secret_v1`).

#### `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`

BotFather + `getUpdates` (see previous setup notes).

#### `QA_SITE_BASE` (optional)

Default `https://wsdc-analytics.github.io`.

### Quick checklist

| Variable | Source | Secret? |
|----------|--------|---------|
| `SUPABASE_URL` | Supabase → Settings → API → Project URL | No |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → `service_role` | **Yes** |
| `QA_ADMIN_SECRET` | You generate | **Yes** |
| `TELEGRAM_BOT_TOKEN` | BotFather | **Yes** |
| `TELEGRAM_CHAT_ID` | `getUpdates` / userinfobot | Semi |
| `QA_SITE_BASE` | Public site origin | No |

Moderation header: `x-qa-admin-secret: <QA_ADMIN_SECRET>`.

## Article reactions (👍/👎)

Replaces Lyket + GitHub `reactions.json` increments.

- Migration: [`supabase/migrations/20260829_article_reactions.sql`](../supabase/migrations/20260829_article_reactions.sql) — **apply in Supabase SQL editor** if not already applied (`article_reaction_votes`, `article_reaction_baseline`).
- API: [`api/reactions.js`](../api/reactions.js) — GET counts, POST upsert/clear vote (needs `SUPABASE_*` on Vercel).
- Client: [`static/js/article-engage.js`](../static/js/article-engage.js) + [`static/css/article-engage.css`](../static/css/article-engage.css).
- Anti-abuse: `localStorage` + cookie `voter_key` (no fingerprint).
- Legacy map: positive→up, negative→down, neutral dropped (baseline seed in migration).
- No reactions inside the Q&A hub (v1).

Mount example:

```html
<link rel="stylesheet" href="static/css/article-engage.css">
<section class="article-engage" data-article-engage data-article-id="rules_evolution_2025_ru" data-lang="ru"></section>
<script src="static/js/article-engage.js" defer></script>
```

Patch helper: [`scripts/patch_article_engage.py`](../scripts/patch_article_engage.py).

## Antispam / privacy (v1)

- Honeypot field `website`
- Min/max lengths (DB check + form)
- ~20s client cooldown per browser
- `author_email` not selectable by anon
- `page_url` must be `https://…`

## Manual test

1. Chrome chat from home → `#board/other`; from Champions → `new-champions`; from article → `articles`.
2. `/qa.html?lang=ru` — UI Russian; switch lang in chrome.
3. Article CTA → hub with `page_url` prefilled; publish thread.
4. 👍/👎 toggle on an article (after migration + Vercel deploy).
5. Unlock moderator → Hide / Pin / **Move** / Delete.

## Out of v1

Language-split boards, reactions on threads, local CTAs on Champions/Points/Calendar, fingerprinting.
