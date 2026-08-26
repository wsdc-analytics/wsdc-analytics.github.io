function setCors(res, origin) {
  res.setHeader('Access-Control-Allow-Origin', origin || '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, apikey');
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

module.exports = async function handler(req, res) {
  const origin = req.headers.origin || '*';

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

  let payload;
  try {
    payload = await parseBody(req);
  } catch {
    return sendJson(res, { error: 'Invalid JSON' }, 400, origin);
  }

  const kind = payload.kind === 'reply' ? 'reply' : 'thread';
  const board = payload.board || 'other';
  const title = String(payload.title || '').slice(0, 160);
  const author = String(payload.author_name || 'anon').slice(0, 80);
  const preview = String(payload.preview || '').slice(0, 280);
  const threadId = String(payload.thread_id || '');
  const siteBase = process.env.QA_SITE_BASE || 'https://wsdc-analytics.github.io';
  const link = threadId
    ? `${siteBase}/qa.html#thread/${threadId}`
    : `${siteBase}/qa.html#board/${board}`;

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
