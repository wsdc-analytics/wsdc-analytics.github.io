#!/usr/bin/env python3
"""Build unified secondary-role country dataset for dashboard.

Output schema:
  year -> role_group -> division -> [country rows]

Role-group semantics:
  - Leader/Follower: selected floor role (event_role)
  - Total: both floor roles combined

Share semantics:
  secondary_share = secondary_points / total_points
where secondary_points are points earned in selected role by dancers
whose dominant role is different from that selected role.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_normalization import normalize_country  # noqa: E402


SKILL_DIVISIONS = {
    "Newcomer",
    "Novice",
    "Intermediate",
    "Advanced",
    "All-Stars",
    "Champions",
}
UI_DIVISIONS = ["Total", "Newcomer", "Novice", "Intermediate", "Advanced", "All-Stars"]
ROLE_GROUPS = ["Total", "Leader", "Follower"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update secondary country unified dataset.")
    parser.add_argument(
        "--source-dir",
        default="/Users/ania/.cursor/projects/python/wsdc-data-pipeline/data",
        help="Path to folder with dancer_role_info.csv, dancers_results_info.csv, location_info.csv",
    )
    parser.add_argument(
        "--output",
        default="/Users/ania/.cursor/wsdc-analytics-repo/static/data/secondary_country_unified.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        default=["2023", "2024", "2025", "2026"],
        help="Years to include",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir)
    output = Path(args.output)
    years = set(args.years)

    role_by_id: dict[str, str] = {}
    name_by_id: dict[str, str] = {}
    with (source_dir / "dancer_role_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dancer_id = row["dancer_id"]
            role_by_id[dancer_id] = (row.get("dominate_role") or "").strip().lower()
            name_by_id[dancer_id] = (row.get("dancer_name") or "").strip()

    country_by_location: dict[str, str] = {}
    with (source_dir / "location_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            country_by_location[row["location_id"]] = normalize_country(row.get("event_country") or "")

    per_dancer = defaultdict(lambda: {"secondary": 0.0, "total": 0.0})
    with (source_dir / "dancers_results_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            year = (row.get("event_year") or "").strip()
            if year not in years:
                continue

            dancer_id = (row.get("dancer_id") or "").strip()
            if not dancer_id:
                continue

            dominant_role = role_by_id.get(dancer_id, "")
            event_role = (row.get("event_role") or "").strip().lower()
            if dominant_role not in ("leader", "follower") or event_role not in ("leader", "follower"):
                continue

            division = (row.get("event_competition") or "").strip()
            if division not in SKILL_DIVISIONS:
                continue

            country = country_by_location.get(row.get("location_id", ""), "")
            if not country:
                continue

            points = float(row.get("event_points") or 0)
            selected_role_group = event_role.title()
            secondary_points = points if dominant_role != event_role else 0.0

            # Selected floor-role totals.
            selected_total_key = (year, selected_role_group, "Total", country, dancer_id)
            per_dancer[selected_total_key]["secondary"] += secondary_points
            per_dancer[selected_total_key]["total"] += points

            if division in set(UI_DIVISIONS[1:]):
                selected_div_key = (year, selected_role_group, division, country, dancer_id)
                per_dancer[selected_div_key]["secondary"] += secondary_points
                per_dancer[selected_div_key]["total"] += points

            # Combined Total role-group.
            combined_total_key = (year, "Total", "Total", country, dancer_id)
            per_dancer[combined_total_key]["secondary"] += secondary_points
            per_dancer[combined_total_key]["total"] += points

            if division in set(UI_DIVISIONS[1:]):
                combined_div_key = (year, "Total", division, country, dancer_id)
                per_dancer[combined_div_key]["secondary"] += secondary_points
                per_dancer[combined_div_key]["total"] += points

    out_obj = {
        year: {group: {div: [] for div in UI_DIVISIONS} for group in ROLE_GROUPS}
        for year in sorted(years)
    }

    country_map = defaultdict(
        lambda: {"secondary": 0.0, "total": 0.0, "dancers": {}, "secondary_dancers": set()}
    )
    for (year, group, division, country, dancer_id), values in per_dancer.items():
        key = (year, group, division, country)
        bucket = country_map[key]
        bucket["secondary"] += values["secondary"]
        bucket["total"] += values["total"]
        bucket["dancers"][dancer_id] = {
            "dancer_id": dancer_id,
            "name": name_by_id.get(dancer_id, dancer_id),
            "secondary_points": values["secondary"],
            "total_points": values["total"],
        }
        if values["secondary"] > 0:
            bucket["secondary_dancers"].add(dancer_id)

    for (year, group, division, country), bucket in country_map.items():
        total = bucket["total"]
        secondary = bucket["secondary"]
        dancers = [d for d in bucket["dancers"].values() if d["secondary_points"] > 0]
        dancers.sort(key=lambda x: (-x["secondary_points"], -x["total_points"], x["name"]))

        out_obj[year][group][division].append(
            {
                "country": country,
                "secondary_points": round(secondary, 4),
                "secondary_share": round((secondary / total) if total > 0 else 0.0, 8),
                "total_points": round(total, 4),
                "dancers_count": len(bucket["dancers"]),
                "transitions": len(bucket["secondary_dancers"]),
                "dancers": [
                    {
                        "dancer_id": d["dancer_id"],
                        "name": d["name"],
                        "secondary_points": round(d["secondary_points"], 4),
                        "total_points": round(d["total_points"], 4),
                    }
                    for d in dancers
                ],
            }
        )

    for year in out_obj:
        for group in out_obj[year]:
            for division in out_obj[year][group]:
                out_obj[year][group][division].sort(
                    key=lambda row: (-row["secondary_points"], -row["total_points"], row["country"])
                )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out_obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"Updated: {output}")
    print(f"Years included: {', '.join(sorted(years))}")


if __name__ == "__main__":
    main()
