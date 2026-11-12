#!/usr/bin/env python3
"""Build simplified OSM city polygons for Event Trends city drill-in.

Reads unique (city, country, state) from static/data/event_growth.json,
fetches admin polygons from Nominatim (1 req/s), writes
static/data/geo/cities.geojson.

Resume-safe: keeps scripts/.cache/city_boundaries_raw.json between runs.
"""

from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROWTH = ROOT / "static" / "data" / "event_growth.json"
OUT = ROOT / "static" / "data" / "geo" / "cities.geojson"
CACHE = ROOT / "scripts" / ".cache" / "city_boundaries_raw.json"
USER_AGENT = "WSDC-Analytics/1.0 (event-trends city boundaries; contact via github.com/wsdc-analytics)"
# Degrees; keeps Austin ~11KB while preserving recognisable shape.
POLYGON_THRESHOLD = 0.005
REQUEST_GAP_S = 1.15
MAX_RETRIES = 3


def city_key(city: str, country: str, state: str | None) -> str:
    if country == "United States" and state:
        return f"{city}|{country}|{state}"
    return f"{city}|{country}"


def unique_cities(editions: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for e in editions:
        city = (e.get("city") or "").strip()
        country = (e.get("country") or "").strip()
        if not city or not country:
            continue
        state = (e.get("state") or "").strip() or None
        if country != "United States":
            state = None
        key = city_key(city, country, state)
        if key in seen:
            continue
        lat = e.get("city_lat")
        lon = e.get("city_lon")
        if lat is None:
            lat = e.get("lat")
        if lon is None:
            lon = e.get("lon")
        seen[key] = {
            "id": key,
            "name": city,
            "country": country,
            "state": state,
            "lat": lat,
            "lon": lon,
        }
    return sorted(seen.values(), key=lambda r: (r["country"], r["state"] or "", r["name"]))


def load_cache() -> dict:
    if not CACHE.exists():
        return {}
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def nominatim_search(params: dict) -> list[dict]:
    qs = urllib.parse.urlencode(params)
    url = f"https://nominatim.openstreetmap.org/search?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            last_err = err
            time.sleep(REQUEST_GAP_S * (attempt + 1))
    if last_err:
        raise last_err
    return []


def point_in_ring(lon: float, lat: float, ring: list) -> bool:
    # Ray casting; ring is [[lon,lat], ...]
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = float(ring[i][0]), float(ring[i][1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def geom_contains(geom: dict, lon: float, lat: float) -> bool:
    t = geom.get("type")
    coords = geom.get("coordinates") or []
    if t == "Polygon":
        return bool(coords) and point_in_ring(lon, lat, coords[0])
    if t == "MultiPolygon":
        for poly in coords:
            if poly and point_in_ring(lon, lat, poly[0]):
                return True
    return False


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def centroid_approx(geom: dict) -> tuple[float, float] | None:
    pts: list[tuple[float, float]] = []

    def walk(ring: list) -> None:
        for p in ring[:-1] if len(ring) > 1 else ring:
            pts.append((float(p[0]), float(p[1])))

    t = geom.get("type")
    coords = geom.get("coordinates") or []
    if t == "Polygon":
        if coords:
            walk(coords[0])
    elif t == "MultiPolygon":
        for poly in coords:
            if poly:
                walk(poly[0])
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def score_hit(hit: dict, city: dict) -> float:
    geom = hit.get("geojson")
    if not geom or geom.get("type") not in ("Polygon", "MultiPolygon"):
        return -1e9
    lat, lon = city.get("lat"), city.get("lon")
    score = 0.0
    cls = hit.get("class") or ""
    typ = hit.get("type") or ""
    if cls == "boundary" and typ == "administrative":
        score += 50
    elif cls == "place" and typ in ("city", "town", "municipality"):
        score += 40
    elif cls == "place":
        score += 20
    # Prefer larger importance
    try:
        score += 10 * float(hit.get("importance") or 0)
    except (TypeError, ValueError):
        pass
    if lat is not None and lon is not None:
        if geom_contains(geom, float(lon), float(lat)):
            score += 100
        else:
            c = centroid_approx(geom)
            if c:
                dist = haversine_km(float(lon), float(lat), c[0], c[1])
                score += max(0, 40 - dist)  # penalise far centroids
                if dist > 80:
                    score -= 80
    return score


# Free-form Nominatim queries for names that don't match OSM admin labels.
QUERY_ALIASES: dict[str, list[str]] = {
    "Gothenburg|Sweden": ["Göteborg, Sweden", "Gothenburg, Sweden"],
    "Glasgow|United Kingdom": [
        "Glasgow City, Scotland",
        "City of Glasgow, Scotland",
        "Glasgow, Scotland, United Kingdom",
    ],
    "Wailea|United States|Hawaii": ["Wailea, Maui, Hawaii, USA", "Wailea-Makena, Hawaii"],
    # Coords sit in Wisconsin even when state on the row is Illinois.
    "Lake Geneva|United States|Illinois": [
        "Lake Geneva, Wisconsin, USA",
        "City of Lake Geneva, Wisconsin",
    ],
    # Event label points at Reno; venue city is South Lake Tahoe, CA.
    "South Lake Tahoe (near Reno)|United States|Nevada": [
        "South Lake Tahoe, California, USA",
        "City of South Lake Tahoe, California",
    ],
    # Wine-region label — prefer a nearby LGA over the natural "valley" feature.
    "Hunter Valley|Australia": [
        "Cessnock, New South Wales, Australia",
        "Singleton, New South Wales, Australia",
    ],
}


def query_variants(city: dict) -> list[dict]:
    name, country, state = city["name"], city["country"], city.get("state")
    base = {
        "format": "json",
        "polygon_geojson": 1,
        "polygon_threshold": POLYGON_THRESHOLD,
        "limit": 5,
        "addressdetails": 1,
    }
    variants: list[dict] = []
    for q in QUERY_ALIASES.get(city["id"], []):
        variants.append({**base, "q": q})
    if country == "United States" and state:
        variants.append({**base, "city": name, "state": state, "country": country})
        variants.append({**base, "q": f"{name}, {state}, USA"})
    else:
        variants.append({**base, "city": name, "country": country})
        variants.append({**base, "q": f"{name}, {country}"})
    return variants


def fetch_best(city: dict) -> dict | None:
    best = None
    best_score = -1e9
    for params in query_variants(city):
        hits = nominatim_search(params)
        time.sleep(REQUEST_GAP_S)
        for hit in hits:
            s = score_hit(hit, city)
            if s > best_score:
                best_score = s
                best = hit
        # Good enough: admin poly containing the city pin
        if best is not None and best_score >= 140:
            break
    # Reject weak hits (e.g. valley / park named like a city).
    if best is None or best_score < 50:
        return None
    return {
        "display_name": best.get("display_name"),
        "osm_type": best.get("osm_type"),
        "osm_id": best.get("osm_id"),
        "class": best.get("class"),
        "type": best.get("type"),
        "importance": best.get("importance"),
        "score": best_score,
        "geojson": best.get("geojson"),
    }


def main() -> int:
    data = json.loads(GROWTH.read_text(encoding="utf-8"))
    cities = unique_cities(data.get("editions") or [])
    cache = load_cache()

    def needs_fetch(city: dict) -> bool:
        row = cache.get(city["id"])
        if not row or not row.get("geojson"):
            return True
        # Re-pull alias cities and weak hits after scoring/query improvements.
        if city["id"] in QUERY_ALIASES:
            return True
        try:
            if float(row.get("score") or 0) < 50:
                return True
        except (TypeError, ValueError):
            return True
        return False

    missing = [c for c in cities if needs_fetch(c)]
    print(f"cities={len(cities)} cached_ok={len(cities) - len(missing)} to_fetch={len(missing)}")

    for i, city in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {city['id']} ...", flush=True)
        try:
            hit = fetch_best(city)
        except Exception as err:  # noqa: BLE001 — keep going; resume later
            print(f"  ERROR {err}")
            continue
        if not hit:
            print("  MISS")
            cache[city["id"]] = {"error": "no_polygon", **{k: city[k] for k in ("name", "country", "state")}}
        else:
            print(
                f"  ok score={hit['score']:.1f} {hit.get('class')}/{hit.get('type')} "
                f"{(hit.get('display_name') or '')[:60]}"
            )
            cache[city["id"]] = {**{k: city[k] for k in ("name", "country", "state", "lat", "lon")}, **hit}
        save_cache(cache)

    features = []
    misses = []
    for city in cities:
        row = cache.get(city["id"]) or {}
        geom = row.get("geojson")
        if not geom:
            misses.append(city["id"])
            continue
        features.append(
            {
                "type": "Feature",
                "id": city["id"],
                "properties": {
                    "id": city["id"],
                    "name": city["name"],
                    "country": city["country"],
                    "state": city.get("state"),
                    "osm_type": row.get("osm_type"),
                    "osm_id": row.get("osm_id"),
                    "source": "nominatim",
                },
                "geometry": geom,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fc = {
        "type": "FeatureCollection",
        "name": "wsdc_event_growth_cities",
        "features": features,
    }
    OUT.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT} features={len(features)} misses={len(misses)} size_kb={kb:.1f}")
    if misses:
        print("misses:", ", ".join(misses[:30]), ("..." if len(misses) > 30 else ""))
    return 0 if features else 1


if __name__ == "__main__":
    raise SystemExit(main())
