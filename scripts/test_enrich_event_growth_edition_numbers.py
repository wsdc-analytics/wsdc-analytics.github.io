#!/usr/bin/env python3
"""Unit tests for edition ordinal series-split helpers."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enrich_event_growth_edition_numbers import (  # noqa: E402
    DEFAULT_ALIASES,
    classify_growth,
    clear_cross_brand_prev,
    edition_splits_from_year_split_rules,
    is_late_era_bucket,
    load_edition_series_splits_from_aliases,
    restore_missing_prev_within_buckets,
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
    assert 68 in by_id  # The Open
    # Same series across rename — must NOT reset
    assert 324 not in by_id  # BTO Open → Calgary Town Open
    assert 342 not in by_id  # GGP


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


def test_restore_missing_prev_bto_to_calgary() -> None:
    """Continuous 324 series: wipe prev, then restore declining vs 2025."""
    editions = [
        {
            "event_id": 324,
            "year": 2025,
            "month": 3,
            "name": "BTO Open",
            "competitors": 222,
            "status": "growing",
            "prev": {"year": 2024, "competitors": 164},
        },
        {
            "event_id": 324,
            "year": 2026,
            "month": 9,
            "name": "Calgary Town Open",
            "competitors": 147,
            "status": "new",
            "prev": None,
            "delta": None,
            "pct": None,
        },
    ]
    n = restore_missing_prev_within_buckets(editions, splits=[])
    assert n == 1
    ed = editions[1]
    assert ed["prev"]["year"] == 2025
    assert ed["prev"]["competitors"] == 222
    assert ed["delta"] == 147 - 222
    assert ed["status"] == "declining"
    # True debut untouched.
    debut = {
        "event_id": 999,
        "year": 2026,
        "month": 1,
        "competitors": 50,
        "status": "new",
        "prev": None,
    }
    assert restore_missing_prev_within_buckets([debut], splits=[]) == 0
    assert debut["prev"] is None


def test_classify_growth_basic() -> None:
    st, delta, pct, gap = classify_growth(147, 222, 1)
    assert st == "declining"
    assert delta == -75
    assert pct is not None and pct < 0
    assert gap is None
    st2, _, _, gap2 = classify_growth(100, 90, 3)
    assert st2 == "restarted"
    assert gap2 == "restarted"


if __name__ == "__main__":
    test_series_bucket_paris_eras()
    test_is_late_era_bucket()
    test_edition_splits_from_year_split_rules_respects_flag()
    test_load_edition_series_splits_from_pipeline_aliases()
    test_clear_cross_brand_prev()
    test_restore_missing_prev_bto_to_calgary()
    test_classify_growth_basic()
    print("OK")
