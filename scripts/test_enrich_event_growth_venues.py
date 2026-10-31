#!/usr/bin/env python3
"""Unit tests for enrich_event_growth_venues helpers."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from enrich_event_growth_venues import (  # noqa: E402
    VenueRow,
    build_lookup_by_event,
    enrich_editions,
    fold_merged_venue_lookups,
    haversine_km,
    match_venue,
    split_mysql_values,
    usable_hotel_name,
    usable_lat_lon,
    venue_lookup_extra_ids,
)


def test_split_mysql_values_quotes_and_null() -> None:
    body = "1, '2026-01-15', NULL, 'O\\'Hare', 'a''b'"
    fields = split_mysql_values(body)
    assert fields[0] == "1"
    assert fields[1] == "2026-01-15"
    assert fields[2] is None
    assert fields[3] == "O'Hare"
    assert fields[4] == "a'b"


def test_haversine_lon_sign_flip() -> None:
    # Monterey: wrong +121 vs city −121 → huge; flipped → near zero.
    city_lat, city_lon = 36.5973, -121.8978
    bad = haversine_km(city_lat, city_lon, 36.5973, 121.8978)
    good = haversine_km(city_lat, city_lon, 36.5973, -121.8978)
    assert bad > 9000
    assert good < 1


def test_match_venue_closest_start_not_calendar_year() -> None:
    rows = [
        VenueRow(42, date(2018, 12, 28), 28.4, -81.4, "Rosen", "addr", "Orlando", 1),
        VenueRow(42, date(2019, 12, 27), 28.4, -81.4, "Rosen", "addr", "Orlando", 2),
    ]
    by = build_lookup_by_event(rows)
    # Growth labels year=2019 but start is Dec 2018 NYE.
    hit = match_venue(42, date(2018, 12, 28), by, 45)
    assert hit is not None
    assert hit.start == date(2018, 12, 28)
    assert hit.ce_id == 1

    hit2 = match_venue(42, date(2019, 12, 27), by, 45)
    assert hit2 is not None
    assert hit2.ce_id == 2


def test_match_venue_rejects_far_dates() -> None:
    rows = [VenueRow(1, date(2020, 6, 1), 1.0, 2.0, "H", "", "X", 1)]
    by = build_lookup_by_event(rows)
    assert match_venue(1, date(2021, 6, 1), by, 45) is None


def test_fold_merged_venue_lookups_paris_style() -> None:
    """Growth id 272 must see CE hotels stored under merged registry id 307."""
    by = build_lookup_by_event(
        [
            VenueRow(
                272, date(2019, 2, 1), 49.01, 2.55, "Hilton CDG", "", "Roissy", 1
            ),
            VenueRow(
                307,
                date(2026, 1, 23),
                48.90,
                2.35,
                "H4 Hotel Wyndham Paris Pleyel",
                "",
                "Saint-Denis",
                2,
            ),
        ]
    )
    folded = fold_merged_venue_lookups(by, {272: (307,)})
    hit = match_venue(272, date(2026, 1, 23), folded, 45)
    assert hit is not None
    assert hit.hotel.startswith("H4")
    assert hit.event_id == 307


def test_venue_lookup_extra_ids_inverts_merge_map() -> None:
    extras = venue_lookup_extra_ids({307: 272, 543: 272, 409: 342})
    assert extras[272] == (307, 543)
    assert extras[342] == (409,)


def test_usable_hotel_name_rejects_placeholders() -> None:
    assert usable_hotel_name("Hotels") is None
    assert usable_hotel_name("Still in negotiation") is None
    assert usable_hotel_name("TBD") is None
    assert usable_hotel_name("H4 Hotel Wyndham") == "H4 Hotel Wyndham"


def test_enrich_soft_rehome_same_hotel_closer_sibling() -> None:
    """Matched CE within MAX_DRIFT but far from city → prefer closer same hotel."""
    by = build_lookup_by_event(
        [
            # ~116 km south of Paris (under 200 km hard cap).
            VenueRow(
                272,
                date(2023, 2, 3),
                47.8249,
                2.35,
                "Novotel Paris East",
                "",
                "Paris",
                1,
            ),
            VenueRow(
                272,
                date(2025, 1, 30),
                48.9039,
                2.48,
                "Novotel Paris East",
                "",
                "Paris",
                2,
            ),
        ]
    )
    editions = [
        {
            "event_id": 272,
            "year": 2023,
            "month": 2,
            "start": "2023-02-03",
            "lat": 48.8575,
            "lon": 2.3514,
            "city": "Paris",
        }
    ]
    stats = enrich_editions(editions, by, 200.0, 45)
    assert stats["venue_applied"] == 1
    assert stats["venue_inherited"] == 1
    assert editions[0]["hotel"] == "Novotel Paris East"
    assert abs(editions[0]["lat"] - 48.9039) < 0.01
    assert editions[0]["venue_start"] == "2025-01-30"


def test_enrich_drift_reject_then_inherit_sibling() -> None:
    """Mexico GPS for a Paris hotel → inherit sibling Novotel coords."""
    by = build_lookup_by_event(
        [
            VenueRow(
                272,
                date(2024, 2, 2),
                19.64,
                -99.03,
                "Novotel Paris East",
                "",
                "",
                1,
            ),
            VenueRow(
                272,
                date(2025, 1, 30),
                48.9039,
                2.48,
                "Novotel Paris East",
                "",
                "Paris",
                2,
            ),
        ]
    )
    editions = [
        {
            "event_id": 272,
            "year": 2024,
            "month": 2,
            "start": "2024-02-02",
            "lat": 48.8575,
            "lon": 2.3514,
            "city": "Paris",
        }
    ]
    stats = enrich_editions(editions, by, 200.0, 45)
    assert stats["venue_rejected_drift"] == 0
    assert stats["venue_inherited"] == 1
    assert editions[0]["geo_source"] == "wsdc_venue"
    assert editions[0]["hotel"] == "Novotel Paris East"
    assert abs(editions[0]["lat"] - 48.9039) < 0.01
    assert editions[0]["venue_start"] == "2025-01-30"


def test_enrich_hotel_only_when_venue_accepted() -> None:
    by = build_lookup_by_event(
        [
            # Far from city → reject; hotel must NOT stick.
            VenueRow(9, date(2026, 5, 1), -37.9, 145.0, "Wrong Hotel", "Melbourne", "X", 1),
            # Near city → accept; hotel sticks.
            VenueRow(10, date(2026, 6, 1), 30.27, -97.74, "DoubleTree", "Austin St", "Austin", 2),
        ]
    )
    editions = [
        {
            "event_id": 9,
            "year": 2026,
            "month": 5,
            "start": "2026-05-01",
            "lat": 38.9,
            "lon": -77.0,
            "city": "Washington",
        },
        {
            "event_id": 10,
            "year": 2026,
            "month": 6,
            "start": "2026-06-01",
            "lat": 30.267,
            "lon": -97.743,
            "city": "Austin",
        },
    ]
    stats = enrich_editions(editions, by, max_drift_km=200.0, max_date_drift_days=45)
    assert stats["venue_rejected_drift"] == 1
    assert stats["venue_applied"] == 1
    assert editions[0].get("geo_source") == "city"
    assert "hotel" not in editions[0]
    assert editions[0].get("venue_rejected_km", 0) > 1000
    assert editions[1]["geo_source"] == "wsdc_venue"
    assert editions[1]["hotel"] == "DoubleTree"
    assert abs(editions[1]["lat"] - 30.27) < 0.01


def test_enrich_lon_sign_fix() -> None:
    by = build_lookup_by_event(
        [
            VenueRow(5, date(2026, 1, 1), 36.5973, 121.8978, "Hyatt", "a", "Monterey", 1),
        ]
    )
    editions = [
        {
            "event_id": 5,
            "year": 2026,
            "month": 1,
            "start": "2026-01-01",
            "lat": 36.5973,
            "lon": -121.8978,
            "city": "Monterey",
        }
    ]
    stats = enrich_editions(editions, by, 200.0, 45)
    assert stats["lon_sign_fixed"] == 1
    assert stats["venue_applied"] == 1
    assert editions[0]["lon"] < 0
    assert editions[0].get("geo_fix") == "lon_sign"
    assert editions[0]["hotel"] == "Hyatt"


def test_enrich_idempotent_city_centroid() -> None:
    by = build_lookup_by_event(
        [VenueRow(10, date(2026, 6, 1), 30.33, -97.70, "DT", "", "Austin", 1)]
    )
    editions = [
        {
            "event_id": 10,
            "year": 2026,
            "month": 6,
            "start": "2026-06-01",
            "lat": 30.267,
            "lon": -97.743,
            "city": "Austin",
        }
    ]
    enrich_editions(editions, by, 200.0, 45)
    assert editions[0]["city_lat"] == 30.267
    assert editions[0]["lat"] == 30.33
    # Second pass must keep city_lat and still apply venue.
    enrich_editions(editions, by, 200.0, 45)
    assert editions[0]["city_lat"] == 30.267
    assert editions[0]["lat"] == 30.33
    assert editions[0]["geo_source"] == "wsdc_venue"


def test_usable_lat_lon_rejects_null_island() -> None:
    assert usable_lat_lon(59.88, 29.86) is True
    assert usable_lat_lon(0.0, 0.0) is False
    assert usable_lat_lon(None, 30.0) is False


def test_enrich_hotel_only_when_sql_missing_gps() -> None:
    by = build_lookup_by_event(
        [VenueRow(338, date(2026, 9, 11), None, None, "Milan", "Shipilovskaya", "Moscow", 1)]
    )
    editions = [
        {
            "event_id": 338,
            "year": 2026,
            "month": 9,
            "start": "2026-09-11",
            "lat": 55.75,
            "lon": 37.61,
            "city": "Moscow",
        }
    ]
    stats = enrich_editions(editions, by, 200.0, 45)
    assert stats["no_sql_geo"] == 1
    assert stats["hotel_only"] == 1
    assert editions[0]["geo_source"] == "city"
    assert editions[0]["hotel"] == "Milan"
    assert editions[0]["lat"] == 55.75


def test_enrich_inherits_coords_when_sql_missing_gps() -> None:
    # SNOW-like: 2025 row has hotel but no GPS; 2024 has Peterhof coords.
    by = build_lookup_by_event(
        [
            VenueRow(
                215,
                date(2024, 2, 1),
                59.88407,
                29.86839,
                "New Peterhof",
                "pr. 34",
                "Peterhof",
                1,
            ),
            VenueRow(
                215,
                date(2025, 1, 29),
                None,
                None,
                "New Peterhof",
                "pr. 34",
                "Peterhof",
                2,
            ),
        ]
    )
    editions = [
        {
            "event_id": 215,
            "year": 2025,
            "month": 1,
            "start": "2025-01-29",
            "lat": 59.9310584,
            "lon": 30.3609097,
            "city": "St. Petersburg",
        }
    ]
    stats = enrich_editions(editions, by, 200.0, 45)
    assert stats["venue_inherited"] == 1
    assert stats["venue_applied"] == 1
    assert editions[0]["geo_source"] == "wsdc_venue"
    assert editions[0].get("geo_fix") == "inherited"
    assert editions[0]["hotel"] == "New Peterhof"
    assert abs(editions[0]["lat"] - 59.88407) < 0.001
    assert abs(editions[0]["lon"] - 29.86839) < 0.001


if __name__ == "__main__":
    test_split_mysql_values_quotes_and_null()
    test_haversine_lon_sign_flip()
    test_match_venue_closest_start_not_calendar_year()
    test_match_venue_rejects_far_dates()
    test_enrich_hotel_only_when_venue_accepted()
    test_enrich_lon_sign_fix()
    test_enrich_idempotent_city_centroid()
    test_usable_lat_lon_rejects_null_island()
    test_enrich_hotel_only_when_sql_missing_gps()
    test_enrich_inherits_coords_when_sql_missing_gps()
    print("OK")
