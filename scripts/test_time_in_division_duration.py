#!/usr/bin/env python3
"""Smoke tests for day/YM duration helper in update_time_in_division_spells."""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "tid_spells",
    Path(__file__).resolve().parent / "update_time_in_division_spells.py",
)
assert _spec and _spec.loader
tid = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tid)


def test_day_path_same_day_floor() -> None:
    months, basis = tid.duration_months(
        (2020, 1), (2020, 1), date(2020, 1, 10), date(2020, 1, 10)
    )
    assert basis == "day"
    assert months == 0.1


def test_day_path_approx_month() -> None:
    months, basis = tid.duration_months(
        (2020, 1), (2020, 2), date(2020, 1, 1), date(2020, 1, 31)
    )
    assert basis == "day"
    assert months == 1.0


def test_ym_fallback_missing_date() -> None:
    months, basis = tid.duration_months((2020, 1), (2020, 3), None, date(2020, 3, 1))
    assert basis == "ym"
    assert months == 3.0


def test_ym_fallback_inverted_dates() -> None:
    months, basis = tid.duration_months(
        (2020, 1), (2020, 2), date(2020, 2, 1), date(2020, 1, 1)
    )
    assert basis == "ym"
    assert months == 2.0


if __name__ == "__main__":
    test_day_path_same_day_floor()
    test_day_path_approx_month()
    test_ym_fallback_missing_date()
    test_ym_fallback_inverted_dates()
    print("OK")
