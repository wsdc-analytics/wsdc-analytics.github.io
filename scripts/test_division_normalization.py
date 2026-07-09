#!/usr/bin/env python3
"""Smoke tests for division_normalization.normalize_division."""

from division_normalization import normalize_division


def test_aliases() -> None:
    assert normalize_division("All-Star") == "All-Stars"
    assert normalize_division("All Stars") == "All-Stars"
    assert normalize_division("Champion") == "Champions"
    assert normalize_division("Novice") == "Novice"


def test_passthrough() -> None:
    assert normalize_division("Sophisticated") == "Sophisticated"
    assert normalize_division("") == ""


if __name__ == "__main__":
    test_aliases()
    test_passthrough()
    print("OK")
