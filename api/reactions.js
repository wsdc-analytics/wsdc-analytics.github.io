/**
 * Article thumbs API (Supabase).
 *
 * GET  ?ids=a,b,c&voter_key=…  → { a: { up, down, mine }, … }
 * POST { article_id, value: 'up'|'down'|null, voter_key }
 *
 * Display counts = baseline + live votes.
 * Legacy: positive→up, negative→down (seeded in migration).
 */

function setCors(res, origin) {
  const allowed = allowOrigin(origin);
  res.setHeader('Access-Control-Allow-Origin', allowed);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
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
  // Vercel preview / prod host when opening API docs or local proxies
  if (origin && /^https:\/\/[\w-]+-[\w-]+-[\w.-]+\.vercel\.app$/i.test(origin)) return origin;
  if (origin === 'https://wsdc-analytics-github-io.vercel.app') return origin;
  return 'https://wsdc-analytics.github.io';
}

function sendJson(res, data, status = 200, origin) {
  if (origin !== undefined) setCors(res, origin);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(data));
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 1e5) {
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
    const msg =
      typeof data === 'object' && data && data.message ? data.message : String(text).slice(0, 300);
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

function isValidArticleId(id) {
  return typeof id === 'string' && /^[a-z0-9][a-z0-9_-]{1,120}$/i.test(id);
}

function isValidVoterKey(key) {
  return typeof key === 'string' && /^[a-z0-9-]{8,80}$/i.test(key);
}

/** Soft per-instance throttle (best-effort on serverless). */
const voteThrottle = new Map();
const VOTE_MIN_MS = 800;

function checkVoteThrottle(voterKey) {
  const now = Date.now();
  const prev = voteThrottle.get(voterKey) || 0;
  if (now - prev < VOTE_MIN_MS) return false;
  voteThrottle.set(voterKey, now);
  if (voteThrottle.size > 5000) {
    const cutoff = now - 60_000;
    for (const [k, t] of voteThrottle) {
      if (t < cutoff) voteThrottle.delete(k);
    }
  }
  return true;
}

async function aggregateCounts(supabaseUrl, serviceKey, ids) {
  const out = {};
  ids.forEach((id) => {
    out[id] = { up: 0, down: 0, mine: null };
  });
  if (!ids.length) return out;

  const inList = ids.map((id) => `"${id.replace(/"/g, '')}"`).join(',');
  const baselines = await sbFetch(
    supabaseUrl,
    serviceKey,
    `article_reaction_baseline?select=article_id,up_count,down_count&article_id=in.(${inList})`
  );
  (baselines || []).forEach((row) => {
    if (!out[row.article_id]) out[row.article_id] = { up: 0, down: 0, mine: null };
    out[row.article_id].up += Number(row.up_count) || 0;
    out[row.article_id].down += Number(row.down_count) || 0;
  });

  const votes = await sbFetch(
    supabaseUrl,
    serviceKey,
    `article_reaction_votes?select=article_id,value&article_id=in.(${inList})`
  );
  (votes || []).forEach((row) => {
    if (!out[row.article_id]) out[row.article_id] = { up: 0, down: 0, mine: null };
    if (row.value === 'up') out[row.article_id].up += 1;
    else if (row.value === 'down') out[row.article_id].down += 1;
  });

  return out;
}

module.exports = async function handler(req, res) {
  const origin = req.headers.origin || '';

  if (req.method === 'OPTIONS') {
    setCors(res, origin);
    res.statusCode = 204;
    return res.end();
  }

  const supabaseUrl = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
  if (!supabaseUrl || !serviceKey) {
    return sendJson(res, { error: 'Server not configured (SUPABASE_*)' }, 503, origin);
  }

  try {
    if (req.method === 'GET') {
      const url = new URL(req.url, 'http://localhost');
      const idsRaw = url.searchParams.get('ids') || '';
      const voterKey = url.searchParams.get('voter_key') || '';
      const ids = idsRaw
        .split(',')
        .map((s) => s.trim())
        .filter(isValidArticleId)
        .slice(0, 40);
      const counts = await aggregateCounts(supabaseUrl, serviceKey, ids);

      if (isValidVoterKey(voterKey) && ids.length) {
        const inList = ids.map((id) => `"${id.replace(/"/g, '')}"`).join(',');
        const mine = await sbFetch(
          supabaseUrl,
          serviceKey,
          `article_reaction_votes?select=article_id,value&voter_key=eq.${encodeURIComponent(
            voterKey
          )}&article_id=in.(${inList})`
        );
        (mine || []).forEach((row) => {
          if (counts[row.article_id]) counts[row.article_id].mine = row.value;
        });
      }

      return sendJson(res, counts, 200, origin);
    }

    if (req.method !== 'POST') {
      return sendJson(res, { error: 'Method not allowed' }, 405, origin);
    }

    let body;
    try {
      body = await parseBody(req);
    } catch {
      return sendJson(res, { error: 'Invalid JSON' }, 400, origin);
    }

    const articleId = body && body.article_id;
    const voterKey = body && body.voter_key;
    let value = body && body.value;
    if (value === '' || value === undefined) value = null;
    if (!isValidArticleId(articleId)) {
      return sendJson(res, { error: 'Invalid article_id' }, 400, origin);
    }
    if (!isValidVoterKey(voterKey)) {
      return sendJson(res, { error: 'Invalid voter_key' }, 400, origin);
    }
    if (value !== null && value !== 'up' && value !== 'down') {
      return sendJson(res, { error: 'Invalid value' }, 400, origin);
    }
    if (!checkVoteThrottle(voterKey)) {
      return sendJson(res, { error: 'Too many votes; slow down' }, 429, origin);
    }

    if (value === null) {
      await sbFetch(
        supabaseUrl,
        serviceKey,
        `article_reaction_votes?article_id=eq.${encodeURIComponent(
          articleId
        )}&voter_key=eq.${encodeURIComponent(voterKey)}`,
        { method: 'DELETE', headers: { Prefer: 'return=minimal' } }
      );
    } else {
      await sbFetch(
        supabaseUrl,
        serviceKey,
        'article_reaction_votes?on_conflict=article_id,voter_key',
        {
          method: 'POST',
          headers: {
            Prefer: 'resolution=merge-duplicates,return=representation',
          },
          body: JSON.stringify({
            article_id: articleId,
            voter_key: voterKey,
            value,
            updated_at: new Date().toISOString(),
          }),
        }
      );
    }

    const counts = await aggregateCounts(supabaseUrl, serviceKey, [articleId]);
    const row = counts[articleId] || { up: 0, down: 0, mine: null };
    row.mine = value;
    return sendJson(res, { article_id: articleId, ...row }, 200, origin);
  } catch (e) {
    return sendJson(
      res,
      { error: (e && e.message) || 'Server error' },
      e && e.status ? e.status : 500,
      origin
    );
  }
};
