#!/usr/bin/env python3
"""Build spell-level time-in-division rows for the Time in division dashboard.

Spell = (dancer × division × role). Duration = months from first point in that
spell until the selected rules threshold (allowed / required) is first reached.
Event count = unique events with a point in that division×role over the career.

Reuses year-month arithmetic and rules epochs from division-transition analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/Users/ania/.cursor/projects/python/wsdc-data-pipeline/data")
DEFAULT_RULES = REPO_ROOT / "static" / "data" / "rules_advancement_thresholds.json"
DEFAULT_OUTPUT = REPO_ROOT / "static" / "data" / "time_in_division_spells.json"

SKILL_DIVISIONS = ["Novice", "Intermediate", "Advanced", "All-Stars", "Champions"]
DASHBOARD_DIVISIONS = ["Novice", "Intermediate", "Advanced", "All-Stars"]
ROLES = ("Leader", "Follower")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update time-in-division spell JSON.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def norm_div(value: str) -> str | None:
    v = (value or "").strip()
    if v in {"All Star", "All-Star", "All Stars", "All-Stars"}:
        return "All-Stars"
    if v in {"Champion", "Champions"}:
        return "Champions"
    if v in SKILL_DIVISIONS:
        return v
    return None


def parse_date(ym: str, year: str = "", month: str = "") -> tuple[int, int] | None:
    if not ym and year and month:
        try:
            return (int(float(year)), int(float(month)))
        except ValueError:
            return None
    if not ym:
        return None
    s = str(ym).strip()
    if "-" in s:
        parts = s.split("-")
        try:
            return (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return None
    if len(s) >= 6:
        try:
            return (int(s[:4]), int(s[4:6]))
        except ValueError:
            return None
    return None


def ym_ord(y: int, m: int) -> int:
    return y * 12 + m


def months_between(a: tuple[int, int], b: tuple[int, int]) -> int:
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def ym_str(ym: tuple[int, int]) -> str:
    return f"{ym[0]:04d}-{ym[1]:02d}"


def epoch_for_year(rules: dict, year: int) -> dict | None:
    for epoch in rules.get("epochs", []):
        vf = epoch.get("valid_from")
        vt = epoch.get("valid_to")
        if vf is not None and year < vf:
            continue
        if vt is not None and year > vt:
            continue
        return epoch
    return None


def threshold_for_year(rules: dict, year: int, division: str) -> dict:
    epoch = epoch_for_year(rules, year)
    if not epoch:
        return {}
    model = epoch.get("model")
    if model in ("allowed_required_36mo", "allowed_required"):
        d = epoch.get("divisions", {}).get(division)
        if not d:
            return {}
        out: dict = {"epoch": epoch["id"]}
        if "allowed" in d:
            out["allowed"] = d["allowed"]
            out["required"] = d["required"]
            out["counting"] = d.get("counting", "cumulative")
        if "champions_allowed" in d:
            out["champions_allowed"] = d["champions_allowed"]
            out["champions_required"] = d["champions_required"]
        return out
    if model == "cumulative":
        trans = epoch.get("transitions", {})
        if division in trans:
            p = trans[division]["points"]
            return {
                "allowed": p,
                "required": p,
                "epoch": epoch["id"],
                "counting": "cumulative",
            }
    return {}


def first_all_stars_rules_year(rules: dict) -> int | None:
    """Earliest valid_from among epochs that define All-Stars→Champions thresholds."""
    years: list[int] = []
    for epoch in rules.get("epochs", []):
        d = (epoch.get("divisions") or {}).get("All-Stars")
        if not d or "champions_allowed" not in d:
            continue
        vf = epoch.get("valid_from")
        if vf is not None:
            years.append(int(vf))
    return min(years) if years else None


def catalogued_all_stars_division(rules: dict) -> dict | None:
    """First All-Stars block in rules JSON (source of champ/AS point targets)."""
    for epoch in rules.get("epochs", []):
        d = (epoch.get("divisions") or {}).get("All-Stars")
        if d and "champions_allowed" in d:
            return d
    return None


def all_stars_eval_specs(rules: dict, year: int) -> dict[str, dict]:
    """May/Must specs for All-Stars at event year.

    - Before formal All-Stars→Champions rules (pre-2021): Champions-point path only
      (1 / 10). AS-point OR is not applied — that threshold did not exist yet.
    - From formal rules year onward: full OR (Champ pts or AS pts) from the active epoch.
    Crossing is recorded only on real AS/Champ events (no synthetic rule-start month).
    """
    formal_from = first_all_stars_rules_year(rules)
    catalog = catalogued_all_stars_division(rules)
    if not catalog:
        return {}

    if formal_from is not None and year >= formal_from:
        th = threshold_for_year(rules, year, "All-Stars")
        out: dict[str, dict] = {}
        for key in ("champions_allowed", "champions_required"):
            spec = th.get(key) if th else None
            if not isinstance(spec, dict):
                spec = catalog.get(key)
            if isinstance(spec, dict):
                out[key] = {
                    "champions_points": float(spec.get("champions_points") or 0),
                    "or_all_star_points": float(spec.get("or_all_star_points") or 0),
                }
        return out

    # Pre-formal era: Champ path only (disable AS OR).
    out = {}
    for key in ("champions_allowed", "champions_required"):
        spec = catalog.get(key)
        if isinstance(spec, dict):
            out[key] = {
                "champions_points": float(spec.get("champions_points") or 0),
                "or_all_star_points": 0.0,
            }
    return out


def rolling_sum(events: list[dict], div: str, at_ym: tuple[int, int], window: int = 36) -> float:
    at = ym_ord(*at_ym)
    lo = at - window + 1
    return sum(e["pts"] for e in events if e["div"] == div and lo <= ym_ord(*e["ym"]) <= at)


def find_nov_int_crossings(
    events: list[dict],
    division: str,
    t0: tuple[int, int],
    rules: dict,
) -> dict[str, dict]:
    reached: dict[str, dict] = {}
    cum = 0.0
    for e in events:
        if e["div"] != division or e["ym"] < t0:
            continue
        th = threshold_for_year(rules, e["year"], division)
        if not th or th.get("allowed") is None:
            continue
        cum += e["pts"]
        months = months_between(t0, e["ym"])
        for kind in ("allowed", "required"):
            if kind in reached:
                continue
            target = th.get(kind)
            if target is not None and cum >= float(target):
                reached[kind] = {
                    "months": months,
                    "done_ym": ym_str(e["ym"]),
                    "threshold": float(target),
                }
        if len(reached) == 2:
            break
    return reached


def find_advanced_crossings(
    events: list[dict],
    t0: tuple[int, int],
    rules: dict,
) -> dict[str, dict]:
    """Cross allowed/required using the counting model active at each event month.

    Cumulative score always includes all Advanced points from first point forward,
    so an era switch (rolling → cumulative) does not drop earlier points.
    Rolling eras still evaluate the 36-month window at each event.
    """
    reached: dict[str, dict] = {}
    cum = 0.0
    for e in events:
        if e["div"] != "Advanced" or e["ym"] < t0:
            continue
        cum += e["pts"]
        th = threshold_for_year(rules, e["year"], "Advanced")
        if not th or th.get("allowed") is None:
            continue
        counting = th.get("counting", "cumulative")
        if counting == "rolling_36mo":
            score = rolling_sum(events, "Advanced", e["ym"], 36)
        else:
            score = cum
        months = months_between(t0, e["ym"])
        for kind in ("allowed", "required"):
            if kind in reached:
                continue
            target = th.get(kind)
            if target is not None and score >= float(target):
                reached[kind] = {
                    "months": months,
                    "done_ym": ym_str(e["ym"]),
                    "threshold": float(target),
                }
        if len(reached) == 2:
            break
    return reached


def find_all_stars_crossings(
    events: list[dict],
    t0: tuple[int, int],
    rules: dict,
) -> dict[str, dict]:
    """All-Stars→Champions may/must on real AS/Champ events.

    Pre-formal rules years: Champions points only (1 allowed / 10 required).
    Formal years (2021+): OR of Champions pts or All-Stars pts from the active epoch.
    """
    reached: dict[str, dict] = {}
    as_pts = 0.0
    champ_pts = 0.0
    for e in events:
        if e["ym"] < t0:
            continue
        if e["div"] == "All-Stars":
            as_pts += e["pts"]
        elif e["div"] == "Champions":
            champ_pts += e["pts"]
        else:
            continue
        specs = all_stars_eval_specs(rules, e["year"])
        if not specs:
            continue
        months = months_between(t0, e["ym"])
        for kind, key in (
            ("allowed", "champions_allowed"),
            ("required", "champions_required"),
        ):
            if kind in reached:
                continue
            spec = specs.get(key)
            if not isinstance(spec, dict):
                continue
            need_c = float(spec.get("champions_points") or 0)
            need_as = float(spec.get("or_all_star_points") or 0)
            if (need_c and champ_pts >= need_c) or (need_as and as_pts >= need_as):
                reached[kind] = {
                    "months": months,
                    "done_ym": ym_str(e["ym"]),
                    "threshold_champions": need_c,
                    "threshold_all_stars": need_as,
                    "champions_points_at_done": round(champ_pts, 2),
                    "all_stars_points_at_done": round(as_pts, 2),
                }
        if len(reached) == 2:
            break
    return reached


def main() -> None:
    args = parse_args()
    source = args.source_dir
    rules = json.loads(args.rules.read_text(encoding="utf-8"))

    name_by_id: dict[str, str] = {}
    with (source / "dancer_role_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            if did:
                name_by_id[did] = (row.get("dancer_name") or "").strip()

    # events keyed by (dancer_id, role)
    events_by_spell_role: dict[tuple[str, str], list[dict]] = defaultdict(list)
    # unique events per (dancer, role, division)
    event_ids: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    first_pts: dict[tuple[str, str, str], tuple[int, int]] = {}

    excluded = {
        "invalid_date": 0,
        "non_skill_division": 0,
        "bad_role": 0,
        "non_positive_points": 0,
    }

    with (source / "dancers_results_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            if not did:
                continue
            div = norm_div(row.get("event_competition") or "")
            if div is None:
                excluded["non_skill_division"] += 1
                continue
            role = (row.get("event_role") or "").strip().title()
            if role not in ROLES:
                excluded["bad_role"] += 1
                continue
            try:
                pts = float(row.get("event_points") or 0)
            except ValueError:
                pts = 0.0
            if pts <= 0:
                excluded["non_positive_points"] += 1
                continue
            dt = parse_date(
                row.get("event_year_and_month") or "",
                row.get("event_year") or "",
                row.get("event_month") or "",
            )
            if dt is None:
                excluded["invalid_date"] += 1
                continue
            y, m = dt
            eid = (row.get("event_name_id") or row.get("event_name") or "").strip()
            if not eid:
                eid = f"{row.get('event_name')}_{y}_{m}"
            events_by_spell_role[(did, role)].append(
                {"div": div, "pts": pts, "ym": dt, "year": y, "eid": eid}
            )
            key = (did, role, div)
            event_ids[key].add(eid)
            if key not in first_pts or dt < first_pts[key]:
                first_pts[key] = dt

    for key in events_by_spell_role:
        events_by_spell_role[key].sort(key=lambda e: (ym_ord(*e["ym"]), e["eid"]))

    observation_end = max(
        (e["ym"] for evs in events_by_spell_role.values() for e in evs),
        default=(date.today().year, date.today().month),
    )
    data_as_of = f"{observation_end[0]:04d}-{observation_end[1]:02d}-01"

    spells: list[dict] = []
    for (did, role, div), t0 in first_pts.items():
        if div not in DASHBOARD_DIVISIONS:
            continue
        evs = events_by_spell_role[(did, role)]
        if div in ("Novice", "Intermediate"):
            crossings = find_nov_int_crossings(evs, div, t0, rules)
        elif div == "Advanced":
            crossings = find_advanced_crossings(evs, t0, rules)
        else:
            crossings = find_all_stars_crossings(evs, t0, rules)

        if not crossings:
            continue

        row = {
            "id": did,
            "name": name_by_id.get(did) or did,
            "role": role,
            "division": div,
            "first_ym": ym_str(t0),
            "events": len(event_ids[(did, role, div)]),
        }
        if "allowed" in crossings:
            row["allowed"] = crossings["allowed"]
        if "required" in crossings:
            row["required"] = crossings["required"]
        spells.append(row)

    spells.sort(key=lambda r: (r["division"], r["role"], r["id"]))

    payload = {
        "data_as_of": data_as_of,
        "rules_ref": "rules_advancement_thresholds.json",
        "bin_months": 6,
        "bin_events": 2,
        "divisions": DASHBOARD_DIVISIONS,
        "n_spells": len(spells),
        "excluded_counts": excluded,
        "methodology": {
            "spell": "dancer × division × event_role",
            "months": "calendar months between first_ym and done_ym (year-month only)",
            "events": "unique events with a point in that division×role over the career",
            "window_filter": "done_ym inside trailing N years from data_as_of",
            "all_stars": (
                "pre-formal rules years: Champions pts only (1 may / 10 must) on real events; "
                "from first All-Stars rules year (2021): full OR Champ pts or AS pts; "
                "no synthetic done_ym at rule start"
            ),
        },
        "spells": spells,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(spells)} spells -> {args.output}")
    print(f"data_as_of={data_as_of} excluded={excluded}")


if __name__ == "__main__":
    main()
