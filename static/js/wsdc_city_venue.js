/**
 * Shared city-boundary + venue helpers for Event Trends and Events Calendar.
 * Browser: window.WsdcCityVenue. Node: module.exports.
 */
(function (root, factory) {
  var api = factory(root);
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.WsdcCityVenue = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) { // v=20261114b
  "use strict";

  var CITY_OUTLINE_MIN_RADIUS_DEG = 0.16;
  var CITY_OUTLINE_PAD = 1.45;
  var CITY_OUTLINE_STEPS = 64;

  function shortHotelName(raw) {
    if (root && root.EGVenue && typeof root.EGVenue.shortHotelName === "function") {
      return root.EGVenue.shortHotelName(raw);
    }
    if (!raw) return null;
    var s = String(raw).replace(/\s+/g, " ").trim();
    return s || null;
  }

  function venueMapsUrl(e) {
    if (!e) return null;
    if (e.lat != null && e.lon != null && isFinite(Number(e.lat)) && isFinite(Number(e.lon))) {
      return "https://www.google.com/maps/search/?api=1&query=" +
        encodeURIComponent(Number(e.lat) + "," + Number(e.lon));
    }
    var q = [e.hotel, e.address, e.city, e.state, e.country].filter(Boolean).join(", ");
    if (!q) return null;
    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(q);
  }

  /**
   * @param {object} e edition-like object
   * @param {object} [opts]
   * @param {function(string):string} [opts.esc] HTML escape
   * @param {string} [opts.venueLabel] default "Venue:"
   * @param {string} [opts.mapLabel] default "Map"
   * @param {string} [opts.wrapClass] default "tt-venue-top"
   */
  function venueLineHtml(e, opts) {
    opts = opts || {};
    if (!e) return "";
    var esc = typeof opts.esc === "function" ? opts.esc : function (s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    };
    var short = shortHotelName(e.hotel);
    var url = venueMapsUrl(e);
    if (!short && !url) return "";
    var venueLabel = opts.venueLabel != null ? opts.venueLabel : "Venue:";
    var mapLabel = opts.mapLabel != null ? opts.mapLabel : "Map";
    var wrapClass = opts.wrapClass || "tt-venue-top";
    var bits = [];
    if (short) {
      bits.push(
        '<span class="tt-venue-lbl">' + esc(venueLabel) + "</span> " +
        '<span class="tt-venue-name" title="' + esc(e.hotel || short) + '">' +
          esc(short) + "</span>"
      );
    }
    if (url) {
      bits.push(
        '<a class="tt-venue-map" href="' + esc(url) +
          '" target="_blank" rel="noopener noreferrer">' + esc(mapLabel) + "</a>"
      );
    }
    return '<div class="' + esc(wrapClass) + '">' +
      bits.join('<span class="tt-venue-sep" aria-hidden="true"> · </span>') +
      "</div>";
  }

  function cityBoundaryLookupKey(cityName, country, regionState) {
    if (!cityName || !country) return null;
    if (country === "United States" && regionState) {
      return cityName + "|" + country + "|" + regionState;
    }
    return cityName + "|" + country;
  }

  function findCityBoundaryFeature(citiesFc, cityName, country, regionState) {
    var feats = citiesFc && citiesFc.features;
    if (!feats || !feats.length || !cityName) return null;
    var id = cityBoundaryLookupKey(cityName, country, regionState);
    var i;
    var f;
    if (id) {
      for (i = 0; i < feats.length; i += 1) {
        f = feats[i];
        if (f && f.properties && f.properties.id === id && f.geometry) return f;
      }
    }
    for (i = 0; i < feats.length; i += 1) {
      f = feats[i];
      if (!f || !f.properties || !f.geometry) continue;
      if (f.properties.name !== cityName) continue;
      if (f.properties.country !== country) continue;
      if (country === "United States" && regionState && f.properties.state &&
          f.properties.state !== regionState) continue;
      return f;
    }
    return null;
  }

  function cityCentroidLngLat(editions) {
    var lat = null;
    var lon = null;
    var n = 0;
    (editions || []).forEach(function (e) {
      var la = e.city_lat != null ? e.city_lat : null;
      var lo = e.city_lon != null ? e.city_lon : null;
      if (la == null || lo == null) return;
      lat = (lat == null ? 0 : lat) + la;
      lon = (lon == null ? 0 : lon) + lo;
      n += 1;
    });
    if (!n) return null;
    return [lon / n, lat / n];
  }

  function circlePolygonLngLat(lng, lat, radiusDeg, steps) {
    var ring = [];
    var n = Math.max(16, steps | 0);
    var cosLat = Math.max(0.2, Math.cos((lat * Math.PI) / 180));
    var i;
    for (i = 0; i <= n; i += 1) {
      var t = (i / n) * Math.PI * 2;
      ring.push([
        lng + (radiusDeg / cosLat) * Math.cos(t),
        lat + radiusDeg * Math.sin(t)
      ]);
    }
    return { type: "Polygon", coordinates: [ring] };
  }

  /**
   * Build city outline Feature (real admin poly, or optional soft disc).
   * @param {object} opts
   * @param {object} opts.citiesFc
   * @param {string} opts.city
   * @param {string} opts.country
   * @param {string} [opts.state]
   * @param {object[]} [opts.editions]
   * @param {object[]} [opts.pts] GeoJSON Point features (lng/lat in geometry.coordinates)
   * @param {string} [opts.id]
   * @param {boolean} [opts.allowSoftDisc=true] When false, return null if no admin poly
   *   (Calendar uses this so interim paint never shows a fake circle).
   */
  function cityVenueOutlineFeature(opts) {
    opts = opts || {};
    var city = opts.city;
    var country = opts.country;
    var regionState = opts.state || null;
    var editions = opts.editions || [];
    var pts = opts.pts || [];
    var allowSoftDisc = opts.allowSoftDisc !== false;
    var real = findCityBoundaryFeature(opts.citiesFc, city, country, regionState);
    var outlineId = opts.id || "city-outline";
    if (real && real.geometry) {
      return {
        type: "Feature",
        id: outlineId,
        properties: {
          id: outlineId,
          fillColor: "#9aa7b5",
          fillOpacity: 0.42,
          realBoundary: true
        },
        geometry: real.geometry
      };
    }
    if (!allowSoftDisc) return null;
    var centroid = cityCentroidLngLat(editions);
    var coords = pts.map(function (f) {
      return f && f.geometry && f.geometry.coordinates;
    }).filter(Boolean);
    if (!centroid && coords.length) {
      var sx = 0;
      var sy = 0;
      coords.forEach(function (c) { sx += c[0]; sy += c[1]; });
      centroid = [sx / coords.length, sy / coords.length];
    }
    if (!centroid) return null;
    var maxDist = 0;
    coords.forEach(function (c) {
      var dx = (c[0] - centroid[0]) * Math.max(0.2, Math.cos((centroid[1] * Math.PI) / 180));
      var dy = c[1] - centroid[1];
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d > maxDist) maxDist = d;
    });
    var radiusDeg = Math.max(CITY_OUTLINE_MIN_RADIUS_DEG, maxDist * CITY_OUTLINE_PAD);
    return {
      type: "Feature",
      id: outlineId,
      properties: {
        id: outlineId,
        fillColor: "#9aa7b5",
        fillOpacity: 0.42,
        realBoundary: false
      },
      geometry: circlePolygonLngLat(
        centroid[0],
        centroid[1],
        radiusDeg,
        CITY_OUTLINE_STEPS
      )
    };
  }

  /**
   * Prefer exact event_id+year; else closest start within same event_id.
   */
  function findGrowthEdition(editions, eventId, year, startDate) {
    if (eventId == null || eventId === "") return null;
    var eid = Number(eventId);
    var list = (editions || []).filter(function (e) {
      return Number(e.event_id) === eid;
    });
    if (!list.length) return null;
    var y = year != null && year !== "" ? Number(year) : NaN;
    if (!Number.isNaN(y)) {
      var sameYear = list.filter(function (e) { return Number(e.year) === y; });
      if (sameYear.length === 1) return sameYear[0];
      if (sameYear.length > 1) list = sameYear;
    }
    var target = String(startDate || "").slice(0, 10);
    if (!target) return list[0];
    var targetNum = Number(target.replace(/-/g, ""));
    if (!isFinite(targetNum)) return list[0];
    var best = list[0];
    var bestDist = Infinity;
    list.forEach(function (e) {
      var sd = String(e.start || e.start_date || "").slice(0, 10);
      if (!sd) return;
      var n = Number(sd.replace(/-/g, ""));
      if (!isFinite(n)) return;
      var dist = Math.abs(n - targetNum);
      if (dist < bestDist) {
        bestDist = dist;
        best = e;
      }
    });
    return best;
  }

  /**
   * Pin lat/lon: venue coords from growth edition, else city centroid, else calendar event.
   * @returns {{ lat: number, lon: number, source: string }|null}
   */
  function resolvePinLatLon(edition, calendarEvent) {
    var ed = edition || null;
    var cal = calendarEvent || null;
    if (ed && ed.lat != null && ed.lon != null &&
        isFinite(Number(ed.lat)) && isFinite(Number(ed.lon))) {
      return { lat: Number(ed.lat), lon: Number(ed.lon), source: "venue" };
    }
    if (ed && ed.city_lat != null && ed.city_lon != null &&
        isFinite(Number(ed.city_lat)) && isFinite(Number(ed.city_lon))) {
      return { lat: Number(ed.city_lat), lon: Number(ed.city_lon), source: "city" };
    }
    if (cal && cal.lat != null && cal.lon != null &&
        isFinite(Number(cal.lat)) && isFinite(Number(cal.lon))) {
      return { lat: Number(cal.lat), lon: Number(cal.lon), source: "calendar" };
    }
    return null;
  }

  /**
   * Merge calendar event + growth edition for venue line / pin display.
   */
  function mergeVenueContext(calendarEvent, edition) {
    var cal = calendarEvent || {};
    var ed = edition || {};
    var pin = resolvePinLatLon(ed, cal);
    return {
      hotel: ed.hotel || null,
      address: ed.address || null,
      city: cal.city || ed.city || null,
      state: cal.state || ed.state || null,
      country: cal.country || ed.country || null,
      lat: pin ? pin.lat : null,
      lon: pin ? pin.lon : null,
      city_lat: ed.city_lat != null ? ed.city_lat : (cal.lat != null ? cal.lat : null),
      city_lon: ed.city_lon != null ? ed.city_lon : (cal.lon != null ? cal.lon : null),
      pinSource: pin ? pin.source : null,
      year: cal.year != null ? cal.year : ed.year,
      event_id: cal.event_id != null ? cal.event_id : ed.event_id,
      name: cal.name || ed.name || null
    };
  }

  function hasRealCityBoundary(citiesFc, city, country, state) {
    return !!findCityBoundaryFeature(citiesFc, city, country, state);
  }

  return {
    CITY_OUTLINE_MIN_RADIUS_DEG: CITY_OUTLINE_MIN_RADIUS_DEG,
    CITY_OUTLINE_PAD: CITY_OUTLINE_PAD,
    CITY_OUTLINE_STEPS: CITY_OUTLINE_STEPS,
    shortHotelName: shortHotelName,
    venueMapsUrl: venueMapsUrl,
    venueLineHtml: venueLineHtml,
    cityBoundaryLookupKey: cityBoundaryLookupKey,
    findCityBoundaryFeature: findCityBoundaryFeature,
    cityCentroidLngLat: cityCentroidLngLat,
    circlePolygonLngLat: circlePolygonLngLat,
    cityVenueOutlineFeature: cityVenueOutlineFeature,
    findGrowthEdition: findGrowthEdition,
    resolvePinLatLon: resolvePinLatLon,
    mergeVenueContext: mergeVenueContext,
    hasRealCityBoundary: hasRealCityBoundary
  };
});
