"""Canonical skill-division labels for WSDC event_competition values."""

from __future__ import annotations

_DIVISION_ALIASES: dict[str, str] = {
    "newcomer": "Newcomer",
    "newcomers": "Newcomer",
    "novice": "Novice",
    "novices": "Novice",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "all-star": "All-Stars",
    "all star": "All-Stars",
    "all stars": "All-Stars",
    "all-stars": "All-Stars",
    "champion": "Champions",
    "champions": "Champions",
}


def normalize_division(value: str) -> str:
    """Map raw event_competition strings to dashboard skill-division labels."""
    raw = (value or "").strip()
    if not raw:
        return ""
    return _DIVISION_ALIASES.get(raw.casefold(), raw)
