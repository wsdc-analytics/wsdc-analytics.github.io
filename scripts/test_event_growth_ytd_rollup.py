#!/usr/bin/env python3
"""Regression tests for Event Trends Monitor calendar YTD/YoY rollups.

Mirrors comparisonMode + region/KPI math in event_growth_dashboard_en.html:
open year → YTD with closed months full; open data_through month matched by
event_id while as_of is still inside that month.
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
    as_of: str | None = None,
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

    as_of_year = as_of_month = None
    if as_of and len(str(as_of)) >= 7:
        ap = str(as_of).split("-")
        if len(ap) >= 2 and ap[0].isdigit() and ap[1].isdigit():
            as_of_year = int(ap[0])
            as_of_month = int(ap[1])

    open_month_is_partial = False
    if mode == "ytd" and through_month is not None and through_year is not None:
        if as_of_year is None or as_of_month is None:
            open_month_is_partial = True
        elif as_of_year < through_year or (
            as_of_year == through_year and as_of_month <= through_month
        ):
            open_month_is_partial = True

    return {
        "mode": mode,
        "year": year,
        "prior_year": prior_year,
        "through_month": through_month if mode == "ytd" else None,
        "through_year": through_year,
        "as_of": as_of,
        "open_month_is_partial": open_month_is_partial,
    }


def in_window(e: dict, mode: dict) -> bool:
    if mode["mode"] != "ytd" or mode["through_month"] is None:
        return True
    m = edition_month(e)
    if m is None:
        return True
    return m <= mode["through_month"]


def open_month_event_ids(current_rows: list[dict], mode: dict) -> set[int]:
    through = mode.get("through_month")
    if through is None:
        return set()
    ids: set[int] = set()
    for e in current_rows:
        if edition_month(e) == through and e.get("event_id") is not None:
            ids.add(int(e["event_id"]))
    return ids


def in_prior_window(e: dict, mode: dict, open_ids: set[int] | None) -> bool:
    if mode["mode"] != "ytd" or mode["through_month"] is None:
        return True
    m = edition_month(e)
    if m is None:
        return True
    through = mode["through_month"]
    if not mode.get("open_month_is_partial"):
        return m <= through
    if m < through:
        return True
    if m == through or m == through + 1:
        return e.get("event_id") is not None and int(e["event_id"]) in (open_ids or set())
    return False


def filter_prior_rows(
    prior_rows: list[dict], current_rows: list[dict], mode: dict
) -> list[dict]:
    open_ids = (
        open_month_event_ids(current_rows, mode)
        if mode.get("open_month_is_partial")
        else None
    )
    return [e for e in prior_rows if in_prior_window(e, mode, open_ids)]


def rollup(
    editions: list[dict],
    year: int,
    country: str | None,
    data_through: str,
    years: list[int] | None = None,
    as_of: str | None = None,
    *,
    continent: str | None = None,
) -> dict:
    mode = comparison_mode(year, data_through, years=years, as_of=as_of)

    def scope_match(e: dict) -> bool:
        if continent is not None and e.get("continent") != continent:
            return False
        if country is not None and e.get("country") != country:
            return False
        return True

    cur = [
        e
        for e in editions
        if e.get("year") == year and scope_match(e) and in_window(e, mode)
    ]
    if mode["prior_year"] is None:
        prior: list[dict] = []
    else:
        prior_base = [
            e
            for e in editions
            if e.get("year") == mode["prior_year"] and scope_match(e)
        ]
        prior = filter_prior_rows(prior_base, cur, mode)
    current = sum(int(e.get("competitors") or 0) for e in cur)
    previous = sum(int(e.get("competitors") or 0) for e in prior)
    if mode["prior_year"] is None:
        delta = None
        pct = None
    else:
        delta = current - previous
        pct = (delta / previous) if previous else None
    avg = (current / len(cur)) if cur else None
    avg_prior = (previous / len(prior)) if prior else None
    if mode["prior_year"] is None or avg is None or avg_prior is None:
        avg_delta = None
        avg_pct = None
    else:
        avg_delta = avg - avg_prior
        avg_pct = (avg_delta / avg_prior) if avg_prior else None
    return {
        "mode": mode["mode"],
        "open_month_is_partial": mode["open_month_is_partial"],
        "events": len(cur),
        "events_prior": len(prior),
        "current": current,
        "previous": previous,
        "delta": delta,
        "pct": pct,
        "avg": avg,
        "avg_prior": avg_prior,
        "avg_delta": avg_delta,
        "avg_pct": avg_pct,
        "prior_year": mode["prior_year"],
        "open_ids": sorted(open_month_event_ids(cur, mode))
        if mode.get("open_month_is_partial")
        else [],
    }


def test_assets_present() -> None:
    assert MAPLIBRE_JS.is_file(), f"missing MapLibre vendor: {MAPLIBRE_JS}"
    assert GEO_COUNTRIES.is_file(), f"missing {GEO_COUNTRIES}"
    assert GEO_STATES.is_file(), f"missing {GEO_STATES}"


def test_open_year_is_ytd() -> None:
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    mode = comparison_mode(
        2026, payload["data_through"], years=years, as_of=payload.get("as_of")
    )
    assert mode["mode"] == "ytd"
    assert mode["prior_year"] == 2025
    assert mode["through_month"] == int(str(payload["data_through"]).split("-")[1])
    assert mode["open_month_is_partial"] is True


def test_finished_year_is_yoy() -> None:
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    mode = comparison_mode(
        2025, payload["data_through"], years=years, as_of=payload.get("as_of")
    )
    assert mode["mode"] == "yoy"
    assert mode["prior_year"] == 2024
    assert mode["through_month"] is None
    assert mode["open_month_is_partial"] is False


def test_first_year_has_no_prior_baseline() -> None:
    """Dashboard must not invent year-1 when it is outside the dataset."""
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    floor = int(payload.get("year_floor") or min(years))
    assert floor in years
    mode = comparison_mode(
        floor, payload["data_through"], years=years, as_of=payload.get("as_of")
    )
    assert mode["prior_year"] is None
    us = rollup(
        payload["editions"],
        floor,
        "United States",
        payload["data_through"],
        years=years,
        as_of=payload.get("as_of"),
    )
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
    us = rollup(
        editions, 2026, "United States", through, years=years, as_of=payload.get("as_of")
    )
    assert us["mode"] == "ytd"
    assert us["open_month_is_partial"] is True
    # YTD snapshot drifts as as_of / calendar refresh adds closed US weekends.
    assert us["events"] == 69
    assert us["events_prior"] == 70
    assert us["current"] == 23188
    assert us["previous"] == 22529
    assert us["delta"] == 659
    assert us["pct"] is not None
    assert round(us["pct"] * 1000) == 29  # +2.9%


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
    # All new/restarted only forces New when the geography had no prior total.
    if n > 0 and neu + restarted == n and previous == 0:
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


def test_true_debut_cities_stay_new() -> None:
    """Cities with no prior-window events stay New even if all editions are new."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    for city in ("Waterloo",):
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


