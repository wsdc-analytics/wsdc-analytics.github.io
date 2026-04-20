#!/usr/bin/env python3
"""
Sync event data from Telegraph Full-Info pages to points_summaries.json.

For each given Telegraph URL:
  1. Fetch page via api.telegra.ph/getPage (path from URL)
  2. Parse event name, dates, and per-division leader/follower/leaders/followers
  3. Find matching event in points_summaries.json by normalized name + dates
  4. Replace only leader, follower, leaders, followers strings (brackets and markers from Telegraph)
  5. Save JSON once after all URLs are processed

Usage:
  python sync_telegraph_to_site.py [URL1] [URL2] ...
  python sync_telegraph_to_site.py --json path/to/points_summaries.json URL1 URL2 ...

Optional: --dry-run to print what would be updated without writing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any


def normalize_name(name: str) -> str:
    """Lowercase, collapse non-alnum to single space, strip."""
    s = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    return " ".join(s.split()).strip()


def normalize_dates(dates: str) -> str:
    """Normalize date string for comparison (trim, collapse spaces)."""
    return " ".join(dates.strip().split())


def extract_path_from_url(url: str) -> str | None:
    """From https://telegra.ph/Event-Name---Full-Info-11-08-4 return Event-Name---Full-Info-11-08-4."""
    url = url.strip()
    for prefix in ("https://telegra.ph/", "http://telegra.ph/"):
        if url.startswith(prefix):
            path = url[len(prefix) :].split("?")[0].rstrip("/")
            return path if path else None
    return None


def fetch_telegraph_page(path: str) -> dict | None:
    """Fetch page from Telegraph API. Returns API result dict or None on error."""
    url = f"https://api.telegra.ph/getPage/{path}?return_content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WSDC-Sync/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("ok") and "result" in data:
                return data["result"]
    except Exception as e:
        print(f"  Error fetching {path}: {e}", file=sys.stderr)
    return None


