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

Where to put them: [Vercel Dashboard](https://vercel.com) → project that serves `https://wsdc-analytics-github-io.vercel.app` (same as reactions/contact) → **Settings → Environment Variables** → add for **Production** (and Preview if you test PRs) → **Redeploy** the latest deployment so functions pick up new vars.

Client `apiBase` in [`static/js/qa-config.js`](../static/js/qa-config.js) must match that Vercel host.

### Env variables — where each value comes from

#### `SUPABASE_URL`

1. Open [Supabase Dashboard](https://supabase.com/dashboard) → project **`tougqwxmahkwnaculiju`** (org project that already has `qa_*` tables).
2. **Project Settings → API** (or **Connect**).
3. Copy **Project URL** — looks like `https://tougqwxmahkwnaculiju.supabase.co`.

Same value as `supabaseUrl` in `qa-config.js`.

#### `SUPABASE_SERVICE_ROLE_KEY`

1. Same page: **Project Settings → API**.
2. Under **Project API keys**, copy **`service_role`** (`secret`) — **not** the `anon` / publishable key.
3. Paste only into Vercel env. Never commit it, never put it in `qa-config.js` or the browser.

This key bypasses RLS so `qa-mod` can hide/pin and list hidden threads.

#### `QA_ADMIN_SECRET`

1. **You invent this** — a long random string (password manager / `openssl rand -hex 32`).
2. Set the **same** string in Vercel as `QA_ADMIN_SECRET`.
3. On the live hub, paste it once into **Moderator secret** → Unlock (stored in browser `localStorage` as `qa_admin_secret_v1`).

Anyone who knows this secret can hide/pin. Rotate by changing Vercel + re-unlocking in the browser.

#### `TELEGRAM_BOT_TOKEN`

1. In Telegram, open [@BotFather](https://t.me/BotFather).
2. `/newbot` (or `/mybots` → existing bot) → copy the **HTTP API token** (`123456:ABC-DEF...`).
3. Put that token in Vercel as `TELEGRAM_BOT_TOKEN`.

Reuse an existing site bot if you already have one for other alerts.

#### `TELEGRAM_CHAT_ID`

Where alerts should arrive (your private chat or a group):

1. Start a chat with the bot (or add the bot to a group).
2. Send any message to the bot / in the group.
3. Open in a browser (replace `<TOKEN>`):  
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find `"chat":{"id": ...}` — that number is `TELEGRAM_CHAT_ID` (for groups it is often negative, e.g. `-100…`).

Or use a small helper bot such as [@userinfobot](https://t.me/userinfobot) for your personal id.

If token/chat are missing, `qa-notify` returns OK with `skipped: true` (posts still work; no Telegram ping).

#### `QA_SITE_BASE` (optional)

Default in code: `https://wsdc-analytics.github.io`.  
Set only if the public site host differs; used to build links inside Telegram messages (`…/qa.html#thread/…`).

### Quick checklist

| Variable | Source | Secret? |
|----------|--------|---------|
| `SUPABASE_URL` | Supabase → Settings → API → Project URL | No |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → `service_role` | **Yes** |
| `QA_ADMIN_SECRET` | You generate | **Yes** |
| `TELEGRAM_BOT_TOKEN` | BotFather | **Yes** |
| `TELEGRAM_CHAT_ID` | `getUpdates` / userinfobot | Semi |
| `QA_SITE_BASE` | Public site origin | No |

Moderation header used by the hub: `x-qa-admin-secret: <QA_ADMIN_SECRET>`.

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
