import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  const token = Deno.env.get("TELEGRAM_BOT_TOKEN") || "";
  const chatId = Deno.env.get("TELEGRAM_CHAT_ID") || "";
  if (!token || !chatId) {
    // Soft-fail so local/dev posts still work before secrets are set
    return json({ ok: false, skipped: true, reason: "Telegram not configured" });
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
    return json({ error: "Invalid JSON" }, 400);
  }

  const kind = payload.kind === "reply" ? "reply" : "thread";
  const board = payload.board || "other";
  const title = (payload.title || "").slice(0, 160);
  const author = (payload.author_name || "anon").slice(0, 80);
  const preview = (payload.preview || "").slice(0, 280);
  const threadId = payload.thread_id || "";
  const siteBase = Deno.env.get("QA_SITE_BASE") || "https://wsdc-analytics.github.io";
  const link = threadId
    ? `${siteBase}/qa.html#thread/${threadId}`
    : `${siteBase}/qa.html#board/${board}`;

  const text = [
    kind === "reply" ? "💬 New Q&A reply" : "🧵 New Q&A thread",
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
    return json({ ok: false, telegram_error: errText }, 502);
  }

  return json({ ok: true });
});
