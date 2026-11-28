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
      var anchor = "middle";
      if (model.years.length > 1) {
        if (i === 0) anchor = "start";
        else if (i === model.years.length - 1) anchor = "end";
      }
      parts.push(
        '<text x="' + x.toFixed(1) + '" y="' + (model.height - 6) +
        '" text-anchor="' + anchor + '" font-size="9" fill="#94a3b8">' +
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
    var years = host.years();
    var s = host.state;
    // Years stay in the island header; grain + metric live in the table toolbar
    // (same pattern as Event Trends list head).
    return '<select id="dynFrom" class="wsdc-select" aria-label="From year">' +
      yearOptsHtml(years, s.dynFrom) + "</select>" +
      '<select id="dynTo" class="wsdc-select" aria-label="To year">' +
      yearOptsHtml(years, s.dynTo) + "</select>";
  }

  function grainSelectHtml(host) {
    var EG = root.EGDynamics;
    var s = host.state;
    var allowed = EG.allowedGrains(s.level, s.continent, s.country, s.city);
    var grain = s.dynGrain;
    if (!grain || allowed.indexOf(grain) === -1) {
      grain = EG.naturalGrain(s.level, s.country, s.city);
      s.dynGrain = grain;
    }
    if (allowed.length <= 1) {
      return '<span class="dyn-muted">' +
        esc(GRAIN_LABELS[allowed[0] || "event"] || "Events") + "</span>";
    }
    return '<select id="dynGrain" class="wsdc-select eg-grain-select" aria-label="Breakdown">' +
      allowed.map(function (g) {
        return '<option value="' + g + '"' +
          (g === grain ? " selected" : "") + ">" +
          esc(GRAIN_LABELS[g] || g) + "</option>";
      }).join("") +
      "</select>";
  }

  var COMPARE_MAX = 5;
  var METRIC_OPTS = [
    { id: "entries", label: "Entries / year", fmt: "n" },
    { id: "events", label: "Events / year", fmt: "n" },
    { id: "entriesPerEvent", label: "Entries / event", fmt: "1" }
  ];

  function metricMeta(id) {
    for (var i = 0; i < METRIC_OPTS.length; i++) {
      if (METRIC_OPTS[i].id === id) return METRIC_OPTS[i];
    }
    return METRIC_OPTS[0];
  }

  function dynMetricOf(host) {
    var id = host.state.dynMetric || "entries";
    return metricMeta(id).id;
  }

  function fmtMetric(fmt, n) {
    return fmt === "1" ? fmt1(n) : fmtN(n);
  }

  function compareKeysOf(host) {
    if (!Array.isArray(host.state.dynCompareKeys)) host.state.dynCompareKeys = [];
    return host.state.dynCompareKeys;
  }

  function showTotalOf(host) {
    if (host.state.dynShowTotal == null) host.state.dynShowTotal = true;
    return !!host.state.dynShowTotal;
  }

  function compareColor(EG, keys, key) {
    var i = keys.indexOf(String(key));
    if (i < 0) return null;
    return EG.colorForIndex(i);
  }

  function toggleCompareKey(host, key) {
    var keys = compareKeysOf(host).slice();
    var k = String(key);
    var i = keys.indexOf(k);
    if (i >= 0) {
      keys.splice(i, 1);
      if (!keys.length) host.state.dynShowTotal = true;
    } else if (keys.length < COMPARE_MAX) {
      // First selection: drop Total so the line is readable (can re-enable).
      if (!keys.length) host.state.dynShowTotal = false;
      keys.push(k);
    } else {
      return false;
    }
    host.state.dynCompareKeys = keys;
    return true;
  }

  /**
   * Default: Total alone. With compare rows: selected lines only,
   * unless dynShowTotal is still on.
   */
  function buildSeriesList(bd, compareKeys, showTotal) {
    var EG = root.EGDynamics;
    var keys = compareKeys || [];
    var list = [];
    var includeTotal = showTotal || !keys.length;
    if (includeTotal) {
      list.push({
        key: "__total__",
        label: "Total",
        color: EG.TOTAL_COLOR,
        points: bd.total || [],
        avg: null
      });
    }
    var byKey = {};
    (bd.rows || []).forEach(function (row) {
      byKey[String(row.key)] = row;
    });
    keys.forEach(function (key, i) {
      var row = byKey[String(key)];
      if (!row) return;
      list.push({
        key: row.key,
        label: row.label,
        color: EG.colorForIndex(i),
        points: row.series,
        avg: null
      });
    });
    return list;
  }

  function metricCard(label, metric, valueHtml, bd, years, compareKeys, showTotal) {
    var EG = root.EGDynamics;
    var series = buildSeriesList(bd, compareKeys, showTotal);
    var model = EG.lineChartModel(series, {
      metric: metric,
      years: years,
      width: 640,
      height: 200,
      padL: 40,
      padR: 22,
      padT: 12,
      padB: 28
    });
    var tipYears = years.map(function (y, i) {
      return {
        year: y,
        x: model.xAt(i),
        rows: model.lines.map(function (line) {
          var pt = (line.points && line.points[i]) ||
            (line.byYear && line.byYear[String(y)]);
          return {
            key: line.key,
            label: line.label,
            color: line.color,
            value: pt ? pt.v : null
          };
        })
      };
    });
    return '<div class="dyn-metric-card" data-metric="' + esc(metric) + '">' +
      '<div class="dyn-metric-card__head">' +
      '<div class="dyn-kpi__lbl">' + esc(label) + "</div>" +
      '<div class="dyn-kpi__val">' + valueHtml + "</div>" +
      "</div>" +
      '<div class="dyn-chart">' +
      renderLineSvg(model, null) +
      '<script type="application/json" class="dyn-chart-tipdata">' +
      JSON.stringify(tipYears).replace(/</g, "\\u003c") +
      "</script></div></div>";
  }

  function sparkSvgHtml(pts) {
    var EG = root.EGDynamics;
    var m = EG.sparklineModel(pts, 72, 22, 3);
    if (!m.path) {
      return '<span class="dyn-muted">—</span>';
    }
    var marks = (m.marks || []).map(function (mk) {
      var fill = mk.kind === "min" ? "#dc2626"
        : (mk.kind === "max" ? "#16a34a" : "#64748b");
      var tip = String(mk.year) + " · " + fmtN(mk.v);
      return '<circle class="dyn-spark-mark" data-spark-tip="' + esc(tip) +
        '" cx="' + mk.x.toFixed(1) + '" cy="' + mk.y.toFixed(1) +
        '" r="2.6" fill="' + fill + '"><title>' + esc(tip) +
        "</title></circle>";
    }).join("");
    return '<span class="dyn-spark-wrap">' +
      '<svg class="dyn-spark" viewBox="0 0 72 22" aria-hidden="true">' +
      '<path d="' + m.path +
      '" fill="none" stroke="#94a3b8" stroke-width="1.4"' +
      ' stroke-linecap="round" stroke-linejoin="round"/>' +
      marks + "</svg></span>";
  }

  function metricSelectHtml(selected) {
    return '<select id="dynMetric" class="wsdc-select eg-metric-select" aria-label="Metric">' +
      METRIC_OPTS.map(function (m) {
        return '<option value="' + m.id + '"' +
          (m.id === selected ? " selected" : "") + ">" +
          esc(m.label) + "</option>";
      }).join("") +
      "</select>";
  }

  function tableHtml(host, bd, compareKeys, grain, metric, showTotal) {
    var EG = root.EGDynamics;
    var keys = compareKeys || [];
    var rows = bd.rows || [];
    var meta = metricMeta(metric);
    var toolbar =
      '<div class="dyn-table-head">' +
      '<div class="dyn-table-head__grain">' + grainSelectHtml(host) + "</div>" +
      '<div class="dyn-table-head__metric">' + metricSelectHtml(metric) +
      "</div></div>";
    var thead =
      "<thead><tr>" +
      '<th class="dyn-col-check" scope="col"><span class="visually-hidden">Compare</span></th>' +
      "<th>" + esc(GRAIN_LABELS[grain] || grain) + "</th>" +
      '<th class="num">' + esc(meta.label) + "</th>" +
      '<th scope="col">Trend</th></tr></thead>';

    var totalChecked = !!showTotal || !keys.length;
    var totalSwatch = totalChecked
      ? '<i class="dyn-chart__swatch" style="background:' + esc(EG.TOTAL_COLOR) +
        '" aria-hidden="true"></i>'
      : "";
    var totalAv = EG.periodAverages(bd.total || []);
    var totalSparkPts = (bd.total || []).map(function (p) {
      return (p.partial || p.missing) ? null : { year: p.year, v: p[metric] };
    }).filter(Boolean);
    var totalRow =
      '<tr class="' + (totalChecked ? "is-compare" : "") +
      '" data-dyn-total-row="1">' +
      '<td class="dyn-col-check"><label class="dyn-compare">' +
      '<input type="checkbox" data-dyn-total="1"' +
      (totalChecked ? " checked" : "") +
      (!keys.length ? " disabled" : "") +
      ' aria-label="Show Total"/>' + totalSwatch + "</label></td>" +
      "<td><strong>Total</strong></td>" +
      '<td class="num">' + esc(fmtMetric(meta.fmt, totalAv[metric])) + "</td>" +
      "<td>" + sparkSvgHtml(totalSparkPts) + "</td></tr>";

    var body = rows.map(function (r) {
      var sparkPts = (r.series || []).map(function (p) {
        return (p.partial || p.missing) ? null : { year: p.year, v: p[metric] };
      }).filter(Boolean);
      var checked = keys.indexOf(String(r.key)) !== -1;
      var color = compareColor(EG, keys, r.key);
      var a = r.averages || {};
      var swatch = checked && color
        ? '<i class="dyn-chart__swatch" style="background:' + esc(color) +
          '" aria-hidden="true"></i>'
        : "";
      return '<tr class="' + (checked ? "is-compare" : "") +
        '" data-dyn-row="' + esc(String(r.key)) + '">' +
        '<td class="dyn-col-check">' +
        '<label class="dyn-compare">' +
        '<input type="checkbox" data-dyn-compare="' + esc(String(r.key)) + '"' +
        (checked ? " checked" : "") +
        (!checked && keys.length >= COMPARE_MAX ? " disabled" : "") +
        ' aria-label="Compare ' + esc(r.label) + '"/>' +
        swatch + "</label></td>" +
        "<td>" + esc(r.label) + "</td>" +
        '<td class="num">' + esc(fmtMetric(meta.fmt, a[metric])) + "</td>" +
        "<td>" + sparkSvgHtml(sparkPts) + "</td>" +
        "</tr>";
    }).join("");
    return '<div class="dyn-table-wrap">' + toolbar +
      '<table class="dyn-table">' + thead + "<tbody>" + totalRow + body +
      "</tbody></table>" +
      '<p class="dyn-compare-hint dyn-muted">Default: Total. Check rows to compare ' +
      "(Total turns off automatically — re-check Total to overlay). " +
      "Double-click a row to drill in.</p></div>";
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
    var metric = dynMetricOf(host);
    host.state.dynMetric = metric;
    var meta = metricMeta(metric);
    var bd = EG.breakdown(
      host.editions(), geo, grain, range, through, EG.DYNAMICS_RULES.topN
    );
    var avgs = EG.periodAverages(bd.total);
    var years = EG.yearsInRange(s.dynFrom, s.dynTo);
    var compareKeys = compareKeysOf(host).filter(function (k) {
      return (bd.rows || []).some(function (r) {
        return String(r.key) === String(k);
      });
    });
    host.state.dynCompareKeys = compareKeys;
    var showTotal = showTotalOf(host);
    if (!compareKeys.length) showTotal = true;
    var kpiSeries = buildSeriesList(bd, compareKeys, showTotal);
    var kpiAvgs = compareKeys.length && !showTotal && kpiSeries.length === 1
      ? EG.periodAverages(kpiSeries[0].points)
      : avgs;
    return '<div class="dyn-charts">' +
      metricCard(meta.label, metric,
        esc(fmtMetric(meta.fmt, kpiAvgs[metric])),
        bd, years, compareKeys, showTotal) +
      "</div>" +
      tableHtml(host, bd, compareKeys, grain, metric, showTotal);
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
      avg: null
    }], {
      metric: "entries",
      years: years,
      width: 640,
      height: 200,
      padL: 40,
      padR: 22,
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

    return '<button type="button" class="dyn-back-link" data-dyn-jump="back-event">← Back to geography</button>' +
      '<div class="dyn-kpis"><div class="dyn-kpi"><div class="dyn-kpi__lbl">Entries / edition</div>' +
      '<div class="dyn-kpi__val">' + esc(fmtN(series.average)) + "</div></div></div>" +
      '<div class="dyn-charts"><div class="dyn-chart">' +
      '<div class="dyn-chart__title">Entries by edition</div>' +
      renderLineSvg(model, null) +
      "</div></div>" +
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
      padR: 22,
      padT: 12,
      padB: 28
    });
    var svg = renderLineSvg(model, null, { tierDots: true });
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

    return '<button type="button" class="dyn-back-link" data-dyn-jump="back-edition">← Back to event</button>' +
      "<h3 style=\"font-size:14px;margin:0 0 8px\">" +
      esc(edition.name) + " · " + esc(s.dynEditionKey) + "</h3>" +
      flagsHtml +
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
        host.state.dynCompareKeys = [];
        host.state.dynShowTotal = true;
        host.writeUrl();
        host.render();
      });
    }
    var metricSel = rootEl.querySelector("#dynMetric");
    if (metricSel) {
      metricSel.addEventListener("change", function () {
        host.state.dynMetric = metricSel.value;
        host.render();
      });
    }
    rootEl.querySelectorAll("[data-dyn-jump]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        host.jump(btn.getAttribute("data-dyn-jump"));
      });
    });
    var totalInp = rootEl.querySelector("[data-dyn-total]");
    if (totalInp) {
      totalInp.addEventListener("click", function (ev) { ev.stopPropagation(); });
      totalInp.addEventListener("change", function () {
        if (!compareKeysOf(host).length) {
          totalInp.checked = true;
          host.state.dynShowTotal = true;
          return;
        }
        host.state.dynShowTotal = !!totalInp.checked;
        host.render();
      });
    }
    rootEl.querySelectorAll("[data-dyn-compare]").forEach(function (inp) {
      inp.addEventListener("click", function (ev) {
        ev.stopPropagation();
      });
      inp.addEventListener("change", function () {
        var key = inp.getAttribute("data-dyn-compare");
        var keys = compareKeysOf(host);
        var on = keys.indexOf(String(key)) !== -1;
        if (inp.checked && !on) {
          if (!toggleCompareKey(host, key)) {
            inp.checked = false;
            return;
          }
        } else if (!inp.checked && on) {
          toggleCompareKey(host, key);
        }
        host.render();
      });
    });
    rootEl.querySelectorAll("[data-dyn-row]").forEach(function (tr) {
      tr.addEventListener("click", function (ev) {
        if (ev.target && ev.target.closest &&
            (ev.target.closest("[data-dyn-compare]") ||
             ev.target.closest("[data-dyn-total]") ||
             ev.target.closest(".dyn-spark-wrap"))) {
          return;
        }
        var key = tr.getAttribute("data-dyn-row");
        toggleCompareKey(host, key);
        host.render();
      });
      tr.addEventListener("dblclick", function () {
        var key = tr.getAttribute("data-dyn-row");
        host.drillRow(key);
      });
    });
    rootEl.querySelectorAll(".dyn-spark-mark").forEach(function (mark) {
      mark.addEventListener("mousemove", function (ev) {
        var t = mark.getAttribute("data-spark-tip") || "";
        if (!t) return;
        showFloatTip(body, '<div class="dyn-float-tip__y">' + esc(t) + "</div>",
          ev.clientX, ev.clientY);
      });
      mark.addEventListener("mouseleave", function () {
        hideFloatTip(body);
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
    if (title) title.textContent = "Dynamics · " + scopeTitle(host);
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
    host.state.dynCompareKeys = [];
    host.state.dynShowTotal = true;
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