def test_ottawa_2026_series_swap_is_growing_not_new() -> None:
    """Ottawa hosted BTO in 2025; 2026 Swing in Bloom is new series but city grows."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    cur = [
        e
        for e in editions
        if e.get("year") == 2026
        and e.get("country") == "Canada"
        and e.get("city") == "Ottawa"
    ]
    assert len(cur) == 1
    assert cur[0].get("name") == "Swing in Bloom"
    assert cur[0].get("status") == "new"
    prior = sum(
        int(e.get("competitors") or 0)
        for e in editions
        if e.get("year") == 2025
        and e.get("country") == "Canada"
        and e.get("city") == "Ottawa"
    )
    assert prior == 222  # BTO Open 2025
    assert sum(int(e.get("competitors") or 0) for e in cur) == 270
    assert region_status_from_editions(cur, prior) == "growing"


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
    mode = comparison_mode(
        2026, payload["data_through"], as_of=payload.get("as_of")
    )
    through = mode["through_month"]
    assert through is not None and 1 <= through < 12
    late_2025 = [
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("country") == "United States"
        and not in_window(e, mode)
    ]
    # With through_month in mid/late year there are Dec (or later) US priors.
    if through < 12:
        assert any(
            edition_month(e) is not None and edition_month(e) > through for e in editions
            if e.get("year") == 2025
        ) or late_2025 or through >= 11
    late_2026 = [
        e
        for e in editions
        if e.get("year") == 2026
        and e.get("country") == "United States"
        and not in_window(e, mode)
    ]
    assert late_2026 == []


def test_open_month_matches_prior_by_event_id() -> None:
    """Europe open month: only Warsaw's prior counts; other Nov 2025 held out."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    years = [int(y) for y in payload["years"]]
    through = int(str(payload["data_through"]).split("-")[1])
    eu = rollup(
        editions,
        2026,
        None,
        payload["data_through"],
        years=years,
        as_of=payload.get("as_of"),
        continent="Europe",
    )
    assert eu["mode"] == "ytd"
    assert eu["open_month_is_partial"] is True
    assert eu["open_ids"] == [236]  # Warsaw Halloween Swing

    # Unmatched prior open-month Europe editions must not enter the prior sum.
    unmatched = [
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("continent") == "Europe"
        and edition_month(e) == through
        and int(e["event_id"]) not in eu["open_ids"]
    ]
    assert len(unmatched) >= 1
    unmatched_sum = sum(int(e.get("competitors") or 0) for e in unmatched)

    # Full prior (old year-to-month) would include unmatched; matched must not.
    mode_full = comparison_mode(
        2026, payload["data_through"], years=years, as_of="2026-12-01"
    )
    assert mode_full["open_month_is_partial"] is False
    prior_full = [
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("continent") == "Europe"
        and in_window(e, mode_full)
    ]
    prior_full_sum = sum(int(e.get("competitors") or 0) for e in prior_full)
    assert eu["previous"] == prior_full_sum - unmatched_sum

    warsaw_prior = next(
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("event_id") == 236
        and e.get("continent") == "Europe"
    )
    assert edition_month(warsaw_prior) == through
    # Matched prior includes Warsaw; closed months keep the rest.
    assert eu["previous"] >= int(warsaw_prior["competitors"])


