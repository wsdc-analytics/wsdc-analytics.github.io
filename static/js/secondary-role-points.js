/** Secondary Role Points bubble chart + filters/KPIs. */
(function () {
  "use strict";

    function buildAdaptiveRadiusMap(rows) {
      // Bubble size should match dancers shown in drawer for current slice:
      // only dancers who contributed secondary-role points.
      const counts = rows.map((r) => Math.max(0, Number(r.transitions) || 0));
      const positives = counts.filter((v) => v > 0);
      if (!positives.length) {
        return rows.map(() => 0);
      }

      const minPositive = Math.min(...positives);
      const maxCount = Math.max(...positives);

      // Keep 1-2 dancers visually small (not dominant), but still clickable.
      // Scale by current slice to preserve differentiation across filters.
      let minR = 5.5;
      let maxR = 30;
      if (maxCount <= 3) {
        minR = 6;
        maxR = 20;
      } else if (maxCount <= 8) {
        minR = 6;
        maxR = 23;
      } else if (maxCount <= 25) {
        minR = 5.5;
        maxR = 26;
      }

      return rows.map((r) => {
        const c = Math.max(0, Number(r.transitions) || 0);
        if (c <= 0) return 0;
        if (maxCount === minPositive) {
          return minR;
        }
        // Perception-friendly area scaling + slight easing for mid-range spread.
        const tRaw = (Math.sqrt(c) - Math.sqrt(minPositive)) / (Math.sqrt(maxCount) - Math.sqrt(minPositive));
        const t = Math.pow(Math.min(1, Math.max(0, tRaw)), 0.9);
        return minR + t * (maxR - minR);
      });
    }

    const COUNTRY_TO_CODE = {
      "United States": "US",
      "Russia": "RU",
      "Germany": "DE",
      "France": "FR",
      "Canada": "CA",
      "Sweden": "SE",
      "Poland": "PL",
      "Hungary": "HU",
      "Australia": "AU",
      "Finland": "FI",
      "Austria": "AT",
      "Netherlands": "NL",
      "United Kingdom": "GB",
      "New Zealand": "NZ",
      "Norway": "NO",
      "Czech Republic": "CZ",
      "Singapore": "SG",
      "Italy": "IT",
      "Israel": "IL",
      "Republic of Korea": "KR",
      "South Korea": "KR",
      "Switzerland": "CH",
      "Belgium": "BE",
      "Latvia": "LV",
      "Spain": "ES",
      "Slovenia": "SI",
      "Portugal": "PT",
      "Romania": "RO",
      "Ireland": "IE",
      "Bulgaria": "BG",
      "Malaysia": "MY"
    };

    function codeToFlag(code) {
      if (!code || code.length !== 2) return "";
      return String.fromCodePoint(
        127397 + code.charCodeAt(0),
        127397 + code.charCodeAt(1)
      );
    }

    function getCountryFlag(country) {
      return codeToFlag(COUNTRY_TO_CODE[country] || "");
    }

    const flagImageCache = {};
    function getFlagImage(code, onReady) {
      if (!code) return null;
      if (flagImageCache[code]) return flagImageCache[code];
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = function () {
        onReady();
      };
      img.src = `static/flags/w80/${code.toLowerCase()}.png`;
      flagImageCache[code] = img;
      return img;
    }

    function getSourceRows(year, group, division) {
      const years = (unifiedData && unifiedData.years) ? unifiedData.years : (unifiedData || {});
      return ((((years || {})[year] || {})[group] || {})[division]) || [];
    }

    function isMobileViewport() {
      return window.matchMedia("(max-width: 900px)").matches;
    }

    function getBubbleScaleFactor() {
      if (!isMobileViewport()) return 1;
      if (window.matchMedia("(max-width: 480px)").matches) return 0.64;
      return 0.74;
    }

    function getDensityScale(pointCount) {
      if (!isMobileViewport()) return 1;
      if (pointCount >= 28) return 0.76;
      if (pointCount >= 20) return 0.84;
      if (pointCount >= 14) return 0.92;
      return 1;
    }

    function isUnitedStates(country) {
      return String(country || "").trim().toLowerCase() === "united states";
    }

    function getPoints(year, group, division, hideUsa) {
      const rows = getSourceRows(year, group, division);
      const filteredRows = rows
        .filter((r) => r.transitions > 0)
        .filter((r) => !hideUsa || !isUnitedStates(r.country));
      const radii = buildAdaptiveRadiusMap(filteredRows);
      const bubbleScale = getBubbleScaleFactor() * getDensityScale(filteredRows.length);
      const points = filteredRows.map((r, i) => ({
          x: r.secondary_share * 100,
          y: r.secondary_points,
          r: Math.max(2.4, (Number(radii[i]) || 0) * bubbleScale),
          country: r.country,
          code: COUNTRY_TO_CODE[r.country] || "",
          flag: getCountryFlag(r.country),
          dancersCount: r.dancers_count,
          transitions: r.transitions,
          share: r.secondary_share,
          total: r.total_points
        }));
      // Draw large bubbles first so small ones stay clickable on top.
      points.sort((a, b) => (Number(b.r) || 0) - (Number(a.r) || 0));
      return points;
    }

    function applyDynamicAxisPadding(points) {
      const xScale = chart.options.scales.x;
      const yScale = chart.options.scales.y;
      if (!points || !points.length) {
        xScale.min = 0;
        xScale.max = undefined;
        yScale.beginAtZero = true;
        yScale.max = undefined;
        return;
      }
      const maxX = points.reduce((m, p) => Math.max(m, Number(p.x) || 0), 0);
      const maxY = points.reduce((m, p) => Math.max(m, Number(p.y) || 0), 0);
      const maxR = points.reduce((m, p) => Math.max(m, Number(p.r) || 0), 0);
      const xPad = Math.min(3.6, Math.max(1.2, maxR * 0.12));
      // Convert bubble pixel radius into Y data units so large countries (USA)
      // stay inside the plot and do not collide with the filter row above.
      const rawAreaH = chart.chartArea
        ? chart.chartArea.bottom - chart.chartArea.top
        : 0;
      const areaH = rawAreaH > 1 ? rawAreaH : 400;
      const yPadFromRadius = maxY > 0 ? (maxY * (maxR * 1.35)) / areaH : maxR;
      const yPad = Math.max(6, maxY * 0.06, yPadFromRadius);
      const xMax = Math.max(5, maxX + xPad);
      xScale.min = 0;
      xScale.max = Math.ceil(xMax / 5) * 5;
      yScale.beginAtZero = true;
      yScale.max = Math.ceil((maxY + yPad) / 5) * 5;
    }

    /** Place external tooltip inside the chart box; flip below when near the top. */
    function placeExtTooltip(tooltipEl, cx, cy, parent) {
      const pad = 10;
      const gap = 8;
      tooltipEl.style.left = `${cx}px`;
      tooltipEl.style.top = `${cy}px`;
      const tw = tooltipEl.offsetWidth;
      const th = tooltipEl.offsetHeight;
      const pw = parent.clientWidth;
      const ph = parent.clientHeight;
      if (!tw || !pw) {
        tooltipEl.style.transform = `translate(-50%, calc(-100% - ${gap}px))`;
        return;
      }
      let dx;
      let dy;
      if (cx - tw / 2 < pad) {
        dx = gap;
        dy = -th / 2;
      } else if (cx + tw / 2 > pw - pad) {
        dx = -tw - gap;
        dy = -th / 2;
      } else {
        dx = -tw / 2;
        dy = cy - th - gap < pad ? gap : -(th + gap);
      }
      if (cy + dy < pad) dy = pad - cy;
      if (cy + dy + th > ph - pad) dy = ph - pad - cy - th;
      tooltipEl.style.transform = `translate(${dx}px, ${dy}px)`;
    }

    const ctx = document.getElementById("geoBubble");
    const yearSelEl = document.getElementById("yearSel");
    const hideUsaEl = document.getElementById("hideUsa");
    const groupSelEl = document.getElementById("groupSel");
    const divisionSelEl = document.getElementById("divisionSel");
    const drawerEl = document.getElementById("dancerDrawer");
    const drawerTitleEl = document.getElementById("dancerDrawerTitle");
    const drawerBodyEl = document.getElementById("dancerDrawerBody");
    const drawerCloseEl = document.getElementById("dancerDrawerClose");
    const kpiTotalEl = document.getElementById("kpiTotal");
    const kpiSecondaryEl = document.getElementById("kpiSecondary");
    const kpiShareEl = document.getElementById("kpiShare");
    const kpiMeanShareEl = document.getElementById("kpiMeanShare");
    const kpiMeanPointsEl = document.getElementById("kpiMeanPoints");
    let activeYear = "2026";
    let activeGroup = "Total";
    let activeDivision = "Total";
    const pinState = { active: false, point: null, x: 0, y: 0 };
    const UNIFIED_URL = "static/data/secondary_country_unified.json?v=20261001c";
    let unifiedData = null;
    let unifiedLoadPromise = null;

    if (!ctx) {
      console.error("Secondary Role Points: #geoBubble canvas missing");
      wireChrome();
      return;
    }

    function getOrCreateTooltip(chart) {
      let tooltipEl = chart.canvas.parentNode.querySelector(".chartjs-ext-tooltip");
      if (!tooltipEl) {
        tooltipEl = document.createElement("div");
        tooltipEl.className = "chartjs-ext-tooltip";
        chart.canvas.parentNode.style.position = "relative";
        chart.canvas.parentNode.appendChild(tooltipEl);
        tooltipEl.addEventListener("click", async (event) => {
          const actionBtn = event.target && event.target.closest("[data-action='show-dancers']");
          if (!actionBtn) return;
          event.preventDefault();
          if (!pinState.point) return;
          await openDancerDrawer(pinState.point);
        });
      }
      return tooltipEl;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#39;");
    }

    async function ensureUnifiedData() {
      if (unifiedData) return unifiedData;
      if (!unifiedLoadPromise) {
        unifiedLoadPromise = fetch(UNIFIED_URL, { cache: "no-cache" })
          .then((res) => {
            if (!res.ok) throw new Error(`Failed to load unified data: ${res.status}`);
            return res.json();
          })
          .then((json) => {
            unifiedData = json;
            const asOf = json && json.data_as_of;
            const updatedEl = document.getElementById("dataUpdated");
            if (updatedEl) updatedEl.textContent = asOf ? `Updated ${asOf}` : "Updated —";
            return unifiedData;
          });
      }
      return unifiedLoadPromise;
    }

    function getDancerRowsFromData(data, year, group, division, country) {
      const years = (data && data.years) ? data.years : (data || {});
      const rows = ((((years || {})[year] || {})[group] || {})[division]) || [];
      const match = rows.find((r) => r.country === country);
      return (match && Array.isArray(match.dancers)) ? match.dancers : [];
    }

    function closeDancerDrawer() {
      drawerEl.hidden = true;
      drawerBodyEl.innerHTML = "";
    }

    function clearPin(chart) {
      pinState.active = false;
      pinState.point = null;
      pinState.x = 0;
      pinState.y = 0;
      const tooltipEl = getOrCreateTooltip(chart);
      tooltipEl.style.opacity = 0;
      tooltipEl.style.transform = "";
      tooltipEl.classList.remove("is-pinned");
    }

    async function openDancerDrawer(point) {
      drawerEl.hidden = false;
      drawerTitleEl.textContent = `${point.country} · ${activeYear} · ${activeGroup} · ${activeDivision}`;
      drawerBodyEl.innerHTML = "<p class=\"drawer-muted\">Loading dancers...</p>";
      try {
        const data = await ensureUnifiedData();
        const rows = getDancerRowsFromData(data, activeYear, activeGroup, activeDivision, point.country);
        if (!rows.length) {
          drawerBodyEl.innerHTML = "<p class=\"drawer-muted\">No dancers with secondary-role points for this slice.</p>";
          return;
        }
        const tableRows = rows.map((row) => (
          `<tr><td>${escapeHtml(row.name || "")}</td><td>${Math.round(Number(row.secondary_points) || 0)}</td></tr>`
        )).join("");
        drawerBodyEl.innerHTML = [
          `<table class="dancer-table">`,
          `<thead><tr><th>Dancer</th><th>Points</th></tr></thead>`,
          `<tbody>${tableRows}</tbody>`,
          `</table>`
        ].join("");
      } catch (err) {
        drawerBodyEl.innerHTML = `<p class="drawer-muted">Unable to load dancers list.</p>`;
      }
    }

    function formatTooltipRows(d) {
      const total = Number(d.total);
      const secPts = Number(d.y);
      const share = Number(d.x);
      const intOrDash = (v) =>
        v == null || Number.isNaN(v) ? "—" : String(Math.round(v));
      const shareStr =
        share == null || Number.isNaN(share) ? "—" : `${share.toFixed(1)}%`;
      const rows = [
        { label: "Total points", value: intOrDash(total) },
        { label: "Secondary-role points", value: intOrDash(secPts) },
        { label: "Secondary-role share", value: shareStr }
      ];
      const metricsHtml = rows
        .map(
          (r) =>
            `<div class="tt-row"><span class="tt-label">${r.label}</span><span class="tt-value">${r.value}</span></div>`
        )
        .join("");
      const dancersInList = Number.isFinite(Number(d.transitions)) ? Math.max(0, Math.round(Number(d.transitions))) : 0;
      const actionHtml = `<div class="tt-action-row"><button class="tt-action" data-action="show-dancers">View dancers (${dancersInList})</button></div>`;
      return metricsHtml + actionHtml;
    }

    function renderPinnedTooltip(chart, tooltipEl) {
      if (!pinState.active || !pinState.point) return;
      tooltipEl.classList.add("is-pinned");
      tooltipEl.innerHTML = `<div class="tt-title">${pinState.point.country || "—"}</div>${formatTooltipRows(pinState.point)}`;
      const canvas = chart.canvas;
      const parent = canvas.parentNode;
      const cx = canvas.offsetLeft + pinState.x;
      const cy = canvas.offsetTop + pinState.y;
      tooltipEl.style.opacity = 1;
      requestAnimationFrame(() => placeExtTooltip(tooltipEl, cx, cy, parent));
    }

    function setSummaryKpis(points) {
      const valid = (points || []).filter((p) => p && Number.isFinite(p.x) && Number.isFinite(p.y));
      const dash = "—";
      if (!valid.length) {
        if (kpiTotalEl) kpiTotalEl.textContent = dash;
        if (kpiSecondaryEl) kpiSecondaryEl.textContent = dash;
        if (kpiShareEl) kpiShareEl.textContent = dash;
        if (kpiMeanShareEl) kpiMeanShareEl.textContent = dash;
        if (kpiMeanPointsEl) kpiMeanPointsEl.textContent = dash;
        return;
      }
      const totalPoints = valid.reduce((s, p) => s + (Number(p.total) || 0), 0);
      const secondaryPoints = valid.reduce((s, p) => s + (Number(p.y) || 0), 0);
      const secondaryShare = totalPoints > 0 ? (secondaryPoints / totalPoints) * 100 : 0;
      const meanX = valid.reduce((s, p) => s + p.x, 0) / valid.length;
      const meanY = valid.reduce((s, p) => s + p.y, 0) / valid.length;
      if (kpiTotalEl) kpiTotalEl.textContent = String(Math.round(totalPoints));
      if (kpiSecondaryEl) kpiSecondaryEl.textContent = String(Math.round(secondaryPoints));
      if (kpiShareEl) kpiShareEl.textContent = `${secondaryShare.toFixed(1)}%`;
      if (kpiMeanShareEl) kpiMeanShareEl.textContent = `${meanX.toFixed(1)}%`;
      if (kpiMeanPointsEl) kpiMeanPointsEl.textContent = meanY.toFixed(0);
    }

    const referenceMeanLinesPlugin = {
      id: "referenceMeanLinesPlugin",
      beforeDatasetsDraw(chart) {
        const dataset = chart.data && chart.data.datasets && chart.data.datasets[0];
        const points = (dataset && dataset.data) ? dataset.data : [];
        const valid = points.filter((p) => p && Number.isFinite(p.x) && Number.isFinite(p.y));
        if (!valid.length) return;

        const meanX = valid.reduce((s, p) => s + p.x, 0) / valid.length;
        const meanY = valid.reduce((s, p) => s + p.y, 0) / valid.length;

        const xScale = chart.scales.x;
        const yScale = chart.scales.y;
        const area = chart.chartArea;
        if (!xScale || !yScale || !area) return;

        const xPx = xScale.getPixelForValue(meanX);
        const yPx = yScale.getPixelForValue(meanY);
        if (!Number.isFinite(xPx) || !Number.isFinite(yPx)) return;

        const ctx = chart.ctx;
        ctx.save();
        ctx.setLineDash([6, 6]);
        ctx.lineWidth = 1.1;
        ctx.strokeStyle = "rgba(107, 114, 128, 0.65)";

        ctx.beginPath();
        ctx.moveTo(xPx, area.top);
        ctx.lineTo(xPx, area.bottom);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(area.left, yPx);
        ctx.lineTo(area.right, yPx);
        ctx.stroke();

        ctx.restore();
      }
    };

    const flagBubblePlugin = {
      id: "flagBubblePlugin",
      afterDatasetsDraw(chart) {
        const meta = chart.getDatasetMeta(0);
        const points = chart.data.datasets[0].data || [];
        const ctx = chart.ctx;
        ctx.save();
        meta.data.forEach((el, i) => {
          const d = points[i];
          if (!d) return;
          const x = el.x;
          const y = el.y;
          const r = Math.max(3, d.r || 8);
          const code = d.code || "";
          const img = getFlagImage(code, () => chart.update("none"));

          // circular clip area for flag-filled bubble
          ctx.save();
          ctx.beginPath();
          ctx.arc(x, y, r, 0, Math.PI * 2);
          ctx.closePath();
          ctx.clip();

          if (img && img.complete && img.naturalWidth > 0) {
            const side = r * 2;
            const sw = img.naturalWidth;
            const sh = img.naturalHeight;
            const srcSize = Math.min(sw, sh);
            const sx = (sw - srcSize) / 2;
            const sy = (sh - srcSize) / 2;
            ctx.globalAlpha = 0.8;
            ctx.drawImage(img, sx, sy, srcSize, srcSize, x - r, y - r, side, side);
            ctx.globalAlpha = 1;
          } else {
            ctx.fillStyle = "rgba(37,99,235,0.35)";
            ctx.fill();
          }
          ctx.restore();

          // thin gray border around each flag bubble
          ctx.beginPath();
          ctx.arc(x, y, r, 0, Math.PI * 2);
          ctx.strokeStyle = "rgba(107, 114, 128, 0.85)";
          ctx.lineWidth = 0.8;
          ctx.stroke();

        });
        ctx.restore();
      }
    };

    const chart = new Chart(ctx, {
      type: "bubble",
      plugins: [referenceMeanLinesPlugin, flagBubblePlugin],
      data: {
        datasets: [{
          label: "Countries",
          data: getPoints(activeYear, activeGroup, activeDivision, false),
          borderColor: "rgba(55,65,81,0.45)",
          backgroundColor: "rgba(59,130,246,0.18)",
          borderWidth: 0.8
        }]
      },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "nearest", intersect: true },
        onClick: (evt, elements, chartInstance) => {
          const hits = chartInstance.getElementsAtEventForMode(
            evt,
            "nearest",
            { intersect: true },
            true
          );
          if (!hits.length) {
            clearPin(chartInstance);
            closeDancerDrawer();
            return;
          }
          const hit = hits[0];
          const ds = chartInstance.data.datasets[hit.datasetIndex];
          const point = ds && ds.data ? ds.data[hit.index] : null;
          const el = chartInstance.getDatasetMeta(hit.datasetIndex).data[hit.index];
          if (!point || !el) return;
          pinState.active = true;
          pinState.point = point;
          pinState.x = el.x;
          pinState.y = el.y;
          const tooltipEl = getOrCreateTooltip(chartInstance);
          renderPinnedTooltip(chartInstance, tooltipEl);
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: false,
            external: ({ chart, tooltip }) => {
              const tooltipEl = getOrCreateTooltip(chart);
              if (pinState.active && pinState.point) {
                renderPinnedTooltip(chart, tooltipEl);
                return;
              }
              tooltipEl.classList.remove("is-pinned");
              if (tooltip.opacity === 0) {
                tooltipEl.style.opacity = 0;
                tooltipEl.style.transform = "";
                return;
              }
              const dp = tooltip.dataPoints && tooltip.dataPoints[0];
              if (!dp || !dp.raw) {
                tooltipEl.style.opacity = 0;
                return;
              }
              const d = dp.raw;
              const title = d.country || "—";
              tooltipEl.innerHTML = `<div class="tt-title">${title}</div>${formatTooltipRows(d)}`;
              const canvas = chart.canvas;
              const parent = canvas.parentNode;
              const cx = canvas.offsetLeft + tooltip.caretX;
              const cy = canvas.offsetTop + tooltip.caretY;
              tooltipEl.style.opacity = 1;
              requestAnimationFrame(() => placeExtTooltip(tooltipEl, cx, cy, parent));
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: "Share of points, %" },
            min: 0,
            ticks: {
              stepSize: 5,
              callback: function(value) {
                const n = Number(this.getLabelForValue(value));
                return Number.isFinite(n) ? Math.round(n) : "";
              }
            },
            grid: { display: false, drawBorder: true, drawTicks: false }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Points" },
            ticks: {
              callback: function(value) {
                const n = Number(this.getLabelForValue(value));
                if (!Number.isFinite(n)) return "";
                if (Math.abs(n) < 1e-9) return "";
                return Math.round(n);
              }
            },
            grid: { display: false, drawBorder: true, drawTicks: false }
          }
        }
      }
    });

    function applyResponsiveChartTypography() {
      const tiny = window.matchMedia("(max-width: 480px)").matches;
      const mobile = isMobileViewport();
      const tickSize = mobile ? (tiny ? 9 : 10) : 12;
      const titleSize = mobile ? (tiny ? 10 : 11) : 13;
      chart.options.scales.x.ticks.font = { size: tickSize };
      chart.options.scales.y.ticks.font = { size: tickSize };
      chart.options.scales.x.title.font = { size: titleSize, weight: "600" };
      chart.options.scales.y.title.font = { size: titleSize, weight: "600" };
    }

    function updateChart() {
      if (!chart || !hideUsaEl) return;
      applyResponsiveChartTypography();
      const points = getPoints(activeYear, activeGroup, activeDivision, !!hideUsaEl.checked);
      applyDynamicAxisPadding(points);
      setSummaryKpis(points);
      chart.data.datasets[0].data = points;
      clearPin(chart);
      closeDancerDrawer();
      chart.update();
    }

    window.addEventListener("resize", updateChart);

    if (yearSelEl) {
      yearSelEl.addEventListener("change", function () {
        activeYear = this.value;
        updateChart();
      });
    }
    if (hideUsaEl) hideUsaEl.addEventListener("change", updateChart);
    if (groupSelEl) {
      groupSelEl.addEventListener("change", function () {
        activeGroup = this.value;
        updateChart();
      });
    }
    if (divisionSelEl) {
      divisionSelEl.addEventListener("change", function () {
        activeDivision = this.value;
        updateChart();
      });
    }
    if (drawerCloseEl) {
      drawerCloseEl.addEventListener("click", () => {
        closeDancerDrawer();
      });
    }

    ensureUnifiedData()
      .then(() => updateChart())
      .catch((err) => {
        console.error(err);
        const updatedEl = document.getElementById("dataUpdated");
        if (updatedEl) updatedEl.textContent = "Updated —";
      });

  // Method island + info tips (TID/ETY pattern)
  function dismissInfoPops() {
    document.querySelectorAll(".srp-pop").forEach((p) => p.remove());
  }
  function openMethod() {
    const layer = document.getElementById("methodLayer");
    const island = document.getElementById("methodIsland");
    const btn = document.getElementById("methodInfoBtn");
    if (!layer || !island) return;
    layer.hidden = false;
    layer.setAttribute("aria-hidden", "false");
    layer.classList.add("is-open");
    if (btn) btn.setAttribute("aria-expanded", "true");
    const w = Math.min(420, window.innerWidth - 24);
    const h = Math.min(520, window.innerHeight - 48);
    island.style.width = w + "px";
    island.style.maxHeight = h + "px";
    island.style.left = Math.max(12, (window.innerWidth - w) / 2) + "px";
    island.style.top = Math.max(24, (window.innerHeight - h) / 2) + "px";
    requestAnimationFrame(() => island.classList.add("is-settled"));
  }
  function closeMethod() {
    const layer = document.getElementById("methodLayer");
    const island = document.getElementById("methodIsland");
    const btn = document.getElementById("methodInfoBtn");
    if (!layer) return;
    layer.classList.remove("is-open");
    layer.hidden = true;
    layer.setAttribute("aria-hidden", "true");
    if (island) island.classList.remove("is-settled");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }
  function wireChrome() {
    const methodBtn = document.getElementById("methodInfoBtn");
    if (methodBtn) methodBtn.addEventListener("click", () => {
      const layer = document.getElementById("methodLayer");
      if (layer && layer.classList.contains("is-open")) closeMethod();
      else openMethod();
    });
    const closeBtn = document.getElementById("methodIslandClose");
    if (closeBtn) closeBtn.addEventListener("click", closeMethod);
    const backdrop = document.getElementById("methodLayerBackdrop");
    if (backdrop) backdrop.addEventListener("click", closeMethod);
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      if (document.querySelector(".srp-pop")) {
        dismissInfoPops();
        return;
      }
      const drawer = document.getElementById("dancerDrawer");
      if (drawer && !drawer.hidden) {
        closeDancerDrawer();
        return;
      }
      closeMethod();
    });
    document.querySelectorAll(".info-tip").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        dismissInfoPops();
        const pop = document.createElement("div");
        pop.className = "srp-pop is-open";
        pop.textContent = btn.getAttribute("data-tip") || "";
        document.body.appendChild(pop);
        const r = btn.getBoundingClientRect();
        pop.style.left = Math.min(window.innerWidth - 280, r.left) + "px";
        pop.style.top = r.bottom + 8 + "px";
        const dismiss = () => {
          pop.remove();
          document.removeEventListener("click", dismiss);
        };
        setTimeout(() => document.addEventListener("click", dismiss), 0);
      });
    });
    if (window.WsdcSelect) {
      WsdcSelect.enhanceAll(document.querySelector(".srp-filters"));
    }
  }
  wireChrome();
})();
