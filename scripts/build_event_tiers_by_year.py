#!/usr/bin/env python3
"""Build static/data/event_tiers_by_year.json for the Event tiers by year dashboard.

Joins edition tiers from event_l2_cards.json with geo/dates from the local
wsdc-data-pipeline catalog + editions CSVs (and continent hints from the
site calendar JSON).

Usage (from repo root):
    python3 scripts/build_event_tiers_by_year.py
    python3 scripts/build_event_tiers_by_year.py \\
      --source-dir /path/to/pipeline/data \\
      --site-repo /path/to/wsdc-analytics-repo
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PIPE = Path(
    os.environ.get(
        "WSDC_PIPELINE_DATA",
        str(Path.home() / ".cursor/projects/python/wsdc-data-pipeline/data"),
    )
)
PIPE = DEFAULT_PIPE
OUT = REPO / "static" / "data" / "event_tiers_by_year.json"
YEAR_FLOOR = 2018

# competitions_best.level → canonical division name used in l2 cards / dashboard
LEVEL_TO_DIV = {
    "Newcomer": "Newcomer",
    "Novice": "Novice",
    "Intermediate": "Intermediate",
    "Advanced": "Advanced",
    "All-Star": "All-Star",
    "All Star": "All-Star",
    "Champion": "Champions",
    "Champions": "Champions",
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing required input: {path}\n"
            f"Pass --source-dir or set WSDC_PIPELINE_DATA "
            f"(currently {PIPE})."
        )
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build event_tiers_by_year.json for the analytics site."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_PIPE,
        help="Pipeline data directory (event_catalog.csv, event_editions.csv, …)",
    )
    parser.add_argument(
        "--site-repo",
        type=Path,
        default=REPO,
        help="Analytics site repo root (reads event_l2_cards.json + calendar)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: <site-repo>/static/data/event_tiers_by_year.json)",
    )
    return parser.parse_args()

# Fallback when country is missing from the live calendar map.
COUNTRY_CONTINENT = {
    "United States": "America",
    "Canada": "America",
    "Mexico": "America",
    "Brazil": "America",
    "Argentina": "America",
    "Colombia": "America",
    "Chile": "America",
    "United Kingdom": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Italy": "Europe",
    "Spain": "Europe",
    "Netherlands": "Europe",
    "Belgium": "Europe",
    "Switzerland": "Europe",
    "Austria": "Europe",
    "Poland": "Europe",
    "Czech Republic": "Europe",
    "Czechia": "Europe",
    "Sweden": "Europe",
    "Norway": "Europe",
    "Denmark": "Europe",
    "Finland": "Europe",
    "Ireland": "Europe",
    "Portugal": "Europe",
    "Romania": "Europe",
    "Hungary": "Europe",
    "Ukraine": "Europe",
    "Russia": "Europe",
    "Estonia": "Europe",
    "Latvia": "Europe",
    "Lithuania": "Europe",
    "Israel": "Asia",
    "Japan": "Asia",
    "Republic of Korea": "Asia",
    "South Korea": "Asia",
    "China": "Asia",
    "Taiwan": "Asia",
    "Hong Kong": "Asia",
    "Singapore": "Asia",
    "Thailand": "Asia",
    "India": "Asia",
    "Australia": "Australia",
    "New Zealand": "Australia",
}

US_STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}


def load_continent_by_country() -> dict[str, str]:
    cal_path = REPO / "static" / "data" / "events_year_calendar.json"
    out = dict(COUNTRY_CONTINENT)
    if cal_path.exists():
        cal = json.loads(cal_path.read_text())
        for e in cal.get("events") or []:
            country = e.get("country")
            continent = e.get("continent")
            if country and continent:
                out[country] = continent
    return out


def load_catalog() -> dict[int, dict]:
    path = require_file(PIPE / "event_catalog.csv")
    out: dict[int, dict] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[int(row["event_id"])] = row
    return out


def load_editions() -> dict[tuple[int, int], list[dict]]:
    """Index editions by (event_id, year)."""
    path = require_file(PIPE / "event_editions.csv")
    out: dict[tuple[int, int], list[dict]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                eid = int(row["event_id"])
                year = int(row["event_year"])
            except (TypeError, ValueError):
                continue
            out[(eid, year)].append(row)
    return out


def load_competition_counts() -> dict[tuple[int, int, int, str], dict[str, int]]:
    """Exact WCS headcounts from competitions_best.csv.

    Key: (event_id, year, month, division) → {Leader, Follower}.
    """
    path = PIPE / "competitions_best.csv"
    if not path.is_file():
        return {}
    out: dict[tuple[int, int, int, str], dict[str, int]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("match_status") or "matched") != "matched":
                continue
            dance = row.get("dance") or ""
            if dance and "West Coast" not in dance:
                continue
            div = LEVEL_TO_DIV.get(str(row.get("level") or "").strip())
            if not div:
                continue
            try:
                eid = int(row["event_id"])
                year = int(row["event_year"])
                month = int(float(row.get("event_month") or 0))
            except (TypeError, ValueError):
                continue
            counts: dict[str, int] = {}
            for role, col in (("Leader", "leader_count"), ("Follower", "follower_count")):
                raw = row.get(col)
                if raw in (None, ""):
                    continue
                try:
                    counts[role] = int(float(raw))
                except (TypeError, ValueError):
                    continue
            if not counts:
                continue
            out[(eid, year, month, div)] = counts
    return out


def lookup_counts(
    idx: dict[tuple[int, int, int, str], dict[str, int]],
    eid: int,
    year: int,
    month: int | None,
    div: str,
) -> dict[str, int] | None:
    if month:
        hit = idx.get((eid, year, month, div))
        if hit:
            return hit
    # Fallback: unique month for this edition/division in that year.
    matches = [v for (i, y, _m, d), v in idx.items() if i == eid and y == year and d == div]
    if len(matches) == 1:
        return matches[0]
    return None


def pick_edition_row(rows: list[dict], month: int | None) -> dict | None:
    if not rows:
        return None
    if month:
        for row in rows:
            try:
                m = int(float(row.get("event_month") or 0))
            except (TypeError, ValueError):
                m = 0
            if m == month:
                return row
    # Prefer a row with start_date.
    ranked = sorted(
        rows,
        key=lambda r: (0 if r.get("start_date") else 1, r.get("edition_date") or ""),
    )
    return ranked[0]


def main() -> int:
    global PIPE, REPO, OUT
    args = parse_args()
    PIPE = args.source_dir.resolve()
    REPO = args.site_repo.resolve()
    OUT = (args.output or (REPO / "static" / "data" / "event_tiers_by_year.json")).resolve()

    cards_path = require_file(REPO / "static" / "data" / "event_l2_cards.json")
    cards = json.loads(cards_path.read_text())
    continent_by_country = load_continent_by_country()
    catalog = load_catalog()
    editions_idx = load_editions()
    competition_counts = load_competition_counts()

    rows_out: list[dict] = []
    missing_geo = 0
    year_max = YEAR_FLOOR
    n_with_counts = 0

    for card in cards.get("cards", {}).values():
        eid = int(card["event_id"])
        cat = catalog.get(eid) or {}
        base_name = cat.get("canonical_name") or f"Event {eid}"
        base_city = (cat.get("typical_city") or "").strip() or None
        base_state = (cat.get("typical_state") or "").strip() or None
        base_country = (cat.get("typical_country") or "").strip() or None

        for ed in card.get("editions") or []:
            year = ed.get("year")
            if year is None or int(year) < YEAR_FLOOR:
                continue
            tiers = ed.get("tiers") or {}
            if not tiers:
                continue
            year = int(year)
            month = int(ed.get("month") or 0) or None
            year_max = max(year_max, year)

            name = base_name
            city = base_city
            state = base_state
            country = base_country
            continent = continent_by_country.get(country) if country else None

            ed_row = pick_edition_row(editions_idx.get((eid, year), []), month)
            start = (ed_row or {}).get("start_date") or None
            end = (ed_row or {}).get("end_date") or None
            # Prefer edition-level place when present.
            if ed_row:
                city = (ed_row.get("place_city") or city or "").strip() or city
                state = (ed_row.get("place_state") or state or "").strip() or state
                country = (ed_row.get("place_country") or country or "").strip() or country
                if country:
                    continent = continent_by_country.get(country) or continent
                if ed_row.get("event_name"):
                    name = ed_row["event_name"]

            if not country or not continent:
                missing_geo += 1

            state_abbr = US_STATE_ABBR.get(state) if state else None
            counts: dict[str, dict[str, int]] = {}
            for div in tiers:
                hit = lookup_counts(competition_counts, eid, year, month, div)
                if hit:
                    counts[div] = hit
            if counts:
                n_with_counts += 1

            row_out: dict = {
                "event_id": eid,
                "name": name,
                "year": year,
                "month": month,
                "start": start,
                "end": end,
                "continent": continent,
                "country": country,
                "state": state,
                "state_abbr": state_abbr,
                "city": city,
                "tiers": tiers,
            }
            if counts:
                row_out["counts"] = counts
            rows_out.append(row_out)

    rows_out.sort(key=lambda r: (r["year"], r["month"] or 0, r["name"].lower(), r["event_id"]))

    continents = sorted({r["continent"] for r in rows_out if r.get("continent")})
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "data_through": f"{year_max}-{date.today().month:02d}" if year_max == date.today().year else f"{year_max}-12",
        "year_floor": YEAR_FLOOR,
        "year_max": year_max,
        "n_editions": len(rows_out),
        "n_missing_geo": missing_geo,
        "n_editions_with_counts": n_with_counts,
        "divisions_default": ["Novice", "Intermediate", "Advanced", "All-Star"],
        "divisions_optional": ["Newcomer", "Champions"],
        "roles": ["Leader", "Follower"],
        "continents": continents,
        "tier_tip": (cards.get("tier_tip") or {}).get("en")
        or "Tier depends on the number of unique competitors in each role.",
        "editions": rows_out,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(
        f"Wrote {OUT} ({len(rows_out)} editions, years {YEAR_FLOOR}–{year_max}, "
        f"missing_geo_editions={missing_geo}, with_counts={n_with_counts})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
