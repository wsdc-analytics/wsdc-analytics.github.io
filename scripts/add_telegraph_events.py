#!/usr/bin/env python3
"""
Add new summary block with events parsed from Telegraph when they are missing in points_summaries.json.

Usage:
  python add_telegraph_events.py --post-date DD-MM-YYYY URL1 [URL2 ...]
  python add_telegraph_events.py --post-date 17-11-2025 \\
    "https://telegra.ph/Flowstate--West-Coast-Swing--Zouk-Festival---Full-Info-11-19" \\
    "https://telegra.ph/Westie-Pink-City---Full-Info-11-19" ...

Uses sync_telegraph_to_site's fetch/parse; builds full event objects and inserts one new summary.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Reuse sync script's fetch and parse
from sync_telegraph_to_site import (
    extract_path_from_url,
    fetch_telegraph_page,
    parse_telegraph_content,
)


PLACE_LABELS = {
    "1": "🥇 1 place",
    "2": "🥈 2 place",
    "3": "🥉 3 place",
    "4": "4 place",
    "5": "5 place",
}


def slugify(name: str) -> str:
    """Lowercase, replace non-alnum with '-', collapse, strip."""
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "event"


def parsed_divisions_to_json_divisions(parsed_divs: dict) -> list[dict]:
    """Convert parse_telegraph_content divisions to points_summaries event divisions format."""
    out = []
    for div_name, pd in (parsed_divs or {}).items():
        places = []
        for p in pd.get("places", []):
            place_key = p.get("place", "")
            label = PLACE_LABELS.get(place_key, f"{place_key} place")
            places.append({
                "place": place_key,
                "place_label": label,
                "leader": p.get("leader"),
                "follower": p.get("follower"),
            })
        final = pd.get("final")
        if final and (final.get("leaders") is not None or final.get("followers") is not None):
            place_f = {
                "place": "F",
                "place_label": "Final",
                "leader": None,
                "follower": None,
            }
            if final.get("leaders") is not None:
                place_f["leaders"] = final["leaders"]
                place_f["points_leader"] = "1"
            if final.get("followers") is not None:
                place_f["followers"] = final["followers"]
                place_f["points_follower"] = "1"
            places.append(place_f)
        out.append({"division": div_name, "places": places})
    return out


def build_event(parsed: dict, telegraph_url: str, post_date_dd_mm_yyyy: str) -> dict:
    """Build full event object for points_summaries.json."""
    # post_date is DD-MM-YYYY -> slug prefix YYYY-MM-DD
    parts = post_date_dd_mm_yyyy.split("-")
    if len(parts) == 3:
        day, month, year = parts
        date_prefix = f"{year}-{month}-{day}"
    else:
        date_prefix = "2025-11-17"
    slug_suffix = slugify(parsed.get("event_name", ""))
    slug = f"{date_prefix}-{slug_suffix}" if slug_suffix else date_prefix

    return {
        "name": parsed.get("event_name", ""),
        "slug": slug,
        "dates": parsed.get("event_dates", ""),
        "location": "",
        "flag": "🌐",
        "continent": "Other",
        "telegraph_url": telegraph_url,
        "divisions": parsed_divisions_to_json_divisions(parsed.get("divisions") or {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Add new summary with events from Telegraph URLs")
    parser.add_argument("--json", default=None, help="Path to points_summaries.json")
    parser.add_argument("--post-date", required=True, metavar="DD-MM-YYYY", help="Post date for the new summary block")
    parser.add_argument("urls", nargs="+", help="Telegraph Full-Info URLs")
    parser.add_argument("--dry-run", action="store_true", help="Do not write JSON")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    json_path = Path(args.json) if args.json else repo_root / "static" / "data" / "points_summaries.json"
    if not json_path.is_file():
        print(f"Error: JSON not found: {json_path}", file=sys.stderr)
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summaries = data.get("summaries", [])
    events = []
    for url in args.urls:
        path = extract_path_from_url(url)
        if not path:
            print(f"Skipping invalid URL: {url}")
            continue
        print(f"Fetching {path} ...")
        result = fetch_telegraph_page(path)
        if not result:
            print(f"  Failed to fetch")
            continue
        parsed = parse_telegraph_content(result)
        if not parsed or not parsed.get("event_name"):
            print(f"  Could not parse event")
            continue
        full_url = url if "://" in url else f"https://telegra.ph/{path}"
        ev = build_event(parsed, full_url, args.post_date)
        events.append(ev)
        print(f"  Added: {ev['name']}")

    if not events:
        print("No events to add.")
        return 1

    for s in summaries:
        if s.get("post_date") == args.post_date:
            print(f"Warning: summary for {args.post_date} already exists; appending events to it.")
            s.setdefault("events", []).extend(events)
            s["events_count"] = len(s["events"])
            if not args.dry_run:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved: {len(events)} event(s) appended to existing summary.")
            return 0

    # Summaries are newest-first: 22-02-2026, ..., 09-11-2025, 02-11-2025
    # We want 17-11-2025 (Nov 17) -> before 09-11-2025 (Nov 9)
    insert_index = len(summaries)
    try:
        o_day, o_month, o_year = map(int, args.post_date.split("-"))
        for i, s in enumerate(summaries):
            s_day, s_month, s_year = map(int, s.get("post_date", "99-99-9999").split("-"))
            if (s_year, s_month, s_day) < (o_year, o_month, o_day):
                insert_index = i
                break
    except Exception:
        pass

    new_summary = {
        "post_date": args.post_date,
        "events_count": len(events),
        "events": events,
    }
    summaries.insert(insert_index, new_summary)
    data["summaries"] = summaries

    if not args.dry_run:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {json_path}: new summary {args.post_date} with {len(events)} event(s).")
    else:
        print(f"Dry run: would add summary {args.post_date} with {len(events)} event(s) at index {insert_index}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
