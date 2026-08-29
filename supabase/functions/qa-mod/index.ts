import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-qa-admin-secret",
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

  const adminSecret = Deno.env.get("QA_ADMIN_SECRET") || "";
  const provided = req.headers.get("x-qa-admin-secret") || "";
  if (!adminSecret || provided !== adminSecret) {
    return json({ error: "Unauthorized" }, 401);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
  if (!supabaseUrl || !serviceKey) {
    return json({ error: "Server misconfigured" }, 500);
  }

  let body: {
    action?: string;
    type?: string;
    id?: string;
    board_slug?: string;
  };
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400);
  }

  const action = String(body.action || "");
  const type = String(body.type || "thread");
  const id = String(body.id || "");
  const sb = createClient(supabaseUrl, serviceKey);

  if (action === "stats") {
    const { data: boards, error: bErr } = await sb
      .from("qa_boards")
      .select("id, slug, title, sort_order")
      .order("sort_order");
    if (bErr) return json({ error: bErr.message }, 500);

    const { data: threads, error: tErr } = await sb
      .from("qa_threads")
      .select("id, board_id, is_hidden, created_at");
    if (tErr) return json({ error: tErr.message }, 500);

    const { data: posts, error: pErr } = await sb
      .from("qa_posts")
      .select("id, is_hidden, created_at");
    if (pErr) return json({ error: pErr.message }, 500);

    const byBoard = (boards || []).map((b) => {
      const bt = (threads || []).filter((t) => t.board_id === b.id);
      return {
        slug: b.slug,
        title: b.title,
        threads: bt.length,
        visible_threads: bt.filter((t) => !t.is_hidden).length,
        hidden_threads: bt.filter((t) => t.is_hidden).length,
      };
    });

    return json({
      boards: byBoard,
      posts_total: (posts || []).length,
      posts_hidden: (posts || []).filter((p) => p.is_hidden).length,
    });
  }

  if (action === "list_threads") {
    let q = sb
      .from("qa_threads")
      .select(
        "id, board_id, title, author_name, page_url, body, is_hidden, is_pinned, created_at, qa_boards(slug, title)",
      )
      .order("is_pinned", { ascending: false })
      .order("created_at", { ascending: false })
      .limit(100);
    if (body.board_slug) {
      const { data: board } = await sb
        .from("qa_boards")
        .select("id")
        .eq("slug", body.board_slug)
        .maybeSingle();
      if (board?.id) q = q.eq("board_id", board.id);
    }
    const { data, error } = await q;
    if (error) return json({ error: error.message }, 500);
    return json({ threads: data || [] });
  }

  if (!id) return json({ error: "Missing id" }, 400);

  const table = type === "post" ? "qa_posts" : "qa_threads";

  if (action === "delete") {
    const { data, error } = await sb.from(table).delete().eq("id", id).select("*").maybeSingle();
    if (error) return json({ error: error.message }, 500);
    if (!data) return json({ error: "Not found" }, 404);
    return json({ ok: true, deleted: data });
  }

  const patch: Record<string, boolean | string> = {};

  if (action === "hide") patch.is_hidden = true;
  else if (action === "unhide") patch.is_hidden = false;
  else if (action === "pin") {
    if (type !== "thread") return json({ error: "Pin only for threads" }, 400);
    patch.is_pinned = true;
  } else if (action === "unpin") {
    if (type !== "thread") return json({ error: "Unpin only for threads" }, 400);
    patch.is_pinned = false;
  } else if (action === "move") {
    if (type !== "thread") return json({ error: "Move only for threads" }, 400);
    const boardSlug = String(body.board_slug || "").trim();
    if (!boardSlug) return json({ error: "Missing board_slug" }, 400);
    const { data: board, error: boardErr } = await sb
      .from("qa_boards")
      .select("id")
      .eq("slug", boardSlug)
      .maybeSingle();
    if (boardErr) return json({ error: boardErr.message }, 500);
    if (!board?.id) return json({ error: "Unknown board" }, 404);
    patch.board_id = board.id;
  } else {
    return json({ error: "Unknown action" }, 400);
  }

  const { data, error } = await sb.from(table).update(patch).eq("id", id).select("*").maybeSingle();
  if (error) return json({ error: error.message }, 500);
  if (!data) return json({ error: "Not found" }, 404);
  return json({ ok: true, row: data });
});
