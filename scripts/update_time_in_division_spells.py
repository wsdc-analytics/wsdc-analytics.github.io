#!/usr/bin/env python3
"""Build spell-level time-in-division rows for the Time in division dashboard.

Spell = (dancer × division × role). Duration prefers edition calendar dates
(start_date → end_date): days / 30.44, rounded to 0.1 month (min 1 day when
dates are valid). If either endpoint lacks a usable date (or end < start),
falls back to inclusive calendar months (same month = 1; Nov→Mar = 5).
Event count = unique event editions in that division×role up to and including
the crossing event for that threshold.

Rolling 36-month Advanced scoring windows stay calendar months (rules), not days.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/Users/ania/.cursor/projects/python/wsdc-data-pipeline/data")
DEFAULT_RULES = REPO_ROOT / "static" / "data" / "rules_advancement_thresholds.json"
DEFAULT_OUTPUT = REPO_ROOT / "static" / "data" / "time_in_division_spells.json"

SKILL_DIVISIONS = ["Novice", "Intermediate", "Advanced", "All-Stars", "Champions"]
DASHBOARD_DIVISIONS = ["Novice", "Intermediate", "Advanced", "All-Stars"]
ROLES = ("Leader", "Follower")

AVG_DAYS_PER_MONTH = 30.44
MIN_DAY_DURATION = 1
FUZZY_NAME_CUTOFF = 0.62


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


def norm_event_name(value: str) -> str:
    s = (value or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def parse_iso_date(value: str | None) -> date | None:
    s = (value or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def edition_anchor_date(row: dict) -> date | None:
    """Prefer start_date, else end_date."""
    for key in ("start_date", "end_date", "planned_start_date", "planned_end_date"):
        d = parse_iso_date(row.get(key))
        if d is not None:
            return d
    return None


def load_edition_day_index(
    source: Path,
) -> tuple[dict[tuple[str, int, int], date], dict[tuple[int, int], list[tuple[str, date]]]]:
    """Exact (norm_name, year, month) → date, plus same-YM candidates for fuzzy match."""
    path = source / "event_editions.csv"
    exact: dict[tuple[str, int, int], date] = {}
    by_ym: dict[tuple[int, int], list[tuple[str, date]]] = defaultdict(list)
    if not path.exists():
        return exact, by_ym
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                y = int(float(row.get("event_year") or 0))
                m = int(float(row.get("event_month") or 0))
            except ValueError:
                continue
            if y < 1900 or not (1 <= m <= 12):
                continue
            day = edition_anchor_date(row)
            if day is None:
                continue
            name = norm_event_name(row.get("event_name") or "")
            if not name:
                continue
            key = (name, y, m)
            prev = exact.get(key)
            if prev is None or day < prev:
                exact[key] = day
            by_ym[(y, m)].append((name, day))
    return exact, by_ym


def lookup_edition_day(
    exact: dict[tuple[str, int, int], date],
    by_ym: dict[tuple[int, int], list[tuple[str, date]]],
    event_name: str,
    year: int,
    month: int,
) -> date | None:
    name = norm_event_name(event_name)
    if not name:
        return None
    hit = exact.get((name, year, month))
    if hit is not None:
        return hit
    cands = by_ym.get((year, month)) or []
    if not cands:
        return None
    names = list({n for n, _ in cands})
    match = difflib.get_close_matches(name, names, n=1, cutoff=FUZZY_NAME_CUTOFF)
    if not match:
        return None
    matched = match[0]
    days = [d for n, d in cands if n == matched]
    return min(days) if days else None


def duration_months(
    start_ym: tuple[int, int],
    end_ym: tuple[int, int],
    start_day: date | None,
    end_day: date | None,
) -> tuple[float, str]:
    """Day-path when both dates usable; else inclusive YM. Returns (months, basis)."""
    if start_day is not None and end_day is not None:
        delta = (end_day - start_day).days
        if delta >= 0:
            days = max(delta, MIN_DAY_DURATION)
            months = round(days / AVG_DAYS_PER_MONTH, 1)
            # 1 day ≈ 0.03 → would round to 0.0; keep a visible 0.1 floor on day-path.
            if months < 0.1:
                months = 0.1
            return months, "day"
    # Inclusive YM never returns < 1 for ordered endpoints; clamp guards inverted YM.
    return float(max(months_inclusive(start_ym, end_ym), 1)), "ym"


def first_event_in_div(
    events: list[dict],
    division: str,
    t0: tuple[int, int],
) -> dict | None:
    same = [e for e in events if e["div"] == division and e["ym"] == t0]
    if same:
        with_day = [e for e in same if e.get("day") is not None]
        return (with_day or same)[0]
    later = [e for e in events if e["div"] == division and e["ym"] >= t0]
    if later:
        with_day = [e for e in later if e.get("day") is not None]
        return (with_day or later)[0]
    return None


def day_for_ym(
    events: list[dict],
    ym: tuple[int, int],
    divs: set[str] | None = None,
    prefer: str = "last",
) -> date | None:
    cands = [
        e
        for e in events
        if e["ym"] == ym and (divs is None or e["div"] in divs)
    ]
    if not cands:
        return None
    with_day = [e for e in cands if e.get("day") is not None]
    pool = with_day or cands
    pick = pool[-1] if prefer == "last" else pool[0]
    return pick.get("day")


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


def activity_years_for_division(events: list[dict], division: str) -> list[int]:
    """Sorted unique calendar years with a scored point in this division.

    All-Stars spells count All-Stars contests only (Champions is next division).
    """
    years = {
        int(e["year"])
        for e in events
        if e.get("div") == division and float(e.get("pts") or 0) > 0
    }
    return sorted(years)


BUFFER_FRACS = (("p25", 0.25), ("p50", 0.50), ("p75", 0.75))
LADDER = ["Novice", "Intermediate", "Advanced", "All-Stars", "Champions"]
NEXT_DIVISION = {
    "Novice": "Intermediate",
    "Intermediate": "Advanced",
    "Advanced": "All-Stars",
    "All-Stars": "Champions",
}


def _ym_from_str(ym: str | None) -> tuple[int, int] | None:
    if not ym:
        return None
    try:
        y, m = str(ym).strip().split("-")[:2]
        return (int(y), int(m))
    except (ValueError, IndexError):
        return None


def _parse_iso_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _event_ord(e: dict) -> tuple[int, date]:
    day = e.get("day")
    return (ym_ord(*e["ym"]), day if isinstance(day, date) else date.min)


def _hit_ord(hit: dict | None) -> tuple[int, date] | None:
    if not hit:
        return None
    ym = _ym_from_str(hit.get("done_ym"))
    if not ym:
        return None
    day = _parse_iso_day(hit.get("done_date"))
    return (ym_ord(*ym), day if day is not None else date.max)


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


def hit_dict(
    months: float,
    done_ym: str,
    events: int,
    *,
    done_date: date | None = None,
    **extra,
) -> dict:
    out = {"months": months, "done_ym": done_ym, "events": events}
    if done_date is not None:
        out["done_date"] = done_date.isoformat()
    out.update(extra)
    return out


def record_buffer_marks(
    buffer: dict[str, dict],
    score: float,
    months: float,
    done_ym: str,
    events: int,
    allowed_t: float | None,
    required_t: float | None,
    months_basis: str = "ym",
    done_date: date | None = None,
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
                done_date=done_date,
                months_basis=months_basis,
                score_target=round(target, 2),
                buffer_frac=frac,
            )


def _basket_from_progress(
    score: float,
    allowed_t: float | None,
    required_t: float | None,
    reached_must: bool,
) -> str:
    if reached_must:
        return "must"
    if allowed_t is None or required_t is None:
        return "lt25"
    span = float(required_t) - float(allowed_t)
    # May == Must (no gap): Buffer cohort already cleared May, so basket is Must.
    if span <= 0:
        return "must"
    progress = (float(score) - float(allowed_t)) / span
    if progress >= 0.75:
        return "p75"
    if progress >= 0.50:
        return "p50"
    if progress >= 0.25:
        return "p25"
    return "lt25"


def _all_stars_path_thresholds(rules: dict, year: int) -> dict[str, float | None]:
    """May/Must targets for both All-Stars Buffer paths (Champ pts and AS pts)."""
    specs = all_stars_eval_specs(rules, year)
    out: dict[str, float | None] = {
        "champ_allowed": None,
        "champ_required": None,
        "as_allowed": None,
        "as_required": None,
    }
    a = specs.get("champions_allowed")
    r = specs.get("champions_required")
    if isinstance(a, dict):
        if a.get("champions_points"):
            out["champ_allowed"] = float(a["champions_points"])
        if a.get("or_all_star_points"):
            out["as_allowed"] = float(a["or_all_star_points"])
    if isinstance(r, dict):
        if r.get("champions_points"):
            out["champ_required"] = float(r["champions_points"])
        if r.get("or_all_star_points"):
            out["as_required"] = float(r["or_all_star_points"])
    return out


_BASKET_RANK = {"lt25": 0, "p25": 1, "p50": 2, "p75": 3, "must": 4}


def _filter_advanced_still_may_eligible(
    events: list[dict],
    div_events: list[dict],
    post_may: list[dict],
    rules: dict,
    t0: tuple[int, int],
) -> list[dict]:
    """Keep only post-May Advanced events where score still meets that year's May.

    Threshold rises (45→60) and rolling windows can remove May rights; later
    Advanced contests without current All-Stars eligibility are not Buffer.
    """
    if not post_may:
        return []
    post_eids = {e["eid"] for e in post_may}
    eligible: list[dict] = []
    cum = 0.0
    for e in div_events:
        if e["div"] != "Advanced" or e["ym"] < t0:
            continue
        cum += e["pts"]
        if e["eid"] not in post_eids:
            continue
        th = threshold_for_year(rules, e["year"], "Advanced")
        allowed = th.get("allowed") if th else None
        if allowed is None:
            continue
        counting = (th or {}).get("counting", "cumulative")
        if counting == "rolling_36mo":
            score = rolling_sum(events, "Advanced", e["ym"], 36)
        else:
            score = cum
        if score >= float(allowed):
            eligible.append(e)
    return eligible


def compute_stay_after_may(
    events: list[dict],
    division: str,
    t0: tuple[int, int],
    crossings: dict[str, dict],
    rules: dict,
    observation_end: tuple[int, int],
) -> dict | None:
    """Post-May stay in the lower division (Buffer chart cohort).

    Cohort: reached May AND ≥1 scored event in the same division×role strictly
    after May, excluding dancers who already had a next-division point before
    that first post-May lower point.
    Window: May → last lower point at or before earliest of Must / first next /
    data cut-off.

    All-Stars: Buffer only counts the formal All-Stars→Champions era (rules year
    onward). Pre-era Champion points do not start the window; effective May is
    the first All-Stars event in the formal era when registry May was earlier.
    Months and events count All-Stars (buffer) performances only — Champions
    contests are ignored for stay length. Required Champions (career Champions
    points reached Must, typically ≥10) are never Buffer Dancers — even if they
    later scored All-Stars points. Buffer basket / Must exit use the All-Stars
    points path only (career AS pts vs 150→225); Champ pts below Must may still
    appear in the tooltip as context.
    """
    allowed = crossings.get("allowed")
    if not allowed:
        return None
    may_ord = _hit_ord(allowed)
    if may_ord is None:
        return None

    next_div = NEXT_DIVISION.get(division)
    if not next_div:
        return None

    # All-Stars: track AS + Champions for point paths; stay metrics use AS only.
    if division == "All-Stars":
        track_divs = {"All-Stars", "Champions"}
    else:
        track_divs = {division}

    div_events = sorted(
        [e for e in events if e["div"] in track_divs and e["ym"] >= t0],
        key=_event_ord,
    )

    may_clipped = False
    may_ym = _ym_from_str(allowed.get("done_ym"))
    may_day = _parse_iso_day(allowed.get("done_date"))
    may_ym_out = allowed.get("done_ym")
    may_date_out = allowed.get("done_date")
    effective_may_ord = may_ord

    if division == "All-Stars":
        formal_from = first_all_stars_rules_year(rules) or 2021
        formal_ord = (ym_ord(formal_from, 1), date.min)
        formal_events = [e for e in div_events if e["year"] >= formal_from]
        formal_as_events = [e for e in formal_events if e["div"] == "All-Stars"]
        if may_ord < formal_ord:
            # Registry May from pre-ladder Champ points: Buffer starts at first
            # formal-era All-Stars event (buffer performance, not a Champions contest).
            if not formal_as_events:
                return None
            eff = formal_as_events[0]
            effective_may_ord = _event_ord(eff)
            may_ym = eff["ym"]
            may_day = eff.get("day")
            may_ym_out = ym_str(eff["ym"])
            may_date_out = may_day.isoformat() if may_day is not None else None
            may_clipped = True
        # Stay cohort: All-Stars events only (ignore Champions appearances).
        post_may = [
            e for e in formal_as_events if _event_ord(e) > effective_may_ord
        ]
    else:
        formal_from = None
        post_may = [e for e in div_events if _event_ord(e) > effective_may_ord]
        if division == "Advanced":
            # Drop contests after May rights lapsed (higher threshold / expired window).
            post_may = _filter_advanced_still_may_eligible(
                events, div_events, post_may, rules, t0
            )

    if not post_may:
        return None

    first_post = post_may[0]
    first_post_ord = _event_ord(first_post)

    next_ord: tuple[int, date] | None = None
    if division != "All-Stars":
        next_events = [e for e in events if e["div"] == next_div]
        next_first = min(next_events, key=_event_ord) if next_events else None
        next_ord = _event_ord(next_first) if next_first else None
        # Exclusion A: next-division point before first post-May lower point.
        if next_ord is not None and next_ord < first_post_ord:
            return None

    must = crossings.get("required")
    must_ord = _hit_ord(must)

    # Thresholds for basket colour (single-path divisions) or AS Buffer path.
    allowed_t = allowed.get("threshold")
    required_t = must.get("threshold") if must else None
    champ_allowed_t: float | None = None
    champ_required_t: float | None = None
    as_allowed_t: float | None = None
    as_required_t: float | None = None
    if division == "All-Stars":
        must_ord = None
        eval_year = formal_from or (may_ym[0] if may_ym else 2021)
        paths = _all_stars_path_thresholds(rules, int(eval_year))
        champ_allowed_t = paths["champ_allowed"]
        champ_required_t = paths["champ_required"]
        as_allowed_t = paths["as_allowed"]
        as_required_t = paths["as_required"]
        # Required Champions cannot be Buffer Dancers (sacrifice petition-like
        # cases who still score All-Stars after Champ Must). Use full role
        # history — Champ Must may predate the first All-Stars point (t0).
        champ_run = 0.0
        for e in events:
            if e.get("div") != "Champions":
                continue
            champ_run += float(e.get("pts") or 0)
            if champ_required_t is not None and champ_run >= float(champ_required_t):
                return None
        # Buffer Must = career All-Stars points path only.
        as_run = 0.0
        for e in div_events:
            if e["div"] != "All-Stars":
                continue
            as_run += e["pts"]
            if (
                must_ord is None
                and as_required_t is not None
                and as_run >= float(as_required_t)
            ):
                must_ord = _event_ord(e)

    obs_ord = (ym_ord(*observation_end), date.max)
    candidates: list[tuple[str, tuple[int, date]]] = [("still", obs_ord)]
    if must_ord is not None:
        # All-Stars: Must on the effective-May event does not end the window.
        if division != "All-Stars" or must_ord > effective_may_ord:
            candidates.append(("must", must_ord))
    if next_ord is not None:
        candidates.append(("next", next_ord))
    exit_reason, window_ord = min(candidates, key=lambda c: (c[1][0], c[1][1], c[0]))

    stay_events = [e for e in post_may if _event_ord(e) <= window_ord]
    if not stay_events:
        return None
    last = stay_events[-1]

    if may_ym is None:
        return None
    months, basis = duration_months(may_ym, last["ym"], may_day, last.get("day"))

    # Score at end of stay (replay division scoring through last stay event).
    score = 0.0
    cum = 0.0
    champ_pts = 0.0
    as_pts = 0.0
    as_pts_in_buffer = 0.0

    # All-Stars: career totals through last buffer AS event (rules are cumulative).
    score_events = div_events

    for e in score_events:
        if _event_ord(e) > _event_ord(last):
            break
        if division == "Advanced":
            if e["div"] != "Advanced":
                continue
            cum += e["pts"]
            th = threshold_for_year(rules, e["year"], "Advanced")
            counting = (th or {}).get("counting", "cumulative")
            if counting == "rolling_36mo":
                score = rolling_sum(events, "Advanced", e["ym"], 36)
            else:
                score = cum
            # Basket thresholds follow rules at end of stay (not the original May era).
            if th and th.get("required") is not None:
                required_t = float(th["required"])
            if th and th.get("allowed") is not None:
                allowed_t = float(th["allowed"])
        elif division == "All-Stars":
            if e["div"] == "Champions":
                champ_pts += e["pts"]
            elif e["div"] == "All-Stars":
                as_pts += e["pts"]
                if _event_ord(e) > effective_may_ord:
                    as_pts_in_buffer += e["pts"]
        else:
            if e["div"] != division:
                continue
            cum += e["pts"]
            score = cum
            th = threshold_for_year(rules, e["year"], division)
            # Use thresholds at end of stay (last event wins), not the first
            # historical epoch hit while replaying — else Must can stick at
            # pre-2018 single-threshold values (e.g. Novice 15).
            if th and th.get("required") is not None:
                required_t = float(th["required"])
            if th and th.get("allowed") is not None:
                allowed_t = float(th["allowed"])

    reached_must = must_ord is not None and must_ord <= window_ord
    if division == "All-Stars":
        basket = _basket_from_progress(
            as_pts, as_allowed_t, as_required_t, reached_must
        )
        score = as_pts
    else:
        basket = _basket_from_progress(score, allowed_t, required_t, reached_must)

    out: dict = {
        "months": months,
        "events": len({e["eid"] for e in stay_events}),
        "months_basis": basis,
        "may_ym": may_ym_out,
        "end_ym": ym_str(last["ym"]),
        "exit": exit_reason,
        "basket": basket,
        "points_at_end": round(float(score), 2),
    }
    if may_date_out:
        out["may_date"] = may_date_out
    if may_clipped:
        out["may_clipped"] = True
        if allowed.get("done_ym"):
            out["registry_may_ym"] = allowed.get("done_ym")
        if allowed.get("done_date"):
            out["registry_may_date"] = allowed.get("done_date")
    if last.get("day") is not None:
        out["end_date"] = last["day"].isoformat()
    if division == "All-Stars":
        out["champions_points_at_end"] = round(float(champ_pts), 2)
        out["all_stars_points_at_end"] = round(float(as_pts), 2)
        out["all_stars_points_in_buffer"] = round(float(as_pts_in_buffer), 2)
        if champ_allowed_t is not None:
            out["may_threshold_champions"] = float(champ_allowed_t)
        if champ_required_t is not None:
            out["must_threshold_champions"] = float(champ_required_t)
        if as_allowed_t is not None:
            out["may_threshold_all_stars"] = float(as_allowed_t)
            out["may_threshold"] = float(as_allowed_t)
        if as_required_t is not None:
            out["must_threshold_all_stars"] = float(as_required_t)
            out["must_threshold"] = float(as_required_t)
    else:
        if allowed_t is not None:
            out["may_threshold"] = float(allowed_t)
        if required_t is not None:
            out["must_threshold"] = float(required_t)
    return out


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
    start_ev = first_event_in_div(events, division, t0)
    start_day = (start_ev or {}).get("day")
    for e in events:
        if e["div"] != division or e["ym"] < t0:
            continue
        th = threshold_for_year(rules, e["year"], division)
        if not th or th.get("allowed") is None:
            continue
        seen_events.add(e["eid"])
        cum += e["pts"]
        months, basis = duration_months(t0, e["ym"], start_day, e.get("day"))
        done = ym_str(e["ym"])
        for kind in ("allowed", "required"):
            if kind in reached:
                continue
            target = th.get(kind)
            if target is not None and cum >= float(target):
                reached[kind] = hit_dict(
                    months,
                    done,
                    len(seen_events),
                    done_date=e.get("day"),
                    months_basis=basis,
                    threshold=float(target),
                )
        if "allowed" in reached:
            record_buffer_marks(
                buffer,
                cum,
                months,
                done,
                len(seen_events),
                reached["allowed"].get("threshold"),
                th.get("required"),
                months_basis=basis,
                done_date=e.get("day"),
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
    start_ev = first_event_in_div(events, "Advanced", t0)
    start_day = (start_ev or {}).get("day")
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
        months, basis = duration_months(t0, e["ym"], start_day, e.get("day"))
        done = ym_str(e["ym"])
        for kind in ("allowed", "required"):
            if kind in reached:
                continue
            target = th.get(kind)
            if target is not None and score >= float(target):
                reached[kind] = hit_dict(
                    months,
                    done,
                    len(seen_events),
                    done_date=e.get("day"),
                    months_basis=basis,
                    threshold=float(target),
                )
        if "allowed" in reached:
            record_buffer_marks(
                buffer,
                score,
                months,
                done,
                len(seen_events),
                reached["allowed"].get("threshold"),
                th.get("required"),
                months_basis=basis,
                done_date=e.get("day"),
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
    start_ev = first_event_in_div(events, "All-Stars", t0)
    start_day = (start_ev or {}).get("day")
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
        months, basis = duration_months(t0, e["ym"], start_day, e.get("day"))
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
                    done_date=e.get("day"),
                    months_basis=basis,
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
                months_basis=basis,
                done_date=e.get("day"),
            )
        # Required done: stop. Champ-path buffer is best-effort (AS-OR crossings may leave it empty).
        if "required" in reached:
            break
    out = dict(reached)
    if buffer:
        out["buffer"] = buffer
    return out


def all_stars_points_path(hit: dict) -> bool:
    """True when May/Must was earned via All-Stars points (not Champions-only / petition)."""
    need_as = float(hit.get("threshold_all_stars") or 0)
    got_as = float(hit.get("all_stars_points_at_done") or 0)
    return need_as > 0 and got_as >= need_as


def pause_months_for_threshold(
    spell: dict | None,
    kind: str,
    from_division: str,
    events: list[dict],
    last_e: dict,
    first_e: dict,
) -> tuple[float | None, str | None, str | None]:
    """Pause: May/Must (points path) → first next; else last point in D → first in D+1.

    Returns (months, pause_path, months_basis) where pause_path is threshold|last_point
    and months_basis is day|ym. Chronology that cannot form a pause returns None.
    """
    last_lo = last_e["ym"]
    first_hi = first_e["ym"]
    hit = (spell or {}).get(kind) if spell else None
    if hit and hit.get("done_ym"):
        use_threshold = (
            all_stars_points_path(hit)
            if from_division == "All-Stars"
            else True
        )
        if use_threshold:
            done = parse_date(str(hit["done_ym"]))
            if done is not None and ym_ord(*first_hi) >= ym_ord(*done):
                done_divs = (
                    {"All-Stars", "Champions"}
                    if from_division == "All-Stars"
                    else {from_division}
                )
                done_day = day_for_ym(events, done, done_divs, prefer="last")
                months, mbasis = duration_months(
                    done, first_hi, done_day, first_e.get("day")
                )
                return months, "threshold", mbasis
    if ym_ord(*first_hi) >= ym_ord(*last_lo):
        months, mbasis = duration_months(
            last_lo, first_hi, last_e.get("day"), first_e.get("day")
        )
        return months, "last_point", mbasis
    return None, None, None


def build_transitions(
    events_by_spell_role: dict[tuple[str, str], list[dict]],
    name_by_id: dict[str, str],
    spells: list[dict],
) -> list[dict]:
    """JT-2: pause from May/Must (points path) or last point in D → first in D+1."""
    spell_ix = {(s["id"], s["role"], s["division"]): s for s in spells}
    rows: list[dict] = []
    for (did, role), evs in events_by_spell_role.items():
        by_div: dict[str, list[dict]] = defaultdict(list)
        for e in evs:
            by_div[e["div"]].append(e)
        for i in range(len(LADDER) - 1):
            lo, hi = LADDER[i], LADDER[i + 1]
            if lo not in by_div or hi not in by_div:
                continue
            last_e = max(
                by_div[lo],
                key=lambda e: (ym_ord(*e["ym"]), e.get("day") or date.min),
            )
            first_e = min(
                by_div[hi],
                key=lambda e: (ym_ord(*e["ym"]), e.get("day") or date.max),
            )
            spell = spell_ix.get((did, role, lo))
            row: dict = {
                "id": did,
                "name": name_by_id.get(did) or did,
                "role": role,
                "from_division": lo,
                "to_division": hi,
                "last_ym": ym_str(last_e["ym"]),
                "first_ym": ym_str(first_e["ym"]),
            }
            if last_e.get("day") is not None:
                row["last_date"] = last_e["day"].isoformat()
            if first_e.get("day") is not None:
                row["first_date"] = first_e["day"].isoformat()
            for kind, months_key, path_key, basis_key in (
                ("allowed", "months_allowed", "pause_basis_allowed", "months_basis_allowed"),
                ("required", "months_required", "pause_basis_required", "months_basis_required"),
            ):
                months, path, mbasis = pause_months_for_threshold(
                    spell, kind, lo, evs, last_e, first_e
                )
                if months is not None:
                    row[months_key] = months
                    row[path_key] = path
                    row[basis_key] = mbasis
            # Prefer May months as the generic field (dashboard picks by threshold).
            if "months_allowed" in row:
                row["months"] = row["months_allowed"]
                if "months_basis_allowed" in row:
                    row["months_basis"] = row["months_basis_allowed"]
            elif "months_required" in row:
                row["months"] = row["months_required"]
                if "months_basis_required" in row:
                    row["months_basis"] = row["months_basis_required"]
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
    edition_exact, edition_by_ym = load_edition_day_index(source)

    name_by_id: dict[str, str] = {}
    dominate_role_by_id: dict[str, str] = {}
    with (source / "dancer_role_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            if not did:
                continue
            name_by_id[did] = (row.get("dancer_name") or "").strip()
            dom = (row.get("dominate_role") or "").strip().title()
            if dom in ROLES:
                dominate_role_by_id[did] = dom

    # events keyed by (dancer_id, role)
    events_by_spell_role: dict[tuple[str, str], list[dict]] = defaultdict(list)
    first_pts: dict[tuple[str, str, str], tuple[int, int]] = {}

    excluded = {
        "invalid_date": 0,
        "non_skill_division": 0,
        "bad_role": 0,
        "non_positive_points": 0,
    }
    edition_date_hits = 0
    edition_date_misses = 0

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
            event_name = (row.get("event_name") or "").strip()
            day = lookup_edition_day(edition_exact, edition_by_ym, event_name, y, m)
            if day is not None:
                edition_date_hits += 1
            else:
                edition_date_misses += 1
            events_by_spell_role[(did, role)].append(
                {
                    "div": div,
                    "pts": pts,
                    "ym": dt,
                    "year": y,
                    "eid": eid,
                    "name": event_name,
                    "day": day,
                }
            )
            key = (did, role, div)
            if key not in first_pts or dt < first_pts[key]:
                first_pts[key] = dt

    for key in events_by_spell_role:
        events_by_spell_role[key].sort(
            key=lambda e: (ym_ord(*e["ym"]), e.get("day") or date.min, e["eid"])
        )

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

        dominate = dominate_role_by_id.get(did)
        if dominate is None:
            role_status = "unknown"
        elif dominate == role:
            role_status = "primary"
        else:
            role_status = "secondary"
        row = {
            "id": did,
            "name": name_by_id.get(did) or did,
            "role": role,
            "role_status": role_status,
            "division": div,
            "first_ym": ym_str(t0),
            "activity_years": activity_years_for_division(evs, div),
        }
        start_div = "All-Stars" if div == "All-Stars" else div
        start_ev = first_event_in_div(evs, start_div, t0)
        if start_ev and start_ev.get("day") is not None:
            row["first_date"] = start_ev["day"].isoformat()
        if "allowed" in crossings:
            row["allowed"] = crossings["allowed"]
        if "required" in crossings:
            row["required"] = crossings["required"]
        if "buffer" in crossings:
            row["buffer"] = crossings["buffer"]
        stay = compute_stay_after_may(
            evs, div, t0, crossings, rules, observation_end
        )
        if stay:
            row["stay_after_may"] = stay
        spells.append(row)

    spells.sort(key=lambda r: (r["division"], r["role"], r["id"]))
    transitions = build_transitions(events_by_spell_role, name_by_id, spells)
    qualify = build_qualify_series(spells, first_pts)

    def count_basis(objs: list[dict], key: str = "months_basis") -> dict[str, int]:
        out = {"day": 0, "ym": 0}
        for obj in objs:
            b = obj.get(key)
            if b in out:
                out[b] += 1
        return out

    spell_basis = {"day": 0, "ym": 0}
    for s in spells:
        for thr in ("allowed", "required"):
            hit = s.get(thr)
            if isinstance(hit, dict):
                b = hit.get("months_basis")
                if b in spell_basis:
                    spell_basis[b] += 1
        buf = s.get("buffer") or {}
        if isinstance(buf, dict):
            for mark in buf.values():
                if isinstance(mark, dict):
                    b = mark.get("months_basis")
                    if b in spell_basis:
                        spell_basis[b] += 1

    pause_basis = count_basis(transitions, "months_basis")

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
            "spell": (
                "dancer × division × event_role; role_status primary|secondary|unknown from "
                "dancer_role_info.dominate_role vs spell role"
            ),
            "months": (
                "prefer edition start_date (else end_date) from event_editions.csv: "
                "days/30.44 rounded to 0.1 (min 1 day → at least 0.1 mo when both dates valid and end≥start); "
                "else inclusive calendar months first_ym→done_ym (same month = 1; Nov→Mar = 5). "
                "Per hit/pause: months_basis day|ym. Cohort year filters still use event_year/done_ym."
            ),
            "events": "unique event editions (name + year-month) in that division×role up to and including the crossing event for the selected threshold; history before the dashboard year floor still counts",
            "buffer": "p25/p50/p75 = first reach of allowed + frac×(required−allowed) points; share among spells that reached May; duration uses same day/YM rule as dwell",
            "stay_after_may": (
                "Buffer chart cohort: May reached AND ≥1 scored event in the same division×role "
                "strictly after May; exclude if next-division point precedes that first post-May "
                "lower point (All-Stars: Champions is threshold path, not exclusion). "
                "Window May→last lower point at/before earliest of Must / first next / data_through. "
                "months/events measured post-May only; basket = lt25|p25|p50|p75|must from score vs "
                "May→Must gap; exit = must|next|still. "
                "All-Stars Buffer: formal All-Stars→Champions era only (rules year, 2021+); "
                "if registry May is earlier, effective May = first All-Stars event in that era; "
                "months/events count All-Stars buffer performances only (Champions contests excluded). "
                "Required Champions (Champ pts ≥ Must, typically 10) are excluded from Buffer even if "
                "they later score All-Stars. Else Buffer Must/basket use career All-Stars pts "
                "vs 150→225 only; Champ pts below Must may appear in tooltips and do not end Buffer. "
                "Advanced: post-May events count only while score still meets that year's May "
                "(so threshold rises / rolling expiry remove Buffer rights)."
            ),
            "pause": (
                "JT-2 months from May/Must done (points path in D) to first point in D+1 "
                "(same role), day-based when both edition dates exist. All-Stars points path = "
                "reached via AS-point OR (e.g. 150 AS); Champions-only / petition use last→first. "
                "No overlap flag."
            ),
            "qualify": "JN-1b yearly n and cumulative: Advanced allowed (eligible) vs first All-Stars point (entered)",
            "activity_years": (
                "sorted unique calendar years with ≥1 scored point in this division×role "
                "(All-Stars: All-Stars contests only). Used by Buffer Dancers card denominator."
            ),
            "window_filter": "display only: done_ym inside From–To and division year floor (Nov/Int/Adv ≥2018, All-Stars ≥2021); calculation uses full spell history from first_ym; pause/qualify sheets do not use the may/must year floor",
            "data_stamp": "generated_at = calendar date this JSON was rebuilt; data_through = latest event year-month in the source export",
            "table_dates": (
                "first_date / done_date on spells and first_date / last_date on transitions are edition "
                "start_date (else end_date) of the milestone event; first_ym / done_ym / last_ym kept for filters"
            ),
            "all_stars": (
                "pre-formal rules years: Champions pts only (1 may / 10 must) on real events; "
                "from first All-Stars rules year (2021): full OR Champ pts or AS pts; "
                "no synthetic done_ym at rule start"
            ),
            "rolling_window": "Advanced rolling_36mo scoring stays calendar months (rules), not day-based",
            "edition_dates": {
                "source": "event_editions.csv",
                "join": "exact norm(name)+year+month, else fuzzy name in same YM (cutoff 0.62)",
                "result_rows_with_day": edition_date_hits,
                "result_rows_without_day": edition_date_misses,
                "spell_hit_months_basis": spell_basis,
                "transition_months_basis": pause_basis,
            },
        },
        "spells": spells,
        "transitions": transitions,
        "qualify": qualify,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(spells)} spells, {len(transitions)} transitions -> {args.output}")
    print(f"generated_at={generated_at} data_through={data_through} excluded={excluded}")
    print(
        f"edition days hit={edition_date_hits} miss={edition_date_misses} "
        f"spell_basis={spell_basis} pause_basis={pause_basis}"
    )

    # Dashboard prefers per-division shards over the monolith; keep them in sync.
    write_division_shards(payload, args.output.parent / "time_in_division")


def _shard_filename(division: str) -> str:
    return (
        str(division or "Novice")
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def write_division_shards(payload: dict, shard_dir: Path) -> None:
    """Write index.json + one JSON per division (spells/transitions only).

    ``time_in_division_dashboard_en.html`` reads index for meta stamps
    (``Updated …``) and loads division shards for table data. If only the
    monolith is refreshed, the UI keeps showing a stale Updated date.
    """
    shard_dir.mkdir(parents=True, exist_ok=True)
    divisions = list(payload.get("divisions") or DASHBOARD_DIVISIONS)
    for div in divisions:
        spells = [s for s in payload.get("spells") or [] if s.get("division") == div]
        transitions = [
            t
            for t in payload.get("transitions") or []
            if t.get("from_division") == div
        ]
        path = shard_dir / f"{_shard_filename(div)}.json"
        path.write_text(
            json.dumps(
                {"spells": spells, "transitions": transitions},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        print(f"  shard {div}: {len(spells)} spells, {len(transitions)} transitions -> {path}")

    index = {
        key: value
        for key, value in payload.items()
        if key not in {"spells", "transitions"}
    }
    index["spells"] = []
    index["transitions"] = []
    index["shards"] = divisions
    index["shard_base"] = "static/data/time_in_division"
    index_path = shard_dir / "index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote shard index -> {index_path}")


if __name__ == "__main__":
    main()
