#!/usr/bin/env node
/**
 * Unit tests for static/js/eg_venue_helpers.js
 * Run: node scripts/test_eg_venue_helpers.mjs
 */
import { createRequire } from "module";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const EG = require(join(root, "static/js/eg_venue_helpers.js"));

let failed = 0;

function assert(cond, label) {
  if (!cond) {
    failed += 1;
    console.error("FAIL", label);
  } else {
    console.log("ok  ", label);
  }
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    failed += 1;
    console.error(`FAIL ${label}\n  got:  ${JSON.stringify(actual)}\n  want: ${JSON.stringify(expected)}`);
  } else {
    console.log("ok  ", label);
  }
}

// --- shortHotelName ---
assertEqual(
  EG.shortHotelName("Embassy Suites by Hilton Round Rock"),
  "Embassy Suites Round Rock",
  "strip by Hilton"
);
assertEqual(
  EG.shortHotelName("DoubleTree by Hilton Austin"),
  "DoubleTree Austin",
  "DoubleTree Austin"
);
assertEqual(
  EG.shortHotelName("Hotel InterContinental Budapest *****"),
  "InterContinental Budapest",
  "stars + leading Hotel"
);
assertEqual(
  EG.shortHotelName("Alte Kongresshalle, Munich"),
  "Alte Kongresshalle",
  "trailing city"
);
assertEqual(
  EG.shortHotelName("Grand Hotel Barone di Sassj"),
  "Grand Hotel Barone di Sassj",
  "keep Grand Hotel"
);
assertEqual(
  EG.shortHotelName("Crowne Plaza Chicago Ohare Hotel & Conf Ctr"),
  "Crowne Plaza Chicago Ohare",
  "conf ctr"
);
assertEqual(
  EG.shortHotelName("The Florida Hotel & Conference Center"),
  "The Florida Hotel",
  "keep Hotel when remainder would be The Florida"
);
assertEqual(
  EG.shortHotelName("The Florida Hotel"),
  "The Florida Hotel",
  "keep The Florida Hotel"
);
assertEqual(EG.shortHotelName(""), null, "empty → null");
assertEqual(EG.shortHotelName(null), null, "null → null");

// --- coord key ---
assertEqual(EG.venueCoordKey(45.53799, 9.23007), "45.538,9.2301", "coord round 4dp");

// --- cluster: same cell ---
const milan = EG.clusterEditionsByVenue([
  { event_id: 1, hotel: "Grand Hotel Barone di Sassj", lat: 45.53799, lon: 9.23007 },
  { event_id: 2, hotel: "Grand Hotel Barone di Sassj", lat: 45.53799, lon: 9.23007 }
]);
assertEqual(milan.length, 1, "Milan same coords → 1 cluster");
assertEqual(milan[0].editions.length, 2, "Milan cluster has 2 editions");

// --- cluster: same hotel, slightly different coords (~40 m) ---
const near = EG.clusterEditionsByVenue([
  { event_id: 1, hotel: "DoubleTree by Hilton Austin", lat: 30.3263, lon: -97.7046 },
  { event_id: 2, hotel: "DoubleTree by Hilton Austin", lat: 30.3266, lon: -97.7049 }
]);
assertEqual(near.length, 1, "same hotel within merge km → 1 cluster");

// --- cluster: different hotels far apart ---
const far = EG.clusterEditionsByVenue([
  { event_id: 1, hotel: "Embassy Suites Round Rock", lat: 30.57, lon: -97.687 },
  { event_id: 2, hotel: "DoubleTree Austin", lat: 30.326, lon: -97.705 }
]);
assertEqual(far.length, 2, "different venues → 2 clusters");

// --- mixed pin status ---
assertEqual(EG.clusterPinStatus(["declining"]), "declining", "single status");
assertEqual(EG.clusterPinStatus(["declining", "new"]), "stable", "mixed → neutral");
assertEqual(EG.clusterPinStatus(["growing", "growing"]), "growing", "uniform growing");

if (failed) {
  console.error(`\n${failed} failed`);
  process.exit(1);
}
console.log("\nOK");
