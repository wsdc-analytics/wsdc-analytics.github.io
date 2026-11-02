#!/usr/bin/env python3
"""Unit tests for audit_event_growth_venues (no network)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_event_growth_venue_overrides import apply_overrides  # noqa: E402
from audit_event_growth_venues import (  # noqa: E402
    build_groups,
    cache_key,
    classify,
    name_overlap,
    override_eligible,
    run,
    write_outputs,
)

# Jenavi, Bolshoy Smolensky pr. 12 — registry pins from three different years.
JENAVI = (59.8986, 30.419985)
CITY_CENTRE = (59.95, 30.31667)
NORTH = (60.035663, 30.336236)


def _ed(
    year,
    lat,
    lon,
    hotel="Jenavi",
    source="wsdc_venue",
    address="Bolshoy Smolenskiy, 12",
    city_lat=CITY_CENTRE[0],
    city_lon=CITY_CENTRE[1],
):
    return {
        "event_id": 280,
        "name": "Saint Petersburg WCS Nights",
        "year": year,
        "city": "St. Petersburg",
        "country": "Russia",
        "hotel": hotel,
        "address": address,
        "lat": lat,
        "lon": lon,
        "city_lat": city_lat,
        "city_lon": city_lon,
        "geo_source": source,
    }


def _hit(lat, lon, name="Jenavi Club Hotel", api="places"):
    return {"api": api, "name": name, "address": "Bolshoy Smolensky pr., 12", "lat": lat, "lon": lon}


def test_build_groups_merges_hotel_spellings_and_skips_city_rows() -> None:
    eds = [
        _ed(2018, *JENAVI),
        _ed(2021, *CITY_CENTRE, hotel="Jenavi hotel"),
        _ed(2022, *NORTH, hotel="Jenavi Hotel"),
        _ed(2020, *CITY_CENTRE, source="city"),
    ]
    groups = build_groups(eds)
    assert len(groups) == 1
    g = groups[0]
    assert sorted(g.points) == [2018, 2021, 2022]
    assert g.spread_km > 10
    assert "Jenavi" in g.query() and "St. Petersburg" in g.query()


def test_build_groups_backfills_city_coords_from_later_edition() -> None:
    eds = [
        _ed(2018, *JENAVI, city_lat=None, city_lon=None),
        _ed(2019, *JENAVI),
    ]
    g = build_groups(eds)[0]
    assert g.city_lat == CITY_CENTRE[0]
    assert g.city_lon == CITY_CENTRE[1]


def test_build_groups_skips_placeholder_hotels() -> None:
    assert build_groups([_ed(2024, *JENAVI, hotel="TBD")]) == []
    assert build_groups([_ed(2024, *JENAVI, hotel="HIATUS")]) == []


def test_classify_flags_years_that_drift_from_google() -> None:
    g = build_groups([_ed(2018, *JENAVI), _ed(2021, *CITY_CENTRE)])[0]
    c = classify(g, _hit(*JENAVI))
    assert c["verdict"] == "fix_some_years"
    assert c["dist_by_year"][2018] < 0.01
    assert c["dist_by_year"][2021] > 4
    assert c["years_to_fix"] == [2021]


def test_classify_ok_and_fix_all() -> None:
    g = build_groups([_ed(2018, *JENAVI), _ed(2019, *JENAVI)])[0]
    assert classify(g, _hit(*JENAVI))["verdict"] == "ok"
    assert classify(g, _hit(*NORTH))["verdict"] == "fix_all_years"


def test_classify_places_weak_name_even_when_close() -> None:
    g = build_groups([_ed(2018, *JENAVI)])[0]
    c = classify(g, _hit(*JENAVI, name="Completely Different Hostel"))
    assert c["verdict"] == "check_weak_match"
    assert not override_eligible(c)


def test_classify_needs_review_for_weak_or_far_hits() -> None:
    g = build_groups([_ed(2018, *JENAVI)])[0]
    assert classify(g, None)["verdict"] == "not_found"
    # Geocode with hotel tokens in formatted address can still be ok.
    geo_ok = _hit(*JENAVI, api="geocode", name="")
    geo_ok["address"] = "Jenavi Club, Bolshoy Smolensky pr., 12"
    assert classify(g, geo_ok)["verdict"] == "ok"
    # Weak geocode name/address → review, even when a street is present.
    assert classify(g, _hit(*JENAVI, api="geocode", name=""))["verdict"] == "check_weak_match"
    assert classify(g, _hit(55.75, 37.62))["verdict"] == "check_google_far_from_city"


def test_name_overlap_ignores_generic_words() -> None:
    assert name_overlap("Jenavi club hotel", "Jenavi") == 1.0
    assert name_overlap("Azimut City Hotel St.Petersburg", "AZIMUT City Hotel Saint Petersburg") >= 0.5
    # Short Places label must still match the longer registry hotel string.
    assert name_overlap("Azimut City hotel St.Petersburg", "AZIMUT") >= 0.5
    assert name_overlap("Jenavi", "Completely Different Hostel") < 0.5


def test_run_uses_cache_and_write_outputs(tmp_path: Path) -> None:
    groups = build_groups([_ed(2018, *JENAVI), _ed(2021, *CITY_CENTRE)])
    calls = []

    def fake_lookup(g):
        calls.append(g.query())
        return _hit(*JENAVI)

    cache = {}
    run(groups, fake_lookup, cache)
    rows = run(groups, fake_lookup, cache)
    assert len(calls) == 1

    counts = write_outputs(rows, tmp_path)
    assert counts == {"fix_some_years": 1}
    with (tmp_path / "venue_audit.csv").open(encoding="utf-8") as fh:
        report = list(csv.DictReader(fh))
    assert report[0]["verdict"] == "fix_some_years"
    assert report[0]["years_to_fix"] == "2021"
    assert "google.com/maps" in report[0]["google_link"]
    overrides = json.loads((tmp_path / "proposed_overrides.json").read_text(encoding="utf-8"))
    assert overrides[0]["event_id"] == 280
    assert overrides[0]["years"] == [2018, 2021]
    assert overrides[0]["years_to_fix"] == [2021]
    assert overrides[0]["verdict"] == "fix_some_years"
    assert overrides[0]["name_match"] >= 0.5


def test_write_outputs_excludes_check_verdicts(tmp_path: Path) -> None:
    g = build_groups([_ed(2018, *JENAVI)])[0]
    rows = [(g, _hit(55.75, 37.62), classify(g, _hit(55.75, 37.62)))]
    write_outputs(rows, tmp_path)
    overrides = json.loads((tmp_path / "proposed_overrides.json").read_text(encoding="utf-8"))
    assert overrides == []


def test_run_cached_null_is_not_found() -> None:
    groups = build_groups([_ed(2018, *JENAVI)])
    rows = run(groups, None, {cache_key(groups[0]): None})
    assert rows[0][2]["verdict"] == "not_found"


def test_run_refetches_corrupt_cache() -> None:
    groups = build_groups([_ed(2018, *JENAVI)])
    calls = []

    def fake_lookup(g):
        calls.append(g.event_id)
        return _hit(*JENAVI)

    rows = run(groups, fake_lookup, {cache_key(groups[0]): {"api": "places"}})
    assert len(calls) == 1
    assert rows[0][2]["verdict"] == "ok"


def test_override_eligible_requires_city_centroid() -> None:
    g = build_groups([_ed(2018, *CITY_CENTRE, city_lat=None, city_lon=None)])[0]
    c = classify(g, _hit(*JENAVI))
    assert c["verdict"] == "fix_all_years"
    assert c["google_city_km"] is None
    assert not override_eligible(c)


def test_run_without_lookup_marks_not_looked_up() -> None:
    groups = build_groups([_ed(2018, *JENAVI)])
    rows = run(groups, None, {})
    assert rows[0][2]["verdict"] == "not_looked_up"


def test_apply_overrides_only_patches_years_to_fix() -> None:
    editions = [
        _ed(2018, *JENAVI),
        _ed(2021, *CITY_CENTRE),
    ]
    overrides = [{
        "event_id": 280,
        "hotel_key": "jenavi",
        "hotel": "Jenavi",
        "verdict": "fix_some_years",
        "lat": JENAVI[0],
        "lon": JENAVI[1],
        "name_match": 1.0,
        "years_to_fix": [2021],
        "google_name": "Jenavi Club Hotel",
        "place_id": "abc",
    }]
    stats = apply_overrides(editions, overrides)
    assert stats["editions_patched"] == 1
    assert editions[0]["lat"] == JENAVI[0]  # untouched
    assert abs(editions[1]["lat"] - JENAVI[0]) < 1e-6
    assert editions[1]["geo_fix"] == "google_audit"
    assert editions[1]["google_place_id"] == "abc"


if __name__ == "__main__":
    import inspect
    import tempfile

    for name, fn in list(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        params = inspect.signature(fn).parameters
        if "tmp_path" in params:
            with tempfile.TemporaryDirectory() as td:
                fn(Path(td))
        else:
            fn()
        print("ok", name)
    print("all passed")
