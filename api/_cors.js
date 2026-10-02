/**
 * Shared CORS allowlist for Vercel API routes (contact, QA, reactions).
 */
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

module.exports = { allowOrigin };
