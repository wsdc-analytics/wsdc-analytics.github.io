#!/usr/bin/env python3
"""Enrich event_growth.json editions with WSDC registry venue lat/lon + hotel.

Reads competitionevents from a mysqldump (.sql), matches each growth edition to
the closest competitionevents.start_date for the same event_id (not calendar
year — NYE editions often have start in Dec of the prior year), and replaces
city-centroid lat/lon with venue coordinates when they look sane (within
MAX_DRIFT_KM of the city point).

Hotel/address are attached only when venue coords are accepted.

Usage:
  python3 scripts/enrich_event_growth_venues.py \\
    --sql ~/Downloads/wsdc101526.sql

  python3 scripts/enrich_event_growth_venues.py --sql ... --dry-run
  python3 scripts/enrich_event_growth_venues.py --sql ... --lookup-out static/data/wsdc_venue_lookup.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
DEFAULT_GROWTH = REPO / "static" / "data" / "event_growth.json"

# Reject registry coords that land far from the edition's city point
# (catches bad dumps like Washington DC → Melbourne).
MAX_DRIFT_KM = 200.0
# Max |start − SQL start| when pairing growth edition ↔ competitionevents row.
MAX_DATE_DRIFT_DAYS = 45

# Source → canonical from pipeline MERGE_EVENT_ID_MAP (keep in sync with
# wsdc-data-pipeline/transform/knowledge/event_aliases.py). CE hotel/GPS often
# still live on the source registry id while growth editions use canonical.
_MERGE_SOURCE_TO_CANONICAL: Dict[int, int] = {
    66: 47,
    466: 47,
    37: 195,
    193: 236,
    99: 119,
    198: 154,
    202: 218,
    39: 334,
    307: 272,  # Paris Swing Classic → points id (Westie Fest lineage)
    543: 272,
    325: 330,
    321: 331,
    279: 283,
    406: 197,
    433: 369,
    442: 120,
    566: 9,
    506: 12,
    571: 179,
    412: 374,
    493: 264,
    477: 264,
    480: 75,
    551: 221,
    552: 221,
    467: 221,
    463: 280,
    409: 342,  # GGP Championships Paris ghost → Reunion series
    437: 342,
    438: 342,
}


def venue_lookup_extra_ids(
    merge_map: Optional[Dict[int, int]] = None,
) -> Dict[int, Tuple[int, ...]]:
    """Invert source→canonical into canonical→(sources…) for CE venue lookup."""
    mapping = merge_map if merge_map is not None else _MERGE_SOURCE_TO_CANONICAL
    rev: Dict[int, List[int]] = defaultdict(list)
    for src, canon in mapping.items():
        if src == canon:
            continue
        rev[int(canon)].append(int(src))
    return {canon: tuple(sorted(sources)) for canon, sources in rev.items()}


# Default fold map (computed once).
VENUE_LOOKUP_EXTRA_IDS: Dict[int, Tuple[int, ...]] = venue_lookup_extra_ids()

# Ignore dump placeholders when inheriting / attaching hotel names.
PLACEHOLDER_HOTEL_KEYS = frozenset(
    {
        "",
        "hotel",
        "hotels",
        "tbd",
        "tba",
        "n/a",
        "na",
        "-",
        "still in negotiation",
    }
)
# Max |edition start − sibling start| when reusing another edition's GPS.
MAX_INHERIT_DATE_DAYS = 400
# Same named hotel may be missing GPS for 1–2 seasons; allow a longer window.
MAX_SAME_HOTEL_INHERIT_DATE_DAYS = 800
# If matched CE GPS is farther from city than this, prefer a same-hotel sibling
# with a tighter city drift (catches dump typos still under MAX_DRIFT_KM).
SOFT_CITY_DRIFT_KM = 80.0

INSERT_RE = re.compile(
    r"^INSERT INTO `competitionevents`\s*\((?P<cols>[^)]+)\)\s*VALUES\s*\((?P<body>.*)\);\s*$"
)


@dataclass
class VenueRow:
    event_id: int
    start: date
    lat: Optional[float]
    lon: Optional[float]
    hotel: str
    address: str
    city: str
    ce_id: int


def split_mysql_values(body: str) -> List[Optional[str]]:
    """Split a single MySQL VALUES(...) body into fields."""
    fields: List[Optional[str]] = []
    i = 0
    n = len(body)
    while i < n:
        while i < n and body[i] in " \t\n\r":
            i += 1
        if i >= n:
            break
        if body.startswith("NULL", i) and (i + 4 >= n or body[i + 4] in ",)"):
            fields.append(None)
            i += 4
        elif body[i] == "'":
            i += 1
            buf: List[str] = []
            while i < n:
                c = body[i]
                if c == "\\" and i + 1 < n:
                    buf.append(body[i + 1])
                    i += 2
                    continue
                if c == "'" and i + 1 < n and body[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                if c == "'":
                    i += 1
                    break
                buf.append(c)
                i += 1
            fields.append("".join(buf))
        else:
            j = i
            while j < n and body[j] not in ",)":
                j += 1
            fields.append(body[i:j].strip())
            i = j
        while i < n and body[i] in " \t\n\r":
            i += 1
        if i < n and body[i] == ",":
            i += 1
    return fields


def parse_float(v: Optional[str]) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_int(v: Optional[str]) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def parse_iso_date(v: Optional[str]) -> Optional[date]:
    if not v or len(v) < 10:
        return None
    try:
        return date.fromisoformat(v[:10])
    except ValueError:
        return None


def usable_lat_lon(lat: Optional[float], lon: Optional[float]) -> bool:
    """True if coords look like a real place (not NULL / NaN / null-island 0,0)."""
    if lat is None or lon is None:
        return False
    try:
        la = float(lat)
        lo = float(lon)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(la) or not math.isfinite(lo):
        return False
    # WSDC dump often stores missing GPS as 0 / 0 (Gulf of Guinea).
    if abs(la) < 1e-6 and abs(lo) < 1e-6:
        return False
    return True


def hotel_match_key(hotel: str) -> str:
    s = re.sub(r"\s+", " ", (hotel or "").lower()).strip()
    s = re.sub(r"\bhotels?\b", "", s)
    return re.sub(r"\s+", " ", s).strip()


def usable_hotel_name(hotel: Optional[str]) -> Optional[str]:
    """Return hotel string if it looks like a real venue name, else None."""
    raw = (hotel or "").strip()
    if not raw:
        return None
    if raw.lower() in PLACEHOLDER_HOTEL_KEYS:
        return None
    key = hotel_match_key(raw)
    if key in PLACEHOLDER_HOTEL_KEYS:
        return None
    return raw


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def drift_to_city_km(
    city_lat: Optional[float],
    city_lon: Optional[float],
    vlat: float,
    vlon: float,
) -> Optional[float]:
    """Smallest haversine to city, trying lon sign flip. None if no city point."""
    if city_lat is None or city_lon is None:
        return None
    clat_f = float(city_lat)
    clon_f = float(city_lon)
    drift = haversine_km(clat_f, clon_f, vlat, vlon)
    alt = haversine_km(clat_f, clon_f, vlat, -vlon)
    return min(drift, alt)


def iter_competitionevents(sql_path: Path) -> Iterable[VenueRow]:
    col_index: Optional[Dict[str, int]] = None
    with sql_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.startswith("INSERT INTO `competitionevents`"):
                continue
            m = INSERT_RE.match(line.rstrip("\n"))
            if not m:
                continue
            if col_index is None:
                cols = [c.strip().strip("`") for c in m.group("cols").split(",")]
                col_index = {name: i for i, name in enumerate(cols)}
                for need in (
                    "id",
                    "event_id",
                    "start_date",
                    "latitude",
                    "longitude",
                    "hotel",
                    "address",
                    "city",
                ):
                    if need not in col_index:
                        raise SystemExit(f"competitionevents missing column: {need}")

            fields = split_mysql_values(m.group("body"))
            if len(fields) < len(col_index):
                continue

            def get(name: str) -> Optional[str]:
                assert col_index is not None
                return fields[col_index[name]]

            eid = parse_int(get("event_id"))
            start = parse_iso_date(get("start_date"))
            if eid is None or start is None:
                continue
            lat = parse_float(get("latitude"))
            lon = parse_float(get("longitude"))
            # Normalize null-island placeholders to missing coords.
            if not usable_lat_lon(lat, lon):
                lat, lon = None, None
            yield VenueRow(
                event_id=eid,
                start=start,
                lat=lat,
                lon=lon,
                hotel=(get("hotel") or "").strip(),
                address=(get("address") or "").strip(),
                city=(get("city") or "").strip(),
                ce_id=parse_int(get("id")) or 0,
            )


def _dedupe_venue_rows(rows: Iterable[VenueRow]) -> List[VenueRow]:
    """Dedupe by start date: prefer geo, then higher ce_id; sort by start."""
    best_at: Dict[date, VenueRow] = {}
    for row in rows:
        prev = best_at.get(row.start)
        if prev is None:
            best_at[row.start] = row
            continue
        prev_geo = usable_lat_lon(prev.lat, prev.lon)
        row_geo = usable_lat_lon(row.lat, row.lon)
        if row_geo and not prev_geo:
            best_at[row.start] = row
        elif row_geo == prev_geo and row.ce_id >= prev.ce_id:
            best_at[row.start] = row
    return sorted(best_at.values(), key=lambda r: (r.start, r.ce_id))


def build_lookup_by_event(rows: Iterable[VenueRow]) -> Dict[int, List[VenueRow]]:
    """event_id → venue rows sorted by start (dedupe same start: prefer geo, then ce_id)."""
    by_raw: Dict[int, List[VenueRow]] = defaultdict(list)
    for row in rows:
        by_raw[row.event_id].append(row)
    return {eid: _dedupe_venue_rows(rs) for eid, rs in by_raw.items()}


def fold_merged_venue_lookups(
    by_event: Dict[int, List[VenueRow]],
    extra_ids: Optional[Dict[int, Tuple[int, ...]]] = None,
) -> Dict[int, List[VenueRow]]:
    """Attach merged-source CE rows under the canonical growth event_id.

    Example: Paris growth editions use event_id 272, but 2023+ hotels are on
    competitionevents.event_id 307 (merged in the points pipeline).
    """
    extras = extra_ids if extra_ids is not None else VENUE_LOOKUP_EXTRA_IDS
    out = {eid: list(rows) for eid, rows in by_event.items()}
    for canonical, sources in extras.items():
        pooled: List[VenueRow] = list(out.get(canonical, []))
        for src in sources:
            pooled.extend(out.get(src, []))
        if pooled:
            out[canonical] = _dedupe_venue_rows(pooled)
    return out


def match_venue(
    eid: int,
    start: Optional[date],
    by_event: Dict[int, List[VenueRow]],
    max_date_drift_days: int,
) -> Optional[VenueRow]:
    """Pick SQL row with closest start_date within max_date_drift_days."""
    candidates = by_event.get(eid) or []
    if not candidates:
        return None
    if start is None:
        # No edition date → last row with coords, else last row.
        with_geo = [r for r in candidates if usable_lat_lon(r.lat, r.lon)]
        return (with_geo or candidates)[-1]

    best: Optional[VenueRow] = None
    best_abs = None
    for row in candidates:
        drift = abs((row.start - start).days)
        if drift > max_date_drift_days:
            continue
        if best is None or drift < best_abs or (
            drift == best_abs and row.ce_id > (best.ce_id if best else 0)
        ):
            best = row
            best_abs = drift
    return best


def inherit_venue_coords(
    eid: int,
    start: Optional[date],
    hotel: str,
    by_event: Dict[int, List[VenueRow]],
    city_lat: Optional[float],
    city_lon: Optional[float],
    max_drift_km: float,
    max_date_days: int = MAX_INHERIT_DATE_DAYS,
    exclude_ce_ids: Optional[Iterable[int]] = None,
) -> Optional[VenueRow]:
    """When this year's SQL row lacks GPS, reuse a sibling edition's coords.

    Prefer same hotel name (normalized), then closest start_date. Sibling must
    still pass the city drift check when a city point exists. Placeholder hotel
    names and far-away dates are skipped.
    """
    hk = hotel_match_key(hotel) if usable_hotel_name(hotel) else ""
    date_cap = (
        max(max_date_days, MAX_SAME_HOTEL_INHERIT_DATE_DAYS) if hk else max_date_days
    )
    skip = {int(x) for x in (exclude_ce_ids or ())}
    scored: List[Tuple[int, int, float, VenueRow]] = []
    for row in by_event.get(eid) or []:
        if row.ce_id in skip:
            continue
        if not usable_lat_lon(row.lat, row.lon):
            continue
        assert row.lat is not None and row.lon is not None
        d_city = drift_to_city_km(city_lat, city_lon, float(row.lat), float(row.lon))
        if d_city is not None and d_city > max_drift_km:
            continue
        date_dist = abs((row.start - start).days) if start is not None else 10_000
        if start is not None and date_dist > date_cap:
            continue
        # Prefer real hotel names; never inherit a placeholder label alone.
        if not usable_hotel_name(row.hotel) and not hk:
            continue
        same_hotel = 0 if (hk and hotel_match_key(row.hotel) == hk) else 1
        city_rank = float(d_city) if d_city is not None else 0.0
        scored.append((same_hotel, date_dist, city_rank, row))
    if not scored:
        return None
    # Same hotel + nearer city beats a far same-date self-match leftover.
    scored.sort(key=lambda t: (t[0], t[2], t[1], -t[3].ce_id))
    return scored[0][3]


def clear_venue_fields(ed: Dict[str, Any]) -> None:
    for key in ("hotel", "address", "geo_fix", "venue_rejected_km", "venue_start"):
        if key in ed:
            del ed[key]


def enrich_editions(
    editions: List[Dict[str, Any]],
    by_event: Dict[int, List[VenueRow]],
    max_drift_km: float,
    max_date_drift_days: int,
) -> Dict[str, int]:
    stats = {
        "editions": len(editions),
        "matched": 0,
        "venue_applied": 0,
        "venue_inherited": 0,
        "venue_rejected_drift": 0,
        "lon_sign_fixed": 0,
        "unmatched": 0,
        "no_sql_geo": 0,
        "hotel_only": 0,
        "date_drift_skipped": 0,
    }
    for ed in editions:
        eid = ed.get("event_id")
        if eid is None:
            stats["unmatched"] += 1
            clear_venue_fields(ed)
            ed["geo_source"] = "city"
            continue

        start = parse_iso_date(ed.get("start"))
        if start is None and ed.get("year") is not None and ed.get("month") is not None:
            try:
                start = date(int(ed["year"]), int(ed["month"]), 1)
            except (TypeError, ValueError):
                start = None

        row = match_venue(int(eid), start, by_event, max_date_drift_days)
        if row is None:
            # Distinguish: event known but no start within window vs unknown event.
            if int(eid) in by_event:
                stats["date_drift_skipped"] += 1
            else:
                stats["unmatched"] += 1
            clear_venue_fields(ed)
            # Restore city centroid if we previously overwrote lat/lon.
            if ed.get("city_lat") is not None:
                ed["lat"] = ed["city_lat"]
            if ed.get("city_lon") is not None:
                ed["lon"] = ed["city_lon"]
            ed["geo_source"] = "city"
            continue

        stats["matched"] += 1

        # Preserve original city centroid for idempotent re-runs + drift checks.
        if "city_lat" not in ed and ed.get("lat") is not None:
            ed["city_lat"] = ed["lat"]
        if "city_lon" not in ed and ed.get("lon") is not None:
            ed["city_lon"] = ed["lon"]
        city_lat = ed.get("city_lat", ed.get("lat"))
        city_lon = ed.get("city_lon", ed.get("lon"))

        vlat, vlon = row.lat, row.lon
        inherited = False
        inherit_from: Optional[VenueRow] = None
        if not usable_lat_lon(vlat, vlon):
            inherit_from = inherit_venue_coords(
                int(eid),
                start,
                row.hotel,
                by_event,
                float(city_lat) if city_lat is not None else None,
                float(city_lon) if city_lon is not None else None,
                max_drift_km,
            )
            if inherit_from is None:
                stats["no_sql_geo"] += 1
                clear_venue_fields(ed)
                ed["geo_source"] = "city"
                if city_lat is not None:
                    ed["lat"] = city_lat
                if city_lon is not None:
                    ed["lon"] = city_lon
                # Hotel/address without GPS is still useful on the tip (e.g. Sea Dance
                # "Milan" in Moscow). Do not attach hotel after drift rejection.
                hotel_only = usable_hotel_name(row.hotel)
                if hotel_only:
                    ed["hotel"] = hotel_only
                    stats["hotel_only"] = stats.get("hotel_only", 0) + 1
                if row.address:
                    ed["address"] = row.address
                ed["venue_start"] = row.start.isoformat()
                continue
            vlat, vlon = inherit_from.lat, inherit_from.lon
            inherited = True

        vlat_f = float(vlat)  # type: ignore[arg-type]
        vlon_f = float(vlon)  # type: ignore[arg-type]
        lon_flipped = False
        if city_lat is not None and city_lon is not None:
            clat_f = float(city_lat)
            clon_f = float(city_lon)
            drift = haversine_km(clat_f, clon_f, vlat_f, vlon_f)
            # Common dump bug: longitude sign flipped (e.g. Monterey +121 → −121).
            if drift > max_drift_km:
                alt_lon = -vlon_f
                alt_drift = haversine_km(clat_f, clon_f, vlat_f, alt_lon)
                if alt_drift <= max_drift_km and alt_drift < drift:
                    vlon_f = alt_lon
                    drift = alt_drift
                    lon_flipped = True
                    stats["lon_sign_fixed"] += 1
            if drift > max_drift_km or (
                not inherited
                and usable_hotel_name(row.hotel)
                and drift > SOFT_CITY_DRIFT_KM
            ):
                # Bad / loose GPS on this year's row: try a sibling with the same
                # hotel and a tighter city drift (Mexico coords; Orléans typo).
                sibling = inherit_venue_coords(
                    int(eid),
                    start,
                    row.hotel,
                    by_event,
                    clat_f,
                    clon_f,
                    max_drift_km,
                    exclude_ce_ids=(row.ce_id,),
                )
                if sibling is not None and usable_lat_lon(sibling.lat, sibling.lon):
                    sib_lat = float(sibling.lat)  # type: ignore[arg-type]
                    sib_lon = float(sibling.lon)  # type: ignore[arg-type]
                    sib_drift = haversine_km(clat_f, clon_f, sib_lat, sib_lon)
                    if sib_drift + 1.0 < drift:
                        vlat_f, vlon_f = sib_lat, sib_lon
                        inherit_from = sibling
                        inherited = True
                        lon_flipped = False
                        drift = sib_drift
                if drift > max_drift_km and not inherited:
                    stats["venue_rejected_drift"] += 1
                    clear_venue_fields(ed)
                    ed["geo_source"] = "city"
                    ed["lat"] = city_lat
                    ed["lon"] = city_lon
                    ed["venue_rejected_km"] = round(drift, 1)
                    continue

        # Accept venue — only then attach hotel/address.
        ed["lat"] = round(vlat_f, 6)
        ed["lon"] = round(vlon_f, 6)
        ed["geo_source"] = "wsdc_venue"
        venue_start_row = inherit_from if inherited and inherit_from else row
        ed["venue_start"] = venue_start_row.start.isoformat()
        hotel = usable_hotel_name(row.hotel) or (
            usable_hotel_name(inherit_from.hotel) if inherit_from else None
        )
        address = (row.address or "").strip() or (
            (inherit_from.address if inherit_from else "") or ""
        )
        if hotel:
            ed["hotel"] = hotel
        elif "hotel" in ed:
            del ed["hotel"]
        if address:
            ed["address"] = address
        elif "address" in ed:
            del ed["address"]
        if inherited:
            ed["geo_fix"] = "inherited"
            stats["venue_inherited"] += 1
        elif lon_flipped:
            ed["geo_fix"] = "lon_sign"
        elif "geo_fix" in ed:
            del ed["geo_fix"]
        if "venue_rejected_km" in ed:
            del ed["venue_rejected_km"]
        stats["venue_applied"] += 1

    return stats


def venue_row_to_dict(row: VenueRow) -> Dict[str, Any]:
    return {
        "event_id": row.event_id,
        "start": row.start.isoformat(),
        "lat": row.lat,
        "lon": row.lon,
        "hotel": row.hotel or None,
        "address": row.address or None,
        "city": row.city or None,
        "ce_id": row.ce_id,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sql",
        type=Path,
        required=True,
        help="Path to WSDC mysqldump containing competitionevents",
    )
    ap.add_argument("--growth", type=Path, default=DEFAULT_GROWTH)
    ap.add_argument(
        "--lookup-out",
        type=Path,
        default=None,
        help="Optional path to write extracted venue lookup JSON (audit/cache)",
    )
    ap.add_argument("--max-drift-km", type=float, default=MAX_DRIFT_KM)
    ap.add_argument("--max-date-drift-days", type=int, default=MAX_DATE_DRIFT_DAYS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.sql.is_file():
        print(f"SQL dump not found: {args.sql}", file=sys.stderr)
        return 1
    if not args.growth.is_file():
        print(f"event_growth.json not found: {args.growth}", file=sys.stderr)
        return 1

    print(f"Parsing competitionevents from {args.sql} …", flush=True)
    by_event = fold_merged_venue_lookups(
        build_lookup_by_event(iter_competitionevents(args.sql))
    )
    n_rows = sum(len(v) for v in by_event.values())
    with_geo = sum(
        1 for rows in by_event.values() for r in rows if usable_lat_lon(r.lat, r.lon)
    )
    print(
        f"  events: {len(by_event)}  rows: {n_rows}  with lat/lon: {with_geo}",
        flush=True,
    )

    growth = json.loads(args.growth.read_text(encoding="utf-8"))
    editions = growth.get("editions") or []
    if not isinstance(editions, list):
        print("event_growth.json.editions must be a list", file=sys.stderr)
        return 1

    stats = enrich_editions(
        editions, by_event, args.max_drift_km, args.max_date_drift_days
    )
    print("Enrichment stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    years = growth.get("years") or []
    focus_year = max(years) if years else None
    if focus_year:
        by_city: Dict[Tuple[Any, ...], List[Tuple[float, float]]] = defaultdict(list)
        for ed in editions:
            if ed.get("year") != focus_year:
                continue
            if ed.get("lat") is None or ed.get("lon") is None:
                continue
            key = (ed.get("city"), ed.get("country"), ed.get("state"))
            by_city[key].append((float(ed["lat"]), float(ed["lon"])))
        multi = {k: pts for k, pts in by_city.items() if len(pts) > 1}
        distinct = sum(
            1
            for pts in multi.values()
            if len({(round(a, 4), round(b, 4)) for a, b in pts}) > 1
        )
        print(
            f"  {focus_year} multi-event cities: {len(multi)}; "
            f"with distinct venue coords: {distinct}"
        )

    # Trust check: hotel must not appear without accepted venue.
    bad_hotel = sum(
        1
        for ed in editions
        if ed.get("hotel") and ed.get("geo_source") != "wsdc_venue"
    )
    if bad_hotel:
        print(f"  WARN: hotel without wsdc_venue: {bad_hotel}", file=sys.stderr)

    meta = {
        "source": str(args.sql.name),
        "enriched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_drift_km": args.max_drift_km,
        "max_date_drift_days": args.max_date_drift_days,
        "stats": stats,
    }
    growth["venue_enrichment"] = meta

    if args.dry_run:
        print("Dry-run: not writing files.")
        return 0

    if args.lookup_out is not None:
        args.lookup_out.parent.mkdir(parents=True, exist_ok=True)
        flat = [
            venue_row_to_dict(r)
            for eid in sorted(by_event)
            for r in by_event[eid]
        ]
        args.lookup_out.write_text(
            json.dumps(
                {
                    "generated_at": meta["enriched_at"],
                    "source": meta["source"],
                    "n": len(flat),
                    "venues": flat,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {args.lookup_out}")

    args.growth.write_text(
        json.dumps(growth, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.growth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
