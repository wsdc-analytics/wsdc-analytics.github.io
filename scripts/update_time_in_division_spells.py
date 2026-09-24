#!/usr/bin/env python3
"""Build spell-level time-in-division rows for the Time in division dashboard.

Spell = (dancer × division × role). Duration = inclusive calendar months from
first point in that spell until the selected rules threshold (allowed / required)
is first reached (same month = 1; Nov→Mar = 5). Event count = unique event
editions in that division×role up to and including the crossing event for that
threshold (not the whole career in the division).

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


def months_inclusive(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Inclusive calendar months from first to done (same month → 1; Nov→Mar → 5).

    Day-of-month is unknown, so we count months touched rather than index delta.
    """
    return (b[0] - a[0]) * 12 + (b[1] - a[1]) + 1


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


BUFFER_FRACS = (("p25", 0.25), ("p50", 0.50), ("p75", 0.75))
LADDER = ["Novice", "Intermediate", "Advanced", "All-Stars", "Champions"]


def buffer_done(
    buffer: dict[str, dict],
    allowed_t: float | None,
    required_t: float | None,
) -> bool:
    """True when buffer marks are complete or the may/must gap has no room for them."""
    if allowed_t is None or required_t is None:
        return True
    if float(required_t) - float(allowed_t) <= 0:
        return True
    return len(buffer) >= len(BUFFER_FRACS)


def hit_dict(months: int, done_ym: str, events: int, **extra) -> dict:
    out = {"months": months, "done_ym": done_ym, "events": events}
    out.update(extra)
    return out


def record_buffer_marks(
    buffer: dict[str, dict],
    score: float,
    months: int,
    done_ym: str,
    events: int,
    allowed_t: float | None,
    required_t: float | None,
) -> None:
    """Mark 25/50/75% of the may→must point gap once allowed is known."""
    if allowed_t is None or required_t is None:
        return
    span = float(required_t) - float(allowed_t)
    if span <= 0:
        return
    for key, frac in BUFFER_FRACS:
        if key in buffer:
            continue
        target = float(allowed_t) + frac * span
        if score >= target:
            buffer[key] = hit_dict(
                months,
                done_ym,
                events,
                score_target=round(target, 2),
                buffer_frac=frac,
            )


def find_nov_int_crossings(
    events: list[dict],
    division: str,
    t0: tuple[int, int],
    rules: dict,
) -> dict[str, dict]:
    reached: dict[str, dict] = {}
    buffer: dict[str, dict] = {}
    cum = 0.0
    seen_events: set[str] = set()
    for e in events:
        if e["div"] != division or e["ym"] < t0:
            continue
        th = threshold_for_year(rules, e["year"], division)
        if not th or th.get("allowed") is None:
            continue
        seen_events.add(e["eid"])
        cum += e["pts"]
        months = months_inclusive(t0, e["ym"])
        done = ym_str(e["ym"])
        for kind in ("allowed", "required"):
            if kind in reached:
                continue
            target = th.get(kind)
            if target is not None and cum >= float(target):
                reached[kind] = hit_dict(months, done, len(seen_events), threshold=float(target))
        if "allowed" in reached:
            record_buffer_marks(
                buffer,
                cum,
                months,
                done,
                len(seen_events),
                reached["allowed"].get("threshold"),
                th.get("required"),
            )
        if "required" in reached and buffer_done(
            buffer, reached["allowed"].get("threshold"), th.get("required")
        ):
            break
    out = dict(reached)
    if buffer:
        out["buffer"] = buffer
    return out


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
    buffer: dict[str, dict] = {}
    cum = 0.0
    seen_events: set[str] = set()
    for e in events:
        if e["div"] != "Advanced" or e["ym"] < t0:
            continue
        seen_events.add(e["eid"])
        cum += e["pts"]
        th = threshold_for_year(rules, e["year"], "Advanced")
        if not th or th.get("allowed") is None:
            continue
        counting = th.get("counting", "cumulative")
        if counting == "rolling_36mo":
            score = rolling_sum(events, "Advanced", e["ym"], 36)
        else:
            score = cum
        months = months_inclusive(t0, e["ym"])
        done = ym_str(e["ym"])
        for kind in ("allowed", "required"):
            if kind in reached:
                continue
            target = th.get(kind)
            if target is not None and score >= float(target):
                reached[kind] = hit_dict(months, done, len(seen_events), threshold=float(target))
        if "allowed" in reached:
            record_buffer_marks(
                buffer,
                score,
                months,
                done,
                len(seen_events),
                reached["allowed"].get("threshold"),
                th.get("required"),
            )
        if "required" in reached and buffer_done(
            buffer, reached["allowed"].get("threshold"), th.get("required")
        ):
            break
    out = dict(reached)
    if buffer:
        out["buffer"] = buffer
    return out


