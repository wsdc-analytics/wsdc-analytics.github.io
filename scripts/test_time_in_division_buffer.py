#!/usr/bin/env python3
"""Unit tests for Buffer stay_after_may logic in update_time_in_division_spells."""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "tid_spells",
    Path(__file__).resolve().parent / "update_time_in_division_spells.py",
)
assert _spec and _spec.loader
tid = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tid)

RULES = json.loads(
    (_REPO / "static" / "data" / "rules_advancement_thresholds.json").read_text(
        encoding="utf-8"
    )
)
OBS = (2026, 10)


def _ev(
    eid: str,
    div: str,
    y: int,
    m: int,
    day: int,
    pts: float,
) -> dict:
    return {
        "eid": eid,
        "div": div,
        "ym": (y, m),
        "year": y,
        "day": date(y, m, day),
        "pts": float(pts),
    }


def _crossing(
    done_ym: str,
    done_date: str,
    *,
    allowed_t: float | None = None,
    required_ym: str | None = None,
    required_date: str | None = None,
    required_t: float | None = None,
) -> dict[str, dict]:
    out: dict[str, dict] = {
        "allowed": {
            "done_ym": done_ym,
            "done_date": done_date,
        }
    }
    if allowed_t is not None:
        out["allowed"]["threshold"] = float(allowed_t)
    if required_ym and required_date:
        out["required"] = {
            "done_ym": required_ym,
            "done_date": required_date,
        }
        if required_t is not None:
            out["required"]["threshold"] = float(required_t)
    return out


def test_basket_may_equals_must_is_must() -> None:
    """Pre-2018 single threshold (May==Must) → basket must once in Buffer cohort."""
    assert tid._basket_from_progress(20.0, 15.0, 15.0, False) == "must"
    assert tid._basket_from_progress(10.0, 15.0, 15.0, False) == "must"


def test_novice_threshold_at_end_not_first_epoch() -> None:
    """Must threshold follows last stay-event year (30), not first hit era (15)."""
    # May at 15 pts in 2015 era; keep competing into 2019 (May 16 / Must 30).
    # No registry Must crossing — window runs to data cut-off.
    events = [
        _ev("n1", "Novice", 2015, 3, 1, 15),
        _ev("n2", "Novice", 2015, 6, 1, 5),  # post-May
        _ev("n3", "Novice", 2019, 4, 1, 5),
    ]
    crossings = _crossing("2015-03", "2015-03-01", allowed_t=15.0)
    stay = tid.compute_stay_after_may(
        events, "Novice", (2015, 1), crossings, RULES, OBS
    )
    assert stay is not None
    assert stay["must_threshold"] == 30.0
    assert stay["may_threshold"] == 16.0
    assert stay["points_at_end"] == 25.0
    assert stay["exit"] == "still"


def test_advanced_drops_after_may_rights_lapse() -> None:
    """Elliot-style: post-May Advanced after May bar rises → no Buffer if under new May."""
    # May at 45 in 2021. Later only 2025 Adv contests under cumulative May=60 —
    # career Adv pts at those events stay below 60 → ineligible → no stay.
    crossings = _crossing("2021-02", "2021-02-01", allowed_t=45.0)
    events_lapse_only = [
        _ev("a1", "Advanced", 2021, 2, 1, 45),
        _ev("a3", "Advanced", 2025, 6, 1, 10),  # cum 55 < 60 May
    ]
    stay = tid.compute_stay_after_may(
        events_lapse_only, "Advanced", (2020, 1), crossings, RULES, OBS
    )
    assert stay is None

    # Eligible 2021 post-May kept; later under-May 2025 contest dropped from window.
    events = [
        _ev("a1", "Advanced", 2021, 2, 1, 45),
        _ev("a2", "Advanced", 2021, 5, 1, 5),  # 50 >= 45
        _ev("a3", "Advanced", 2025, 6, 1, 5),  # cum 55 < 60 → dropped
    ]
    stay_ok = tid.compute_stay_after_may(
        events, "Advanced", (2020, 1), crossings, RULES, OBS
    )
    assert stay_ok is not None
    assert stay_ok["events"] == 1
    assert stay_ok["end_ym"] == "2021-05"


def test_all_stars_ignores_champ_for_stay_and_must() -> None:
    """Champ contests below Must do not lengthen stay or drive Must basket."""
    events = [
        _ev("as0", "All-Stars", 2021, 3, 1, 150),  # May on AS path
        _ev("as1", "All-Stars", 2021, 6, 1, 10),  # post-May AS
        _ev("ch1", "Champions", 2022, 1, 1, 5),  # below Champ Must — ignored for stay
        _ev("as2", "All-Stars", 2022, 4, 1, 10),
    ]
    crossings = _crossing("2021-03", "2021-03-01", allowed_t=150.0)
    stay = tid.compute_stay_after_may(
        events, "All-Stars", (2018, 1), crossings, RULES, OBS
    )
    assert stay is not None
    assert stay["events"] == 2  # as1 + as2 only
    assert stay["basket"] != "must"  # 170 AS pts < 225
    assert stay["all_stars_points_at_end"] == 170.0
    assert stay["champions_points_at_end"] == 5.0
    assert stay["exit"] == "still"


