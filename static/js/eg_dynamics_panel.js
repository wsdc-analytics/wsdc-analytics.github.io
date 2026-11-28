/**
 * Event Trends Dynamics L2 panel renderer.
 * Expects window.EGDynamics. Host API is passed to bind/render.
 */
(function (root) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fmtN(n) {
    if (n == null || !isFinite(n)) return "—";
    return Math.round(n).toLocaleString("en-US");
  }

  function fmt1(n) {
    if (n == null || !isFinite(n)) return "—";
    return (Math.round(n * 10) / 10).toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1
    });
  }

  function fmtPct(n) {
    if (n == null || !isFinite(n)) return "—";
    var s = (n >= 0 ? "+" : "") + Math.round(n * 100) + "%";
    return s;
  }

  function pathD(pts) {
    if (!pts || !pts.length) return "";
    return pts.map(function (p, i) {
      return (i ? "L" : "M") + p.x.toFixed(1) + "," + p.y.toFixed(1);
    }).join(" ");
  }

  function tierColor(tier) {
    var t = Number(tier);
    if (!isFinite(t)) return "#94a3b8";
    var map = {
      1: "#7c3aed",
      2: "#2563eb",
      3: "#059669",
      4: "#d97706",
      5: "#db2777",
      6: "#64748b"
    };
    return map[t] || "#94a3b8";
  }

  function renderLineSvg(model, highlightKey, opts) {
    opts = opts || {};
    var tierDots = !!opts.tierDots;
    var parts = [];
    parts.push(
      '<svg class="dyn-chart-svg" viewBox="0 0 ' + model.width + " " +
      model.height + '" role="img" aria-hidden="true">'
    );
    // Hover guide (updated from JS).
    parts.push(
      '<line class="dyn-year-guide" x1="0" x2="0" y1="' + model.padT +
      '" y2="' + (model.height - model.padB) +
      '" stroke="#94a3b8" stroke-width="1" opacity="0" />'
    );
    // Solid colored lines only. Gaps where a year has no editions.
    model.lines.forEach(function (line) {
      var dim = !!(highlightKey && String(line.key) !== String(highlightKey));
      var op = dim ? 0.14 : 1;
      var sw = dim ? 1.2 : (highlightKey ? 2.35 : 1.8);
      line.segs.forEach(function (seg) {
        if (seg.length >= 2) {
          parts.push(
            '<path data-line="' + esc(line.key) + '" d="' + pathD(seg) +
            '" fill="none" stroke="' + esc(line.color) +
            '" stroke-width="' + sw + '" opacity="' + op +
            '" stroke-linecap="round" stroke-linejoin="round"/>'
          );
        } else if (seg.length === 1) {
          // Single active year — small mark so the series is still visible.
          parts.push(
            '<circle data-line="' + esc(line.key) + '" cx="' +
            seg[0].x.toFixed(1) + '" cy="' + seg[0].y.toFixed(1) +
            '" r="2.5" fill="' + esc(line.color) + '" opacity="' + op + '"/>'
          );
        }
      });
    });
    if (tierDots) {
      model.lines.forEach(function (line) {
        line.points.forEach(function (p) {
          if (!p) return;
          var tier = p.meta && p.meta.tier;
          parts.push(
            '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) +
            '" r="3.5" fill="' + esc(tierColor(tier)) +
            '" stroke="#fff" stroke-width="0.8">' +
            "<title>" + esc(line.label) + " · tier " +
            esc(String(tier || "—")) + " · " + esc(fmtN(p.v)) +
            "</title></circle>"
          );
        });
      });
    }
    // Invisible year hit strips for shared tooltip.
    model.years.forEach(function (y, i) {
      var x = model.xAt(i);
      var half = model.years.length > 1
        ? Math.abs(model.xAt(1) - model.xAt(0)) / 2
        : 16;
      parts.push(
        '<rect class="dyn-year-hit" data-year-idx="' + i +
        '" data-year="' + esc(String(y)) + '" x="' + (x - half).toFixed(1) +
        '" y="' + model.padT + '" width="' + (half * 2).toFixed(1) +
        '" height="' + (model.height - model.padT - model.padB) +
        '" fill="transparent"/>'
      );
    });
    model.years.forEach(function (y, i) {
      var x = model.xAt(i);
      parts.push(
        '<text x="' + x.toFixed(1) + '" y="' + (model.height - 6) +
        '" text-anchor="middle" font-size="9" fill="#94a3b8">' +
        esc(String(y)) + "</text>"
      );
    });
    parts.push(
      '<text x="4" y="' + (model.padT + 8) +
      '" font-size="9" fill="#94a3b8">' + esc(fmtN(model.max)) + "</text>"
    );
    parts.push(
      '<text x="4" y="' + (model.height - model.padB) +
      '" font-size="9" fill="#94a3b8">' + esc(fmtN(Math.max(0, model.min))) + "</text>"
    );
    parts.push("</svg>");
    return parts.join("");
  }

  function geoFilterFromHost(host) {
    var s = host.state;
    var g = {};
    if (s.continent) g.continent = s.continent;
    if (s.country) g.country = s.country;
    if (s.regionState) g.state = s.regionState;
    if (s.city) g.city = s.city;
    if (s.dynEventId != null) g.event_id = s.dynEventId;
    return g;
  }

  function scopeTitle(host) {
    var s = host.state;
    if (s.dynEditionKey) return "Edition";
    if (s.dynEventId != null) {
      var eds = host.editions().filter(function (e) {
        return Number(e.event_id) === Number(s.dynEventId);
      });
      return (eds[0] && eds[0].name) || ("Event " + s.dynEventId);
    }
    if (s.city) return s.city;
    if (s.regionState) return s.regionState;
    if (s.country) return s.country;
    if (s.continent) return s.continent;
    return "World";
  }

  function eventSample(host) {
    if (host.state.dynEventId == null) return null;
    var eid = Number(host.state.dynEventId);
    var hit = host.editions().find(function (e) {
      return Number(e.event_id) === eid;
    });
    return hit || null;
  }

  function crumbHtml(host) {
    var s = host.state;
    var sample = eventSample(host);
    var parts = [];
    function add(label, action, current) {
      if (parts.length) parts.push('<span class="sep">/</span>');
      if (current) {
        parts.push('<button type="button" disabled>' + esc(label) + "</button>");
      } else {
        parts.push(
          '<button type="button" data-dyn-jump="' + esc(action) + '">' +
          esc(label) + "</button>"
        );
      }
    }
    var atEvent = s.dynEventId != null;
    var atEdition = !!s.dynEditionKey;
    add("World", "world", !s.continent && !atEvent);
    if (s.continent || (sample && sample.continent)) {
      add(s.continent || sample.continent, "continent",
        !s.country && !s.city && !atEvent);
    }
    if (s.country || (sample && sample.country)) {
      add(s.country || sample.country, "country",
        !s.regionState && !s.city && !atEvent);
    }
    if (s.regionState || (sample && sample.country === "United States" && sample.state)) {
      add(s.regionState || sample.state, "state", !s.city && !atEvent);
    }
    var cityLabel = s.city || (sample && sample.city);
    if (cityLabel) {
      add(cityLabel, "city", !atEvent);
    }
    if (atEvent) {
      var evLabel = (sample && sample.name) || ("Event " + s.dynEventId);
      add(evLabel, "event", !atEdition);
    }
    if (atEdition) {
      // Year only in the trail (month kept in dynEditionKey for lookup).
      add(String(s.dynEditionKey).split("-")[0], "edition", true);
    }
    return parts.join("");
  }

  var GRAIN_LABELS = {
    continent: "Continents",
    country: "Countries",
    region: "Regions",
    state: "States",
    city: "Cities",
    event: "Events"
  };

  function yearOptsHtml(years, selected) {
    return years.map(function (y) {
      return '<option value="' + y + '"' +
        (Number(y) === Number(selected) ? " selected" : "") + ">" +
        y + "</option>";
    }).join("");
  }

  function headControlsHtml(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var years = host.years();
    var allowed = EG.allowedGrains(s.level, s.continent, s.country, s.city);
    var grain = s.dynGrain;
    if (!grain || allowed.indexOf(grain) === -1) {
      grain = EG.naturalGrain(s.level, s.country, s.city);
      s.dynGrain = grain;
    }
    var grainHtml;
    if (allowed.length <= 1) {
      grainHtml = '<span class="dyn-muted">' +
        esc(GRAIN_LABELS[allowed[0] || "event"] || "Events") + "</span>";
    } else {
      grainHtml = '<select id="dynGrain" class="wsdc-select eg-grain-select" aria-label="Breakdown">' +
        allowed.map(function (g) {
          return '<option value="' + g + '"' +
            (g === grain ? " selected" : "") + ">" +
            esc(GRAIN_LABELS[g] || g) + "</option>";
        }).join("") +
        "</select>";
    }
    return '<select id="dynFrom" class="wsdc-select" aria-label="From year">' +
      yearOptsHtml(years, s.dynFrom) + "</select>" +
      '<select id="dynTo" class="wsdc-select" aria-label="To year">' +
      yearOptsHtml(years, s.dynTo) + "</select>" +
      grainHtml;
  }

  function kpiHtml(avgs) {
    return '<div class="dyn-kpis">' +
      '<div class="dyn-kpi"><div class="dyn-kpi__lbl">Entries / year</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(avgs.entries)) + "</div></div>" +
      '<div class="dyn-kpi"><div class="dyn-kpi__lbl">Events / year</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(avgs.events)) + "</div></div>" +
      '<div class="dyn-kpi"><div class="dyn-kpi__lbl">Entries / event</div>' +
      '<div class="dyn-kpi__val">' + esc(fmt1(avgs.entriesPerEvent)) + "</div></div>" +
      "</div>";
  }

  /** Chart series: top-N breakdown only (no Total / Other / average lines). */
  function buildSeriesList(bd) {
    var EG = root.EGDynamics;
    return (bd.top || []).map(function (row, i) {
      return {
        key: row.key,
        label: row.label,
        color: EG.colorForIndex(i),
        points: row.series,
        avg: null
      };
    });
  }

  function chartBlock(title, metric, bd, highlightKey, years) {
    var EG = root.EGDynamics;
    var series = buildSeriesList(bd);
    var model = EG.lineChartModel(series, {
      metric: metric,
      years: years,
      width: 300,
      height: 160,
      padL: 34,
      padR: 8,
      padT: 10,
      padB: 22
    });
    var tipYears = years.map(function (y, i) {
      return {
        year: y,
        x: model.xAt(i),
        rows: model.lines.map(function (line) {
          var pt = line.points && line.points[i];
          return {
            key: line.key,
            label: line.label,
            color: line.color,
            value: pt ? pt.v : null
          };
        })
      };
    });
    var legend = model.lines.map(function (l) {
      var hi = highlightKey && String(l.key) === String(highlightKey) ? " is-hi" : "";
      return '<button type="button" class="' + hi + '" data-dyn-legend="' +
        esc(String(l.key)) + '"><i class="dyn-chart__swatch" style="background:' +
        esc(l.color) + '"></i>' + esc(l.label) + "</button>";
    }).join("");
    return '<div class="dyn-chart" data-metric="' + esc(metric) + '">' +
      '<div class="dyn-chart__title">' + esc(title) + "</div>" +
      renderLineSvg(model, highlightKey) +
      '<script type="application/json" class="dyn-chart-tipdata">' +
      JSON.stringify(tipYears).replace(/</g, "\\u003c") +
      "</script>" +
      '<div class="dyn-chart__legend">' + legend + "</div>" +
      "</div>";
  }

  function tableHtml(bd, highlightKey, grain) {
    var EG = root.EGDynamics;
    var rows = bd.rows || [];
    var head =
      "<thead><tr><th>" + esc(GRAIN_LABELS[grain] || grain) +
      "</th><th class=\"num\">Entries / year</th><th class=\"num\">Events / year</th>" +
      "<th class=\"num\">Entries / event</th><th>Trend</th></tr></thead>";
    var body = rows.map(function (r) {
      var vals = (r.series || []).map(function (p) {
        return p.partial ? null : p.entries;
      }).filter(function (v) { return v != null; });
      var spark = EG.sparklinePath(vals, 72, 22, 2);
      var hi = highlightKey && String(r.key) === String(highlightKey) ? " is-hi" : "";
      var a = r.averages || {};
      return '<tr class="' + hi + '" data-dyn-row="' + esc(String(r.key)) + '">' +
        "<td>" + esc(r.label) + "</td>" +
        '<td class="num">' + esc(fmtN(a.entries)) + "</td>" +
        '<td class="num">' + esc(fmtN(a.events)) + "</td>" +
        '<td class="num">' + esc(fmt1(a.entriesPerEvent)) + "</td>" +
        '<td><svg class="dyn-spark" viewBox="0 0 72 22"><path d="' +
        spark + '" fill="none" stroke="#2563eb" stroke-width="1.5"/></svg></td>' +
        "</tr>";
    }).join("");
    return '<div class="dyn-table-wrap"><table class="dyn-table">' +
      head + "<tbody>" + body + "</tbody></table></div>";
  }

  function renderGeoView(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var range = { from: s.dynFrom, to: s.dynTo };
    var through = host.dataThrough();
    var geo = geoFilterFromHost(host);
    delete geo.event_id;
    var grain = s.dynGrain;
    var allowed = EG.allowedGrains(s.level, s.continent, s.country, s.city);
    if (!grain || allowed.indexOf(grain) === -1) {
      grain = EG.naturalGrain(s.level, s.country, s.city);
      s.dynGrain = grain;
    }
    var bd = EG.breakdown(
      host.editions(), geo, grain, range, through, EG.DYNAMICS_RULES.topN
    );
    var avgs = EG.periodAverages(bd.total);
    var years = EG.yearsInRange(s.dynFrom, s.dynTo);
    var hi = s.dynHighlightKey;
    return kpiHtml(avgs) +
      '<div class="dyn-charts is-geo">' +
      chartBlock("Entries / year", "entries", bd, hi, years) +
      chartBlock("Events / year", "events", bd, hi, years) +
      chartBlock("Entries / event", "entriesPerEvent", bd, hi, years) +
      "</div>" +
      tableHtml(bd, hi, grain);
  }

  function editionKey(e) {
    return e.year + "-" + String(e.month).padStart(2, "0");
  }

  function editionAxisLabels(editions) {
    // Year on the axis; duplicate years stay as the same label (rare).
    return editions.map(function (e) { return String(e.year); });
  }

  function renderEventView(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var range = { from: s.dynFrom, to: s.dynTo };
    var through = host.dataThrough();
    var series = EG.eventEditionSeries(
      host.editions(), s.dynEventId, range, through
    );
    var years = editionAxisLabels(series.editions);
    var modelPts = series.editions.map(function (e, i) {
      return {
        year: years[i],
        entries: e.entries,
        missing: !e.entries && e.entries !== 0,
        partial: e.partial,
        meta: e
      };
    });
    var model = EG.lineChartModel([{
      key: "__event__",
      label: "Entries",
      color: EG.TOTAL_COLOR,
      points: modelPts,
      avg: null
    }], {
      metric: "entries",
      years: years,
      width: 640,
      height: 200,
      padL: 40,
      padR: 12,
      padT: 12,
      padB: 28
    });
    var tipYears = years.map(function (y, i) {
      var ed = series.editions[i];
      return {
        year: y,
        x: model.xAt(i),
        rows: [{
          key: "__event__",
          label: "Entries",
          color: EG.TOTAL_COLOR,
          value: ed ? ed.entries : null
        }]
      };
    });

    var role = s.dynRole || "Leader";
    var divChart = renderDivisionChart(host, series.editions, role);

    var ranked = series.editions.slice().sort(function (a, b) {
      return b.entries - a.entries;
    });
    var table =
      '<div class="dyn-table-wrap"><table class="dyn-table"><thead><tr>' +
      "<th>Edition</th><th class=\"num\">Entries</th><th class=\"num\">vs avg</th>" +
      "<th></th></tr></thead><tbody>" +
      ranked.map(function (e, i) {
        var key = editionKey(e);
        var tag = i === 0 ? "Best" : (i === ranked.length - 1 ? "Lowest" : "");
        return '<tr data-dyn-edition="' + esc(key) + '">' +
          "<td>" + esc(String(e.year)) + "</td>" +
          '<td class="num">' + esc(fmtN(e.entries)) + "</td>" +
          '<td class="num">' + esc(fmtPct(e.pctFromAvg)) + "</td>" +
          "<td>" + esc(tag) + "</td></tr>";
      }).join("") +
      "</tbody></table></div>";

    return '<div class="dyn-kpis"><div class="dyn-kpi"><div class="dyn-kpi__lbl">Entries / edition</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(series.average)) + "</div></div></div>" +
      '<div class="dyn-charts"><div class="dyn-chart">' +
      '<div class="dyn-chart__title">Entries by edition</div>' +
      renderLineSvg(model, null) +
      '<script type="application/json" class="dyn-chart-tipdata">' +
      JSON.stringify(tipYears).replace(/</g, "\\u003c") +
      "</script></div></div>" +
      '<div class="dyn-seg" role="group" aria-label="Role">' +
      '<button type="button" data-dyn-role="Leader" aria-pressed="' +
      (role === "Leader" ? "true" : "false") + '">Leader</button>' +
      '<button type="button" data-dyn-role="Follower" aria-pressed="' +
      (role === "Follower" ? "true" : "false") + '">Follower</button>' +
      "</div>" +
      divChart +
      "<h3 style=\"font-size:12px;margin:12px 0 6px\">Editions ranked</h3>" +
      table;
  }

  function renderDivisionChart(host, eventEditions, role) {
    var EG = root.EGDynamics;
    var tiers = host.tiersEditions();
    var years = editionAxisLabels(eventEditions);
    var seriesList = EG.DYNAMICS_RULES.divisions.map(function (div, i) {
      var points = eventEditions.map(function (e, idx) {
        var row = EG.findTiersRow(tiers, e.event_id, e.year, e.month);
        var counts = (row && row.counts && row.counts[div]) || {};
        var n = Number(counts[role]) || 0;
        var tier = row && row.tiers && row.tiers[div] ? row.tiers[div][role] : null;
        return {
          year: years[idx],
          entries: n,
          missing: false,
          meta: { div: div, tier: tier, edition: e }
        };
      });
      return {
        key: div,
        label: div,
        color: EG.colorForIndex(i),
        points: points,
        avg: null
      };
    });
    var model = EG.lineChartModel(seriesList, {
      metric: "entries",
      years: years,
      width: 640,
      height: 220,
      padL: 36,
      padR: 10,
      padT: 12,
      padB: 28
    });
    var tipYears = years.map(function (y, i) {
      return {
        year: y,
        x: model.xAt(i),
        rows: model.lines.map(function (line) {
          var pt = line.points && line.points[i];
          var tier = pt && pt.meta && pt.meta.tier;
          return {
            key: line.key,
            label: line.label + (tier != null ? (" · T" + tier) : ""),
            color: line.color,
            value: pt ? pt.v : null
          };
        })
      };
    });
    var svg = renderLineSvg(model, null, { tierDots: true });
    return '<div class="dyn-chart dyn-chart--divisions">' +
      '<div class="dyn-chart__title">Division headcount (' + esc(role) + ")</div>" +
      '<div class="dyn-chart__legend dyn-chart__legend--divisions">' +
      EG.DYNAMICS_RULES.divisions.map(function (d, i) {
        return '<span><i class="dyn-chart__swatch" style="background:' +
          EG.colorForIndex(i) + '"></i>' + esc(d) + "</span>";
      }).join("") +
      "</div>" +
      svg +
      '<script type="application/json" class="dyn-chart-tipdata">' +
      JSON.stringify(tipYears).replace(/</g, "\\u003c") +
      "</script></div>";
  }

  function renderEditionCard(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var parts = String(s.dynEditionKey || "").split("-");
    var year = Number(parts[0]);
    var month = Number(parts[1]);
    var eds = host.editions().filter(function (e) {
      return Number(e.event_id) === Number(s.dynEventId);
    }).sort(function (a, b) {
      return Number(a.year) - Number(b.year) || Number(a.month) - Number(b.month);
    });
    var edition = eds.find(function (e) {
      return Number(e.year) === year && Number(e.month) === month;
    });
    if (!edition) {
      return '<p class="dyn-muted">Edition not found.</p>';
    }
    var idx = eds.indexOf(edition);
    var prev = idx > 0 ? eds[idx - 1] : null;
    var tiers = host.tiersEditions();
    var tRow = EG.findTiersRow(tiers, edition.event_id, edition.year, edition.month);
    var tPrev = prev
      ? EG.findTiersRow(tiers, prev.event_id, prev.year, prev.month)
      : null;
    var flags = EG.editionFlags(edition, prev, tRow, tPrev);
    var concurrent = EG.concurrentEditions(edition, host.editions());
    if (concurrent.length && !flags.some(function (f) { return f.id === "concurrent"; })) {
      flags.unshift({
        id: "concurrent",
        label: "Same-weekend events",
        detail: concurrent.length + " on this continent"
      });
    }

    var flagsHtml = flags.length
      ? '<div class="dyn-flags">' + flags.map(function (f) {
          return '<span class="dyn-flag">' + esc(f.label) +
            (f.detail ? '<span class="dyn-flag__detail">· ' + esc(f.detail) + "</span>" : "") +
            "</span>";
        }).join("") + "</div>"
      : '<p class="dyn-muted">No automatic hypothesis flags for this edition.</p>';

    var divRows = EG.DYNAMICS_RULES.divisions.map(function (div) {
      var cur = (tRow && tRow.counts && tRow.counts[div]) || {};
      var prv = (tPrev && tPrev.counts && tPrev.counts[div]) || {};
      var tiersCur = (tRow && tRow.tiers && tRow.tiers[div]) || {};
      return EG.DYNAMICS_RULES.roles.map(function (role) {
        var c = Number(cur[role]) || 0;
        var p = Number(prv[role]) || 0;
        var dlt = prev ? c - p : null;
        return "<tr><td>" + esc(div) + "</td><td>" + esc(role) + "</td>" +
          '<td class="num">' + esc(fmtN(c)) + "</td>" +
          '<td class="num">' + (dlt == null ? "—" : esc((dlt >= 0 ? "+" : "") + dlt)) +
          "</td><td class=\"num\">" + esc(String(tiersCur[role] != null ? tiersCur[role] : "—")) +
          "</td></tr>";
      }).join("");
    }).join("");

    var concHtml = concurrent.length
      ? '<div class="dyn-table-wrap"><table class="dyn-table"><thead><tr>' +
        "<th>Event</th><th class=\"num\">Entries</th><th class=\"num\">km</th>" +
        "<th>Dates</th></tr></thead><tbody>" +
        concurrent.map(function (c) {
          return "<tr><td>" + esc(c.name) + "</td>" +
            '<td class="num">' + esc(fmtN(c.competitors)) + "</td>" +
            '<td class="num">' + (c.km == null ? "—" : esc(String(Math.round(c.km)))) +
            "</td><td>" + esc(String(c.start || "")) +
            (c.end ? " – " + esc(String(c.end)) : "") +
            "</td></tr>";
        }).join("") +
        "</tbody></table></div>"
      : '<p class="dyn-muted">No overlapping events on this continent.</p>';

    var venueHtml =
      "<p><strong>Venue now:</strong> " + esc(edition.hotel || "—") +
      " · " + esc([edition.city, edition.country].filter(Boolean).join(", ")) + "</p>" +
      (prev
        ? "<p><strong>Prior edition:</strong> " + esc(prev.hotel || "—") +
          " · " + esc(String(prev.start || "")) + "</p>"
        : "") +
      "<p><strong>Dates:</strong> " + esc(String(edition.start || "")) +
      (edition.end ? " – " + esc(String(edition.end)) : "") +
      " · <strong>Entries:</strong> " + esc(fmtN(edition.competitors)) + "</p>";

    return flagsHtml +
      '<div class="dyn-blocks">' +
      '<div class="dyn-block"><h3>Divisions × roles</h3>' +
      '<div class="dyn-table-wrap"><table class="dyn-table"><thead><tr>' +
      "<th>Division</th><th>Role</th><th class=\"num\">Entries</th>" +
      "<th class=\"num\">Δ vs prior</th><th class=\"num\">Tier</th></tr></thead><tbody>" +
      divRows + "</tbody></table></div></div>" +
      '<div class="dyn-block"><h3>Same-weekend competitors (continent)</h3>' +
      concHtml + "</div>" +
      '<div class="dyn-block"><h3>Venue &amp; dates</h3>' + venueHtml + "</div>" +
      "</div>";
  }

  function renderBody(host) {
    var s = host.state;
    if (s.dynEditionKey && s.dynEventId != null) return renderEditionCard(host);
    if (s.dynEventId != null) return renderEventView(host);
    return renderGeoView(host);
  }

  function ensureFloatTip(body) {
    var tip = body.querySelector(".dyn-float-tip");
    if (tip) return tip;
    tip = document.createElement("div");
    tip.className = "dyn-float-tip";
    tip.setAttribute("role", "tooltip");
    body.appendChild(tip);
    return tip;
  }

  function showFloatTip(body, html, clientX, clientY) {
    var tip = ensureFloatTip(body);
    var rect = body.getBoundingClientRect();
    tip.innerHTML = html;
    tip.classList.add("is-open");
    // Measure after paint so we can clamp inside the L2 body.
    var tipW = tip.offsetWidth || 180;
    var tipH = tip.offsetHeight || 80;
    var pad = 8;
    var x = clientX - rect.left + body.scrollLeft + 12;
    var y = clientY - rect.top + body.scrollTop + 12;
    var maxX = body.scrollLeft + body.clientWidth - tipW - pad;
    var maxY = body.scrollTop + body.clientHeight - tipH - pad;
    var minX = body.scrollLeft + pad;
    var minY = body.scrollTop + pad;
    if (x > maxX) x = Math.max(minX, maxX);
    if (y > maxY) {
      // Flip above the cursor when near the bottom edge.
      y = clientY - rect.top + body.scrollTop - tipH - 12;
    }
    if (x < minX) x = minX;
    if (y < minY) y = minY;
    if (y > maxY) y = Math.max(minY, maxY);
    tip.style.left = x + "px";
    tip.style.top = y + "px";
  }

  function hideFloatTip(body) {
    var tip = body.querySelector(".dyn-float-tip");
    if (tip) tip.classList.remove("is-open");
  }

  function wire(host, rootEl) {
    var body = rootEl.querySelector("#dynBody") || rootEl;
    var from = rootEl.querySelector("#dynFrom");
    var to = rootEl.querySelector("#dynTo");
    if (from) {
      from.addEventListener("change", function () {
        var c = root.EGDynamics.clampPeriod(
          Number(from.value), host.state.dynTo, host.years()
        );
        host.state.dynFrom = c.from;
        host.state.dynTo = c.to;
        host.writeUrl();
        host.render();
      });
    }
    if (to) {
      to.addEventListener("change", function () {
        var c = root.EGDynamics.clampPeriod(
          host.state.dynFrom, Number(to.value), host.years()
        );
        host.state.dynFrom = c.from;
        host.state.dynTo = c.to;
        host.writeUrl();
        host.render();
      });
    }
    var grain = rootEl.querySelector("#dynGrain");
    if (grain) {
      grain.addEventListener("change", function () {
        host.state.dynGrain = grain.value;
        host.state.dynHighlightKey = null;
        host.writeUrl();
        host.render();
      });
    }
    rootEl.querySelectorAll("[data-dyn-jump]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        host.jump(btn.getAttribute("data-dyn-jump"));
      });
    });
    rootEl.querySelectorAll("[data-dyn-row]").forEach(function (tr) {
      tr.addEventListener("click", function () {
        var key = tr.getAttribute("data-dyn-row");
        if (String(host.state.dynHighlightKey) === String(key)) {
          host.drillRow(key);
        } else {
          host.state.dynHighlightKey = key;
          host.render();
        }
      });
    });
    rootEl.querySelectorAll("[data-dyn-legend]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-dyn-legend");
        host.state.dynHighlightKey =
          String(host.state.dynHighlightKey) === String(key) ? null : key;
        host.render();
      });
    });
    rootEl.querySelectorAll("[data-dyn-edition]").forEach(function (tr) {
      tr.addEventListener("click", function () {
        host.state.dynEditionKey = tr.getAttribute("data-dyn-edition");
        host.writeUrl();
        host.render();
      });
    });
    rootEl.querySelectorAll("[data-dyn-role]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        host.state.dynRole = btn.getAttribute("data-dyn-role");
        host.render();
      });
    });
    rootEl.querySelectorAll(".dyn-chart").forEach(function (chart) {
      var dataEl = chart.querySelector(".dyn-chart-tipdata");
      if (!dataEl) return;
      var tipYears = [];
      try {
        tipYears = JSON.parse(dataEl.textContent || "[]");
      } catch (err) {
        tipYears = [];
      }
      if (!tipYears.length) return;
      var svg = chart.querySelector(".dyn-chart-svg");
      var guide = chart.querySelector(".dyn-year-guide");
      function paintYear(idx, clientX, clientY) {
        var row = tipYears[idx];
        if (!row) return;
        if (guide) {
          guide.setAttribute("x1", String(row.x));
          guide.setAttribute("x2", String(row.x));
          guide.setAttribute("opacity", "0.55");
        }
        var html = "<div class=\"dyn-float-tip__y\">" + esc(String(row.year)) + "</div>";
        row.rows.forEach(function (r) {
          html += '<div class="dyn-float-tip__row">' +
            '<i class="dyn-chart__swatch" style="background:' + esc(r.color) + '"></i>' +
            "<span>" + esc(r.label) + "</span>" +
            "<strong>" + (r.value == null ? "—" : esc(fmtN(r.value))) +
            "</strong></div>";
        });
        showFloatTip(body, html, clientX, clientY);
      }
      chart.querySelectorAll(".dyn-year-hit").forEach(function (hit) {
        hit.addEventListener("mousemove", function (ev) {
          paintYear(Number(hit.getAttribute("data-year-idx")), ev.clientX, ev.clientY);
        });
        hit.addEventListener("mouseleave", function () {
          if (guide) guide.setAttribute("opacity", "0");
          hideFloatTip(body);
        });
      });
      if (svg) {
        svg.addEventListener("mouseleave", function () {
          if (guide) guide.setAttribute("opacity", "0");
          hideFloatTip(body);
        });
      }
    });
  }

  function render(host) {
    var layer = document.getElementById("dynLayer");
    var body = document.getElementById("dynBody");
    var crumb = document.getElementById("dynCrumb");
    var title = document.getElementById("dynTitle");
    var headControls = document.getElementById("dynHeadControls");
    if (!layer || !body || !host.state.dynOpen) return;
    // Panel title stays "Dynamics"; geography/event path lives only in the crumb.
    if (title) title.textContent = "Dynamics";
    if (crumb) crumb.innerHTML = crumbHtml(host);
    if (headControls) {
      var showGrain = host.state.dynEventId == null && !host.state.dynEditionKey;
      headControls.innerHTML = showGrain ? headControlsHtml(host) : (
        '<select id="dynFrom" class="wsdc-select" aria-label="From year">' +
        yearOptsHtml(host.years(), host.state.dynFrom) + "</select>" +
        '<select id="dynTo" class="wsdc-select" aria-label="To year">' +
        yearOptsHtml(host.years(), host.state.dynTo) + "</select>"
      );
    }
    body.innerHTML = renderBody(host);
    if (window.WsdcSelect) WsdcSelect.enhanceAll(layer);
    wire(host, layer);
  }

  function open(host) {
    var layer = document.getElementById("dynLayer");
    var btn = document.getElementById("dynOpenBtn");
    if (!layer) return;
    host.state.dynOpen = true;
    var years = host.years();
    var clamped = root.EGDynamics.clampPeriod(
      host.state.dynFrom,
      host.state.dynTo,
      years
    );
    host.state.dynFrom = clamped.from;
    host.state.dynTo = clamped.to;
    if (!host.state.dynGrain) {
      host.state.dynGrain = root.EGDynamics.naturalGrain(
        host.state.level, host.state.country, host.state.city
      );
    }
    layer.hidden = false;
    layer.classList.add("is-open");
    layer.setAttribute("aria-hidden", "false");
    if (btn) btn.setAttribute("aria-pressed", "true");
    host.writeUrl();
    render(host);
    var closeBtn = document.getElementById("dynCloseBtn");
    if (closeBtn) closeBtn.focus();
  }

  function close(host) {
    var layer = document.getElementById("dynLayer");
    var btn = document.getElementById("dynOpenBtn");
    if (!layer) return;
    host.state.dynOpen = false;
    host.state.dynHighlightKey = null;
    host.state.dynEventId = null;
    host.state.dynEditionKey = null;
    layer.classList.remove("is-open");
    layer.hidden = true;
    layer.setAttribute("aria-hidden", "true");
    if (btn) {
      btn.setAttribute("aria-pressed", "false");
      btn.focus();
    }
    host.writeUrl();
  }

  root.EGDynamicsPanel = {
    open: open,
    close: close,
    render: render
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