def find_all_stars_crossings(
    events: list[dict],
    t0: tuple[int, int],
    rules: dict,
) -> dict[str, dict]:
    """All-Stars→Champions may/must on real AS/Champ events.

    Pre-formal rules years: Champions points only (1 allowed / 10 required).
    Formal years (2021+): OR of Champions pts or All-Stars pts from the active epoch.
    Buffer marks use Champions-point path only (numeric Champ targets).
    """
    reached: dict[str, dict] = {}
    buffer: dict[str, dict] = {}
    as_pts = 0.0
    champ_pts = 0.0
    seen_events: set[str] = set()
    allowed_champ_t: float | None = None
    required_champ_t: float | None = None
    for e in events:
        if e["ym"] < t0:
            continue
        if e["div"] == "All-Stars":
            as_pts += e["pts"]
        elif e["div"] == "Champions":
            champ_pts += e["pts"]
        else:
            continue
        seen_events.add(e["eid"])
        specs = all_stars_eval_specs(rules, e["year"])
        if not specs:
            continue
        months = months_inclusive(t0, e["ym"])
        done = ym_str(e["ym"])
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
            if kind == "allowed":
                allowed_champ_t = need_c or None
            else:
                required_champ_t = need_c or None
            if (need_c and champ_pts >= need_c) or (need_as and as_pts >= need_as):
                reached[kind] = hit_dict(
                    months,
                    done,
                    len(seen_events),
                    threshold_champions=need_c,
                    threshold_all_stars=need_as,
                    champions_points_at_done=round(champ_pts, 2),
                    all_stars_points_at_done=round(as_pts, 2),
                )
        if "allowed" in reached and allowed_champ_t and required_champ_t:
            record_buffer_marks(
                buffer,
                champ_pts,
                months,
                done,
                len(seen_events),
                allowed_champ_t,
                required_champ_t,
            )
        # Required done: stop. Champ-path buffer is best-effort (AS-OR crossings may leave it empty).
        if "required" in reached:
            break
    out = dict(reached)
    if buffer:
        out["buffer"] = buffer
    return out


def build_transitions(
    events_by_spell_role: dict[tuple[str, str], list[dict]],
    name_by_id: dict[str, str],
) -> list[dict]:
    """JT-2: inclusive months from last point in D to first point in D+1 (same role)."""
    rows: list[dict] = []
    for (did, role), evs in events_by_spell_role.items():
        by_div: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for e in evs:
            by_div[e["div"]].append(e["ym"])
        for i in range(len(LADDER) - 1):
            lo, hi = LADDER[i], LADDER[i + 1]
            if lo not in by_div or hi not in by_div:
                continue
            last_lo = max(by_div[lo])
            first_hi = min(by_div[hi])
            overlap = ym_ord(*first_hi) < ym_ord(*last_lo)
            row = {
                "id": did,
                "name": name_by_id.get(did) or did,
                "role": role,
                "from_division": lo,
                "to_division": hi,
                "last_ym": ym_str(last_lo),
                "first_ym": ym_str(first_hi),
                "overlap": overlap,
            }
            if not overlap:
                row["months"] = months_inclusive(last_lo, first_hi)
            rows.append(row)
    rows.sort(key=lambda r: (r["from_division"], r["to_division"], r["role"], r["id"]))
    return rows


