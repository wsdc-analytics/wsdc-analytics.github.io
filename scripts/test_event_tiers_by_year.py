#!/usr/bin/env python3
"""Smoke tests for event_tiers_by_year data + geo-selection rules."""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "static" / "data" / "event_tiers_by_year.json"


def pick_geo_value(current: str, options: list[str], preserve: bool) -> str:
    """Mirrors pickGeoValue() in event_tiers_by_year_dashboard_en.html."""
    if preserve and current in options:
        return current
    return "All"


def resolve_continent(current: str, continents: list[str]) -> str:
    """Mirrors syncGeoOptions continent keep-alive (always preserve if valid)."""
    return current if current in continents else "All"


def sort_keys_by_count_desc(keys: list[str], counts: dict[str, int]) -> list[str]:
    """Mirrors sortKeysByCountDesc() — desc by count, then A→Z."""
    return sorted(keys, key=lambda k: (-counts.get(k, 0), k))


def test_continent_survives_downstream_rebuild() -> None:
    continents = ["All", "America", "Asia", "Australia", "Europe"]
    # After user picks America, country rebuild must not wipe continent.
    assert resolve_continent("America", continents) == "America"
    assert pick_geo_value("All", ["All", "United States", "Canada"], preserve=False) == "All"
    assert pick_geo_value("United States", ["All", "United States", "Canada"], preserve=True) == "United States"
    assert pick_geo_value("France", ["All", "United States", "Canada"], preserve=True) == "All"
    assert resolve_continent("Atlantis", continents) == "All"


def test_geo_sort_by_event_count_desc() -> None:
    counts = {"France": 3, "United States": 40, "Canada": 12, "Austria": 3}
    assert sort_keys_by_count_desc(list(counts), counts) == [
        "United States",
        "Canada",
        "Austria",
        "France",
    ]


def test_json_payload() -> None:
    assert DATA.is_file(), f"missing {DATA}"
    payload = json.loads(DATA.read_text())
    assert payload.get("year_floor") == 2018
    assert payload.get("year_max") >= 2018
    editions = payload["editions"]
    assert len(editions) == payload["n_editions"]
    assert payload["n_missing_geo"] == sum(
        1 for e in editions if not e.get("country") or not e.get("continent")
    )
    assert payload["divisions_default"]
    assert "Novice" in payload["divisions_default"]
    years = {e["year"] for e in editions}
    assert min(years) >= payload["year_floor"]
    assert max(years) == payload["year_max"]
    for e in editions:
        assert e.get("event_id") is not None
        assert e.get("tiers")
        for _div, roles in e["tiers"].items():
            for _role, tier in (roles or {}).items():
                if tier is None:
                    continue
                assert isinstance(tier, int) and 1 <= tier <= 6
    with_counts = [e for e in editions if e.get("counts")]
    assert with_counts, "expected competitor counts from competitions_best"
    assert payload.get("n_editions_with_counts") == len(with_counts)
    sample = with_counts[0]["counts"]
    assert isinstance(sample, dict) and sample
    for _div, roles in sample.items():
        assert set(roles.keys()) <= {"Leader", "Follower"}
        for n in roles.values():
            assert isinstance(n, int) and n >= 0


def test_pipeline_path_env() -> None:
    # Import after path setup — build script must honor WSDC_PIPELINE_DATA.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_ety",
        REPO / "scripts" / "build_event_tiers_by_year.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    prev = os.environ.get("WSDC_PIPELINE_DATA")
    os.environ["WSDC_PIPELINE_DATA"] = "/tmp/wsdc-pipeline-missing-xyz"
    try:
        spec.loader.exec_module(mod)
        assert str(mod.PIPE) == "/tmp/wsdc-pipeline-missing-xyz"
        try:
            mod.require_file(mod.PIPE / "event_catalog.csv")
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "WSDC_PIPELINE_DATA" in str(exc)
    finally:
        if prev is None:
            os.environ.pop("WSDC_PIPELINE_DATA", None)
        else:
            os.environ["WSDC_PIPELINE_DATA"] = prev


if __name__ == "__main__":
    test_continent_survives_downstream_rebuild()
    test_geo_sort_by_event_count_desc()
    test_json_payload()
    test_pipeline_path_env()
    print("OK")
