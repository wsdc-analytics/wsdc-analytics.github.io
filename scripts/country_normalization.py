"""Canonical country names for WSDC location_info.event_country values."""

from __future__ import annotations

import re

# Lowercase alias -> canonical label shown on dashboards.
_COUNTRY_ALIASES: dict[str, str] = {
    "usa": "United States",
    "us": "United States",
    "u.s.a.": "United States",
    "u.s.": "United States",
    "ga usa": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "nederland": "Netherlands",
    "the netherlands": "Netherlands",
    "holland": "Netherlands",
    "korea, republic of": "Republic of Korea",
    "south korea": "Republic of Korea",
    "republic of korea": "Republic of Korea",
    "russian federation": "Russia",
    "czechia": "Czech Republic",
}

# Two-letter US state + " USA" (e.g. GA USA, CA USA).
_US_STATE_USA = re.compile(r"^[A-Za-z]{2}\s+USA$", re.IGNORECASE)


def normalize_country(value: str) -> str:
    """Map raw event_country strings to a single canonical country label."""
    raw = (value or "").strip()
    if not raw:
        return ""

    lowered = raw.casefold()
    if lowered in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[lowered]

    if _US_STATE_USA.match(raw):
        return "United States"

    return raw
