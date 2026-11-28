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

console.log("eg_dynamics smoke OK", {
  worldYears: world.length,
  continents: bd.rows.length,
  avgEntries: Math.round(avg.entries),
  concurrentSample: conc.length,
  flags: flags.map(function (f) { return f.id; })
});