def test_open_month_closes_when_as_of_moves_past() -> None:
    """After as_of leaves data_through month, prior open month is full again."""
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    years = [int(y) for y in payload["years"]]
    through = payload["data_through"]
    partial = rollup(
        editions,
        2026,
        None,
        through,
        years=years,
        as_of=payload.get("as_of"),
        continent="Europe",
    )
    closed = rollup(
        editions,
        2026,
        None,
        through,
        years=years,
        as_of="2026-12-01",
        continent="Europe",
    )
    assert partial["open_month_is_partial"] is True
    assert closed["open_month_is_partial"] is False
    assert closed["events"] == partial["events"]
    assert closed["current"] == partial["current"]
    assert closed["events_prior"] > partial["events_prior"]
    assert closed["previous"] > partial["previous"]


def test_australia_open_month_holds_unmatched_prior() -> None:
    payload = json.loads(DATA.read_text())
    editions = payload["editions"]
    years = [int(y) for y in payload["years"]]
    au = rollup(
        editions,
        2026,
        "Australia",
        payload["data_through"],
        years=years,
        as_of=payload.get("as_of"),
    )
    assert au["open_month_is_partial"] is True
    assert au["open_ids"] == []
    # Simply Adelaide (2025-11) held out until matched or month closes.
    adelaide_prior = [
        e
        for e in editions
        if e.get("year") == 2025
        and e.get("country") == "Australia"
        and e.get("event_id") == 330
    ]
    assert adelaide_prior
    assert edition_month(adelaide_prior[0]) == int(
        str(payload["data_through"]).split("-")[1]
    )
    closed = rollup(
        editions,
        2026,
        "Australia",
        payload["data_through"],
        years=years,
        as_of="2026-12-01",
    )
    assert closed["previous"] == au["previous"] + int(adelaide_prior[0]["competitors"])


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


def test_avg_per_event_is_sum_over_count() -> None:
    """Mirrors dashboard Avg / event = Σ competitors ÷ N events."""
    payload = json.loads(DATA.read_text())
    years = [int(y) for y in payload["years"]]
    us = rollup(
        payload["editions"],
        2025,
        "United States",
        payload["data_through"],
        years=years,
        as_of=payload.get("as_of"),
    )
    assert us["events"] > 0
    assert us["avg"] is not None
    assert abs(us["avg"] - (us["current"] / us["events"])) < 1e-9
    if us["events_prior"]:
        assert us["avg_prior"] is not None
        assert us["avg_delta"] is not None
        assert abs(us["avg_delta"] - (us["avg"] - us["avg_prior"])) < 1e-9


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
    assert 177 in split_ids  # River City Swing → Jax Westie Fest
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
    test_open_month_matches_prior_by_event_id()
    test_open_month_closes_when_as_of_moves_past()
    test_australia_open_month_holds_unmatched_prior()
    test_edition_field_asia_open_full_history()
    test_avg_per_event_is_sum_over_count()
    test_edition_field_paris_resets_on_swing_classic_era()
    test_edition_field_present_and_positive()
    test_edition_enrichment_meta()
    print("OK")