def get_text_from_node(node: Any) -> str:
    """Flatten Telegraph content node to plain text."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        tag = node.get("tag", "")
        children = node.get("children", [])
        if tag == "br":
            return "\n"
        return "".join(get_text_from_node(c) for c in children)
    return ""


def parse_leader_follower(line: str) -> tuple[str | None, str | None]:
    """Parse 'Leader (+X) [N] & Follower (+X) [N]' or similar. Returns (leader_str, follower_str)."""
    if " & " not in line:
        return (line.strip() if line.strip() else None, None)
    parts = line.split(" & ", 1)
    leader = parts[0].strip() if len(parts) > 0 else None
    follower = parts[1].strip() if len(parts) > 1 else None
    return (leader, follower)


def parse_finalists_list(line: str) -> list[str]:
    """Parse 'Name [X], Name [Y] 🟢, ...' into list of strings."""
    items = []
    # Split by comma but be careful with names that might contain commas
    for part in re.split(r",\s*", line):
        part = part.strip()
        if part:
            items.append(part)
    return items


def parse_telegraph_content(result: dict) -> dict | None:
    """
    Parse API result into structure:
    {
      "event_name": str,
      "event_dates": str,
      "divisions": {
        "Champions": {
          "places": [ {"place": "1", "leader": "...", "follower": "..."}, ... ],
          "final": {"leaders": [...], "followers": []} or None
        },
        ...
      }
    }
    """
    title = (result.get("title") or "").strip()
    description = (result.get("description") or "").strip()
    # Event name: strip " - Full Info" or " – Full Info"
    event_name = re.sub(r"\s*[-\u2013]\s*Full\s+Info\s*$", "", title, flags=re.I).strip()
    # Event dates: "📅 Event Dates: Oct 30 - Nov 3, 2025" -> "Oct 30 - Nov 3, 2025"
    event_dates = ""
    if "Event Dates:" in description or "Event Dates:" in description:
        event_dates = re.sub(r"^.*?Event\s+Dates\s*:\s*", "", description, flags=re.I).strip()
    else:
        event_dates = description

    content = result.get("content") or []
    divisions: dict[str, dict] = {}
    current_division: str | None = None
    current_places: list[dict] = []
    current_final: dict | None = None

    i = 0
    while i < len(content):
        node = content[i]
        text = get_text_from_node(node).strip()
        if isinstance(node, dict) and node.get("tag") == "h4":
            if current_division and (current_places or current_final):
                divisions[current_division] = {"places": current_places, "final": current_final}
            current_division = text
            current_places = []
            current_final = None
            i += 1
            continue
        if isinstance(node, dict) and node.get("tag") == "p" and text:
            if current_division is None:
                i += 1
                continue
            # Place line: "🥇 1 place\n Leader & Follower" or "4 place\n Leader & Follower"
            place_match = re.match(r"^(?:[^\d]*?)(\d)\s+place\s*[\s\n]*(.*)$", text, re.DOTALL)
            if place_match:
                place_num = place_match.group(1)
                rest = place_match.group(2).strip()
                leader, follower = parse_leader_follower(rest)
                current_places.append({"place": place_num, "leader": leader, "follower": follower})
                i += 1
                continue
            if "Finalists Leaders" in text or "Finalists Leaders" in text:
                rest = re.sub(r"^.*?Finalists\s+Leaders\s*\([^)]*\)\s*:\s*", "", text, flags=re.I).strip()
                current_final = current_final or {}
                current_final["leaders"] = parse_finalists_list(rest)
                i += 1
                continue
            if "Finalists Followers" in text or "Finalists Followers" in text:
                rest = re.sub(r"^.*?Finalists\s+Followers\s*\([^)]*\)\s*:\s*", "", text, flags=re.I).strip()
                current_final = current_final or {}
                current_final["followers"] = parse_finalists_list(rest)
                i += 1
                continue
        i += 1

    if current_division and (current_places or current_final):
        divisions[current_division] = {"places": current_places, "final": current_final}

    return {
        "event_name": event_name,
        "event_dates": event_dates,
        "divisions": divisions,
    }


def find_event_in_data(data: dict, event_name: str, event_dates: str, slug_hint: str | None = None, post_date_hint: str | None = None) -> tuple[dict, dict] | None:
    """
    Find event in data["summaries"][*]["events"].
    Match by normalized name + dates, or by slug/post_date if provided.
    Returns (summary_obj, event_obj) or None.
    """
    norm_name = normalize_name(event_name)
    norm_dates = normalize_dates(event_dates)
    candidates = []
    for s in data.get("summaries", []):
        for ev in s.get("events", []):
            if slug_hint and ev.get("slug") == slug_hint:
                return (s, ev)
            if post_date_hint and s.get("post_date") == post_date_hint and normalize_name(ev.get("name", "")) == norm_name:
                return (s, ev)
            if normalize_name(ev.get("name", "")) == norm_name and normalize_dates(ev.get("dates", "")) == norm_dates:
                candidates.append((s, ev))
    return candidates[0] if candidates else None


def apply_telegraph_to_event(ev: dict, parsed: dict) -> bool:
    """
    Replace leader/follower/leaders/followers in ev["divisions"] with parsed data.
    Returns True if any change was made.
    """
    changed = False
    parsed_divs = parsed.get("divisions") or {}
    for json_div in ev.get("divisions", []):
        div_name = json_div.get("division")
        if not div_name or div_name not in parsed_divs:
            continue
        pd = parsed_divs[div_name]
        # Places 1-5
        parsed_places = {p["place"]: p for p in pd.get("places", [])}
        for place_obj in json_div.get("places", []):
            place_key = place_obj.get("place")
            if place_key == "F":
                final = pd.get("final")
                if not final:
                    continue
                if final.get("leaders") is not None and "leaders" in place_obj:
                    if place_obj["leaders"] != final["leaders"]:
                        place_obj["leaders"] = final["leaders"]
                        changed = True
                if final.get("followers") is not None and "followers" in place_obj:
                    if place_obj["followers"] != final["followers"]:
                        place_obj["followers"] = final["followers"]
                        changed = True
                continue
            if place_key not in parsed_places:
                continue
            pp = parsed_places[place_key]
            if pp.get("leader") is not None and place_obj.get("leader") != pp["leader"]:
                place_obj["leader"] = pp["leader"]
                changed = True
            if pp.get("follower") is not None and place_obj.get("follower") != pp["follower"]:
                place_obj["follower"] = pp["follower"]
                changed = True
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Telegraph Full-Info pages to points_summaries.json")
    parser.add_argument("urls", nargs="*", help="Telegraph page URLs")
    parser.add_argument("--json", default=None, help="Path to points_summaries.json (default: static/data/points_summaries.json next to script)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write JSON")
    parser.add_argument("--slug", action="append", metavar="SLUG", help="Optional: match event by slug for URL at same index (repeat for each URL)")
    parser.add_argument("--post-date", action="append", metavar="DD-MM-YYYY", help="Optional: match by summary post_date for URL at same index")
    args = parser.parse_args()

    if not args.urls:
        parser.print_help()
        return 0

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    json_path = Path(args.json) if args.json else repo_root / "static" / "data" / "points_summaries.json"
    if not json_path.is_file():
        print(f"Error: JSON not found: {json_path}", file=sys.stderr)
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = []
    skipped = []
    slug_hints = (args.slug or []) + [None] * max(0, len(args.urls) - len(args.slug or []))
    post_date_hints = (args.post_date or []) + [None] * max(0, len(args.urls) - len(args.post_date or []))
    for idx, url in enumerate(args.urls):
        path = extract_path_from_url(url)
        slug_hint = slug_hints[idx] if idx < len(slug_hints) else None
        post_date_hint = post_date_hints[idx] if idx < len(post_date_hints) else None
        if not path:
            print(f"Skipping invalid URL: {url}")
            skipped.append(url)
            continue
        print(f"Fetching {path} ...")
        result = fetch_telegraph_page(path)
        if not result:
            print(f"  Failed to fetch")
            skipped.append(url)
            continue
        parsed = parse_telegraph_content(result)
        if not parsed or not parsed.get("event_name"):
            print(f"  Could not parse event name/dates")
            skipped.append(url)
            continue
        name = parsed["event_name"]
        dates = parsed["event_dates"]
        found = find_event_in_data(data, name, dates, slug_hint=slug_hint, post_date_hint=post_date_hint)
        if not found:
            print(f"  Event not found in JSON: '{name}' / '{dates}'")
            skipped.append(url)
            continue
        _, ev = found
        if apply_telegraph_to_event(ev, parsed):
            updated.append((name, dates))
            print(f"  Updated: {name}")
        else:
            print(f"  No changes: {name}")

    if updated and not args.dry_run:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {json_path} ({len(updated)} event(s) updated).")
    elif updated and args.dry_run:
        print(f"\nDry run: would update {len(updated)} event(s).")

    if skipped:
        print(f"Skipped/failed: {len(skipped)} URL(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
