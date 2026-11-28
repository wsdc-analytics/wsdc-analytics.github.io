#!/usr/bin/env node
"use strict";

var path = require("path");
var fs = require("fs");
var assert = require("assert");
var EG = require("../static/js/eg_dynamics.js");

var root = path.join(__dirname, "..");
var growth = JSON.parse(
  fs.readFileSync(path.join(root, "static/data/event_growth.json"), "utf8")
);
var tiers = JSON.parse(
  fs.readFileSync(path.join(root, "static/data/event_tiers_by_year.json"), "utf8")
);

var editions = growth.editions;
var through = growth.data_through;
var range = { from: 2019, to: 2025 };

var world = EG.seriesByYear(editions, {}, range, through);
assert.strictEqual(world.length, 7, "world series years");
assert.ok(world.every(function (p) { return !p.partial; }), "full years only in range");

var avg = EG.periodAverages(world, { fullYearsOnly: true });
assert.ok(avg.entries > 0 && avg.events > 0 && avg.entriesPerEvent > 0);

var bd = EG.breakdown(editions, {}, "continent", range, through, 5);
var sumTop = bd.top.reduce(function (s, r) { return s + r.sumEntries; }, 0);
var sumOther = bd.other ? bd.other.sumEntries : 0;
var sumAll = bd.rows.reduce(function (s, r) { return s + r.sumEntries; }, 0);
assert.strictEqual(sumTop + sumOther, sumAll, "top+other == all");

var worldEntries = world.reduce(function (s, p) { return s + p.entries; }, 0);
assert.strictEqual(sumAll, worldEntries, "continent sum == world");

var partialRange = { from: 2024, to: 2026 };
var withPartial = EG.seriesByYear(editions, {}, partialRange, through);
assert.ok(withPartial.some(function (p) { return p.year === 2026 && p.partial; }));
var avgEx = EG.periodAverages(withPartial, { fullYearsOnly: true });
assert.strictEqual(avgEx.nYears, 2, "2026 excluded from averages");

var europe = EG.filterEditions(editions, { continent: "Europe" }, { from: 2024, to: 2024 });
assert.ok(europe.length > 0, "europe 2024");
var sample = europe[0];
var tiersSample = EG.findTiersRow(
  tiers.editions, sample.event_id, sample.year, sample.month
);
assert.ok(tiersSample, "tiers row for sample");
var conc = EG.concurrentEditions(
  Object.assign({}, sample, { end: tiersSample.end }),
  editions.map(function (e) {
    var tr = EG.findTiersRow(tiers.editions, e.event_id, e.year, e.month);
    return Object.assign({}, e, { end: tr ? tr.end : e.start });
  })
);
assert.ok(Array.isArray(conc), "concurrent returns array");

var seriesEvt = EG.eventEditionSeries(editions, sample.event_id, range, through);
assert.ok(seriesEvt.editions.length >= 1);

var prev = seriesEvt.editions.length > 1
  ? editions.find(function (e) {
      return Number(e.event_id) === Number(sample.event_id) &&
        Number(e.year) === Number(sample.prev && sample.prev.year);
    })
  : null;
var flags = EG.editionFlags(
  sample,
  prev,
  tiersSample,
  prev ? EG.findTiersRow(tiers.editions, prev.event_id, prev.year, prev.month) : null
);
assert.ok(Array.isArray(flags));

// clampPeriod: invert, out-of-range, nulls
var years = growth.years;
var c1 = EG.clampPeriod(2030, 2010, years);
assert.ok(c1.from <= c1.to, "clamp from<=to");
assert.ok(c1.from >= years[0] && c1.to <= years[years.length - 1], "clamp in years");
var c2 = EG.clampPeriod(null, null, years);
assert.deepStrictEqual(c2, { from: years[0], to: years[years.length - 1] });

// concurrent: known Europe weekend with overlaps
var allWithEnds = editions.map(function (e) {
  var tr = EG.findTiersRow(tiers.editions, e.event_id, e.year, e.month);
  return Object.assign({}, e, { end: tr ? tr.end : e.start });
});
var sea = allWithEnds.find(function (e) {
  return e.name && e.name.indexOf("Sea Sun and Swing") === 0 && e.year === 2024;
});
assert.ok(sea, "Sea Sun and Swing 2024 present");
var seaConc = EG.concurrentEditions(sea, allWithEnds);
assert.ok(seaConc.length >= 1, "Sea Sun has concurrent on continent");
assert.ok(seaConc.every(function (c) {
  return c.continent === sea.continent;
}), "concurrent same continent");

// editionFlags: synthetic venue move + hotel change
var fakePrev = {
  lat: 48.85, lon: 2.35, hotel: "Old Hotel", start: "2023-06-01"
};
var fakeCur = {
  lat: 45.46, lon: 9.19, hotel: "New Hotel", start: "2024-07-15",
  gap_flag: "after_1yr_break", continent: "Europe"
};
var synFlags = EG.editionFlags(fakeCur, fakePrev, null, null);
var ids = synFlags.map(function (f) { return f.id; });
assert.ok(ids.indexOf("venue_move") >= 0, "venue_move flag");
assert.ok(ids.indexOf("date_shift") >= 0, "date_shift flag");
assert.ok(ids.indexOf("gap") >= 0, "gap flag");

// Missing years gap: zero-event years are null, not 0.
var gapSeries = EG.seriesByYear(
  [
    { event_id: 1, year: 2020, competitors: 100, continent: "Asia", country: "Israel" },
    { event_id: 1, year: 2022, competitors: 80, continent: "Asia", country: "Israel" }
  ],
  { country: "Israel" },
  { from: 2020, to: 2022 },
  "2026-11"
);
assert.strictEqual(gapSeries[0].entries, 100);
assert.strictEqual(gapSeries[1].entries, null, "gap year is null");
assert.strictEqual(gapSeries[1].missing, true);
assert.strictEqual(gapSeries[2].entries, 80);
var gapModel = EG.lineChartModel([{
  key: "il",
  label: "Israel",
  color: "#000",
  points: gapSeries,
  avg: null
}], { metric: "entries", years: [2020, 2021, 2022] });
assert.strictEqual(gapModel.lines[0].segs.length, 2, "line breaks across missing year");

var spark = EG.sparklineModel([
  { year: 2019, v: 10 },
  { year: 2020, v: 40 },
  { year: 2021, v: 25 },
  { year: 2022, v: null },
  { year: 2023, v: 5 }
], 72, 22, 3);
assert.ok(spark.path, "spark path");
assert.strictEqual(spark.max, 40);
assert.strictEqual(spark.min, 5);
assert.ok(spark.marks.length >= 2, "min and max marks");
assert.strictEqual(spark.marks.filter(function (m) { return m.kind === "max"; })[0].year, 2020);
assert.strictEqual(spark.marks.filter(function (m) { return m.kind === "min"; })[0].year, 2023);

console.log("eg_dynamics smoke OK", {
  worldYears: world.length,
  continents: bd.rows.length,
  avgEntries: Math.round(avg.entries),
  concurrentSample: seaConc.length,
  clamp: c1,
  flagIds: ids,
  gapSegs: gapModel.lines[0].segs.length
});
