#!/usr/bin/env python3
"""Apply reviewed Google venue overrides into event_growth.json.

Only patches editions whose (event_id, hotel_key, year) is listed in
years_to_fix. Already-correct years are left untouched.

  python3 scripts/apply_event_growth_venue_overrides.py \\
    --overrides /tmp/venue_audit_places/proposed_overrides.json --dry-run
  python3 scripts/apply_event_growth_venue_overrides.py \\
    --overrides /tmp/venue_audit_places/proposed_overrides.json \\
    --verdict fix_all_years
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_event_growth_venues import NAME_MATCH_MIN, OK_KM  # noqa: E402
from enrich_event_growth_venues import haversine_km, hotel_match_key, usable_hotel_name  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DEFAULT_GROWTH = REPO / "static" / "data" / "event_growth.json"


def load_overrides(
    path: Path,
    *,
    verdicts: Optional[Set[str]] = None,
    event_ids: Optional[Set[int]] = None,
    min_name_match: float = NAME_MATCH_MIN,
) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for row in raw:
        if verdicts is not None and row.get("verdict") not in verdicts:
            continue
        if event_ids is not None and int(row["event_id"]) not in event_ids:
            continue
        if float(row.get("name_match") or 0) < min_name_match:
            continue
        years = row.get("years_to_fix") or []
        if not years:
            continue
        if row.get("lat") is None or row.get("lon") is None:
            continue
        out.append(row)
    return out


def apply_overrides(
    editions: List[Dict[str, Any]],
    overrides: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Mutate editions in place. Returns stats."""
    index: Dict[Tuple[int, str, int], Dict[str, Any]] = {}
    for ed in editions:
        if ed.get("geo_source") != "wsdc_venue":
            continue
        hotel = usable_hotel_name(ed.get("hotel"))
        if not hotel or ed.get("year") is None:
            continue
        key = (int(ed["event_id"]), hotel_match_key(hotel), int(ed["year"]))
        index[key] = ed

    stats = {
        "override_rows": len(overrides),
        "editions_patched": 0,
        "editions_skipped_missing": 0,
        "editions_already_close": 0,
        "years_requested": 0,
    }
    for ov in overrides:
        eid = int(ov["event_id"])
        hkey = ov.get("hotel_key") or hotel_match_key(ov.get("hotel") or "")
        glat, glon = float(ov["lat"]), float(ov["lon"])
        for year in ov["years_to_fix"]:
            stats["years_requested"] += 1
            ed = index.get((eid, hkey, int(year)))
            if ed is None:
                stats["editions_skipped_missing"] += 1
                continue
            if ed.get("lat") is None or ed.get("lon") is None:
                stats["editions_skipped_missing"] += 1
                continue
            cur_lat, cur_lon = float(ed["lat"]), float(ed["lon"])
            if haversine_km(cur_lat, cur_lon, glat, glon) <= OK_KM:
                stats["editions_already_close"] += 1
                continue
            ed["lat"] = round(glat, 6)
            ed["lon"] = round(glon, 6)
            ed["geo_fix"] = "google_audit"
            if ov.get("google_name"):
                ed["google_venue_name"] = ov["google_name"]
            if ov.get("place_id"):
                ed["google_place_id"] = ov["place_id"]
            stats["editions_patched"] += 1
    return stats


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--growth", type=Path, default=DEFAULT_GROWTH)
    ap.add_argument("--overrides", type=Path, required=True)
    ap.add_argument(
        "--verdict",
        action="append",
        dest="verdicts",
        help="Restrict to verdict(s); repeatable. Default: fix_all_years + fix_some_years",
    )
    ap.add_argument(
        "--event-id",
        action="append",
        type=int,
        dest="event_ids",
        help="Restrict to event_id(s); repeatable",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    verdicts = set(args.verdicts) if args.verdicts else {"fix_all_years", "fix_some_years"}
    event_ids = set(args.event_ids) if args.event_ids else None
    overrides = load_overrides(
        args.overrides, verdicts=verdicts, event_ids=event_ids
    )
    data = json.loads(args.growth.read_text(encoding="utf-8"))
    stats = apply_overrides(data["editions"], overrides)
    meta = data.setdefault("venue_enrichment", {})
    meta["google_audit"] = {
        "overrides_file": str(args.overrides),
        "verdicts": sorted(verdicts),
        "stats": stats,
    }
    print(json.dumps(stats, indent=2))
    if args.dry_run:
        print("dry-run: not writing", args.growth)
        return 0
    args.growth.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.growth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
