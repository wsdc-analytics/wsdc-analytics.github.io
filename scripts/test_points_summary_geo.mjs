#!/usr/bin/env node
/**
 * Smoke tests for static/js/points-summary-geo.js
 * Run: node scripts/test_points_summary_geo.mjs
 */
import { createRequire } from 'module';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const geo = require(join(root, 'static/js/points-summary-geo.js'));

let failed = 0;

function assertEqual(actual, expected, label) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    failed += 1;
    console.error(`FAIL ${label}\n  got:  ${a}\n  want: ${e}`);
  } else {
    console.log(`ok   ${label}`);
  }
}

function geoOnly(ev) {
  const g = geo.parsePointsEventGeo(ev);
  return { country: g.country, state: g.state, city: g.city };
}

// --- unit cases from code review ---
assertEqual(
  geoOnly({ location: 'Denver, CO', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'Colorado', city: 'Denver' },
  'Denver, CO'
);
assertEqual(
  geoOnly({ location: 'Cleveland, OH', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'Ohio', city: 'Cleveland' },
  'Cleveland, OH'
);
assertEqual(
  geoOnly({ location: 'Atlanta, GA USA', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'Georgia', city: 'Atlanta' },
  'Atlanta, GA USA'
);
assertEqual(
  geoOnly({ location: 'Baton Rouge, LA, United States', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'Louisiana', city: 'Baton Rouge' },
  'Baton Rouge full'
);
assertEqual(
  geoOnly({ location: 'Washington DC, USA', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'District of Columbia', city: 'Washington DC' },
  'Washington DC, USA'
);
assertEqual(
  geoOnly({ location: 'Nashville, Tennesse, USA', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'Tennessee', city: 'Nashville' },
  'Tennesse typo'
);
assertEqual(
  geoOnly({ location: 'Washington, DC / VA, USA', flag: '🇺🇸', continent: 'America' }),
  { country: 'United States', state: 'District of Columbia', city: 'Washington' },
  'DC / VA'
);
assertEqual(
  geoOnly({
    location: 'Springfield, Ma / Hartford, CT, , United States',
    flag: '🇺🇸',
    continent: 'America'
  }),
  { country: 'United States', state: 'Massachusetts', city: 'Springfield' },
  'Springfield dual city'
);
assertEqual(
  geoOnly({ location: 'Singapore', flag: '🇸🇬', continent: 'Asia' }),
  { country: 'Singapore', state: '', city: '' },
  'country-only Singapore'
);
assertEqual(
  geoOnly({ location: 'Poland', flag: '🇵🇱', continent: 'Europe' }),
  { country: 'Poland', state: '', city: '' },
  'country-only Poland'
);
assertEqual(
  geoOnly({ location: 'Czech Republic', flag: '🇨🇿', continent: 'Europe' }),
  { country: 'Czech Republic', state: '', city: '' },
  'country-only Czech Republic'
);
assertEqual(
  geo.standardizeCountry('FRANCE'),
  'France',
  'FRANCE → France'
);
assertEqual(
  geo.standardizeCountry('Deutschland'),
  'Germany',
  'Deutschland → Germany'
);
assertEqual(
  geo.standardizeCountry('Nederland'),
  'Netherlands',
  'Nederland → Netherlands'
);
assertEqual(
  geo.standardizeCountry('Polska'),
  'Poland',
  'Polska → Poland'
);
assertEqual(
  geo.standardizeCountry('Republic of Korea'),
  'South Korea',
  'Republic of Korea → South Korea'
);
assertEqual(
  geo.standardizeCountry('SCOTLAND'),
  'United Kingdom',
  'SCOTLAND → United Kingdom'
);
assertEqual(
  geo.standardizeCountry('CO'),
  '',
  'CO is not a country'
);

// --- live data audit ---
const data = JSON.parse(readFileSync(join(root, 'static/data/points_summaries.json'), 'utf8'));
const fakeCountries = new Set();
const usMissingState = [];
let usCount = 0;

for (const s of data.summaries || []) {
  for (const ev of s.events || []) {
    const g = geo.parsePointsEventGeo(ev);
    if (g.country === 'United States') {
      usCount += 1;
      if (!g.state) usMissingState.push({ name: ev.name, location: ev.location });
    }
    // Fake: 2-letter codes or "XX USA" style leftovers
    if (/^[A-Z]{2}$/.test(g.country) || /\bUSA\b/i.test(g.country) || g.country === 'GA USA') {
      fakeCountries.add(`${g.country} ← ${ev.location}`);
    }
  }
}

if (fakeCountries.size) {
  failed += 1;
  console.error('FAIL live data still has fake countries:', [...fakeCountries]);
} else {
  console.log('ok   live data: no fake US-state countries');
}

console.log(`info US events: ${usCount}, missing state: ${usMissingState.length}`);
if (usMissingState.length) {
  usMissingState.forEach((row) => console.log('  US no state:', row.name, '|', row.location));
}

// Country alias fragmentation check
const countries = new Set();
for (const s of data.summaries || []) {
  for (const ev of s.events || []) {
    const g = geo.parsePointsEventGeo(ev);
    if (g.country) countries.add(g.country);
  }
}
const badAliases = [...countries].filter((c) =>
  ['FRANCE', 'Deutschland', 'Nederland', 'Polska', 'SCOTLAND', 'The Netherlands', 'Republic of Korea'].includes(c)
);
if (badAliases.length) {
  failed += 1;
  console.error('FAIL unnormalized country labels:', badAliases);
} else {
  console.log('ok   live data: country aliases normalized');
  console.log('info countries:', [...countries].sort().join(', '));
}

if (failed) {
  console.error(`\n${failed} failure(s)`);
  process.exit(1);
}
console.log('\nAll tests passed.');
