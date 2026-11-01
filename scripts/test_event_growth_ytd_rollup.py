#!/usr/bin/env python3
"""Regression tests for Event Growth Monitor calendar YTD/YoY rollups.

Mirrors comparisonMode + region/KPI math in event_growth_dashboard_en.html:
open year (data_through month < 12) → both sides filtered to month <= through.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "static" / "data" / "event_growth.json"
MAPLIBRE_JS = REPO / "static" / "vendor" / "maplibre" / "maplibre-gl.js"
GEO_COUNTRIES = REPO / "static" / "data" / "geo" / "countries.geojson"
GEO_STATES = REPO / "static" / "data" / "geo" / "us_states.geojson"


def edition_month(e: dict) -> int | None:
    if e.get("month") is not None:
        try:
            return int(e["month"])
        except (TypeError, ValueError):
            pass
    start = e.get("start")
    if start and len(str(start)) >= 7:
        try:
            return int(str(start)[5:7])
        except ValueError:
            return None
    return None


def comparison_mode(
    year: int,
    data_through: str,
    years: list[int] | None = None,
) -> dict:
    """Mirrors dashboard comparisonMode: first year in `years` has no prior."""
    parts = str(data_through).split("-")
    through_year = int(parts[0]) if parts and parts[0].isdigit() else None
    through_month = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    mode = "yoy"
    if (
        through_year is not None
        and year == through_year
        and through_month is not None
        and through_month < 12
    ):
        mode = "ytd"
    candidate_prior = year - 1
    if years is not None and candidate_prior not in years:
        prior_year = None
    else:
        prior_year = candidate_prior
    return {
        "mode": mode,
        "year": year,
        "prior_year": prior_year,
        "through_month": through_month if mode == "ytd" else None,
    }


def in_window(e: dict, mode: dict) -> bool:
    if mode["mode"] != "ytd" or mode["through_month"] is None:
        return True
    m = edition_month(e)
    if m is None:
        return True
    return m <= mode["through_month"]


def rollup(
    editions: list[dict],
    year: int,
    country: str,
    data_through: str,
    years: list[int] | None = None,
) -> dict:
    mode = comparison_mode(year, data_through, years=years)
    cur = [
        e
        for e in editions
        if e.get("year") == year and e.get("country") == country and in_window(e, mode)
    ]
    if mode["prior_year"] is None:
        prior: list[dict] = []
    else:
        prior = [
            e
            for e in editions
            if e.get("year") == mode["prior_year"]
            and e.get("country") == country
            and in_window(e, mode)
        ]
    current = sum(int(e.get("competitors") or 0) for e in cur)
    previous = sum(int(e.get("competitors") or 0) for e in prior)
    if mode["prior_year"] is None:
        delta = None
        pct = None
    else:
        delta = current - previous
        pct = (delta / previous) if previous else None
    return {
        "mode": mode["mode"],
        "events": len(cur),
        "events_prior": len(prior),
        "current": current,
        "previous": previous,
        "delta": delta,
        "pct": pct,
        "prior_year": mode["prior_year"],
    }


def test_assets_present() -> None:
    assert MAPLIBRE_JS.is_file(), f"missing MapLibre vendor: {MAPLIBRE_JS}"
    assert GEO_COUNTRIES.is_file(), f"missing {GEO_COUNTRIES}"
    assert GEO_STATES.is_file(), f"missing {GEO_STATES}"


def test_open_year_is_ytd() -> None:
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    mode = comparison_mode(2026, payload["data_through"], years=years)
    assert mode["mode"] == "ytd"
    assert mode["prior_year"] == 2025
    assert mode["through_month"] == int(str(payload["data_through"]).split("-")[1])


def test_finished_year_is_yoy() -> None:
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    mode = comparison_mode(2025, payload["data_through"], years=years)
    assert mode["mode"] == "yoy"
    assert mode["prior_year"] == 2024
    assert mode["through_month"] is None


def test_first_year_has_no_prior_baseline() -> None:
    """Dashboard must not invent year-1 when it is outside the dataset."""
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    floor = int(payload.get("year_floor") or min(years))
    assert floor in years
    mode = comparison_mode(floor, payload["data_through"], years=years)
    assert mode["prior_year"] is None
    us = rollup(payload["editions"], floor, "United States", payload["data_through"], years=years)
    assert us["prior_year"] is None
    assert us["events_prior"] == 0
    assert us["delta"] is None
    assert us["pct"] is None
    assert us["events"] > 0


def continent_for_country(editions: list[dict], country: str) -> str | None:
    for e in editions:
        if e.get("country") == country and e.get("continent"):
            return str(e["continent"])
    return None


def normalize_geo(
    editions: list[dict], *, continent: str | None, country: str | None
) -> tuple[str | None, str | None]:
    """Mirrors dashboard normalizeGeoFromData for country/continent only."""
    if not country:
        return continent, country
    expected = continent_for_country(editions, country)
    if not expected:
        return continent, None
    if not continent or continent != expected:
        return expected, country
    return continent, country


def test_mismatched_continent_corrected_from_data() -> None:
    """normalizeGeoFromData: country wins over a wrong continent in the URL."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    assert continent_for_country(editions, "Germany") == "Europe"
    # Bad URL: continent=Asia&country=Germany → correct to Europe.
    cont, ctry = normalize_geo(editions, continent="Asia", country="Germany")
    assert ctry == "Germany"
    assert cont == "Europe"
    # Orphan country fills missing continent.
    cont2, ctry2 = normalize_geo(editions, continent=None, country="Germany")
    assert (cont2, ctry2) == ("Europe", "Germany")
    # Unknown country drops the country filter.
    cont3, ctry3 = normalize_geo(editions, continent="Europe", country="Narnia")
    assert ctry3 is None


