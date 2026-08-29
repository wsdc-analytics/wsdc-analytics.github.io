function setCors(res, origin) {
  const allowed = allowOrigin(origin);
  res.setHeader('Access-Control-Allow-Origin', allowed);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'Content-Type, x-qa-admin-secret, Authorization, apikey'
  );
  res.setHeader('Vary', 'Origin');
}

function allowOrigin(origin) {
  const allowed = new Set([
    'https://wsdc-analytics.github.io',
    'http://127.0.0.1:4173',
    'http://localhost:4173',
    'http://127.0.0.1:5500',
    'http://localhost:5500',
  ]);
  if (origin && allowed.has(origin)) return origin;
  return 'https://wsdc-analytics.github.io';
}

function sendJson(res, data, status = 200, origin) {
  if (origin !== undefined) setCors(res, origin);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(data));
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 1e6) {
        req.socket.destroy();
        reject(new Error('Body too large'));
      }
    });
    req.on('end', () => {
      if (!body) return resolve({});
      try {
        resolve(JSON.parse(body));
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function sbHeaders(serviceKey) {
  return {
    apikey: serviceKey,
    Authorization: `Bearer ${serviceKey}`,
    'Content-Type': 'application/json',
    Prefer: 'return=representation',
  };
}

async function sbFetch(baseUrl, serviceKey, path, options = {}) {
  const res = await fetch(`${baseUrl}/rest/v1/${path}`, {
    ...options,
    headers: {
      ...sbHeaders(serviceKey),
      ...(options.headers || {}),
    },
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg = typeof data === 'object' && data && data.message ? data.message : String(text).slice(0, 300);
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

module.exports = async function handler(req, res) {
  const origin = req.headers.origin || '';

  if (req.method === 'OPTIONS') {
    setCors(res, origin);
    res.statusCode = 204;
    return res.end();
  }

  if (req.method !== 'POST') {
    return sendJson(res, { error: 'Method not allowed' }, 405, origin);
  }

  const adminSecret = process.env.QA_ADMIN_SECRET || '';
  const provided = req.headers['x-qa-admin-secret'] || '';
  if (!adminSecret || provided !== adminSecret) {
    return sendJson(res, { error: 'Unauthorized' }, 401, origin);
  }

  const supabaseUrl = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
  if (!supabaseUrl || !serviceKey) {
    return sendJson(res, { error: 'Server not configured (SUPABASE_*)' }, 503, origin);
  }

  let body;
  try {
    body = await parseBody(req);
  } catch {
    return sendJson(res, { error: 'Invalid JSON' }, 400, origin);
  }

  const action = String(body.action || '');
  const type = String(body.type || 'thread');
  const id = String(body.id || '');

  try {
    if (action === 'stats') {
      const boards = await sbFetch(
        supabaseUrl,
        serviceKey,
        'qa_boards?select=id,slug,title,sort_order&order=sort_order.asc'
      );
      const threads = await sbFetch(
        supabaseUrl,
        serviceKey,
        'qa_threads?select=id,board_id,is_hidden,created_at'
      );
      const posts = await sbFetch(
        supabaseUrl,
        serviceKey,
        'qa_posts?select=id,is_hidden,created_at'
      );

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

      return sendJson(
        res,
        {
          boards: byBoard,
          posts_total: (posts || []).length,
          posts_hidden: (posts || []).filter((p) => p.is_hidden).length,
        },
        200,
        origin
      );
    }

    if (action === 'list_threads') {
      let path =
        'qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,is_moderator,created_at,qa_boards(slug,title)&order=is_pinned.desc,created_at.desc&limit=100';
      if (body.board_slug) {
        const boards = await sbFetch(
          supabaseUrl,
          serviceKey,
          `qa_boards?select=id&slug=eq.${encodeURIComponent(body.board_slug)}`
        );
        if (boards && boards[0] && boards[0].id) {
          path += `&board_id=eq.${boards[0].id}`;
        }
      }
      const threads = await sbFetch(supabaseUrl, serviceKey, path);
      return sendJson(res, { threads: threads || [] }, 200, origin);
    }

    if (action === 'list_posts') {
      const threadId = String(body.thread_id || '').trim();
      if (!threadId) return sendJson(res, { error: 'Missing thread_id' }, 400, origin);
      const posts = await sbFetch(
        supabaseUrl,
        serviceKey,
        `qa_posts?select=id,thread_id,author_name,body,is_hidden,is_op,is_moderator,created_at&thread_id=eq.${encodeURIComponent(
          threadId
        )}&order=created_at.asc`
      );
      return sendJson(res, { posts: posts || [] }, 200, origin);
    }

    if (action === 'create_post') {
      const threadId = String(body.thread_id || '').trim();
      const authorName = String(body.author_name || '').trim();
      const authorEmail = String(body.author_email || '').trim() || null;
      const postBody = String(body.body || '').trim();
      const isOp = Boolean(body.is_op);
      if (!threadId) return sendJson(res, { error: 'Missing thread_id' }, 400, origin);
      if (!authorName) return sendJson(res, { error: 'Missing author_name' }, 400, origin);
      if (!postBody) return sendJson(res, { error: 'Missing body' }, 400, origin);
      const rows = await sbFetch(
        supabaseUrl,
        serviceKey,
        'qa_posts?select=id,thread_id,author_name,body,is_hidden,is_op,is_moderator,created_at',
        {
          method: 'POST',
          body: JSON.stringify({
            thread_id: threadId,
            author_name: authorName.slice(0, 80),
            author_email: authorEmail,
            body: postBody.slice(0, 8000),
            is_op: isOp,
            is_moderator: true,
          }),
        }
      );
      const row = Array.isArray(rows) ? rows[0] : rows;
      return sendJson(res, { ok: true, row }, 200, origin);
    }

    if (action === 'create_thread') {
      const boardId = String(body.board_id || '').trim();
      const title = String(body.title || '').trim();
      const authorName = String(body.author_name || '').trim();
      const authorEmail = String(body.author_email || '').trim() || null;
      const pageUrl = body.page_url ? String(body.page_url).trim() : null;
      const threadBody = String(body.body || '').trim();
      if (!boardId) return sendJson(res, { error: 'Missing board_id' }, 400, origin);
      if (!title || title.length < 3) return sendJson(res, { error: 'Invalid title' }, 400, origin);
      if (!authorName) return sendJson(res, { error: 'Missing author_name' }, 400, origin);
      if (!threadBody || threadBody.length < 3) return sendJson(res, { error: 'Invalid body' }, 400, origin);
      const threads = await sbFetch(
        supabaseUrl,
        serviceKey,
        'qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,is_moderator,created_at',
        {
          method: 'POST',
          body: JSON.stringify({
            board_id: boardId,
            title: title.slice(0, 160),
            author_name: authorName.slice(0, 80),
            author_email: authorEmail,
            page_url: pageUrl,
            body: threadBody.slice(0, 8000),
            is_moderator: true,
          }),
        }
      );
      const thread = Array.isArray(threads) ? threads[0] : threads;
      if (!thread || !thread.id) return sendJson(res, { error: 'Failed to create thread' }, 500, origin);
      const posts = await sbFetch(
        supabaseUrl,
        serviceKey,
        'qa_posts?select=id,thread_id,author_name,body,is_hidden,is_op,is_moderator,created_at',
        {
          method: 'POST',
          body: JSON.stringify({
            thread_id: thread.id,
            author_name: authorName.slice(0, 80),
            author_email: authorEmail,
            body: threadBody.slice(0, 8000),
            is_op: true,
            is_moderator: true,
          }),
        }
      );
      const post = Array.isArray(posts) ? posts[0] : posts;
      return sendJson(res, { ok: true, thread, post }, 200, origin);
    }

    if (!id) return sendJson(res, { error: 'Missing id' }, 400, origin);

    const table = type === 'post' ? 'qa_posts' : 'qa_threads';

    if (action === 'delete') {
      // Deleting a thread cascades to qa_posts (FK on delete cascade).
      const rows = await sbFetch(
        supabaseUrl,
        serviceKey,
        `${table}?id=eq.${encodeURIComponent(id)}`,
        {
          method: 'DELETE',
          headers: { Prefer: 'return=representation' },
        }
      );
      const row = Array.isArray(rows) ? rows[0] : rows;
      if (!row) return sendJson(res, { error: 'Not found' }, 404, origin);
      return sendJson(res, { ok: true, deleted: row }, 200, origin);
    }

    const patch = {};
    if (action === 'hide') patch.is_hidden = true;
    else if (action === 'unhide') patch.is_hidden = false;
    else if (action === 'pin') {
      if (type !== 'thread') return sendJson(res, { error: 'Pin only for threads' }, 400, origin);
      patch.is_pinned = true;
    } else if (action === 'unpin') {
      if (type !== 'thread') return sendJson(res, { error: 'Pin only for threads' }, 400, origin);
      patch.is_pinned = false;
    } else if (action === 'move') {
      if (type !== 'thread') return sendJson(res, { error: 'Move only for threads' }, 400, origin);
      const boardSlug = String(body.board_slug || '').trim();
      if (!boardSlug) return sendJson(res, { error: 'Missing board_slug' }, 400, origin);
      const boards = await sbFetch(
        supabaseUrl,
        serviceKey,
        `qa_boards?select=id,slug&slug=eq.${encodeURIComponent(boardSlug)}`
      );
      if (!boards || !boards[0] || !boards[0].id) {
        return sendJson(res, { error: 'Unknown board' }, 404, origin);
      }
      patch.board_id = boards[0].id;
    } else {
      return sendJson(res, { error: 'Unknown action' }, 400, origin);
    }

    const rows = await sbFetch(supabaseUrl, serviceKey, `${table}?id=eq.${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
    const row = Array.isArray(rows) ? rows[0] : rows;
    if (!row) return sendJson(res, { error: 'Not found' }, 404, origin);
    return sendJson(res, { ok: true, row }, 200, origin);
  } catch (e) {
    const detail = (e && e.message) || 'unknown';
    return sendJson(
      res,
      { error: detail, message: detail },
      e && e.status ? e.status : 500,
      origin
    );
  }
};
