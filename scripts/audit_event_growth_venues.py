#!/usr/bin/env python3
"""Audit Event Trends Monitor venue pins against Google Maps (report only).

Registry GPS is typed by organizers per edition, so one hotel often lands in
several places across years (or on a generic city-centre point). This groups
editions by (event_id, hotel), looks the venue up on Google (Places "Find
Place", falling back to the Geocoding API), and writes a review report.
Nothing in static/data is modified — use apply_event_growth_venue_overrides.py
after reviewing proposed_overrides.json.

Outputs (under --out-dir, default output/venue_audit/):
  venue_audit.csv            one row per (event, hotel) with verdict + map links
  proposed_overrides.json    safe candidates only (name_match gate + years_to_fix)
  google_cache.json          raw lookup cache — reruns do not spend quota

Usage:
  GOOGLE_MAPS_API_KEY=... python3 scripts/audit_event_growth_venues.py
  python3 scripts/audit_event_growth_venues.py --env-file ../wsdc-data-pipeline/.env
  python3 scripts/audit_event_growth_venues.py --offline   # cache only, no API calls
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_event_growth_venues import (  # noqa: E402
    haversine_km,
    hotel_match_key,
    usable_hotel_name,
)

REPO = Path(__file__).resolve().parents[1]
DEFAULT_GROWTH = REPO / "static" / "data" / "event_growth.json"
DEFAULT_OUT = REPO / "output" / "venue_audit"

# Registry pins this close to Google count as the same place.
OK_KM = 0.4
# Google hit farther than this from the city point is probably a namesake.
GOOGLE_CITY_MAX_KM = 60.0
# Minimum token overlap before trusting ok / emitting an override.
NAME_MATCH_MIN = 0.5
# Places locationbias circle radius (metres) around the city centroid.
PLACES_BIAS_RADIUS_M = 50_000

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

LookupFn = Callable[["VenueGroup"], Optional[Dict[str, Any]]]


@dataclass
class VenueGroup:
    event_id: int
    event: str
    hotel: str
    city: str
    country: str
    address: str
    city_lat: Optional[float]
    city_lon: Optional[float]
    points: Dict[int, Tuple[float, float]] = field(default_factory=dict)

    @property
    def spread_km(self) -> float:
        pts = list(self.points.values())
        if len(pts) < 2:
            return 0.0
        return max(haversine_km(a[0], a[1], b[0], b[1]) for a in pts for b in pts)

    def query(self) -> str:
        parts = [self.hotel, self.address, self.city, self.country]
        return ", ".join(p for p in parts if p)


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ without overriding set vars."""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        # Allow "KEY = value" (spaces around =) as in some hand-edited .env files.
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def build_groups(editions: List[Dict[str, Any]]) -> List[VenueGroup]:
    groups: Dict[Tuple[int, str], VenueGroup] = {}
    addresses: Dict[Tuple[int, str], Counter] = defaultdict(Counter)
    for ed in editions:
        if ed.get("geo_source") != "wsdc_venue":
            continue
        hotel = usable_hotel_name(ed.get("hotel"))
        if not hotel or ed.get("lat") is None or ed.get("lon") is None:
            continue
        key = (int(ed["event_id"]), hotel_match_key(hotel))
        g = groups.get(key)
        if g is None:
            g = groups[key] = VenueGroup(
                event_id=key[0],
                event=ed.get("name") or "",
                hotel=hotel,
                city=ed.get("city") or "",
                country=ed.get("country") or "",
                address="",
                city_lat=None,
                city_lon=None,
            )
        g.points[int(ed["year"])] = (float(ed["lat"]), float(ed["lon"]))
        # Backfill city centroid from any edition that has it (not only the first).
        if g.city_lat is None and ed.get("city_lat") is not None:
            g.city_lat = ed.get("city_lat")
            g.city_lon = ed.get("city_lon")
        if ed.get("address"):
            addresses[key][ed["address"].strip()] += 1
    for key, g in groups.items():
        if addresses[key]:
            g.address = addresses[key].most_common(1)[0][0]
    return sorted(groups.values(), key=lambda g: (g.country, g.city, g.event, g.hotel))


