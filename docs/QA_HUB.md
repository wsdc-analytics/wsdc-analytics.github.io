# Q&A / Community Hub

EN-only hub at [`qa.html`](../qa.html): boards, threads, chronological replies. No accounts (display name + optional email). Posts publish immediately; spam is hidden after the fact.

Legacy `article-feedback` forms are unchanged. Site chrome is not linked in v1.

## Boards

| Slug | Title |
|------|--------|
| `articles` | Articles |
| `dashboards` | Dashboards |
| `summary-points` | Summary Points |
| `new-champions` | New Champions |
| `calendar` | Calendar |
| `other` | Other |

Hash routes: `#board/<slug>`, `#thread/<uuid>`.

## Backend

Schema lives as `qa_*` tables on the existing Supabase project `tougqwxmahkwnaculiju` (dedicated project was deferred; plan fallback).

- Migration: [`supabase/migrations/20260826_qa_hub_schema.sql`](../supabase/migrations/20260826_qa_hub_schema.sql)
- Tables: `qa_boards`, `qa_threads`, `qa_posts`
- RLS: public **SELECT** where `not is_hidden`; public **INSERT** with length checks; no public UPDATE/DELETE

Client config (anon key is publishable): [`static/js/qa-config.js`](../static/js/qa-config.js).

## Moderation & Telegram (Vercel)

Primary path matches existing `api/contact.js` / reactions style:

| Endpoint | Role |
|----------|------|
| `POST /api/qa-mod` | Hide / unhide / pin / unpin; `stats`; `list_threads` (incl. hidden) |
| `POST /api/qa-notify` | Telegram alert on new thread/reply (soft-skip if unset) |

Set on the Vercel project (`apiBase` in `qa-config.js`):

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only; never in the browser |
| `QA_ADMIN_SECRET` | Shared secret; paste once in the hub → `localStorage` |
| `TELEGRAM_BOT_TOKEN` | Bot API token |
| `TELEGRAM_CHAT_ID` | Destination chat |
| `QA_SITE_BASE` | Optional; default `https://wsdc-analytics.github.io` |

Moderation header: `x-qa-admin-secret: <QA_ADMIN_SECRET>`.

Optional Edge Function sources (same behaviour) under `supabase/functions/qa-mod` and `qa-notify` if you deploy to Supabase later instead of Vercel.

## Antispam (v1)

- Honeypot field `website`
- Min/max lengths (DB check + form)
- ~20s client cooldown per browser
- Optional email format check on insert

## Manual test

1. Open `/qa.html` → each board lists / creates threads.
2. Reply on a thread; confirm chronological order.
3. With Vercel env set: new post → Telegram ping.
4. Unlock with `QA_ADMIN_SECRET` → Hide / Pin; hidden threads disappear for anon readers.
5. Confirm article feedback forms and chrome unchanged.

## Out of v1

Chrome nav link, RU/ES hubs, replacing article-feedback, accounts, AI digests.