def test_us_2026_kpi_matches_region_rollup() -> None:
    """Tooltip/region Change for United States must equal US KPI delta."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    through = payload["data_through"]
    years = [int(y) for y in payload["years"]]
    us = rollup(editions, 2026, "United States", through, years=years)
    assert us["mode"] == "ytd"
    assert us["events"] == 67
    assert us["events_prior"] == 69
    assert us["current"] == 22779
    assert us["previous"] == 22302
    assert us["delta"] == 477
    assert us["pct"] is not None
    assert round(us["pct"] * 1000) == 21  # +2.1%


def region_status_from_editions(
    current: list[dict], previous_competitors: int, thr_pct: float = 0.10, thr_abs: int = 10
) -> str:
    """Mirrors buildRegions status rules for a single city/region key."""
    n = len(current)
    neu = sum(1 for e in current if e.get("status") == "new")
    restarted = sum(1 for e in current if e.get("status") == "restarted")
    current_all = sum(int(e.get("competitors") or 0) for e in current)
    previous = previous_competitors
    delta = current_all - previous
    pct = (delta / previous) if previous else None
    pair_cur = 0
    pair_prev = 0
    pair_n = 0
    for e in current:
        prev = e.get("prev") or {}
        if prev.get("competitors") is not None and e.get("delta") is not None:
            pair_n += 1
            pair_cur += int(e.get("competitors") or 0)
            pair_prev += int(prev["competitors"])
    if n > 0 and neu + restarted == n:
        return "new"
    if previous == 0 and current_all > 0:
        # Gap year for the geography: use event-pair totals when available.
        if pair_n > 0:
            previous = pair_prev
            delta = pair_cur - pair_prev
            pct = (delta / previous) if previous else None
        else:
            return "new"
    if pct is None:
        if delta > 0:
            return "new"
        if delta < 0:
            return "declining"
        return "stable"
    if abs(pct) >= thr_pct and abs(delta) >= thr_abs:
        return "growing" if delta > 0 else "declining"
    return "stable"


def test_new_cities_not_marked_growing() -> None:
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    for city in ("Ottawa", "Waterloo"):
        cur = [
            e
            for e in editions
            if e.get("year") == 2026
            and e.get("country") == "Canada"
            and e.get("city") == city
        ]
        assert cur, f"missing 2026 editions for {city}"
        assert all(e.get("status") == "new" for e in cur)
        prior = sum(
            int(e.get("competitors") or 0)
            for e in editions
            if e.get("year") == 2025
            and e.get("country") == "Canada"
            and e.get("city") == city
        )
        assert prior == 0
        assert region_status_from_editions(cur, prior) == "new"


def _geo_key(e: dict) -> tuple[str, str]:
    if e.get("country") == "United States":
        return ("US", str(e.get("state") or "?"))
    return (str(e.get("country") or "?"), str(e.get("city") or e.get("name") or "?"))


def test_indiana_2025_gap_year_not_new_when_event_declined() -> None:
    """No Indiana events in 2024, but Indy Dance Explosion declined vs 2023."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    cur = [
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("country") == "United States"
        and e.get("state") == "Indiana"
    ]
    assert len(cur) == 1
    assert cur[0].get("name") == "Indy Dance Explosion"
    assert cur[0].get("status") == "declining"
    prior = sum(
        int(e.get("competitors") or 0)
        for e in editions
        if e.get("year") == 2024
        and e.get("country") == "United States"
        and e.get("state") == "Indiana"
    )
    assert prior == 0
    assert region_status_from_editions(cur, prior) == "declining"


