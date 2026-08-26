import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const ALLOWED_ORIGINS = new Set([
  "https://wsdc-analytics.github.io",
  "http://127.0.0.1:4173",
  "http://localhost:4173",
]);

function corsHeadersFor(origin: string | null) {
  const allow =
    origin && ALLOWED_ORIGINS.has(origin) ? origin : "https://wsdc-analytics.github.io";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    Vary: "Origin",
  };
}

function json(data: unknown, status = 200, origin: string | null = null) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeadersFor(origin), "Content-Type": "application/json" },
  });
}

function isFresh(iso: string | null | undefined, maxAgeMs: number) {
  if (!iso) return false;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return false;
  return Date.now() - t <= maxAgeMs;
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("origin");
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeadersFor(origin) });
  }
  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405, origin);
  }

  const token = Deno.env.get("TELEGRAM_BOT_TOKEN") || "";
  const chatId = Deno.env.get("TELEGRAM_CHAT_ID") || "";
  if (!token || !chatId) {
    return json({ ok: false, skipped: true, reason: "Telegram not configured" }, 200, origin);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
  if (!supabaseUrl || !serviceKey) {
    return json({ error: "Server misconfigured" }, 500, origin);
  }

  let payload: {
    kind?: string;
    board?: string;
    title?: string;
    author_name?: string;
    thread_id?: string;
    preview?: string;
  };
  try {
    payload = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400, origin);
  }

  const kind = payload.kind === "reply" ? "reply" : "thread";
  const threadId = String(payload.thread_id || "").trim();
  if (!/^[0-9a-f-]{36}$/i.test(threadId)) {
    return json({ error: "Invalid thread_id" }, 400, origin);
  }

  const sb = createClient(supabaseUrl, serviceKey);
  const FRESH_MS = 3 * 60 * 1000;

  if (kind === "thread") {
    const { data, error } = await sb
      .from("qa_threads")
      .select("id, created_at")
      .eq("id", threadId)
      .maybeSingle();
    if (error) return json({ error: error.message }, 500, origin);
    if (!data) return json({ error: "Thread not found" }, 404, origin);
    if (!isFresh(data.created_at, FRESH_MS)) {
      return json({ error: "Notify window expired" }, 409, origin);
    }
  } else {
    const { data, error } = await sb
      .from("qa_posts")
      .select("id, created_at")
      .eq("thread_id", threadId)
      .eq("is_op", false)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) return json({ error: error.message }, 500, origin);
    if (!data) return json({ error: "Reply not found" }, 404, origin);
    if (!isFresh(data.created_at, FRESH_MS)) {
      return json({ error: "Notify window expired" }, 409, origin);
    }
  }

  const board = (payload.board || "other").slice(0, 64);
  const title = (payload.title || "").slice(0, 160);
  const author = (payload.author_name || "anon").slice(0, 80);
  const preview = (payload.preview || "").slice(0, 280);
  const siteBase = Deno.env.get("QA_SITE_BASE") || "https://wsdc-analytics.github.io";
  const link = `${siteBase}/qa.html#thread/${threadId}`;

  const text = [
    kind === "reply" ? "New Q&A reply" : "New Q&A thread",
    `Board: ${board}`,
    title ? `Title: ${title}` : null,
    `By: ${author}`,
    preview ? `Preview: ${preview}` : null,
    `Link: ${link}`,
  ]
    .filter(Boolean)
    .join("\n");

  const tgRes = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      disable_web_page_preview: true,
    }),
  });

  if (!tgRes.ok) {
    const errText = await tgRes.text();
    return json({ ok: false, telegram_error: errText }, 502, origin);
  }

  return json({ ok: true }, 200, origin);
});
