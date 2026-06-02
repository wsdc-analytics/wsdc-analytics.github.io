#!/usr/bin/env python3
"""Smoke tests for country_normalization.normalize_country."""

from country_normalization import normalize_country


def test_aliases() -> None:
    assert normalize_country("Nederland") == "Netherlands"
    assert normalize_country("GA USA") == "United States"
    assert normalize_country("CA USA") == "United States"
    assert normalize_country("Usa") == "United States"
    assert normalize_country("Holland") == "Netherlands"
    assert normalize_country("England") == "United Kingdom"


def test_passthrough() -> None:
    assert normalize_country("France") == "France"
    assert normalize_country("") == ""


if __name__ == "__main__":
    test_aliases()
    test_passthrough()
    print("OK")
