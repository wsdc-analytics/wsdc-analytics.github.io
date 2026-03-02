const GITHUB_API = 'https://api.github.com';

function setCors(res, origin) {
  const allow = origin || '*';
  res.setHeader('Access-Control-Allow-Origin', allow);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

function sendJson(res, data, status = 200, origin) {
  if (origin !== undefined) {
    setCors(res, origin);
  }
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(data));
}

async function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
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

  const token = process.env.GITHUB_TOKEN;
  const repoEnv = process.env.FEEDBACK_REPO || process.env.GITHUB_REPO || '';

  if (!token || !repoEnv) {
    return sendJson(
      res,
      { error: 'Server not configured (GITHUB_TOKEN / FEEDBACK_REPO)' },
      503,
      origin
    );
  }

  const parts = repoEnv.split('/').filter(Boolean);
  const owner = parts[0];
  const repo = parts[1];

  if (!owner || !repo) {
    return sendJson(res, { error: 'Invalid FEEDBACK_REPO / GITHUB_REPO' }, 503, origin);
  }

  let body;
  try {
    body = await parseBody(req);
  } catch {
    return sendJson(res, { error: 'Invalid JSON' }, 400, origin);
  }

  const message = (body.message || '').trim();
  const email = (body.email || '').trim();
  const articleId = (body.articleId || '').trim();
  const articleUrl = (body.articleUrl || '').trim();

  if (!message || message.length < 5) {
    return sendJson(res, { error: 'Message is too short' }, 400, origin);
  }

  const titleBase = articleId || 'site-feedback';
  const title = `[feedback] ${titleBase}`;

  const lines = [];
  if (articleUrl) lines.push(`Article: ${articleUrl}`);
  if (articleId) lines.push(`Article ID: ${articleId}`);
  if (email) lines.push(`From: ${email}`);
  lines.push('');
  lines.push('Message:');
  lines.push(message);

  const issueBody = lines.join('\n');

  try {
    const resp = await fetch(`${GITHUB_API}/repos/${owner}/${repo}/issues`, {
      method: 'POST',
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title,
        body: issueBody,
        labels: ['feedback'].filter(Boolean),
      }),
    });

    if (!resp.ok) {
      const txt = await resp.text();
      return sendJson(
        res,
        { error: 'GitHub issue create failed', details: txt.slice(0, 200) },
        502,
        origin
      );
    }

    const data = await resp.json().catch(() => ({}));
    return sendJson(
      res,
      {
        ok: true,
        issue_number: data.number,
        issue_url: data.html_url,
      },
      200,
      origin
    );
  } catch (e) {
    return sendJson(
      res,
      { error: 'Server error', message: e && e.message },
      500,
      origin
    );
  }
};

