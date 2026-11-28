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
    var skipPoints = !!opts.skipPoints;
    var EG = root.EGDynamics;
    var parts = [];
    parts.push(
      '<svg viewBox="0 0 ' + model.width + " " + model.height +
      '" role="img" aria-hidden="true">'
    );
    // avg dashed
    model.lines.forEach(function (line) {
      if (line.avgY == null) return;
      if (highlightKey && line.key !== highlightKey && line.key !== "__total__") return;
      parts.push(
        '<line x1="' + model.padL + '" x2="' + (model.width - model.padR) +
        '" y1="' + line.avgY.toFixed(1) + '" y2="' + line.avgY.toFixed(1) +
        '" stroke="' + EG.AVG_COLOR +
        '" stroke-width="1" stroke-dasharray="4 3" opacity="0.85"/>'
      );
    });
    model.lines.forEach(function (line) {
      var dim = highlightKey && line.key !== highlightKey && line.key !== "__total__";
      var op = dim ? 0.18 : 1;
      line.segs.forEach(function (seg) {
        if (seg.length < 2) return;
        // If any point is partial, draw that segment dashed.
        var hasPartial = seg.some(function (p) { return p.partial; });
        parts.push(
          '<path d="' + pathD(seg) + '" fill="none" stroke="' + esc(line.color) +
          '" stroke-width="' + (line.key === "__total__" ? 2.25 : 1.5) +
          '" opacity="' + op + '"' +
          (hasPartial ? ' stroke-dasharray="5 4"' : "") + "/>"
        );
      });
      if (skipPoints) return;
      line.points.forEach(function (p) {
        parts.push(
          '<circle class="dyn-pt" data-line="' + esc(line.key) +
          '" data-year="' + esc(String(p.year)) +
          '" cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) +
          '" r="3" fill="' + esc(line.color) + '" opacity="' + op + '"/>'
        );
      });
    });
    // year ticks
    model.years.forEach(function (y, i) {
      var x = model.xAt(i);
      parts.push(
        '<text x="' + x.toFixed(1) + '" y="' + (model.height - 6) +
        '" text-anchor="middle" font-size="9" fill="#94a3b8">' +
        esc(String(y)) + "</text>"
      );
    });
    // y labels
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

  function crumbHtml(host) {
    var s = host.state;
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
    add("World", "world", !s.continent && !s.dynEventId);
    if (s.continent) {
      add(s.continent, "continent", !!s.continent && !s.country && !s.dynEventId);
    }
    if (s.country) {
      add(s.country, "country", !!s.country && !s.regionState && !s.city && !s.dynEventId);
    }
    if (s.regionState) {
      add(s.regionState, "state", !!s.regionState && !s.city && !s.dynEventId);
    }
    if (s.city) {
      add(s.city, "city", !!s.city && s.dynEventId == null);
    }
    if (s.dynEventId != null) {
      add(scopeTitle(host), "event", s.dynEditionKey == null);
    }
    if (s.dynEditionKey) {
      add(s.dynEditionKey, "edition", true);
    }
    return parts.join("");
  }

  function periodControlsHtml(host) {
    var years = host.years();
    var from = host.state.dynFrom;
    var to = host.state.dynTo;
    var through = host.dataThrough();
    function opts(selected) {
      return years.map(function (y) {
        return '<option value="' + y + '"' +
          (Number(y) === Number(selected) ? " selected" : "") + ">" +
          y + "</option>";
      }).join("");
    }
    return '<div class="dyn-period">' +
      '<label>From<select id="dynFrom">' + opts(from) + "</select></label>" +
      '<label>To<select id="dynTo">' + opts(to) + "</select></label>" +
      (through
        ? '<div class="dyn-period__note">Partial year ' +
          esc(String(through).slice(0, 4)) + " shown dashed · excluded from averages</div>"
        : "") +
      "</div>";
  }

  function kpiHtml(avgs, yearsLabel) {
    return '<div class="dyn-kpis">' +
      '<div class="dyn-kpi"><div class="dyn-kpi__lbl">Avg entries / year</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(avgs.entries)) + "</div>" +
      '<div class="dyn-kpi__sub">' + esc(yearsLabel) + "</div></div>" +
      '<div class="dyn-kpi"><div class="dyn-kpi__lbl">Avg events / year</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(avgs.events)) + "</div>" +
      '<div class="dyn-kpi__sub">' + esc(yearsLabel) + "</div></div>" +
      '<div class="dyn-kpi"><div class="dyn-kpi__lbl">Avg entries / event</div>' +
      '<div class="dyn-kpi__val">' + esc(fmt1(avgs.entriesPerEvent)) + "</div>" +
      '<div class="dyn-kpi__sub">' + esc(yearsLabel) + "</div></div>" +
      "</div>";
  }

  function buildSeriesList(bd, metric) {
    var EG = root.EGDynamics;
    var avgObj = EG.periodAverages(bd.total);
    var list = [{
      key: "__total__",
      label: "Total",
      color: EG.TOTAL_COLOR,
      points: bd.total,
      avg: metric === "entries" ? avgObj.entries
        : metric === "events" ? avgObj.events
        : avgObj.entriesPerEvent
    }];

    (bd.top || []).forEach(function (row, i) {
      var a = row.averages || {};
      list.push({
        key: row.key,
        label: row.label,
        color: EG.colorForIndex(i),
        points: row.series,
        avg: metric === "entries" ? a.entries
          : metric === "events" ? a.events
          : a.entriesPerEvent
      });
    });
    if (bd.other) {
      var oa = bd.other.averages || {};
      list.push({
        key: "__other__",
        label: "Other",
        color: EG.OTHER_COLOR,
        points: bd.other.series,
        avg: metric === "entries" ? oa.entries
          : metric === "events" ? oa.events
          : oa.entriesPerEvent
      });
    }
    return list;
  }

  function chartBlock(title, metric, bd, highlightKey, years) {
    var EG = root.EGDynamics;
    var model = EG.lineChartModel(buildSeriesList(bd, metric), {
      metric: metric,
      years: years,
      width: 300,
      height: 160,
      padL: 34,
      padR: 8,
      padT: 10,
      padB: 22
    });
    var legend = model.lines.slice(0, 7).map(function (l) {
      return '<span><i class="dyn-chart__swatch" style="background:' +
        esc(l.color) + '"></i>' + esc(l.label) + "</span>";
    }).join("");
    return '<div class="dyn-chart" data-metric="' + esc(metric) + '">' +
      '<div class="dyn-chart__title">' + esc(title) + "</div>" +
      renderLineSvg(model, highlightKey) +
      '<div class="dyn-chart__legend">' + legend + "</div>" +
      '<div class="dyn-chart__tip" data-dyn-tip></div>' +
      "</div>";
  }

  function tableHtml(bd, highlightKey, grain) {
    var EG = root.EGDynamics;
    var rows = bd.rows || [];
    var head =
      "<thead><tr><th>" + esc(grain) +
      "</th><th class=\"num\">Avg entries</th><th class=\"num\">Avg events</th>" +
      "<th class=\"num\">Avg / event</th><th>Trend</th></tr></thead>";
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

  function grainSelectHtml(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var allowed = EG.allowedGrains(s.level, s.continent, s.country, s.city);
    var grain = s.dynGrain;
    if (!grain || allowed.indexOf(grain) === -1) {
      grain = EG.naturalGrain(s.level, s.country, s.city);
    }
    var labels = {
      continent: "Continents",
      country: "Countries",
      region: "Regions",
      state: "States",
      city: "Cities",
      event: "Events"
    };
    return '<div class="dyn-toolbar"><label for="dynGrain">Breakdown</label>' +
      '<select id="dynGrain">' +
      allowed.map(function (g) {
        return '<option value="' + g + '"' +
          (g === grain ? " selected" : "") + ">" +
          esc(labels[g] || g) + "</option>";
      }).join("") +
      "</select></div>";
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
    var yearsLabel = avgs.nYears
      ? ("Full years in " + s.dynFrom + "–" + s.dynTo + " (n=" + avgs.nYears + ")")
      : "No full years in range";
    var years = EG.yearsInRange(s.dynFrom, s.dynTo);
    var hi = s.dynHighlightKey;
    return periodControlsHtml(host) +
      kpiHtml(avgs, yearsLabel) +
      '<div class="dyn-charts is-geo">' +
      chartBlock("Entries / year", "entries", bd, hi, years) +
      chartBlock("Events / year", "events", bd, hi, years) +
      chartBlock("Entries / event", "entriesPerEvent", bd, hi, years) +
      "</div>" +
      grainSelectHtml(host) +
      tableHtml(bd, hi, grain);
  }

  function renderEventView(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var range = { from: s.dynFrom, to: s.dynTo };
    var through = host.dataThrough();
    var series = EG.eventEditionSeries(
      host.editions(), s.dynEventId, range, through
    );
    var points = series.editions.map(function (e) {
      return {
        year: e.year,
        month: e.month,
        entries: e.entries,
        events: 1,
        entriesPerEvent: e.entries,
        partial: e.partial,
        start: e.start,
        key: e.year + "-" + String(e.month).padStart(2, "0")
      };
    });
    // Use edition index on x via synthetic year labels
    var years = points.map(function (p) {
      return String(p.year).slice(2) + "/" + String(p.month).padStart(2, "0");
    });
    var modelPts = points.map(function (p, i) {
      return {
        year: years[i],
        entries: p.entries,
        partial: p.partial,
        meta: p
      };
    });
    var model = EG.lineChartModel([{
      key: "__event__",
      label: "Entries",
      color: EG.TOTAL_COLOR,
      points: modelPts,
      avg: series.average
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
        var key = e.year + "-" + String(e.month).padStart(2, "0");
        var tag = i === 0 ? "Best" : (i === ranked.length - 1 ? "Lowest" : "");
        return '<tr data-dyn-edition="' + esc(key) + '">' +
          "<td>" + esc(key) + (e.partial ? " · partial" : "") + "</td>" +
          '<td class="num">' + esc(fmtN(e.entries)) + "</td>" +
          '<td class="num">' + esc(fmtPct(e.pctFromAvg)) + "</td>" +
          "<td>" + esc(tag) + "</td></tr>";
      }).join("") +
      "</tbody></table></div>";

    return periodControlsHtml(host) +
      '<button type="button" class="dyn-back-link" data-dyn-jump="back-event">← Back to geography</button>' +
      '<div class="dyn-kpis"><div class="dyn-kpi"><div class="dyn-kpi__lbl">Avg entries / edition</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(series.average)) + "</div>" +
      '<div class="dyn-kpi__sub">' + esc(String(series.editions.length)) +
      " editions in range</div></div></div>" +
      '<div class="dyn-charts"><div class="dyn-chart">' +
      '<div class="dyn-chart__title">Entries by edition</div>' +
      renderLineSvg(model, null) +
      '<div class="dyn-chart__tip" data-dyn-tip>Hover a point for concurrent events · click a row for edition card</div>' +
      "</div></div>" +
      '<div class="dyn-toolbar"><span class="dyn-muted">Divisions</span>' +
      '<div class="dyn-seg" role="group" aria-label="Role">' +
      '<button type="button" data-dyn-role="Leader" aria-pressed="' +
      (role === "Leader" ? "true" : "false") + '">Leader</button>' +
      '<button type="button" data-dyn-role="Follower" aria-pressed="' +
      (role === "Follower" ? "true" : "false") + '">Follower</button>' +
      "</div></div>" +
      divChart +
      "<h3 style=\"font-size:12px;margin:12px 0 6px\">Editions ranked</h3>" +
      table;
  }

  function renderDivisionChart(host, eventEditions, role) {
    var EG = root.EGDynamics;
    var tiers = host.tiersEditions();
    var years = eventEditions.map(function (e) {
      return String(e.year).slice(2) + "/" + String(e.month).padStart(2, "0");
    });
    var seriesList = EG.DYNAMICS_RULES.divisions.map(function (div, i) {
      var points = eventEditions.map(function (e, idx) {
        var row = EG.findTiersRow(tiers, e.event_id, e.year, e.month);
        var counts = (row && row.counts && row.counts[div]) || {};
        var n = Number(counts[role]) || 0;
        var tier = row && row.tiers && row.tiers[div] ? row.tiers[div][role] : null;
        return {
          year: years[idx],
          entries: n,
          partial: !!e.partial,
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
    // Paths only from renderLineSvg; points are tier-colored (not division color).
    var svg = renderLineSvg(model, null, { skipPoints: true });
    var dots = [];
    model.lines.forEach(function (line) {
      line.points.forEach(function (p) {
        var tier = p.meta && p.meta.tier;
        dots.push(
          '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) +
          '" r="3.5" fill="' + esc(tierColor(tier)) +
          '" stroke="#fff" stroke-width="0.8">' +
          "<title>" + esc(line.label) + " · tier " + esc(String(tier || "—")) +
          " · " + esc(fmtN(p.v)) + "</title></circle>"
        );
      });
    });
    svg = svg.replace(
      "</svg>",
      dots.join("") + "</svg>"
    );
    return '<div class="dyn-chart"><div class="dyn-chart__title">Division headcount (' +
      esc(role) + ") — point color = tier</div>" + svg +
      '<div class="dyn-chart__legend">' +
      EG.DYNAMICS_RULES.divisions.map(function (d, i) {
        return '<span><i class="dyn-chart__swatch" style="background:' +
          EG.colorForIndex(i) + '"></i>' + esc(d) + "</span>";
      }).join("") +
      "</div></div>";
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

    return periodControlsHtml(host) +
      '<button type="button" class="dyn-back-link" data-dyn-jump="back-edition">← Back to event</button>' +
      "<h3 style=\"font-size:14px;margin:0 0 8px\">" +
      esc(edition.name) + " · " + esc(s.dynEditionKey) + "</h3>" +
      flagsHtml +
      '<div class="dyn-blocks">' +
      '<div class="dyn-block"><h3>Hypothesis flags</h3>' +
      '<p class="dyn-muted">Automatic signals — not verdicts. Use the facts below.</p></div>' +
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

  function wire(host, rootEl) {
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
    rootEl.querySelectorAll(".dyn-pt").forEach(function (pt) {
      pt.addEventListener("mouseenter", function () {
        var tip = pt.closest(".dyn-chart") &&
          pt.closest(".dyn-chart").querySelector("[data-dyn-tip]");
        if (!tip) return;
        var year = pt.getAttribute("data-year");
        var line = pt.getAttribute("data-line");
        var msg = line + " · " + year;
        if (host.state.dynEventId != null && line === "__event__") {
          var EG = root.EGDynamics;
          var ym = String(year || "");
          // year axis labels are yy/mm in event view
          var m = /^(\d{2})\/(\d{2})$/.exec(ym);
          if (m) {
            var fullY = 2000 + Number(m[1]);
            if (fullY < 1990) fullY = 1900 + Number(m[1]);
            var mon = Number(m[2]);
            var ed = host.editions().find(function (e) {
              return Number(e.event_id) === Number(host.state.dynEventId) &&
                Number(e.year) === fullY && Number(e.month) === mon;
            });
            if (ed) {
              var conc = EG.concurrentEditions(ed, host.editions());
              if (conc.length) {
                msg += " · " + conc.length + " same-weekend: " +
                  conc.slice(0, 3).map(function (c) { return c.name; }).join(", ");
              } else {
                msg += " · no same-weekend competitors on continent";
              }
            }
          }
        }
        tip.textContent = msg;
      });
    });
  }

  function render(host) {
    var layer = document.getElementById("dynLayer");
    var body = document.getElementById("dynBody");
    var crumb = document.getElementById("dynCrumb");
    var title = document.getElementById("dynTitle");
    if (!layer || !body || !host.state.dynOpen) return;
    if (title) title.textContent = "Dynamics · " + scopeTitle(host);
    if (crumb) crumb.innerHTML = crumbHtml(host);
    body.innerHTML = renderBody(host);
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
