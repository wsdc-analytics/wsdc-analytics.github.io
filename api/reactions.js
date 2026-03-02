const DATA_PATH = 'static/data/reactions.json';

function setCorsHeaders(res, origin) {
  const allow = origin || '*';
  res.setHeader('Access-Control-Allow-Origin', allow);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

function sendJson(res, data, status = 200, origin) {
  if (origin !== undefined) {
    setCorsHeaders(res, origin);
  }
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(data));
}

function rawUrl() {
  const repo = process.env.GITHUB_REPO || '';
  const branch = process.env.GITHUB_BRANCH || 'main';
  if (!repo) return null;
  const [owner, name] = repo.split('/').filter(Boolean);
  if (!owner || !name) return null;
  return `https://raw.githubusercontent.com/${owner}/${name}/${branch}/${DATA_PATH}`;
}

async function fetchCounts() {
  const url = rawUrl();
  if (!url) return {};
  const res = await fetch(url);
  if (!res.ok) return {};
  const data = await res.json();
  return typeof data === 'object' && data !== null ? data : {};
}

async function parseJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk;
      // simple safety guard
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
    setCorsHeaders(res, origin);
    res.statusCode = 204;
    return res.end();
  }

  if (req.method === 'GET') {
    try {
      const counts = await fetchCounts();
      return sendJson(res, counts, 200, origin);
    } catch (e) {
      return sendJson(res, { error: 'Failed to load counts' }, 500, origin);
    }
  }

  if (req.method !== 'POST') {
    return sendJson(res, { error: 'Method not allowed' }, 405, origin);
  }

  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO || '';
  const branch = process.env.GITHUB_BRANCH || 'main';

  if (!token || !repo) {
    return sendJson(
      res,
      { error: 'Server not configured (GITHUB_TOKEN, GITHUB_REPO)' },
      503,
      origin
    );
  }

  let body;
  try {
    body = await parseJsonBody(req);
  } catch {
    return sendJson(res, { error: 'Invalid JSON' }, 400, origin);
  }

  const id = body && typeof body.id === 'string' ? body.id.trim() : null;
  if (!id || !/^[a-z0-9_]+$/i.test(id)) {
    return sendJson(res, { error: 'Invalid or missing id' }, 400, origin);
  }

  const [owner, name] = repo.split('/').filter(Boolean);
  if (!owner || !name) {
    return sendJson(res, { error: 'Invalid GITHUB_REPO' }, 503, origin);
  }

  try {
    const counts = await fetchCounts();
    const prev = typeof counts[id] === 'number' && counts[id] >= 0 ? counts[id] : 0;
    counts[id] = prev + 1;

    const getRes = await fetch(
      `https://api.github.com/repos/${owner}/${name}/contents/${DATA_PATH}?ref=${branch}`,
      { headers: { Accept: 'application/vnd.github.v3+json', Authorization: `Bearer ${token}` } }
    );

    if (!getRes.ok) {
      const err = await getRes.text();
      return sendJson(
        res,
        { error: 'GitHub get file failed', details: err.slice(0, 200) },
        502,
        origin
      );
    }

    const file = await getRes.json();
    const content = Buffer.from(JSON.stringify(counts, null, 2)).toString('base64');

    const putRes = await fetch(
      `https://api.github.com/repos/${owner}/${name}/contents/${DATA_PATH}`,
      {
        method: 'PUT',
        headers: {
          Accept: 'application/vnd.github.v3+json',
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `chore: increment reaction ${id}`,
          content,
          sha: file.sha,
          branch,
        }),
      }
    );

    if (!putRes.ok) {
      const err = await putRes.text();
      return sendJson(
        res,
        { error: 'GitHub update file failed', details: err.slice(0, 200) },
        502,
        origin
      );
    }

    return sendJson(res, { id, count: counts[id] }, 200, origin);
  } catch (e) {
    return sendJson(
      res,
      { error: 'Server error', message: e && e.message },
      500,
      origin
    );
  }
};
