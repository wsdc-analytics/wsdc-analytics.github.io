/**
 * Event Trends — Dynamics mode helpers (descriptive multi-year view).
 * Browser: window.EGDynamics. Node: module.exports.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.EGDynamics = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () { // v=20261128a
  "use strict";

  var DYNAMICS_RULES = {
    concurrentSameContinent: true,
    venueMoveKm: 5,
    dateShiftDays: 14,
    divisionDropPct: 0.25,
    divisionMinCount: 5,
    roleImbalancePct: 0.2,
    topN: 5,
    // Reserved for later manual overrides.
    concurrentExcludeCountryPairs: [],
    concurrentAlwaysIncludeEventIds: [],
    divisions: [
      "Newcomer",
      "Novice",
      "Intermediate",
      "Advanced",
      "All-Star",
      "Champions"
    ],
    roles: ["Leader", "Follower"]
  };

  var PALETTE = [
    "#2563eb",
    "#059669",
    "#d97706",
    "#7c3aed",
    "#db2777",
    "#0d9488",
    "#ca8a04",
    "#4f46e5"
  ];
  var TOTAL_COLOR = "#111827";
  var OTHER_COLOR = "#9ca3af";
  var AVG_COLOR = "#6b7280";

  function parseThroughYearMonth(dataThrough) {
    var s = String(dataThrough || "");
    var m = /^(\d{4})-(\d{2})$/.exec(s);
    if (!m) return null;
    return { year: Number(m[1]), month: Number(m[2]) };
  }

  function isPartialYear(year, dataThrough) {
    var through = parseThroughYearMonth(dataThrough);
    return !!(through && Number(year) === through.year);
  }

  function yearsInRange(fromY, toY) {
    var a = Number(fromY);
    var b = Number(toY);
    if (!isFinite(a) || !isFinite(b) || b < a) return [];
    var out = [];
    var y;
    for (y = a; y <= b; y += 1) out.push(y);
    return out;
  }

  function matchesGeo(e, geoFilter) {
    if (!e) return false;
    var g = geoFilter || {};
    if (g.continent && e.continent !== g.continent) return false;
    if (g.country && e.country !== g.country) return false;
    if (g.state && e.state !== g.state) return false;
    if (g.city && e.city !== g.city) return false;
    if (g.event_id != null && Number(e.event_id) !== Number(g.event_id)) return false;
    return true;
  }

  function filterEditions(editions, geoFilter, range) {
    var fromY = range && range.from != null ? Number(range.from) : -Infinity;
    var toY = range && range.to != null ? Number(range.to) : Infinity;
    return (editions || []).filter(function (e) {
      if (!matchesGeo(e, geoFilter)) return false;
      var y = Number(e.year);
      if (!isFinite(y)) return false;
      return y >= fromY && y <= toY;
    });
  }

  function emptyYearPoint(year, dataThrough) {
    return {
      year: year,
      entries: 0,
      events: 0,
      entriesPerEvent: null,
      partial: isPartialYear(year, dataThrough)
    };
  }

  /**
   * Aggregate metrics by calendar year for a geo slice.
   * @returns {{ year:number, entries:number, events:number, entriesPerEvent:number|null, partial:boolean }[]}
   */
  function seriesByYear(editions, geoFilter, range, dataThrough) {
    var years = yearsInRange(range && range.from, range && range.to);
    var byYear = {};
    years.forEach(function (y) {
      byYear[y] = emptyYearPoint(y, dataThrough);
    });
    filterEditions(editions, geoFilter, range).forEach(function (e) {
      var y = Number(e.year);
      var row = byYear[y];
      if (!row) return;
      var n = Number(e.competitors);
      if (!isFinite(n)) n = 0;
      row.entries += n;
      row.events += 1;
    });
    return years.map(function (y) {
      var row = byYear[y];
      row.entriesPerEvent = row.events ? row.entries / row.events : null;
      return row;
    });
  }

  function periodAverages(series, opts) {
    opts = opts || {};
    var fullYearsOnly = opts.fullYearsOnly !== false;
    var rows = (series || []).filter(function (r) {
      if (!r) return false;
      if (fullYearsOnly && r.partial) return false;
      return true;
    });
    if (!rows.length) {
      return { entries: null, events: null, entriesPerEvent: null, nYears: 0 };
    }
    var sumE = 0;
    var sumN = 0;
    var sumAvg = 0;
    var nAvg = 0;
    rows.forEach(function (r) {
      sumE += r.entries || 0;
      sumN += r.events || 0;
      if (r.entriesPerEvent != null && isFinite(r.entriesPerEvent)) {
        sumAvg += r.entriesPerEvent;
        nAvg += 1;
      }
    });
    return {
      entries: sumE / rows.length,
      events: sumN / rows.length,
      entriesPerEvent: nAvg ? sumAvg / nAvg : null,
      nYears: rows.length
    };
  }

  function grainKey(e, grain) {
    if (!e) return null;
    if (grain === "continent") return e.continent || "Unknown";
    if (grain === "country") return e.country || "Unknown";
    if (grain === "state") return e.state || "Unknown";
    if (grain === "region") {
      if (e.country === "United States" && e.state) return "US|" + e.state;
      return e.country ? ("C|" + e.country) : "Unknown";
    }
    if (grain === "city") {
      return [e.city || "Unknown", e.country || "", e.state || ""].join("|");
    }
    if (grain === "event") {
      return e.event_id != null ? String(e.event_id) : null;
    }
    return null;
  }

  function grainLabel(e, grain) {
    if (!e) return "—";
    if (grain === "continent") return e.continent || "Unknown";
    if (grain === "country") return e.country || "Unknown";
    if (grain === "state") return e.state || "Unknown";
    if (grain === "region") {
      if (e.country === "United States" && e.state) return e.state;
      return e.country || "Unknown";
    }
    if (grain === "city") return e.city || "Unknown";
    if (grain === "event") return e.name || ("Event " + e.event_id);
    return "—";
  }

  function naturalGrain(level, country, city) {
    if (city) return "event";
    if (level === "world") return "continent";
    if (level === "continent") return "country";
    if (level === "country" && country === "United States") return "state";
    if (level === "country" || level === "state") return "city";
    return "continent";
  }

  function allowedGrains(level, continent, country, city) {
    if (city) return ["event"];
    if (level === "world") return ["continent", "region", "city", "event"];
    if (level === "continent") {
      if (continent === "America") return ["country", "region", "city", "event"];
      return ["country", "city", "event"];
    }
    if (level === "country" && country === "United States") {
      return ["state", "city", "event"];
    }
    if (level === "country" || level === "state") return ["city", "event"];
    return ["continent"];
  }

  /**
   * Breakdown series for chart + table.
   * @returns {{ total: object[], rows: object[], other: object[]|null, topKeys: string[] }}
   */
  function breakdown(editions, geoFilter, grain, range, dataThrough, topN) {
    var n = topN != null ? Number(topN) : DYNAMICS_RULES.topN;
    if (!isFinite(n) || n < 1) n = 5;
    var scoped = filterEditions(editions, geoFilter, range);
    var total = seriesByYear(scoped, null, range, dataThrough);
    var groups = {};
    scoped.forEach(function (e) {
      var key = grainKey(e, grain);
      if (key == null) return;
      if (!groups[key]) {
        groups[key] = {
          key: key,
          label: grainLabel(e, grain),
          sample: e,
          editions: []
        };
      }
      groups[key].editions.push(e);
    });
    var rows = Object.keys(groups).map(function (k) {
      var g = groups[k];
      var series = seriesByYear(g.editions, null, range, dataThrough);
      var sumEntries = 0;
      series.forEach(function (p) {
        if (!p.partial) sumEntries += p.entries;
      });
      return {
        key: g.key,
        label: g.label,
        sample: g.sample,
        series: series,
        sumEntries: sumEntries,
        averages: periodAverages(series, { fullYearsOnly: true })
      };
    });
    rows.sort(function (a, b) {
      return b.sumEntries - a.sumEntries ||
        String(a.label).localeCompare(String(b.label));
    });
    var top = rows.slice(0, n);
    var rest = rows.slice(n);
    var other = null;
    if (rest.length) {
      var otherEds = [];
      rest.forEach(function (r) {
        otherEds = otherEds.concat(r.editions || groups[r.key].editions);
      });
      // Rebuild from leftover editions.
      otherEds = [];
      rest.forEach(function (r) {
        (groups[r.key].editions || []).forEach(function (e) {
          otherEds.push(e);
        });
      });
      var otherSeries = seriesByYear(otherEds, null, range, dataThrough);
      other = {
        key: "__other__",
        label: "Other",
        series: otherSeries,
        sumEntries: rest.reduce(function (s, r) { return s + r.sumEntries; }, 0),
        averages: periodAverages(otherSeries, { fullYearsOnly: true }),
        n: rest.length
      };
    }
    return {
      total: total,
      rows: rows,
      top: top,
      other: other,
      topKeys: top.map(function (r) { return r.key; })
    };
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    if (![lat1, lon1, lat2, lon2].every(function (v) {
      return v != null && isFinite(Number(v));
    })) return null;
    var toRad = Math.PI / 180;
    var r = 6371;
    var dLat = (Number(lat2) - Number(lat1)) * toRad;
    var dLon = (Number(lon2) - Number(lon1)) * toRad;
    var a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(Number(lat1) * toRad) * Math.cos(Number(lat2) * toRad) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * r * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  function parseIsoDate(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ""));
    if (!m) return null;
    return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  }

  function dateRangesOverlap(aStart, aEnd, bStart, bEnd) {
    var as = parseIsoDate(aStart);
    var ae = parseIsoDate(aEnd) || as;
    var bs = parseIsoDate(bStart);
    var be = parseIsoDate(bEnd) || bs;
    if (as == null || bs == null) return false;
    return as <= be && bs <= ae;
  }

  function dayOfYear(iso) {
    var t = parseIsoDate(iso);
    if (t == null) return null;
    var d = new Date(t);
    var start = Date.UTC(d.getUTCFullYear(), 0, 0);
    return Math.floor((t - start) / 86400000);
  }

  /**
   * Concurrent editions: overlapping dates, same continent (configurable).
   */
  function concurrentEditions(edition, allEditions, rules) {
    rules = rules || DYNAMICS_RULES;
    if (!edition) return [];
    var start = edition.start;
    var end = edition.end || edition.start;
    var out = [];
    (allEditions || []).forEach(function (o) {
      if (!o || o === edition) return;
      if (Number(o.event_id) === Number(edition.event_id) &&
          Number(o.year) === Number(edition.year) &&
          Number(o.month) === Number(edition.month)) return;
      if (rules.concurrentSameContinent !== false) {
        if ((o.continent || "") !== (edition.continent || "")) return;
      }
      if (!dateRangesOverlap(start, end, o.start, o.end || o.start)) return;
      var km = haversineKm(edition.lat, edition.lon, o.lat, o.lon);
      if (km == null) {
        km = haversineKm(edition.city_lat, edition.city_lon, o.city_lat, o.city_lon);
      }
      out.push({
        event_id: o.event_id,
        name: o.name,
        year: o.year,
        month: o.month,
        start: o.start,
        end: o.end || null,
        competitors: o.competitors,
        continent: o.continent,
        country: o.country,
        city: o.city,
        km: km
      });
    });
    out.sort(function (a, b) {
      var ak = a.km == null ? Infinity : a.km;
      var bk = b.km == null ? Infinity : b.km;
      return ak - bk || (b.competitors || 0) - (a.competitors || 0);
    });
    return out;
  }

  function divisionCounts(tiersRow, role) {
    var counts = (tiersRow && tiersRow.counts) || {};
    var out = {};
    DYNAMICS_RULES.divisions.forEach(function (div) {
      var cell = counts[div] || {};
      if (role) {
        out[div] = Number(cell[role]) || 0;
      } else {
        out[div] = (Number(cell.Leader) || 0) + (Number(cell.Follower) || 0);
      }
    });
    return out;
  }

  function editionFlags(edition, prevEdition, tiersRow, prevTiersRow, rules) {
    rules = rules || DYNAMICS_RULES;
    var flags = [];
    if (!edition) return flags;

    if (edition.gap_flag) {
      flags.push({
        id: "gap",
        label: "Gap before this edition",
        detail: String(edition.gap_flag)
      });
    }

    if (prevEdition) {
      var km = haversineKm(
        prevEdition.lat, prevEdition.lon, edition.lat, edition.lon
      );
      var hotelChanged = !!(prevEdition.hotel && edition.hotel &&
        String(prevEdition.hotel).toLowerCase() !== String(edition.hotel).toLowerCase());
      if ((km != null && km >= rules.venueMoveKm) || hotelChanged) {
        flags.push({
          id: "venue_move",
          label: "Venue changed",
          detail: km != null
            ? (Math.round(km) + " km" + (hotelChanged ? "; hotel changed" : ""))
            : "Hotel changed"
        });
      }
      var d0 = dayOfYear(prevEdition.start);
      var d1 = dayOfYear(edition.start);
      if (d0 != null && d1 != null) {
        var shift = Math.abs(d1 - d0);
        if (shift > 180) shift = 365 - shift;
        if (shift >= rules.dateShiftDays) {
          flags.push({
            id: "date_shift",
            label: "Date shifted",
            detail: shift + " days vs prior edition"
          });
        }
      }
    }

    var cur = divisionCounts(tiersRow, null);
    var prev = divisionCounts(prevTiersRow, null);
    DYNAMICS_RULES.divisions.forEach(function (div) {
      var c = cur[div] || 0;
      var p = prev[div] || 0;
      if (p < rules.divisionMinCount) return;
      if (c <= p * (1 - rules.divisionDropPct)) {
        var pct = p ? Math.round((1 - c / p) * 100) : 0;
        flags.push({
          id: "div_drop_" + div,
          label: div + " drop",
          detail: c + " vs " + p + " (−" + pct + "%)"
        });
      }
    });

    var L = 0;
    var F = 0;
    DYNAMICS_RULES.divisions.forEach(function (div) {
      var cell = (tiersRow && tiersRow.counts && tiersRow.counts[div]) || {};
      L += Number(cell.Leader) || 0;
      F += Number(cell.Follower) || 0;
    });
    var tot = L + F;
    if (tot >= rules.divisionMinCount * 2) {
      var shareL = L / tot;
      var shareF = F / tot;
      if (Math.abs(shareL - shareF) >= rules.roleImbalancePct) {
        flags.push({
          id: "role_imbalance",
          label: "Role imbalance",
          detail: "L " + L + " / F " + F
        });
      }
    }

    return flags;
  }

  function findTiersRow(tiersEditions, eventId, year, month) {
    var list = tiersEditions || [];
    var eid = Number(eventId);
    var y = Number(year);
    var m = month != null ? Number(month) : NaN;
    var i;
    var best = null;
    for (i = 0; i < list.length; i += 1) {
      var row = list[i];
      if (!row || Number(row.event_id) !== eid || Number(row.year) !== y) continue;
      if (isFinite(m) && Number(row.month) === m) return row;
      if (!best) best = row;
    }
    return best;
  }

  function eventEditionSeries(editions, eventId, range, dataThrough) {
    var eid = Number(eventId);
    var rows = filterEditions(editions, { event_id: eid }, range)
      .slice()
      .sort(function (a, b) {
        return Number(a.year) - Number(b.year) ||
          Number(a.month) - Number(b.month);
      });
    var avgBase = rows.filter(function (e) {
      return !isPartialYear(e.year, dataThrough);
    });
    var sum = 0;
    avgBase.forEach(function (e) {
      sum += Number(e.competitors) || 0;
    });
    var avg = avgBase.length ? sum / avgBase.length : null;
    return {
      editions: rows.map(function (e) {
        var n = Number(e.competitors);
        if (!isFinite(n)) n = 0;
        return {
          event_id: e.event_id,
          name: e.name,
          year: e.year,
          month: e.month,
          start: e.start,
          entries: n,
          partial: isPartialYear(e.year, dataThrough),
          deltaFromAvg: avg != null ? n - avg : null,
          pctFromAvg: avg ? (n - avg) / avg : null,
          hotel: e.hotel || null,
          lat: e.lat,
          lon: e.lon,
          city: e.city,
          country: e.country,
          continent: e.continent,
          gap_flag: e.gap_flag || null,
          prev: e.prev || null
        };
      }),
      average: avg
    };
  }

  function sparklinePath(values, w, h, pad) {
    pad = pad == null ? 2 : pad;
    var vals = (values || []).map(function (v) {
      return isFinite(Number(v)) ? Number(v) : 0;
    });
    if (!vals.length) return "";
    var min = Math.min.apply(null, vals);
    var max = Math.max.apply(null, vals);
    var span = max - min || 1;
    var plotW = w - pad * 2;
    var plotH = h - pad * 2;
    return vals.map(function (v, i) {
      var x = pad + (vals.length === 1 ? plotW / 2 : (i / (vals.length - 1)) * plotW);
      var y = pad + plotH - ((v - min) / span) * plotH;
      return (i ? "L" : "M") + x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  }

  function lineChartModel(seriesList, opts) {
    opts = opts || {};
    var w = opts.width || 560;
    var h = opts.height || 180;
    var padL = opts.padL != null ? opts.padL : 36;
    var padR = opts.padR != null ? opts.padR : 12;
    var padT = opts.padT != null ? opts.padT : 12;
    var padB = opts.padB != null ? opts.padB : 24;
    var metric = opts.metric || "entries";
    var years = opts.years || [];
    if (!years.length && seriesList && seriesList[0] && seriesList[0].points) {
      years = seriesList[0].points.map(function (p) { return p.year; });
    }
    var allVals = [];
    (seriesList || []).forEach(function (s) {
      (s.points || []).forEach(function (p) {
        var v = p[metric];
        if (v != null && isFinite(v)) allVals.push(v);
      });
      if (s.avg != null && isFinite(s.avg)) allVals.push(s.avg);
    });
    var min = allVals.length ? Math.min.apply(null, allVals) : 0;
    var max = allVals.length ? Math.max.apply(null, allVals) : 1;
    if (min === max) {
      min = Math.max(0, min - 1);
      max = max + 1;
    }
    var yPad = (max - min) * 0.08;
    min -= yPad;
    max += yPad;
    var plotW = w - padL - padR;
    var plotH = h - padT - padB;
    function xAt(i, n) {
      if (n <= 1) return padL + plotW / 2;
      return padL + (i / (n - 1)) * plotW;
    }
    function yAt(v) {
      return padT + plotH - ((v - min) / (max - min || 1)) * plotH;
    }
    var lines = (seriesList || []).map(function (s) {
      var pts = s.points || [];
      var segs = [];
      var cur = [];
      pts.forEach(function (p, i) {
        var v = p[metric];
        if (v == null || !isFinite(v)) {
          if (cur.length) {
            segs.push(cur);
            cur = [];
          }
          return;
        }
        var pt = {
          x: xAt(i, pts.length),
          y: yAt(v),
          v: v,
          year: p.year,
          partial: !!p.partial,
          meta: p
        };
        if (cur.length && cur[cur.length - 1].partial !== pt.partial) {
          // Keep continuity: end previous seg and start new with shared point.
          cur.push(pt);
          segs.push(cur);
          cur = [pt];
        } else {
          cur.push(pt);
        }
      });
      if (cur.length) segs.push(cur);
      return {
        key: s.key,
        label: s.label,
        color: s.color,
        avg: s.avg,
        avgY: s.avg != null && isFinite(s.avg) ? yAt(s.avg) : null,
        segs: segs,
        points: pts.map(function (p, i) {
          var v = p[metric];
          if (v == null || !isFinite(v)) return null;
          return {
            x: xAt(i, pts.length),
            y: yAt(v),
            v: v,
            year: p.year,
            partial: !!p.partial,
            meta: p
          };
        }).filter(Boolean)
      };
    });
    return {
      width: w,
      height: h,
      padL: padL,
      padR: padR,
      padT: padT,
      padB: padB,
      min: min,
      max: max,
      years: years,
      lines: lines,
      xAt: function (i) { return xAt(i, years.length); },
      yAt: yAt
    };
  }

  function colorForIndex(i) {
    return PALETTE[i % PALETTE.length];
  }

  return {
    DYNAMICS_RULES: DYNAMICS_RULES,
    TOTAL_COLOR: TOTAL_COLOR,
    OTHER_COLOR: OTHER_COLOR,
    AVG_COLOR: AVG_COLOR,
    PALETTE: PALETTE,
    parseThroughYearMonth: parseThroughYearMonth,
    isPartialYear: isPartialYear,
    yearsInRange: yearsInRange,
    matchesGeo: matchesGeo,
    filterEditions: filterEditions,
    seriesByYear: seriesByYear,
    periodAverages: periodAverages,
    grainKey: grainKey,
    grainLabel: grainLabel,
    naturalGrain: naturalGrain,
    allowedGrains: allowedGrains,
    breakdown: breakdown,
    haversineKm: haversineKm,
    dateRangesOverlap: dateRangesOverlap,
    concurrentEditions: concurrentEditions,
    divisionCounts: divisionCounts,
    editionFlags: editionFlags,
    findTiersRow: findTiersRow,
    eventEditionSeries: eventEditionSeries,
    sparklinePath: sparklinePath,
    lineChartModel: lineChartModel,
    colorForIndex: colorForIndex
  };
});