def test_required_champion_excluded_from_buffer() -> None:
    """Career Champ Must (≥10) → not Buffer, even with later All-Stars points."""
    events = [
        _ev("ch0", "Champions", 2019, 5, 1, 10),
        _ev("as0", "All-Stars", 2021, 3, 1, 150),
        _ev("as1", "All-Stars", 2022, 1, 1, 20),
    ]
    crossings = _crossing("2021-03", "2021-03-01", allowed_t=150.0)
    stay = tid.compute_stay_after_may(
        events, "All-Stars", (2018, 1), crossings, RULES, OBS
    )
    assert stay is None


def test_required_champion_before_first_as_still_excluded() -> None:
    """Champ Must before first All-Stars point (before t0) still excludes."""
    events = [
        _ev("ch0", "Champions", 2015, 1, 1, 12),  # Must long before AS career
        _ev("as0", "All-Stars", 2022, 4, 1, 150),
        _ev("as1", "All-Stars", 2023, 2, 1, 20),
    ]
    crossings = _crossing("2022-04", "2022-04-01", allowed_t=150.0)
    # t0 = first AS month — Champ events are earlier than t0.
    stay = tid.compute_stay_after_may(
        events, "All-Stars", (2022, 4), crossings, RULES, OBS
    )
    assert stay is None


def test_all_stars_must_basket_while_still_buffering() -> None:
    """AS Must already on May event → Must basket + exit still (petition stay)."""
    # Must on the May event is not added as an exit for All-Stars, so they can
    # keep buffering after May with basket=must (Share Must KPI / chart colour).
    events = [
        _ev("as0", "All-Stars", 2021, 3, 1, 225),  # May + Must same day
        _ev("as1", "All-Stars", 2022, 1, 1, 40),
        _ev("ch1", "Champions", 2022, 6, 1, 5),
    ]
    crossings = _crossing("2021-03", "2021-03-01", allowed_t=150.0)
    stay = tid.compute_stay_after_may(
        events, "All-Stars", (2018, 1), crossings, RULES, OBS
    )
    assert stay is not None
    assert stay["basket"] == "must"
    assert stay["exit"] == "still"
    assert stay["events"] == 1
    assert stay["must_threshold"] == 225.0
    assert stay["all_stars_points_at_end"] == 265.0


def test_all_stars_formal_era_clips_pre_2021_may() -> None:
    """Registry May before formal era → effective May = first AS event in 2021+."""
    events = [
        _ev("as_old", "All-Stars", 2019, 5, 1, 200),
        _ev("as_new", "All-Stars", 2021, 8, 1, 10),  # effective May
        _ev("as_post", "All-Stars", 2022, 2, 1, 10),
    ]
    crossings = _crossing("2019-05", "2019-05-01", allowed_t=1.0)
    stay = tid.compute_stay_after_may(
        events, "All-Stars", (2018, 1), crossings, RULES, OBS
    )
    assert stay is not None
    assert stay.get("may_clipped") is True
    assert stay["may_ym"] == "2021-08"
    assert stay["events"] == 1
    assert stay["end_ym"] == "2022-02"


def test_activity_years_for_division() -> None:
    events = [
        _ev("n1", "Novice", 2019, 3, 1, 5),
        _ev("n2", "Novice", 2019, 8, 1, 5),
        _ev("n3", "Novice", 2021, 1, 1, 5),
        _ev("i1", "Intermediate", 2022, 2, 1, 5),
        _ev("as1", "All-Stars", 2021, 5, 1, 10),
        _ev("ch1", "Champions", 2022, 1, 1, 5),
    ]
    assert tid.activity_years_for_division(events, "Novice") == [2019, 2021]
    assert tid.activity_years_for_division(events, "All-Stars") == [2021]
    assert tid.activity_years_for_division(events, "Champions") == [2022]


def test_excludes_next_division_before_first_post_may() -> None:
    events = [
        _ev("n1", "Novice", 2019, 1, 1, 16),
        _ev("i1", "Intermediate", 2019, 2, 1, 5),  # next before post-May Novice
        _ev("n2", "Novice", 2019, 3, 1, 5),
    ]
    crossings = _crossing("2019-01", "2019-01-01", allowed_t=16.0)
    stay = tid.compute_stay_after_may(
        events, "Novice", (2018, 1), crossings, RULES, OBS
    )
    assert stay is None


if __name__ == "__main__":
    test_basket_may_equals_must_is_must()
    test_novice_threshold_at_end_not_first_epoch()
    test_advanced_drops_after_may_rights_lapse()
    test_all_stars_ignores_champ_for_stay_and_must()
    test_required_champion_excluded_from_buffer()
    test_required_champion_before_first_as_still_excluded()
    test_all_stars_must_basket_while_still_buffering()
    test_all_stars_formal_era_clips_pre_2021_may()
    test_activity_years_for_division()
    test_excludes_next_division_before_first_post_may()
    print("OK")