def test_gap_year_regions_not_new_when_events_have_pairs() -> None:
    """Calendar-empty prior year must not paint New if editions carry a prev pair.

    Catches Indiana 2025, Connecticut 2024, Sea Sun and Swing 2026, etc.
    True debuts (all new, no pairs) stay New.
    """
    from collections import defaultdict

    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    years = sorted({int(e["year"]) for e in editions})
    false_new: list[str] = []
    for year in years:
        if year - 1 not in years:
            continue
        cur_by: dict[tuple[str, str], list[dict]] = defaultdict(list)
        prior_by: dict[tuple[str, str], int] = defaultdict(int)
        for e in editions:
            key = _geo_key(e)
            if int(e["year"]) == year:
                cur_by[key].append(e)
            elif int(e["year"]) == year - 1:
                prior_by[key] += int(e.get("competitors") or 0)
        for key, cur in cur_by.items():
            prior = prior_by.get(key, 0)
            if prior != 0:
                continue
            status = region_status_from_editions(cur, prior)
            has_pair = any(
                (e.get("prev") or {}).get("competitors") is not None
                and e.get("delta") is not None
                for e in cur
            )
            if has_pair and status == "new":
                false_new.append(f"{year} {key[0]}/{key[1]}")
            if not has_pair and all(e.get("status") in ("new", "restarted") for e in cur):
                assert status == "new", f"{year} {key} should stay New"
    assert false_new == [], f"gap-year regions still New despite pairs: {false_new}"


def status_pill_pair_rollup(editions: list[dict], year: int, country: str, status: str) -> dict:
    """Mirrors status-pill KPI: selected events vs their own previous editions."""
    cur = [
        e
        for e in editions
        if e.get("year") == year
        and e.get("country") == country
        and (e.get("status") == status or (status == "new" and e.get("status") == "restarted"))
    ]
    total = sum(int(e.get("competitors") or 0) for e in cur)
    pair_cur = 0
    pair_prev = 0
    pairs = 0
    for e in cur:
        prev = e.get("prev") or {}
        if prev.get("competitors") is not None and e.get("delta") is not None:
            pairs += 1
            pair_cur += int(e.get("competitors") or 0)
            pair_prev += int(prev["competitors"])
    delta = (pair_cur - pair_prev) if pairs else None
    pct = (delta / pair_prev) if pairs and pair_prev else None
    return {
        "events": len(cur),
        "total": total,
        "pairs": pairs,
        "delta": delta,
        "pct": pct,
    }


def test_growing_pill_uses_event_pairs_not_prior_status() -> None:
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    us = status_pill_pair_rollup(editions, 2026, "United States", "growing")
    assert us["events"] > 0
    assert us["pairs"] == us["events"]  # growing editions always have a prior
    assert us["delta"] is not None
    assert us["pct"] is not None
    # Delta must equal sum(current) - sum(e.prev) for the selected growing set —
    # not a calendar total of whatever was "growing" in the prior year.
    growing = [
        e
        for e in editions
        if e.get("year") == 2026
        and e.get("country") == "United States"
        and e.get("status") == "growing"
    ]
    pair_cur = sum(int(e.get("competitors") or 0) for e in growing)
    pair_prev = sum(int(e["prev"]["competitors"]) for e in growing)
    assert us["total"] == pair_cur
    assert us["delta"] == pair_cur - pair_prev
    prior_year_growing_total = sum(
        int(e.get("competitors") or 0)
        for e in editions
        if e.get("year") == 2025
        and e.get("country") == "United States"
        and e.get("status") == "growing"
    )
    assert pair_prev != prior_year_growing_total


