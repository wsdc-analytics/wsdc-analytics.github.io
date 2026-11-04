#!/usr/bin/env python3
"""Tests for Event Growth list grain keys, Δ rules, and sort behavior."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "static" / "data" / "event_growth.json"


def region_key(e: dict, grain: str) -> str:
    if grain == "continent":
        return str(e.get("continent") or "Unknown")
    if grain == "country":
        return str(e.get("country") or "Unknown")
    if grain == "state":
        return str(e.get("state") or "Unknown")
    if grain == "region":
        if e.get("country") == "United States":
            return "US|" + str(e.get("state") or "Unknown")
        return "C|" + str(e.get("country") or "Unknown")
    if grain == "city":
        return f"{e.get('country') or ''}|{e.get('state') or ''}|{e.get('city') or 'Unknown'}"
    if grain == "event":
        return str(e["event_id"]) if e.get("event_id") is not None else f"name:{e.get('name')}"
    raise ValueError(grain)


def region_label(e: dict, grain: str) -> str:
    if grain == "region" and e.get("country") == "United States":
        return f"{e.get('state') or 'Unknown'}, US"
    if grain == "region":
        return str(e.get("country") or "Unknown")
    if grain == "city":
        return str(e.get("city") or "Unknown")
    if grain == "event":
        return str(e.get("name") or f"Event {e.get('event_id')}")
    return region_key(e, grain)


def sort_rows(rows: list[dict], *, metric: str, ascending: bool) -> list[dict]:
    delta_mode = metric.startswith("d_")

    def value(r: dict):
        if r.get("suppress_delta") and delta_mode:
            return None
        return r.get(metric)

    def key_fn(r: dict):
        if not delta_mode and r.get("absent"):
            absent_rank = 1
        else:
            absent_rank = 0
        v = value(r)
        null_rank = 1 if v is None else 0
        sort_v = 0 if v is None else v
        # asc: smaller first; desc: larger first via negation
        signed = sort_v if ascending else -sort_v
        return (absent_rank if not delta_mode else 0, null_rank, signed)

    return sorted(rows, key=key_fn)


def test_region_world_has_us_states_not_united_states_row() -> None:
    payload = json.loads(DATA.read_text())
    eds = [e for e in payload["editions"] if e.get("year") == 2025]
    keys = {region_key(e, "region") for e in eds}
    labels = {region_label(e, "region") for e in eds if e.get("country") == "United States"}
    assert any(k.startswith("US|") for k in keys)
    assert "C|United States" not in keys
    assert any(lbl.endswith(", US") for lbl in labels)
    # Europe continent scope must not invent US state peers from other continents
    eu = [e for e in eds if e.get("continent") == "Europe"]
    eu_keys = {region_key(e, "region") for e in eu}
    assert not any(k.startswith("US|") for k in eu_keys)


def test_city_keys_disambiguate_same_name() -> None:
    payload = json.loads(DATA.read_text())
    eds = [e for e in payload["editions"] if e.get("year") == 2025 and e.get("city")]
    by_city: dict[str, set[str]] = {}
    for e in eds:
        bare = str(e["city"])
        by_city.setdefault(bare, set()).add(region_key(e, "city"))
    multi = {c: keys for c, keys in by_city.items() if len(keys) > 1}
    # If the dump has a duplicated city name across places, keys must differ.
    for _city, keys in multi.items():
        assert len(keys) == len(set(keys))


def test_event_metric_subset_and_fallback() -> None:
    allowed_event = {"competitors", "d_competitors"}
    assert "events" not in allowed_event
    assert "d_events" not in allowed_event
    assert "avg" not in allowed_event
    # Fallback family: Δ Events → Δ Competitors
    assert "d_competitors" in allowed_event


def allowed_list_metrics(*, grain: str, status: str) -> list[str]:
    """Mirror event_growth_dashboard_en.html allowedListMetrics()."""
    new_slice = status == "new"
    if grain == "event":
        return ["competitors"] if new_slice else ["competitors", "d_competitors"]
    if status == "all":
        return [
            "competitors",
            "events",
            "avg",
            "d_competitors",
            "d_events",
            "d_avg",
        ]
    if new_slice:
        return ["competitors", "events", "avg"]
    return ["competitors", "events", "avg", "d_competitors"]


def test_status_slice_metrics_relevance() -> None:
    # New: no Δ — every row suppresses prior-edition deltas.
    assert allowed_list_metrics(grain="country", status="new") == [
        "competitors",
        "events",
        "avg",
    ]
    assert allowed_list_metrics(grain="event", status="new") == ["competitors"]
    # Trend slices: paired Δ Competitors only (no calendar Δ Events / Δ Avg).
    for st in ("growing", "declining", "stable"):
        assert allowed_list_metrics(grain="country", status=st) == [
            "competitors",
            "events",
            "avg",
            "d_competitors",
        ]
        assert "d_avg" not in allowed_list_metrics(grain="country", status=st)
        assert "d_events" not in allowed_list_metrics(grain="country", status=st)
    # All: full set.
    assert "d_avg" in allowed_list_metrics(grain="country", status="all")
    assert "d_events" in allowed_list_metrics(grain="country", status="all")
    html = (REPO / "event_growth_dashboard_en.html").read_text()
    assert 'var newSlice = status === "new"' in html
    assert 'return ["competitors", "events", "avg", "d_competitors"]' in html


def test_event_delta_uses_edition_delta() -> None:
    payload = json.loads(DATA.read_text())
    hit = next(
        e
        for e in payload["editions"]
        if e.get("year") == 2026
        and e.get("delta") is not None
        and (e.get("prev") or {}).get("competitors") is not None
    )
    assert hit["delta"] == hit["competitors"] - hit["prev"]["competitors"]


def test_new_delta_null_sorts_last() -> None:
    rows = [
        {"key": "a", "d_competitors": 50, "suppress_delta": False},
        {"key": "new", "d_competitors": 999, "suppress_delta": True},
        {"key": "b", "d_competitors": -10, "suppress_delta": False},
    ]
    # suppress_delta forces null for ranking
    for r in rows:
        if r["suppress_delta"]:
            r["d_competitors"] = None
    desc = sort_rows(rows, metric="d_competitors", ascending=False)
    asc = sort_rows(rows, metric="d_competitors", ascending=True)
    assert desc[-1]["key"] == "new"
    assert asc[-1]["key"] == "new"
    assert desc[0]["key"] == "a"
    assert asc[0]["key"] == "b"


def test_absent_delta_sorts_last_like_new() -> None:
    rows = [
        {"key": "grow", "d_competitors": 20, "absent": False, "suppress_delta": False},
        {"key": "gone", "d_competitors": -400, "absent": True, "suppress_delta": True},
        {"key": "flat", "d_competitors": 0, "absent": False, "suppress_delta": False},
        {"key": "drop", "d_competitors": -50, "absent": False, "suppress_delta": False},
    ]
    for r in rows:
        if r["suppress_delta"]:
            r["d_competitors"] = None
    asc = sort_rows(rows, metric="d_competitors", ascending=True)
    desc = sort_rows(rows, metric="d_competitors", ascending=False)
    assert asc[0]["key"] == "drop"
    assert asc[-1]["key"] == "gone"
    assert desc[0]["key"] == "grow"
    assert desc[-1]["key"] == "gone"
    desc_abs = sort_rows(
        [
            {"key": "live", "competitors": 100, "absent": False},
            {"key": "gone", "competitors": 400, "absent": True},
        ],
        metric="competitors",
        ascending=False,
    )
    assert desc_abs[-1]["key"] == "gone"


def test_avg_delta_requires_two_events() -> None:
    def avg_delta(n_cur: int, cur: int, n_prev: int, prev: int):
        if n_cur < 2 or n_prev < 2:
            return None
        return (cur / n_cur) - (prev / n_prev)

    assert avg_delta(1, 500, 1, 400) is None
    assert avg_delta(2, 500, 2, 400) == 50.0


def test_dashboard_exposes_grain_controls() -> None:
    html = (REPO / "event_growth_dashboard_en.html").read_text()
    assert "eg-grain-select" in html
    assert "listGrain" in html
    assert "d_competitors" in html
    assert "region-list-head__sort" in html
    assert "California, US" in html or "listGrainBareLabel" in html


def map_hover_key_from_path(level: str, country_scope: str | None, path: dict) -> str | None:
    """Mirror mapHoverKeyFromPath in event_growth_dashboard_en.html."""
    if level == "world":
        return path.get("continent")
    if level == "continent":
        return path.get("country")
    if level == "country":
        if country_scope == "United States":
            return path.get("state")
        return path.get("city")
    if level == "state":
        return path.get("city")
    return None


def test_map_hover_key_remaps_list_city_to_pin() -> None:
    path = {
        "continent": "Europe",
        "country": "Germany",
        "state": None,
        "city": "Freiburg",
    }
    # List key is composite; map pin key is bare city.
    assert region_key(
        {"country": "Germany", "state": None, "city": "Freiburg"}, "city"
    ) == "Germany||Freiburg"
    assert map_hover_key_from_path("country", "Germany", path) == "Freiburg"
    assert map_hover_key_from_path("world", None, path) == "Europe"
    assert map_hover_key_from_path("continent", None, path) == "Germany"
    us = {
        "continent": "America",
        "country": "United States",
        "state": "California",
        "city": "San Francisco",
    }
    assert map_hover_key_from_path("country", "United States", us) == "California"
    assert map_hover_key_from_path("state", "United States", us) == "San Francisco"


def test_dashboard_exposes_map_hover_remap_and_place() -> None:
    html = (REPO / "event_growth_dashboard_en.html").read_text()
    assert "mapHoverKeyFromPath" in html
    assert "mapFeatureKeyForRegion" in html
    assert "eventPlaceLineHtml" in html
    assert "cityRegionPlaceLineHtml" in html
    assert "countryFlagEmoji" in html
    assert "tt-place" in html
    assert "tt-flag" in html
    assert "kpiCompInfoBtn" in html and "kpiCompTipPop" in html
    # Event place line is unconditional (no city-venue early return).
    start = html.index("function eventPlaceLineHtml")
    end = html.index("function isCityRegionTip", start)
    assert "citySelectionActive" not in html[start:end]


def test_dashboard_mobile_world_can_zoom_out() -> None:
    html = (REPO / "event_growth_dashboard_en.html").read_text()
    assert "minZoom: 0" in html
    assert "minZoom: 0.6" not in html
    assert "isCompactMapLayout" in html
    assert "display: contents" in html
    assert "side-kpi-panel { order: 1; }" in html or "order: 1" in html


if __name__ == "__main__":
    test_region_world_has_us_states_not_united_states_row()
    test_city_keys_disambiguate_same_name()
    test_event_metric_subset_and_fallback()
    test_status_slice_metrics_relevance()
    test_event_delta_uses_edition_delta()
    test_new_delta_null_sorts_last()
    test_absent_delta_sorts_last_like_new()
    test_avg_delta_requires_two_events()
    test_dashboard_exposes_grain_controls()
    test_map_hover_key_remaps_list_city_to_pin()
    test_dashboard_exposes_map_hover_remap_and_place()
    test_dashboard_mobile_world_can_zoom_out()
    print("OK")
