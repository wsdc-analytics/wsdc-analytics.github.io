function setCors(res, origin) {
  const allowed = allowOrigin(origin);
  res.setHeader('Access-Control-Allow-Origin', allowed);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, apikey');
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

function isFresh(iso, maxAgeMs) {
  if (!iso) return false;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return false;
  return Date.now() - t <= maxAgeMs;
}

async function sbGet(baseUrl, serviceKey, path) {
  const res = await fetch(`${baseUrl}/rest/v1/${path}`, {
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      'Content-Type': 'application/json',
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
    const msg =
      typeof data === 'object' && data && data.message ? data.message : String(text).slice(0, 300);
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

  const token = process.env.TELEGRAM_BOT_TOKEN || '';
  const chatId = process.env.TELEGRAM_CHAT_ID || '';
  if (!token || !chatId) {
    return sendJson(res, { ok: false, skipped: true, reason: 'Telegram not configured' }, 200, origin);
  }

  const supabaseUrl = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
  if (!supabaseUrl || !serviceKey) {
    return sendJson(res, { error: 'Server not configured (SUPABASE_*)' }, 503, origin);
  }

  let payload;
  try {
    payload = await parseBody(req);
  } catch {
    return sendJson(res, { error: 'Invalid JSON' }, 400, origin);
  }

  const kind = payload.kind === 'reply' ? 'reply' : 'thread';
  const threadId = String(payload.thread_id || '').trim();
  if (!/^[0-9a-f-]{36}$/i.test(threadId)) {
    return sendJson(res, { error: 'Invalid thread_id' }, 400, origin);
  }

  const FRESH_MS = 3 * 60 * 1000;

  try {
    if (kind === 'thread') {
      const rows = await sbGet(
        supabaseUrl,
        serviceKey,
        `qa_threads?select=id,created_at&id=eq.${encodeURIComponent(threadId)}&limit=1`
      );
      const row = Array.isArray(rows) ? rows[0] : null;
      if (!row) return sendJson(res, { error: 'Thread not found' }, 404, origin);
      if (!isFresh(row.created_at, FRESH_MS)) {
        return sendJson(res, { error: 'Notify window expired' }, 409, origin);
      }
    } else {
      const rows = await sbGet(
        supabaseUrl,
        serviceKey,
        `qa_posts?select=id,created_at,is_op&thread_id=eq.${encodeURIComponent(
          threadId
        )}&is_op=eq.false&order=created_at.desc&limit=1`
      );
      const row = Array.isArray(rows) ? rows[0] : null;
      if (!row) return sendJson(res, { error: 'Reply not found' }, 404, origin);
      if (!isFresh(row.created_at, FRESH_MS)) {
        return sendJson(res, { error: 'Notify window expired' }, 409, origin);
      }
    }
  } catch (e) {
    return sendJson(
      res,
      { error: 'Verify failed', message: e && e.message },
      e && e.status ? e.status : 500,
      origin
    );
  }

  const board = String(payload.board || 'other').slice(0, 64);
  const title = String(payload.title || '').slice(0, 160);
  const author = String(payload.author_name || 'anon').slice(0, 80);
  const preview = String(payload.preview || '').slice(0, 280);
  const siteBase = process.env.QA_SITE_BASE || 'https://wsdc-analytics.github.io';
  const link = `${siteBase}/qa.html#thread/${threadId}`;

  const text = [
    kind === 'reply' ? 'New Q&A reply' : 'New Q&A thread',
    `Board: ${board}`,
    title ? `Title: ${title}` : null,
    `By: ${author}`,
    preview ? `Preview: ${preview}` : null,
    `Link: ${link}`,
  ]
    .filter(Boolean)
    .join('\n');

  try {
    const tgRes = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        disable_web_page_preview: true,
      }),
    });
    if (!tgRes.ok) {
      const errText = await tgRes.text();
      return sendJson(res, { ok: false, telegram_error: errText.slice(0, 300) }, 502, origin);
    }
    return sendJson(res, { ok: true }, 200, origin);
  } catch (e) {
    return sendJson(res, { error: 'Server error', message: e && e.message }, 500, origin);
  }
};