def build_qualify_series(
    spells: list[dict],
    first_pts: dict[tuple[str, str, str], tuple[int, int]],
) -> dict:
    """JN-1b: yearly counts — Advanced may (eligible) vs first All-Stars point."""
    adv_allowed: dict[str, int] = defaultdict(int)
    first_as: dict[str, int] = defaultdict(int)
    for s in spells:
        if s.get("division") == "Advanced" and "allowed" in s:
            y = str(s["allowed"]["done_ym"])[:4]
            adv_allowed[y] += 1
    for (did, role, div), t0 in first_pts.items():
        if div != "All-Stars":
            continue
        first_as[f"{t0[0]:04d}"] += 1

    def series(by_year: dict[str, int]) -> list[dict]:
        years = sorted(by_year)
        cum = 0
        out = []
        for y in years:
            cum += by_year[y]
            out.append({"year": int(y), "n": by_year[y], "cumulative": cum})
        return out

    return {
        "advanced_allowed": series(adv_allowed),
        "first_all_stars": series(first_as),
    }


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
            # Edition-unique id: event_name alone collides across years (e.g. annual MADjam),
            # which under-counts events-to-threshold when the spell spans the year floor.
            eid_base = (row.get("event_name_id") or row.get("event_name") or "").strip() or "event"
            eid = f"{eid_base}|{y:04d}-{m:02d}"
            events_by_spell_role[(did, role)].append(
                {"div": div, "pts": pts, "ym": dt, "year": y, "eid": eid}
            )
            key = (did, role, div)
            if key not in first_pts or dt < first_pts[key]:
                first_pts[key] = dt

    for key in events_by_spell_role:
        events_by_spell_role[key].sort(key=lambda e: (ym_ord(*e["ym"]), e["eid"]))

    observation_end = max(
        (e["ym"] for evs in events_by_spell_role.values() for e in evs),
        default=(date.today().year, date.today().month),
    )
    # Concrete calendar date of this rebuild (title-row "Updated"), not event month.
    generated_at = date.today().isoformat()
    data_through = f"{observation_end[0]:04d}-{observation_end[1]:02d}"
    # Backward-compatible alias: dashboards historically read data_as_of as the stamp.
    data_as_of = generated_at

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
        }
        if "allowed" in crossings:
            row["allowed"] = crossings["allowed"]
        if "required" in crossings:
            row["required"] = crossings["required"]
        if "buffer" in crossings:
            row["buffer"] = crossings["buffer"]
        spells.append(row)

    spells.sort(key=lambda r: (r["division"], r["role"], r["id"]))
    transitions = build_transitions(events_by_spell_role, name_by_id)
    qualify = build_qualify_series(spells, first_pts)

    payload = {
        "data_as_of": data_as_of,
        "generated_at": generated_at,
        "data_through": data_through,
        "rules_ref": "rules_advancement_thresholds.json",
        "bin_months": 6,
        "bin_events": 2,
        "divisions": DASHBOARD_DIVISIONS,
        "ladder": LADDER,
        "n_spells": len(spells),
        "n_transitions": len(transitions),
        "excluded_counts": excluded,
        "methodology": {
            "spell": "dancer × division × event_role",
            "months": "inclusive calendar months from first_ym through done_ym (same month = 1; Nov→Mar = 5); day-of-month unknown",
            "events": "unique event editions (name + year-month) in that division×role up to and including the crossing event for the selected threshold; history before the dashboard year floor still counts",
            "buffer": "p25/p50/p75 = first reach of allowed + frac×(required−allowed) points; share among spells that reached May",
            "pause": "JT-2 inclusive months from last point in division D to first in D+1 (same role); overlap flagged and excluded from pause median",
            "qualify": "JN-1b yearly n and cumulative: Advanced allowed (eligible) vs first All-Stars point (entered)",
            "window_filter": "display only: done_ym inside From–To and division year floor (Nov/Int/Adv ≥2018, All-Stars ≥2021); calculation uses full spell history from first_ym; pause/qualify sheets do not use the may/must year floor",
            "data_stamp": "generated_at = calendar date this JSON was rebuilt; data_through = latest event year-month in the source export",
            "all_stars": (
                "pre-formal rules years: Champions pts only (1 may / 10 must) on real events; "
                "from first All-Stars rules year (2021): full OR Champ pts or AS pts; "
                "no synthetic done_ym at rule start"
            ),
        },
        "spells": spells,
        "transitions": transitions,
        "qualify": qualify,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(spells)} spells, {len(transitions)} transitions -> {args.output}")
    print(f"generated_at={generated_at} data_through={data_through} excluded={excluded}")


if __name__ == "__main__":
    main()
