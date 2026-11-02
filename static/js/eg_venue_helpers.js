/**
 * Event Growth Monitor — venue label + co-location clustering helpers.
 * Browser: window.EGVenue. Node: module.exports.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.EGVenue = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var COORD_DECIMALS = 4;
  // Merge pins with the same short hotel name within this distance (km).
  var HOTEL_MERGE_KM = 0.08;

  function shortHotelName(raw) {
    if (!raw) return null;
    var s = String(raw).replace(/\s+/g, " ").trim();
    if (!s) return null;
    s = s.replace(/\*+/g, "").trim();
    s = s.replace(/\s*\([^)]*\)\s*/g, " ").trim();
    s = s.replace(/\s*[&/]\s*conf\.?\s*ctr\b/gi, "");
    s = s.replace(/\s*(&|and)\s*conference\s*cent(er|re)\b/gi, "");
    s = s.replace(/\s*(&|and)\s*convention\s*cent(er|re)\b/gi, "");
    s = s.replace(/\s*hotel\s*(&|and)\s*conference\s*cent(er|re)\b/gi, "");
    s = s.replace(/\s*resort\s*(&|and)\s*spa\b/gi, "");
    s = s.replace(/\s*(&|and)\s*spa\b/gi, "");
    s = s.replace(/\s+by\s+(hilton|marriott|marriot|hyatt|wyndham|ihg|radisson)\b/gi, "");
    s = s.replace(/\bcurio\s+collection\b/gi, "");
    s = s.replace(/\binternational\s+airport\b/gi, "Airport");
    s = s.replace(/\s*,\s*[^,]{2,40}\s*$/g, function (tail) {
      return /^,\s*[A-Za-zÀ-ž .'-]{2,40}$/.test(tail) ? "" : tail;
    });
    // Strip leading/trailing "Hotel" only when the remainder stays a real name
    // ("Grand Hotel …" kept; "The Florida Hotel" must not become "The Florida").
    s = s.replace(/^hotels?\s+/i, "");
    var strippedHotel = s.replace(/\s+hotels?$/i, "").replace(/\s+/g, " ").trim();
    if (
      strippedHotel &&
      strippedHotel.length >= 12 &&
      !/^the\s+\w+$/i.test(strippedHotel)
    ) {
      s = strippedHotel;
    }
    s = s.replace(/\s+/g, " ").trim();
    if (s.length > 28) s = s.replace(/^the\s+/i, "");
    if (s.length > 32) {
      var cut = s.slice(0, 32);
      var sp = cut.lastIndexOf(" ");
      s = (sp > 16 ? cut.slice(0, sp) : cut).replace(/[,\s-]+$/, "") + "…";
    }
    return s || null;
  }

  function venueCoordKey(lat, lon) {
    var f = Math.pow(10, COORD_DECIMALS);
    return (Math.round(Number(lat) * f) / f) + "," + (Math.round(Number(lon) * f) / f);
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    var r = 6371;
    var p1 = (lat1 * Math.PI) / 180;
    var p2 = (lat2 * Math.PI) / 180;
    var dp = ((lat2 - lat1) * Math.PI) / 180;
    var dl = ((lon2 - lon1) * Math.PI) / 180;
    var a =
      Math.sin(dp / 2) * Math.sin(dp / 2) +
      Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return 2 * r * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  /**
   * Group editions that share a venue cell (~11 m) or the same short hotel
   * name within HOTEL_MERGE_KM.
   * @returns {{ key: string, editions: object[], lat: number, lon: number }[]}
   */
  function clusterEditionsByVenue(editions) {
    var clusters = [];
    (editions || []).forEach(function (e) {
      if (!e || e.lat == null || e.lon == null) return;
      if (!isFinite(Number(e.lat)) || !isFinite(Number(e.lon))) return;
      var short = (shortHotelName(e.hotel) || "").toLowerCase();
      var cell = venueCoordKey(e.lat, e.lon);
      var hit = null;
      for (var i = 0; i < clusters.length; i++) {
        var c = clusters[i];
        var dist = haversineKm(e.lat, e.lon, c.lat, c.lon);
        var sameCell = cell === c.cell;
        var sameHotel = !!(short && c.shortHotel && short === c.shortHotel);
        if (sameCell || (sameHotel && dist <= HOTEL_MERGE_KM)) {
          hit = c;
          break;
        }
      }
      if (!hit) {
        hit = {
          cell: cell,
          shortHotel: short,
          editions: [],
          latSum: 0,
          lonSum: 0,
          lat: Number(e.lat),
          lon: Number(e.lon)
        };
        clusters.push(hit);
      }
      hit.editions.push(e);
      hit.latSum += Number(e.lat);
      hit.lonSum += Number(e.lon);
      hit.lat = hit.latSum / hit.editions.length;
      hit.lon = hit.lonSum / hit.editions.length;
      if (short && !hit.shortHotel) hit.shortHotel = short;
    });

    return clusters.map(function (c, i) {
      return {
        key: "v" + i + ":" + c.cell + (c.shortHotel ? ":" + c.shortHotel : ""),
        editions: c.editions.slice(),
        lat: c.lat,
        lon: c.lon
      };
    });
  }

  function clusterPinStatus(statuses) {
    var seen = {};
    (statuses || []).forEach(function (s) {
      if (s) seen[s] = true;
    });
    var keys = Object.keys(seen);
    if (keys.length === 1) return keys[0];
    // Mixed / empty → neutral pin; individual chips stay in the stacked tip.
    return "stable";
  }

  return {
    COORD_DECIMALS: COORD_DECIMALS,
    HOTEL_MERGE_KM: HOTEL_MERGE_KM,
    shortHotelName: shortHotelName,
    venueCoordKey: venueCoordKey,
    haversineKm: haversineKm,
    clusterEditionsByVenue: clusterEditionsByVenue,
    clusterPinStatus: clusterPinStatus
  };
});
