#!/usr/bin/env python3
"""Unit tests for edition ordinal series-split helpers."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enrich_event_growth_edition_numbers import (  # noqa: E402
    DEFAULT_ALIASES,
    clear_cross_brand_prev,
    edition_splits_from_year_split_rules,
    is_late_era_bucket,
    load_edition_series_splits_from_aliases,
    series_bucket,
)


def test_series_bucket_paris_eras() -> None:
    splits = [{"event_id": 272, "early_year_max": 2022, "late_year_min": 2023}]
    assert series_bucket(272, 2020, splits) == "272:early:<=2022"
    assert series_bucket(272, 2022, splits) == "272:early:<=2022"
    assert series_bucket(272, 2023, splits) == "272:late:>=2023"
    assert series_bucket(218, 2023, splits) == "218"


def test_is_late_era_bucket() -> None:
    assert is_late_era_bucket("272:late:>=2023") is True
    assert is_late_era_bucket("272:early:<=2022") is False
    assert is_late_era_bucket("218") is False


def test_edition_splits_from_year_split_rules_respects_flag() -> None:
    rules = [
        {
            "early_event_id": 272,
            "late_event_id": 272,
            "early_year_max": 2022,
            "late_year_min": 2023,
            "reset_edition_ordinal": True,
        },
        {
            "early_event_id": 342,
            "late_event_id": 342,
            "early_year_max": 2025,
            "late_year_min": 2026,
            "reset_edition_ordinal": False,
        },
        {
            "early_event_id": 221,
            "late_event_id": 221,
            "early_year_max": 2025,
            "late_year_min": 2026,
            "reset_edition_ordinal": True,
        },
    ]
    splits = edition_splits_from_year_split_rules(rules)
    ids = {s["event_id"] for s in splits}
    assert ids == {272, 221}
    assert 342 not in ids


def test_load_edition_series_splits_from_pipeline_aliases() -> None:
    assert DEFAULT_ALIASES.is_file(), f"missing {DEFAULT_ALIASES}"
    splits = load_edition_series_splits_from_aliases(DEFAULT_ALIASES)
    by_id = {s["event_id"]: s for s in splits}
    assert 272 in by_id
    assert by_id[272]["early_year_max"] == 2022
    assert by_id[272]["late_year_min"] == 2023
    # Rebrands with reset flag
    assert 221 in by_id  # Gateway
    assert 264 in by_id  # UpTown
    assert 324 in by_id  # Calgary Town Open
    assert 68 in by_id  # The Open
    # Same championship series — must NOT reset
    assert 342 not in by_id


def test_clear_cross_brand_prev() -> None:
    ed = {
        "status": "restarted",
        "gap_flag": "restarted",
        "prev": {"year": 2020, "competitors": 320},
        "delta": 100,
        "pct": 30.0,
    }
    clear_cross_brand_prev(ed)
    assert ed["status"] == "new"
    assert "prev" not in ed
    assert "gap_flag" not in ed
    assert ed["delta"] is None
    assert ed["pct"] is None


if __name__ == "__main__":
    test_series_bucket_paris_eras()
    test_is_late_era_bucket()
    test_edition_splits_from_year_split_rules_respects_flag()
    test_load_edition_series_splits_from_pipeline_aliases()
    test_clear_cross_brand_prev()
    print("OK")