def test_new_pill_has_no_pct() -> None:
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    us = status_pill_pair_rollup(editions, 2026, "United States", "new")
    assert us["events"] >= 1
    assert us["pairs"] == 0
    assert us["delta"] is None
    assert us["pct"] is None
    assert us["total"] > 0


def test_symmetric_window_excludes_late_prior_only() -> None:
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    mode = comparison_mode(2026, payload["data_through"])
    assert mode["through_month"] == 10
    late_2025 = [
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("country") == "United States"
        and not in_window(e, mode)
    ]
    assert late_2025, "expected some US 2025 editions after data_through month"
    # Current 2026 US editions are all inside the window with this snapshot.
    late_2026 = [
        e
        for e in editions
        if e.get("year") == 2026
        and e.get("country") == "United States"
        and not in_window(e, mode)
    ]
    assert late_2026 == []


def test_edition_field_asia_open_full_history() -> None:
    """edition is baked from event_editions.csv (1991+), not year_floor window."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    asia_2023 = next(
        e
        for e in editions
        if e.get("event_id") == 218 and e.get("year") == 2023
    )
    assert asia_2023.get("status") == "restarted"
    assert asia_2023.get("edition") == 8
    asia_2018 = next(
        e
        for e in editions
        if e.get("event_id") == 218 and e.get("year") == 2018
    )
    assert asia_2018.get("edition") == 6
    assert asia_2018.get("status") != "new"


def test_edition_field_paris_resets_on_swing_classic_era() -> None:
    """Paris Swing Classic (≥2023) does not continue Westie Fest #N."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    pwf_2020 = next(
        e for e in editions if e.get("event_id") == 272 and e.get("year") == 2020
    )
    psc_2023 = next(
        e for e in editions if e.get("event_id") == 272 and e.get("year") == 2023
    )
    psc_2026 = next(
        e for e in editions if e.get("event_id") == 272 and e.get("year") == 2026
    )
    assert pwf_2020.get("name") == "Paris Westie Fest"
    assert psc_2023.get("name") == "Paris Swing Classic"
    assert pwf_2020.get("edition") == 4  # 2017–2020
    assert psc_2023.get("edition") == 1
    assert psc_2026.get("edition") == 4  # 2023–2026
    # First PSC edition is a debut — not a restart vs Westie Fest 2020.
    assert psc_2023.get("status") == "new"
    assert psc_2023.get("prev") is None
    assert psc_2023.get("delta") is None


def test_edition_field_present_and_positive() -> None:
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    missing = [e for e in editions if not e.get("edition")]
    assert not missing, f"{len(missing)} editions missing edition ordinal"
    assert all(int(e["edition"]) >= 1 for e in editions)
    # year_floor rows are not all debuts once full history is applied
    floor = payload.get("year_floor", 2018)
    at_floor = [e for e in editions if e.get("year") == floor]
    assert any(int(e["edition"]) > 1 for e in at_floor)


def test_edition_enrichment_meta() -> None:
    payload = json.loads(DATA.read_text())
    meta = payload.get("edition_enrichment") or {}
    assert meta.get("source") == "event_editions.csv"
    stats = meta.get("stats") or {}
    assert stats.get("with_history", 0) == payload.get("n_editions")
    splits = meta.get("series_splits") or []
    split_ids = {int(s["event_id"]) for s in splits if s.get("event_id") is not None}
    assert 272 in split_ids
    # Loaded from pipeline reset_edition_ordinal flags (not GGP 342).
    assert 221 in split_ids
    assert 342 not in split_ids


if __name__ == "__main__":
    test_assets_present()
    test_open_year_is_ytd()
    test_finished_year_is_yoy()
    test_first_year_has_no_prior_baseline()
    test_mismatched_continent_corrected_from_data()
    test_us_2026_kpi_matches_region_rollup()
    test_new_cities_not_marked_growing()
    test_indiana_2025_gap_year_not_new_when_event_declined()
    test_gap_year_regions_not_new_when_events_have_pairs()
    test_growing_pill_uses_event_pairs_not_prior_status()
    test_new_pill_has_no_pct()
    test_symmetric_window_excludes_late_prior_only()
    test_edition_field_asia_open_full_history()
    test_edition_field_paris_resets_on_swing_classic_era()
    test_edition_field_present_and_positive()
    test_edition_enrichment_meta()
    print("OK")