def _http_json(url: str, params: Dict[str, str]) -> Dict[str, Any]:
    full = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def google_lookup(
    query: str,
    key: str,
    *,
    bias_lat: Optional[float] = None,
    bias_lon: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Places Find Place first (knows hotels by name); Geocoding as fallback."""
    params: Dict[str, str] = {
        "input": query,
        "inputtype": "textquery",
        "fields": "name,formatted_address,geometry,place_id,types",
        "key": key,
    }
    if bias_lat is not None and bias_lon is not None:
        params["locationbias"] = (
            f"circle:{PLACES_BIAS_RADIUS_M}@{float(bias_lat)},{float(bias_lon)}"
        )
    data = _http_json(FIND_PLACE_URL, params)
    status = data.get("status")
    if status == "OK" and data.get("candidates"):
        c = data["candidates"][0]
        loc = c["geometry"]["location"]
        return {
            "api": "places",
            "name": c.get("name", ""),
            "address": c.get("formatted_address", ""),
            "lat": loc["lat"],
            "lon": loc["lng"],
            "place_id": c.get("place_id", ""),
            "types": c.get("types", []),
        }
    if status not in ("OK", "ZERO_RESULTS", "REQUEST_DENIED"):
        raise RuntimeError(f"Places error {status}: {data.get('error_message', '')}")
    data = _http_json(GEOCODE_URL, {"address": query, "key": key})
    status = data.get("status")
    if status == "OK" and data.get("results"):
        r = data["results"][0]
        loc = r["geometry"]["location"]
        return {
            "api": "geocode",
            "name": "",
            "address": r.get("formatted_address", ""),
            "lat": loc["lat"],
            "lon": loc["lng"],
            "place_id": r.get("place_id", ""),
            "types": r.get("types", []),
        }
    if status == "ZERO_RESULTS":
        return None
    raise RuntimeError(f"Geocoding error {status}: {data.get('error_message', '')}")


def name_overlap(a: str, b: str) -> float:
    """Best directional token overlap (generic words ignored).

    Takes max of hotel→Google and Google→hotel so a short Places label like
    ``AZIMUT`` still matches ``Azimut City hotel St.Petersburg``.
    """
    stop = {
        "hotel", "the", "and", "club", "resort", "spa", "&", "at", "by", "de", "la",
        "city", "st", "saint",
    }
    ta = {t for t in re.findall(r"[a-z0-9]+", a.lower()) if t not in stop}
    tb = {t for t in re.findall(r"[a-z0-9]+", b.lower()) if t not in stop}
    if not ta:
        return 0.0
    inter = len(ta & tb)
    forward = inter / len(ta)
    reverse = inter / len(tb) if tb else 0.0
    return max(forward, reverse)


def years_to_fix(dists: Dict[int, float]) -> List[int]:
    """Years whose registry pin is farther than OK_KM from Google."""
    return [y for y, d in sorted(dists.items()) if d > OK_KM]


def normalize_hit(hit: Any) -> Optional[Dict[str, Any]]:
    """Validate a cache entry; return None for missing/corrupt hits."""
    if hit is None:
        return None
    if not isinstance(hit, dict):
        return None
    if hit.get("lat") is None or hit.get("lon") is None:
        return None
    return hit


def classify(g: VenueGroup, hit: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "verdict": "",
        "dist_by_year": {},
        "max_dist_km": None,
        "years_to_fix": [],
        "name_match": None,
        "google_city_km": None,
    }
    hit = normalize_hit(hit)
    if hit is None:
        out["verdict"] = "not_found"
        return out
    glat, glon = float(hit["lat"]), float(hit["lon"])
    dists = {y: haversine_km(p[0], p[1], glat, glon) for y, p in sorted(g.points.items())}
    out["dist_by_year"] = dists
    out["max_dist_km"] = max(dists.values())
    out["years_to_fix"] = years_to_fix(dists)
    out["name_match"] = name_overlap(g.hotel, hit.get("name") or hit.get("address", ""))
    city_km = None
    if g.city_lat is not None and g.city_lon is not None:
        city_km = haversine_km(float(g.city_lat), float(g.city_lon), glat, glon)
    out["google_city_km"] = city_km

    weak_name = out["name_match"] < NAME_MATCH_MIN
    if city_km is not None and city_km > GOOGLE_CITY_MAX_KM:
        out["verdict"] = "check_google_far_from_city"
    elif weak_name and (
        hit.get("api") == "places"
        or hit.get("api") == "geocode"
    ):
        # Places first candidate / geocode address can still be a namesake.
        out["verdict"] = "check_weak_match"
    elif out["max_dist_km"] <= OK_KM:
        out["verdict"] = "ok"
    elif all(d > OK_KM for d in dists.values()):
        out["verdict"] = "fix_all_years"
    else:
        out["verdict"] = "fix_some_years"
    return out


def override_eligible(c: Dict[str, Any]) -> bool:
    """True when proposed_overrides may emit a Google point for years_to_fix."""
    if c.get("verdict") not in ("fix_all_years", "fix_some_years"):
        return False
    if not c.get("years_to_fix"):
        return False
    nm = c.get("name_match")
    if nm is None or nm < NAME_MATCH_MIN:
        return False
    # Require a city centroid so far-from-city namesakes cannot slip through.
    city_km = c.get("google_city_km")
    if city_km is None or city_km > GOOGLE_CITY_MAX_KM:
        return False
    return True


def maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}"


def cache_key(g: VenueGroup) -> str:
    """Include event_id so same hotel text for two events does not share a hit."""
    return f"{g.event_id}|{g.query()}"


def run(
    groups: List[VenueGroup],
    lookup: Optional[LookupFn],
    cache: Dict[str, Any],
) -> List[Tuple[VenueGroup, Optional[Dict[str, Any]], Dict[str, Any]]]:
    rows = []
    for g in groups:
        key = cache_key(g)
        # Legacy caches keyed by query alone — migrate on read.
        legacy = g.query()
        if key not in cache and legacy in cache:
            cache[key] = cache[legacy]
        raw = cache.get(key)
        hit = normalize_hit(raw) if key in cache else None
        # Refetch when missing or corrupt (None is a valid cached miss).
        needs_lookup = key not in cache or (
            raw is not None and hit is None
        )
        if needs_lookup and lookup is not None:
            cache[key] = lookup(g)
            raw = cache[key]
            hit = normalize_hit(raw)
        if key in cache:
            rows.append((g, hit, classify(g, hit)))
        else:
            rows.append((g, None, {"verdict": "not_looked_up", "years_to_fix": []}))
    return rows


VERDICT_ORDER = {
    "fix_all_years": 0,
    "fix_some_years": 1,
    "check_google_far_from_city": 2,
    "check_weak_match": 3,
    "not_found": 4,
    "not_looked_up": 5,
    "ok": 6,
}


def write_outputs(rows, out_dir: Path) -> Dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(
        rows,
        key=lambda r: (VERDICT_ORDER.get(r[2]["verdict"], 9), -(r[2].get("max_dist_km") or 0)),
    )
    overrides = []
    with (out_dir / "venue_audit.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "verdict", "event_id", "event", "city", "country", "hotel", "address",
            "years", "years_to_fix", "registry_points", "registry_spread_km",
            "google_api", "google_name", "google_address", "name_match", "max_dist_km",
            "dist_by_year_km", "google_city_km", "google_link", "registry_links",
        ])
        for g, hit, c in rows:
            uniq = sorted({(round(p[0], 5), round(p[1], 5)) for p in g.points.values()})
            yfix = c.get("years_to_fix") or []
            w.writerow([
                c["verdict"], g.event_id, g.event, g.city, g.country, g.hotel, g.address,
                " ".join(str(y) for y in sorted(g.points)),
                " ".join(str(y) for y in yfix),
                len(uniq),
                f"{g.spread_km:.1f}",
                hit["api"] if hit else "",
                hit.get("name", "") if hit else "",
                hit.get("address", "") if hit else "",
                f"{c['name_match']:.2f}" if c.get("name_match") is not None else "",
                f"{c['max_dist_km']:.1f}" if c.get("max_dist_km") is not None else "",
                " ".join(f"{y}:{d:.1f}" for y, d in c.get("dist_by_year", {}).items()),
                f"{c['google_city_km']:.1f}" if c.get("google_city_km") is not None else "",
                maps_link(hit["lat"], hit["lon"]) if hit else "",
                " ".join(maps_link(a, b) for a, b in uniq),
            ])
            if hit and override_eligible(c):
                overrides.append({
                    "event_id": g.event_id,
                    "hotel_key": hotel_match_key(g.hotel),
                    "hotel": g.hotel,
                    "verdict": c["verdict"],
                    "lat": round(float(hit["lat"]), 6),
                    "lon": round(float(hit["lon"]), 6),
                    "google_name": hit.get("name", ""),
                    "google_address": hit.get("address", ""),
                    "place_id": hit.get("place_id", ""),
                    "name_match": round(float(c["name_match"]), 3),
                    "max_dist_km": round(float(c["max_dist_km"]), 2),
                    "years": sorted(g.points),
                    "years_to_fix": list(yfix),
                    "dist_by_year_km": {
                        str(y): round(d, 2) for y, d in c.get("dist_by_year", {}).items()
                    },
                })
    (out_dir / "proposed_overrides.json").write_text(
        json.dumps(overrides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return dict(Counter(r[2]["verdict"] for r in rows))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--growth", type=Path, default=DEFAULT_GROWTH)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--env-file", type=Path, help="Read GOOGLE_MAPS_API_KEY from a .env file")
    ap.add_argument("--offline", action="store_true", help="Use cache only; no API calls")
    ap.add_argument("--limit", type=int, help="Look up at most N new groups (smoke test)")
    ap.add_argument("--sleep", type=float, default=0.05, help="Seconds between API calls")
    args = ap.parse_args(argv)

    if args.env_file:
        load_env_file(args.env_file)
    editions = json.loads(args.growth.read_text(encoding="utf-8"))["editions"]
    groups = build_groups(editions)

    cache_path = args.out_dir / "google_cache.json"
    cache: Dict[str, Any] = {}
    if cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    lookup: Optional[LookupFn] = None
    if not args.offline:
        key = (os.getenv("GOOGLE_MAPS_API_KEY") or "").strip()
        if not key:
            print("GOOGLE_MAPS_API_KEY not set (use --env-file or --offline)", file=sys.stderr)
            return 2
        budget = [args.limit if args.limit is not None else len(groups)]

        def lookup(g: VenueGroup) -> Optional[Dict[str, Any]]:
            if budget[0] <= 0:
                raise _BudgetSpent
            budget[0] -= 1
            time.sleep(args.sleep)
            return google_lookup(
                g.query(),
                key,
                bias_lat=g.city_lat,
                bias_lon=g.city_lon,
            )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    try:
        rows = run(groups, lookup, cache)
    except _BudgetSpent:
        rows = run(groups, None, cache)
    finally:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    counts = write_outputs(rows, args.out_dir)
    print(f"groups={len(groups)} looked_up={len(cache)}")
    for verdict in sorted(counts, key=lambda v: VERDICT_ORDER.get(v, 9)):
        print(f"  {verdict}: {counts[verdict]}")
    eligible = sum(1 for _, _, c in rows if override_eligible(c))
    print(f"override_candidates={eligible}")
    print(f"report: {args.out_dir / 'venue_audit.csv'}")
    return 0


class _BudgetSpent(Exception):
    pass


if __name__ == "__main__":
    raise SystemExit(main())
