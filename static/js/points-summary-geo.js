/**
 * Geo parsing for Points Summary location filters.
 * Browser: window.WsdcPointsGeo. Node: module.exports.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.WsdcPointsGeo = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var US_COUNTRY = 'United States';

  var US_STATE_CODE_TO_NAME = {
    AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado',
    CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho',
    IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana',
    ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota',
    MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire',
    NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota',
    OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island',
    SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
    VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming', DC: 'District of Columbia'
  };

  var US_STATE_NAME_ALIASES = {
    tennesse: 'Tennessee',
    tennesee: 'Tennessee',
    'washington dc': 'District of Columbia',
    'washington d.c.': 'District of Columbia',
    'washington d.c': 'District of Columbia',
    'district of columbia': 'District of Columbia'
  };

  var FLAG_TO_COUNTRY = {
    '🇺🇸': 'United States',
    '🇩🇪': 'Germany',
    '🇪🇸': 'Spain',
    '🇸🇪': 'Sweden',
    '🇬🇧': 'United Kingdom',
    '🇷🇺': 'Russia',
    '🇸🇮': 'Slovenia',
    '🇨🇦': 'Canada',
    '🇸🇬': 'Singapore',
    '🇮🇹': 'Italy',
    '🇫🇷': 'France',
    '🇰🇷': 'South Korea',
    '🇵🇱': 'Poland',
    '🇳🇱': 'Netherlands',
    '🇭🇺': 'Hungary',
    '🇦🇺': 'Australia',
    '🇳🇿': 'New Zealand',
    '🇨🇿': 'Czech Republic',
    '🇨🇭': 'Switzerland',
    '🇮🇪': 'Ireland',
    '🇵🇹': 'Portugal',
    '🇦🇹': 'Austria',
    '🇧🇪': 'Belgium',
    '🇩🇰': 'Denmark',
    '🇳🇴': 'Norway',
    '🇷🇴': 'Romania',
    '🇺🇦': 'Ukraine',
    '🇯🇵': 'Japan',
    '🇲🇽': 'Mexico',
    '🇧🇷': 'Brazil',
    '🇦🇷': 'Argentina',
    '🇿🇦': 'South Africa',
    '🇫🇮': 'Finland',
    '🇧🇬': 'Bulgaria',
    '🇲🇾': 'Malaysia'
  };

  /** Lowercase alias → canonical country display name. */
  var COUNTRY_ALIASES = {
    us: US_COUNTRY,
    usa: US_COUNTRY,
    'u.s.': US_COUNTRY,
    'u.s.a.': US_COUNTRY,
    'united states': US_COUNTRY,
    'united states of america': US_COUNTRY,
    uk: 'United Kingdom',
    'united kingdom': 'United Kingdom',
    'great britain': 'United Kingdom',
    britain: 'United Kingdom',
    scotland: 'United Kingdom',
    england: 'United Kingdom',
    wales: 'United Kingdom',
    'northern ireland': 'United Kingdom',
    czechia: 'Czech Republic',
    'czech republic': 'Czech Republic',
    deutschland: 'Germany',
    germany: 'Germany',
    france: 'France',
    nederland: 'Netherlands',
    'the netherlands': 'Netherlands',
    holland: 'Netherlands',
    netherlands: 'Netherlands',
    polska: 'Poland',
    poland: 'Poland',
    'republic of korea': 'South Korea',
    'south korea': 'South Korea',
    korea: 'South Korea',
    singapore: 'Singapore',
    australia: 'Australia',
    austria: 'Austria',
    belgium: 'Belgium',
    bulgaria: 'Bulgaria',
    canada: 'Canada',
    finland: 'Finland',
    hungary: 'Hungary',
    ireland: 'Ireland',
    italy: 'Italy',
    japan: 'Japan',
    malaysia: 'Malaysia',
    mexico: 'Mexico',
    'new zealand': 'New Zealand',
    norway: 'Norway',
    portugal: 'Portugal',
    romania: 'Romania',
    russia: 'Russia',
    slovenia: 'Slovenia',
    spain: 'Spain',
    sweden: 'Sweden',
    switzerland: 'Switzerland',
    ukraine: 'Ukraine',
    brazil: 'Brazil',
    argentina: 'Argentina',
    'south africa': 'South Africa'
  };

  var KNOWN_COUNTRIES = (function () {
    var set = {};
    Object.keys(COUNTRY_ALIASES).forEach(function (k) {
      set[COUNTRY_ALIASES[k]] = true;
    });
    Object.keys(FLAG_TO_COUNTRY).forEach(function (f) {
      set[FLAG_TO_COUNTRY[f]] = true;
    });
    return set;
  })();

  function normKey(value) {
    return String(value || '')
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\./g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function isUsStateCode(token) {
    var t = String(token || '').trim();
    return t.length === 2 && !!US_STATE_CODE_TO_NAME[t.toUpperCase()];
  }

  function parseUsStateToken(token) {
    var t = String(token || '').trim();
    if (!t) return '';

    var withUsa = t.match(/^([A-Za-z]{2})\s+(USA|US|U\.S\.A\.?|U\.S\.?)$/i);
    if (withUsa) {
      return US_STATE_CODE_TO_NAME[withUsa[1].toUpperCase()] || '';
    }

    if (isUsStateCode(t)) {
      return US_STATE_CODE_TO_NAME[t.toUpperCase()];
    }

    var key = normKey(t);
    if (US_STATE_NAME_ALIASES[key]) {
      return US_STATE_NAME_ALIASES[key];
    }

    var names = Object.keys(US_STATE_CODE_TO_NAME).map(function (code) {
      return US_STATE_CODE_TO_NAME[code];
    });
    for (var i = 0; i < names.length; i += 1) {
      if (normKey(names[i]) === key) return names[i];
    }
    return '';
  }

  function standardizeCountry(raw) {
    var u = String(raw || '').trim().replace(/\.$/, '').trim();
    if (!u) return '';

    // "GA USA" / "CO US" → United States (not a country name fragment).
    if (/^[A-Za-z]{2}\s+(USA|US|U\.S\.A\.?|U\.S\.?)$/i.test(u)) {
      return US_COUNTRY;
    }

    // Bare state code is not a country.
    if (isUsStateCode(u)) {
      return '';
    }

    var key = normKey(u);
    if (COUNTRY_ALIASES[key]) {
      return COUNTRY_ALIASES[key];
    }

    // Preserve multi-word unknowns; single-word title-case for display consistency.
    if (u.indexOf(' ') === -1) {
      return u.charAt(0).toUpperCase() + u.slice(1).toLowerCase();
    }
    return u;
  }

  function isKnownCountry(name) {
    return !!(name && KNOWN_COUNTRIES[name]);
  }

  function splitLocationParts(location) {
    return String(location || '')
      .split(',')
      .map(function (p) {
        return p.trim();
      })
      .filter(Boolean);
  }

  function cityFromFirstPart(first) {
    var raw = String(first || '').trim();
    if (!raw) return '';
    // Dual venues: "Springfield, Ma / Hartford, CT" → city Springfield only (first part).
    // "Washington, DC / VA" is handled via state tokens, city stays Washington.
    var beforeSlash = raw.split(/\s*\/\s*/)[0].trim();
    return beforeSlash || raw;
  }

  function parseUsStateFromParts(parts) {
    if (!parts || !parts.length) return '';

    var city = cityFromFirstPart(parts[0]);
    var cityKey = normKey(city);
    if (US_STATE_NAME_ALIASES[cityKey]) {
      return US_STATE_NAME_ALIASES[cityKey];
    }
    if (/\bwashington\s*d\.?c\.?\b/i.test(city) || cityKey === 'washington dc') {
      return 'District of Columbia';
    }

    for (var i = 1; i < parts.length; i += 1) {
      var part = parts[i];
      var direct = parseUsStateToken(part);
      if (direct) return direct;

      var slashBits = part.split(/\s*\/\s*/);
      for (var j = 0; j < slashBits.length; j += 1) {
        var bit = slashBits[j].trim();
        // "Ma / Hartford" → try Ma; "Hartford" alone is not a state.
        var st = parseUsStateToken(bit);
        if (st) return st;
        // Leading token before extra words: "Ma Hartford" unlikely; skip.
      }
    }
    return '';
  }

  function parsePointsEventGeo(ev) {
    var location = String((ev && ev.location) || '').trim();
    var parts = splitLocationParts(location);
    var continent = String((ev && ev.continent) || 'Other').trim() || 'Other';
    var flagCountry = ev && ev.flag && FLAG_TO_COUNTRY[ev.flag] ? FLAG_TO_COUNTRY[ev.flag] : '';

    var city = '';
    var country = '';
    var state = '';

    if (parts.length === 0) {
      return { continent: continent, country: flagCountry || '', state: '', city: '' };
    }

    if (parts.length === 1) {
      var only = parts[0];
      var onlyCountry = standardizeCountry(only);
      if (isKnownCountry(onlyCountry) || (flagCountry && onlyCountry === flagCountry)) {
        return {
          continent: continent,
          country: onlyCountry || flagCountry,
          state: '',
          city: ''
        };
      }
      if (flagCountry && normKey(only) === normKey(flagCountry)) {
        return { continent: continent, country: flagCountry, state: '', city: '' };
      }
      city = cityFromFirstPart(only);
      country = flagCountry || '';
      if (country === US_COUNTRY) {
        state = parseUsStateFromParts(parts);
      }
      return { continent: continent, country: country, state: state, city: city };
    }

    city = cityFromFirstPart(parts[0]);
    var last = parts[parts.length - 1];
    var lastState = parseUsStateToken(last);
    country = standardizeCountry(last);

    // Bare / "GA USA" state tokens are not countries.
    if (lastState && !isKnownCountry(country)) {
      country = US_COUNTRY;
    }

    if (!country && flagCountry) {
      country = flagCountry;
    }

    // US flag + recoverable state → force United States when last token was junk.
    if (flagCountry === US_COUNTRY && country !== US_COUNTRY) {
      var maybeState = parseUsStateFromParts(parts) || lastState;
      if (maybeState || !isKnownCountry(country)) {
        country = US_COUNTRY;
      }
    }

    if (country === US_COUNTRY) {
      state = parseUsStateFromParts(parts) || lastState || '';
    }

    if (city && country && normKey(city) === normKey(country)) {
      city = '';
    }

    return { continent: continent, country: country || '', state: state || '', city: city || '' };
  }

  return {
    US_COUNTRY: US_COUNTRY,
    FLAG_TO_COUNTRY: FLAG_TO_COUNTRY,
    standardizeCountry: standardizeCountry,
    parseUsStateToken: parseUsStateToken,
    parsePointsEventGeo: parsePointsEventGeo
  };
});
