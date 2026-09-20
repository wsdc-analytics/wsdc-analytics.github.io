#!/usr/bin/env python3
"""Rebuild event-portrait metrics JSON for BotB / Asia Open / SPb Nights.

Compatible with UK article insights.peer_context schema (events/002).
Uses pipeline CSVs under projects/python/wsdc-data-pipeline/data/.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

PIPELINE_DATA = Path(
    "/Users/ania/.cursor/projects/python/wsdc-data-pipeline/data"
)
OUT_DIR = Path(__file__).resolve().parent

SKILL_DIVISIONS = {
    "Newcomer",
    "Novice",
    "Intermediate",
    "Advanced",
    "All-Star",
    "Champion",
    "All-Stars",  # legacy alias
    "Champions",
}
DIV_CANON = {"All-Stars": "All-Star", "Champions": "Champion"}
DIV_RANK = {
    "Newcomer": 1,
    "Novice": 2,
    "Intermediate": 3,
    "Advanced": 4,
    "All-Star": 5,
    "Champion": 6,
}
DIV_ORDER = ["Newcomer", "Novice", "Intermediate", "Advanced", "All-Star", "Champion"]

EUROPE = {
    "United Kingdom",
    "France",
    "Germany",
    "Spain",
    "Italy",
    "Netherlands",
    "Poland",
    "Polska",
    "Sweden",
    "Denmark",
    "Norway",
    "Finland",
    "Finalnd",
    "Belgium",
    "Belgique",
    "Switzerland",
    "Austria",
    "Portugal",
    "Greece",
    "Ireland",
    "Czech Republic",
    "Hungary",
    "Romania",
    "Croatia",
    "Slovenia",
    "Estonia",
    "Latvia",
    "Lithuania",
    "Ukraine",
    "Belarus",
    "Bulgaria",
    "Serbia",
    "Russia",
    "Russian Federation",
    "Slovakia",
    "Iceland",
    "Malta",
    "Cyprus",
    "Luxembourg",
    "Bosnia and Herzegovina",
    "North Macedonia",
    "Moldova",
    "Albania",
    "Montenegro",
    "Kosovo",
}

ASIA = {
    "Singapore",
    "Japan",
    "China",
    "Hong Kong",
    "Taiwan",
    "Thailand",
    "Malaysia",
    "Philippines",
    "Indonesia",
    "India",
    "Vietnam",
    "Republic of Korea",
    "South Korea",
    "Korea",
    "Macau",
    "Cambodia",
    "Myanmar",
    "Nepal",
    "Sri Lanka",
    "Pakistan",
    "Bangladesh",
    "Mongolia",
    "Laos",
    "Brunei",
}

OCEANIA = {
    "Australia",
    "New Zealand",
    "Fiji",
    "Papua New Guinea",
    "Samoa",
    "Tonga",
    "Vanuatu",
    "New Caledonia",
    "French Polynesia",
    "Cook Islands",
    "Guam",
    "American Samoa",
}

# Target events: slug → discovery + regional nest key
TARGETS = [
    {
        "slug": "003",
        "out": "metrics_003.json",
        "name_contains": ["Best of the Best"],
        "hint_id": 167,
        "region_key": "oceania",
        "region_countries": OCEANIA,
        "region_label": "Oceania (Australia + New Zealand + Pacific)",
    },
    {
        "slug": "004",
        "out": "metrics_004.json",
        "name_contains": ["Asia West Coast Swing Open"],
        "hint_id": 218,
        "region_key": "asia",
        "region_countries": ASIA,
        "region_label": "Asia",
    },
    {
        "slug": "005",
        "out": "metrics_005.json",
        "name_contains": ["Saint Petersburg WCS Nights", "St. Petersburg WCS Nights"],
        "hint_id": 280,
        "region_key": "europe",
        "region_countries": EUROPE,
        "region_label": "Europe",
    },
]


def _pct(n: float, d: float, digits: int = 1) -> float | None:
    if d <= 0:
        return None
    return round(100.0 * n / d, digits)


def _canon_div(v: str) -> str:
    v = (v or "").strip()
    return DIV_CANON.get(v, v)


def load_frames() -> dict[str, pd.DataFrame]:
    results = pd.read_csv(PIPELINE_DATA / "dancers_results_info.csv")
    roles = pd.read_csv(PIPELINE_DATA / "dancer_role_info.csv")
    catalog = pd.read_csv(PIPELINE_DATA / "event_catalog.csv")
    locations = pd.read_csv(PIPELINE_DATA / "location_info.csv")
    editions = pd.read_csv(PIPELINE_DATA / "event_editions.csv")
    events_wsdc = pd.read_csv(PIPELINE_DATA / "events_wsdc.csv")
    return {
        "results": results,
        "roles": roles,
        "catalog": catalog,
        "locations": locations,
        "editions": editions,
        "events_wsdc": events_wsdc,
    }


def build_skill_jj(results: pd.DataFrame, events_wsdc: pd.DataFrame) -> pd.DataFrame:
    df = results.copy()
    df["event_competition"] = df["event_competition"].map(_canon_div)
    df["event_points"] = pd.to_numeric(df["event_points"], errors="coerce").fillna(0)
    df["dancer_id"] = df["dancer_id"].astype(str)
    mask = (
        (df["event_dance"] == "West Coast Swing")
        & (df["event_competition"].isin(SKILL_DIVISIONS | set(DIV_CANON.values())))
        & (df["event_points"] > 0)
    )
    jj = df.loc[mask].copy()
    name_to_id = (
        events_wsdc.groupby("name")["id"]
        .agg(lambda s: int(s.mode().iloc[0]))
        .to_dict()
    )
    jj["event_id"] = jj["event_name"].map(name_to_id)
    if jj["event_id"].isna().any():
        missing = jj.loc[jj["event_id"].isna(), "event_name"].unique()[:10]
        raise ValueError(f"Unmapped event_name → event_id: {missing}")
    jj["event_id"] = jj["event_id"].astype(int)
    jj["event_year"] = jj["event_year"].astype(int)
    return jj


def event_country_map(
    catalog: pd.DataFrame,
    editions: pd.DataFrame,
    jj: pd.DataFrame,
    locations: pd.DataFrame,
) -> dict[int, str]:
    """Map event_id → country for regional peer slices.

    Prefer results majority location (where points were scored), then edition
    place_country, then catalog typical_country. Always key by int event_id
    so dtype=str CSVs cannot silently miss catalog rows.
    """

    def _mode(series: pd.Series) -> str | None:
        s = series.dropna()
        s = s[s.astype(str).str.strip() != ""]
        if s.empty:
            return None
        return str(s.mode().iloc[0]).strip()

    def _by_int(d: dict) -> dict[int, str]:
        out: dict[int, str] = {}
        for k, v in d.items():
            if v is None or str(v).strip() == "" or str(v).lower() == "nan":
                continue
            try:
                out[int(k)] = str(v).strip()
            except (TypeError, ValueError):
                continue
        return out

    cat = _by_int(catalog.set_index("event_id")["typical_country"].to_dict())
    ed_mode = _by_int(
        editions.groupby("event_id")["place_country"].agg(_mode).to_dict()
    )
    jl = jj.merge(
        locations[["location_id", "event_country"]], on="location_id", how="left"
    )
    res_mode = _by_int(jl.groupby("event_id")["event_country"].agg(_mode).to_dict())

    out: dict[int, str] = {}
    all_ids = set(jj["event_id"].astype(int).unique()) | set(cat) | set(ed_mode) | set(
        res_mode
    )
    # Results first: peer geography = where Skill JJ points were actually scored
    # (avoids catalog quirks / shared wrong typical_country pulling US events into Asia).
    for eid in all_ids:
        for src in (res_mode, ed_mode, cat):
            v = src.get(int(eid))
            if v:
                out[int(eid)] = v
                break
    return out


def year_gaps(years: list[int]) -> list[int]:
    if not years:
        return []
    y0, y1 = min(years), max(years)
    have = set(years)
    return [y for y in range(y0, y1 + 1) if y not in have]


def first_points_by_event(jj: pd.DataFrame) -> dict[int, set[str]]:
    """Debut month = min(event_year_and_month). Count event if scored there that month."""
    first_ym = jj.groupby("dancer_id")["event_year_and_month"].min()
    tmp = jj[["dancer_id", "event_id", "event_year_and_month"]].copy()
    tmp["first_ym"] = tmp["dancer_id"].map(first_ym)
    debut = tmp[tmp["event_year_and_month"] == tmp["first_ym"]]
    out: dict[int, set[str]] = defaultdict(set)
    for eid, did in debut[["event_id", "dancer_id"]].itertuples(index=False):
        out[int(eid)].add(str(did))
    return out


def primary_debut_event(jj: pd.DataFrame) -> dict[str, int]:
    """Single debut event per dancer: earliest ym, then lowest event_id (stable)."""
    first_ym = jj.groupby("dancer_id")["event_year_and_month"].min()
    tmp = jj[["dancer_id", "event_id", "event_year_and_month"]].copy()
    tmp["first_ym"] = tmp["dancer_id"].map(first_ym)
    debut = tmp[tmp["event_year_and_month"] == tmp["first_ym"]]
    debut = debut.sort_values(["dancer_id", "event_id"])
    return debut.groupby("dancer_id")["event_id"].first().astype(int).to_dict()


def peer_table(
    jj: pd.DataFrame, first_by_event: dict[int, set[str]]
) -> pd.DataFrame:
    g = (
        jj.groupby(["event_id", "event_name"], as_index=False)
        .agg(
            unique_dancers=("dancer_id", "nunique"),
            total_points=("event_points", "sum"),
            editions=("event_year", "nunique"),
        )
    )
    g["first_points_here"] = g["event_id"].map(
        lambda e: len(first_by_event.get(int(e), set()))
    )
    g["total_points"] = g["total_points"].astype(int)
    return g


def rank_series(s: pd.Series) -> pd.Series:
    return s.rank(ascending=False, method="min").astype(int)


def top12_peers(
    table: pd.DataFrame, metric: str, this_id: int, this_name: str
) -> list[dict[str, Any]]:
    ordered = table.sort_values(
        [metric, "editions", "event_name"], ascending=[False, False, True]
    )
    rows = []
    seen = False
    for _, r in ordered.head(12).iterrows():
        is_this = int(r["event_id"]) == this_id
        if is_this:
            seen = True
        rows.append(
            {
                "event_id": int(r["event_id"]),
                "event_name": r["event_name"],
                "name": r["event_name"],
                "editions": int(r["editions"]),
                "unique_dancers": int(r["unique_dancers"]),
                "first_points_here": int(r["first_points_here"]),
                "total_points": int(r["total_points"]),
                "value": int(r[metric]),
                "is_this_event": is_this,
            }
        )
    if not seen:
        mine = table[table["event_id"] == this_id]
        if not mine.empty:
            r = mine.iloc[0]
            rows.append(
                {
                    "event_id": this_id,
                    "event_name": this_name,
                    "name": this_name,
                    "editions": int(r["editions"]),
                    "unique_dancers": int(r["unique_dancers"]),
                    "first_points_here": int(r["first_points_here"]),
                    "total_points": int(r["total_points"]),
                    "value": int(r[metric]),
                    "is_this_event": True,
                }
            )
    return rows


def build_peer_context(
    table: pd.DataFrame,
    this_id: int,
    this_name: str,
    countries: dict[int, str],
    region_key: str,
    region_countries: set[str],
    region_label: str,
) -> dict[str, Any]:
    t = table.copy()
    t["rank_unique"] = rank_series(t["unique_dancers"])
    t["rank_first"] = rank_series(t["first_points_here"])
    t["rank_points"] = rank_series(t["total_points"])
    t["rank_editions"] = rank_series(t["editions"])
    long = t[t["editions"] >= 10].copy()
    long["rank_unique_long"] = rank_series(long["unique_dancers"])

    mine = t[t["event_id"] == this_id].iloc[0]
    long_rank = None
    if this_id in set(long["event_id"]):
        long_rank = int(long.loc[long["event_id"] == this_id, "rank_unique_long"].iloc[0])

    pc: dict[str, Any] = {
        "definition": (
            "Among all Skill JJ events; ranks by unique dancers / "
            "first-ever WSDC points at this event / total Skill JJ points / edition years"
        ),
        "this_event": this_name,
        "events_total_n": int(len(t)),
        "long_events_n": int(len(long)),
        "unique_dancers": int(mine["unique_dancers"]),
        "first_points_here": int(mine["first_points_here"]),
        "total_points": int(mine["total_points"]),
        "editions": int(mine["editions"]),
        "rank_by_unique_all": int(mine["rank_unique"]),
        "rank_by_first_points_all": int(mine["rank_first"]),
        "rank_by_total_points_all": int(mine["rank_points"]),
        "rank_by_editions": int(mine["rank_editions"]),
        "rank_by_unique_among_long": long_rank,
        "peers_top12_by_unique": top12_peers(t, "unique_dancers", this_id, this_name),
        "peers_top12_by_first_points": top12_peers(
            t, "first_points_here", this_id, this_name
        ),
        "peers_top12_by_total_points": top12_peers(
            t, "total_points", this_id, this_name
        ),
        "peers_top15_by_first_points": top12_peers(
            t, "first_points_here", this_id, this_name
        )[:15],
    }

    # Regional nest
    t["country"] = t["event_id"].map(countries)
    reg = t[t["country"].isin(region_countries)].copy()
    if this_id not in set(reg["event_id"]):
        # Force-include this event (e.g. catalog quirk)
        reg = pd.concat([reg, t[t["event_id"] == this_id]], ignore_index=True)
    reg["rank_unique"] = rank_series(reg["unique_dancers"])
    reg["rank_first"] = rank_series(reg["first_points_here"])
    reg["rank_points"] = rank_series(reg["total_points"])
    rm = reg[reg["event_id"] == this_id].iloc[0]
    pc[region_key] = {
        "definition": f"Among {region_label} Skill JJ events (typical_country / mode location)",
        "events_n": int(len(reg)),
        "rank_by_unique": int(rm["rank_unique"]),
        "rank_by_first_points": int(rm["rank_first"]),
        "rank_by_total_points": int(rm["rank_points"]),
        "peers_top12_by_unique": top12_peers(reg, "unique_dancers", this_id, this_name),
        "peers_top12_by_first_points": top12_peers(
            reg, "first_points_here", this_id, this_name
        ),
        "peers_top12_by_total_points": top12_peers(
            reg, "total_points", this_id, this_name
        ),
    }
    return pc


def timeseries_for_event(
    ev: pd.DataFrame, starters: set[str]
) -> list[dict[str, Any]]:
    rows = []
    for year, g in ev.groupby("event_year"):
        dancers = set(g["dancer_id"].astype(str))
        # new = starters whose first points month falls in this year at this event
        # Approximate: starters present this year whose career first ym year == year
        new_n = 0  # filled by caller via first_ym map — see below
        rows.append(
            {
                "event_year": int(year),
                "unique_dancers": int(g["dancer_id"].nunique()),
                "total_points": int(g["event_points"].sum()),
                "dancers": dancers,
            }
        )
    return rows


def build_timeseries(
    ev: pd.DataFrame, jj: pd.DataFrame, first_by_event: dict[int, set[str]], event_id: int
) -> list[dict[str, Any]]:
    first_ym = jj.groupby("dancer_id")["event_year_and_month"].min()
    starters = first_by_event.get(event_id, set())
    starter_first_year = {}
    for did in starters:
        ym = first_ym.get(did)
        if ym is None or (isinstance(ym, float) and pd.isna(ym)):
            continue
        starter_first_year[did] = int(str(ym)[:4])

    out = []
    for year, g in sorted(ev.groupby("event_year"), key=lambda x: x[0]):
        year = int(year)
        new_dancers = sum(1 for d, y in starter_first_year.items() if y == year)
        out.append(
            {
                "event_year": year,
                "unique_dancers": int(g["dancer_id"].nunique()),
                "total_points": int(g["event_points"].sum()),
                "new_dancers": int(new_dancers),
            }
        )
    return out


def retention_block(ev: pd.DataFrame, gaps: list[int]) -> dict[str, Any]:
    years = sorted(ev["event_year"].unique())
    by_year = {
        int(y): set(g["dancer_id"].astype(str)) for y, g in ev.groupby("event_year")
    }
    dancer_years: dict[str, set[int]] = defaultdict(set)
    dancer_pts: dict[str, float] = defaultdict(float)
    for _, r in ev.iterrows():
        did = str(r["dancer_id"])
        dancer_years[did].add(int(r["event_year"]))
        dancer_pts[did] += float(r["event_points"])

    hist_counter: Counter[int] = Counter(len(ys) for ys in dancer_years.values())
    unique_n = len(dancer_years)
    total_pts = sum(dancer_pts.values()) or 1.0

    edition_histogram = []
    for ed in range(1, max(hist_counter.keys(), default=0) + 1):
        n = hist_counter.get(ed, 0)
        pts = sum(
            dancer_pts[d] for d, ys in dancer_years.items() if len(ys) == ed
        )
        edition_histogram.append(
            {
                "editions": ed,
                "dancers": n,
                "dancers_share_pct": _pct(n, unique_n) or 0.0,
                "points": int(pts),
                "points_share_pct": _pct(pts, total_pts) or 0.0,
            }
        )

    one_n = hist_counter.get(1, 0)
    three_plus = sum(n for ed, n in hist_counter.items() if ed >= 3)
    five_plus = sum(n for ed, n in hist_counter.items() if ed >= 5)
    one_pts = sum(dancer_pts[d] for d, ys in dancer_years.items() if len(ys) == 1)
    five_pts = sum(dancer_pts[d] for d, ys in dancer_years.items() if len(ys) >= 5)

    next_year_return = []
    gap_set = set(gaps)
    for i, y in enumerate(years):
        y = int(y)
        # find next edition year
        later = [int(x) for x in years if int(x) > y]
        if not later:
            continue
        nxt = later[0]
        if nxt == y + 1:
            base = by_year[y]
            returned = len(base & by_year[nxt])
            next_year_return.append(
                {
                    "from_year": y,
                    "to_year": nxt,
                    "base": len(base),
                    "returned": returned,
                    "rate_pct": _pct(returned, len(base)),
                }
            )
        else:
            # multi-year gap — record separately once
            pass

    return_after_gap = None
    if gaps:
        # first gap-crossing pair: last year before contiguous gap → first year after
        g0, g1 = min(gaps), max(gaps)
        before = [int(y) for y in years if int(y) < g0]
        after = [int(y) for y in years if int(y) > g1]
        if before and after:
            fy, ty = before[-1], after[0]
            base = by_year[fy]
            returned = len(base & by_year[ty])
            return_after_gap = {
                "from_year": fy,
                "to_year": ty,
                "base": len(base),
                "returned": None,
                "rate_pct": None,
                "note": (
                    f"after multi-year gap {g0}-{g1}; consecutive YoY N/A"
                    if g0 != g1
                    else f"after gap year {g0}; consecutive YoY N/A"
                ),
                "returned_after_gap_n": returned,
                "returned_after_gap_pct": _pct(returned, len(base)),
            }

    rates = [r["rate_pct"] for r in next_year_return if r["rate_pct"] is not None]
    recent = rates[-3:] if rates else []

    return {
        "definition": (
            "Return = scored points at this event in year Y and again in Y+1; "
            "editions = distinct years with points here"
        ),
        "unique_dancers": unique_n,
        "one_edition_n": one_n,
        "one_edition_pct": _pct(one_n, unique_n) or 0.0,
        "three_plus_editions_n": three_plus,
        "three_plus_editions_pct": _pct(three_plus, unique_n) or 0.0,
        "five_plus_editions_n": five_plus,
        "one_edition_points_share_pct": _pct(one_pts, total_pts) or 0.0,
        "five_plus_points_share_pct": _pct(five_pts, total_pts) or 0.0,
        "edition_histogram": edition_histogram,
        "next_year_return": next_year_return,
        "return_after_gap": return_after_gap,
        "return_rate_range_pct": (
            [min(rates), max(rates)] if rates else None
        ),
        "recent_return_rate_range_pct": (
            [min(recent), max(recent)] if recent else None
        ),
    }


def launchpad_block(
    jj: pd.DataFrame,
    starters: set[str],
    names: dict[str, str],
) -> dict[str, Any]:
    if not starters:
        return {
            "definition": "first-ever WSDC Skill JJ points at this event",
            "starters_n": 0,
            "highest_division_counts": [],
            "reached_allstar_plus_n": 0,
            "reached_allstar_plus_pct": 0.0,
            "reached_champion_n": 0,
            "reached_champion_pct": 0.0,
            "notable_allstar_starters": [],
            "notable_champion_starters": [],
        }

    career = jj[jj["dancer_id"].isin(starters)].copy()
    # highest division by DIV_RANK
    career["div_rank"] = career["event_competition"].map(DIV_RANK)
    highest = career.groupby("dancer_id")["div_rank"].max()
    rev = {v: k for k, v in DIV_RANK.items()}
    counts = Counter(rev[int(r)] for r in highest.values if int(r) in rev)
    highest_division_counts = [
        {"division": d, "n": int(counts.get(d, 0))} for d in DIV_ORDER
    ]

    as_plus = {d for d, r in highest.items() if r >= DIV_RANK["All-Star"]}
    champs = {d for d, r in highest.items() if r >= DIV_RANK["Champion"]}

    # career points share outside this event — need event_id of starters event
    # computed by caller enrichment; here compute median share outside for starters
    # using all career points vs points at debut events — approximate with all events

    # months to All-Star / Champion from first points ym
    first_ym = jj.groupby("dancer_id")["event_year_and_month"].min()

    def months_between(ym_a: str, ym_b: str) -> int:
        ya, ma = int(str(ym_a)[:4]), int(str(ym_a)[5:7])
        yb, mb = int(str(ym_b)[:4]), int(str(ym_b)[5:7])
        return (yb - ya) * 12 + (mb - ma)

    def median_months_to(target_div: str) -> float | None:
        vals = []
        sub = career[career["event_competition"] == target_div]
        first_hit = sub.groupby("dancer_id")["event_year_and_month"].min()
        for did, hit_ym in first_hit.items():
            base = first_ym.get(did)
            if base is None or pd.isna(base):
                continue
            vals.append(months_between(str(base), str(hit_ym)))
        if not vals:
            return None
        vals.sort()
        mid = len(vals) // 2
        if len(vals) % 2:
            return float(vals[mid])
        return (vals[mid - 1] + vals[mid]) / 2.0

    # notable starters: those who reached AS/Champ, ranked by career points in that div since 2009
    since = career[career["event_year"] >= 2009]

    def notable(div: str, key: str, limit: int = 10) -> list[dict[str, Any]]:
        pool = champs if div == "Champion" else as_plus
        sub = since[
            (since["dancer_id"].isin(pool)) & (since["event_competition"] == div)
        ]
        if sub.empty:
            return []
        agg = (
            sub.groupby("dancer_id")
            .agg(pts=("event_points", "sum"), last_year=("event_year", "max"))
            .sort_values("pts", ascending=False)
            .head(limit)
        )
        # starter year at this event ≈ first_ym year
        out = []
        for did, r in agg.iterrows():
            ym = first_ym.get(did)
            out.append(
                {
                    "dancer_name": names.get(str(did), str(did)),
                    "dancer_id": str(did),
                    "event_year": int(str(ym)[:4]) if ym is not None and not pd.isna(ym) else None,
                    key: int(r["pts"]),
                    "last_as_year" if div == "All-Star" else "last_champ_year": int(
                        r["last_year"]
                    ),
                }
            )
        return out

    # median career points share outside: need this_event_id — pass via starters' points
    return {
        "definition": "first-ever WSDC Skill JJ points at this event",
        "starters_n": len(starters),
        "reached_allstar_plus_n": len(as_plus),
        "reached_allstar_plus_pct": _pct(len(as_plus), len(starters)) or 0.0,
        "reached_champion_n": len(champs),
        "reached_champion_pct": _pct(len(champs), len(starters)) or 0.0,
        "median_months_to_allstar": median_months_to("All-Star"),
        "median_months_to_champion": median_months_to("Champion"),
        "highest_division_counts": highest_division_counts,
        "notable_allstar_starters": notable("All-Star", "allstar_pts_since_2009"),
        "notable_champion_starters": notable("Champion", "champ_pts"),
    }


def enrich_launchpad_shares(
    launchpad: dict[str, Any],
    jj: pd.DataFrame,
    starters: set[str],
    event_id: int,
) -> None:
    if not starters:
        launchpad["median_career_points_share_outside_pct"] = None
        launchpad["as_plus_median_career_points_share_outside_pct"] = None
        return
    career = jj[jj["dancer_id"].isin(starters)]
    total = career.groupby("dancer_id")["event_points"].sum()
    here = (
        career[career["event_id"] == event_id]
        .groupby("dancer_id")["event_points"]
        .sum()
    )
    shares = []
    for did, tot in total.items():
        if tot <= 0:
            continue
        h = float(here.get(did, 0))
        shares.append(100.0 * (1.0 - h / float(tot)))
    shares.sort()
    if shares:
        mid = len(shares) // 2
        med = (
            float(shares[mid])
            if len(shares) % 2
            else (shares[mid - 1] + shares[mid]) / 2.0
        )
        launchpad["median_career_points_share_outside_pct"] = round(med, 1)
    else:
        launchpad["median_career_points_share_outside_pct"] = None

    # AS+ subset
    career2 = career.copy()
    career2["div_rank"] = career2["event_competition"].map(DIV_RANK)
    highest = career2.groupby("dancer_id")["div_rank"].max()
    as_plus = {d for d, r in highest.items() if r >= DIV_RANK["All-Star"]}
    shares2 = []
    for did in as_plus:
        tot = float(total.get(did, 0))
        if tot <= 0:
            continue
        h = float(here.get(did, 0))
        shares2.append(100.0 * (1.0 - h / tot))
    shares2.sort()
    if shares2:
        mid = len(shares2) // 2
        med = (
            float(shares2[mid])
            if len(shares2) % 2
            else (shares2[mid - 1] + shares2[mid]) / 2.0
        )
        launchpad["as_plus_median_career_points_share_outside_pct"] = round(med, 1)
    else:
        launchpad["as_plus_median_career_points_share_outside_pct"] = None


def top5_block(ev: pd.DataFrame, names: dict[str, str]) -> dict[str, list]:
    wins = (
        ev[ev["event_result_standardized"].astype(str) == "1"]
        .groupby("dancer_id")
        .size()
        .rename("wins")
    )
    agg = (
        ev.groupby("dancer_id")
        .agg(
            points_here=("event_points", "sum"),
            editions=("event_year", "nunique"),
        )
        .join(wins, how="left")
        .fillna({"wins": 0})
    )
    agg["wins"] = agg["wins"].astype(int)
    agg["points_here"] = agg["points_here"].astype(int)

    def top(metric: str, secondary: list[str]) -> list[dict[str, Any]]:
        ordered = agg.sort_values(
            [metric, *secondary], ascending=[False] * (1 + len(secondary))
        ).head(5)
        out = []
        for did, r in ordered.iterrows():
            out.append(
                {
                    "dancer_name": names.get(str(did), str(did)),
                    "points_here": int(r["points_here"]),
                    "editions": int(r["editions"]),
                    "wins": int(r["wins"]),
                }
            )
        return out

    return {
        "points": top("points_here", ["wins", "editions"]),
        "editions": top("editions", ["points_here", "wins"]),
        "wins": top("wins", ["points_here", "editions"]),
    }


def division_cuts(ev: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for div in DIV_ORDER:
        g = ev[ev["event_competition"] == div]
        if g.empty:
            continue
        out.append(
            {
                "division": div,
                "unique_dancers": int(g["dancer_id"].nunique()),
                "total_points": int(g["event_points"].sum()),
            }
        )
    return out


def division_era_mix(ev: pd.DataFrame, gaps: list[int]) -> dict[str, Any]:
    years = sorted(int(y) for y in ev["event_year"].unique())
    if not years:
        return {"definition": "Share of Skill JJ points by division by era", "eras": []}

    # Build eras as contiguous runs between gaps
    gap_set = set(gaps)
    eras_years: list[list[int]] = []
    cur: list[int] = []
    for y in range(years[0], years[-1] + 1):
        if y in gap_set:
            if cur:
                eras_years.append(cur)
                cur = []
            continue
        if y in years:
            cur.append(y)
    if cur:
        eras_years.append(cur)

    eras = []
    for block in eras_years:
        if not block:
            continue
        label = f"{block[0]}–{block[-1]}" if block[0] != block[-1] else str(block[0])
        g = ev[ev["event_year"].isin(block)]
        pts = {
            div: int(g.loc[g["event_competition"] == div, "event_points"].sum())
            for div in DIV_ORDER
            if (g["event_competition"] == div).any()
        }
        total = sum(pts.values()) or 1
        eras.append(
            {
                "era": label,
                "total_points": int(sum(pts.values())),
                "points": pts,
                "share_pct": {k: _pct(v, total) or 0.0 for k, v in pts.items()},
            }
        )
    gap_note = ""
    if gaps:
        gap_note = f"; gap {min(gaps)}-{max(gaps)} excluded" if min(gaps) != max(gaps) else f"; gap {gaps[0]} excluded"
    return {
        "definition": f"Share of Skill JJ points by division by era{gap_note}",
        "eras": eras,
    }


def pairs_block(ev: pd.DataFrame, names: dict[str, str]) -> dict[str, Any]:
    """Place-matched Leader+Follower same place 1-5, same year+division."""
    places = {"1", "2", "3", "4", "5"}
    sub = ev[ev["event_result_standardized"].astype(str).isin(places)].copy()
    sub["place"] = sub["event_result_standardized"].astype(str)
    leaders = sub[sub["event_role"].str.lower().str.startswith("lead")]
    followers = sub[sub["event_role"].str.lower().str.startswith("follow")]
    key_cols = ["event_year", "event_competition", "place"]
    merged = leaders.merge(
        followers,
        on=key_cols,
        suffixes=("_L", "_F"),
    )
    if merged.empty:
        return {
            "method_note": (
                "Place-matched Leader+Follower (same place 1-5) "
                "in any Skill Level JJ division at this event"
            ),
            "repeat_pairs_n": 0,
            "pairs_total": 0,
            "max_together": 0,
            "by_wins": [],
        }

    pair_rows = []
    for _, r in merged.iterrows():
        pair_rows.append(
            {
                "leader": str(r["dancer_id_L"]),
                "follower": str(r["dancer_id_F"]),
                "year": int(r["event_year"]),
                "div": r["event_competition"],
                "place": r["place"],
            }
        )
    pdf = pd.DataFrame(pair_rows)
    pairs_total = len(pdf)
    grp = pdf.groupby(["leader", "follower"])
    stats = []
    for (lead, follow), g in grp:
        wins = int((g["place"] == "1").sum())
        stats.append(
            {
                "leader_name": names.get(lead, lead),
                "follower_name": names.get(follow, follow),
                "placed_together": int(len(g)),
                "wins_together": wins,
                "years": int(g["year"].nunique()),
                "divisions": sorted(g["div"].unique().tolist()),
            }
        )
    stats.sort(
        key=lambda x: (-x["wins_together"], -x["placed_together"], -x["years"])
    )
    repeat_n = sum(1 for s in stats if s["placed_together"] >= 2)
    max_together = max((s["placed_together"] for s in stats), default=0)
    return {
        "method_note": (
            "Place-matched Leader+Follower (same place 1-5) "
            "in any Skill Level JJ division at this event"
        ),
        "repeat_pairs_n": repeat_n,
        "pairs_total": pairs_total,
        "max_together": max_together,
        "by_wins": stats[:12],
    }


def resolve_event(catalog: pd.DataFrame, target: dict[str, Any]) -> pd.Series:
    mask = False
    for frag in target["name_contains"]:
        mask = mask | catalog["canonical_name"].str.contains(frag, case=False, na=False)
    hits = catalog[mask].copy()
    # Prefer rows with editions
    hits = hits[hits["edition_count"].fillna(0) > 0]
    if hits.empty:
        raise ValueError(f"No catalog match for {target['name_contains']}")
    if target.get("hint_id") is not None:
        prefer = hits[hits["event_id"] == target["hint_id"]]
        if not prefer.empty:
            return prefer.iloc[0]
    return hits.sort_values("edition_count", ascending=False).iloc[0]


def build_one(
    target: dict[str, Any],
    frames: dict[str, pd.DataFrame],
    jj: pd.DataFrame,
    peers: pd.DataFrame,
    first_by_event: dict[int, set[str]],
    countries: dict[int, str],
    names: dict[str, str],
) -> dict[str, Any]:
    cat_row = resolve_event(frames["catalog"], target)
    event_id = int(cat_row["event_id"])
    name = str(cat_row["canonical_name"])
    ev = jj[jj["event_id"] == event_id].copy()
    if ev.empty:
        raise ValueError(f"No Skill JJ rows for event_id={event_id} ({name})")

    years = sorted(int(y) for y in ev["event_year"].unique())
    gaps = year_gaps(years)
    starters = first_by_event.get(event_id, set())
    ts = build_timeseries(ev, jj, first_by_event, event_id)

    wins_n = int((ev["event_result_standardized"].astype(str) == "1").sum())
    peak_d = max(ts, key=lambda r: r["unique_dancers"])
    peak_p = max(ts, key=lambda r: r["total_points"])
    peak_n = max(ts, key=lambda r: r["new_dancers"])

    other_divs = sorted(
        set(
            frames["results"]
            .loc[
                (frames["results"]["event_name"] == name)
                & (frames["results"]["event_dance"] == "West Coast Swing")
                & (~frames["results"]["event_competition"].map(_canon_div).isin(DIV_ORDER)),
                "event_competition",
            ]
            .dropna()
            .unique()
        )
    )

    launchpad = launchpad_block(jj, starters, names)
    enrich_launchpad_shares(launchpad, jj, starters, event_id)

    # Notable examples for top-level fields (UK shape)
    champ_ex = [
        {
            "dancer_name": x["dancer_name"],
            "event_year": x["event_year"],
            "champ_pts": x["champ_pts"],
            "note": "Champion pts since 2009",
        }
        for x in launchpad.get("notable_champion_starters", [])[:8]
    ]
    as_ex = [
        {
            "dancer_name": x["dancer_name"],
            "event_year": x["event_year"],
            "allstar_pts_since_2009": x["allstar_pts_since_2009"],
            "last_as_year": x.get("last_as_year"),
        }
        for x in launchpad.get("notable_allstar_starters", [])[:8]
    ]

    peer_context = build_peer_context(
        peers,
        event_id,
        name,
        countries,
        target["region_key"],
        target["region_countries"],
        target["region_label"],
    )

    catalog_out = {
        "canonical_name": name,
        "url": cat_row.get("url") if pd.notna(cat_row.get("url")) else None,
        "typical_location": cat_row.get("typical_location")
        if pd.notna(cat_row.get("typical_location"))
        else None,
        "typical_city": cat_row.get("typical_city")
        if pd.notna(cat_row.get("typical_city"))
        else None,
        "typical_state": cat_row.get("typical_state")
        if pd.notna(cat_row.get("typical_state"))
        else None,
        "typical_country": cat_row.get("typical_country")
        if pd.notna(cat_row.get("typical_country"))
        else countries.get(event_id),
        "first_edition_year": int(years[0]),
        "last_edition_year": int(years[-1]),
        "edition_count": int(len(years)),
        "unique_dancers_all_divisions": int(cat_row["unique_dancers"])
        if pd.notna(cat_row.get("unique_dancers"))
        else None,
        "total_result_rows_all_divisions": int(cat_row["total_result_rows"])
        if pd.notna(cat_row.get("total_result_rows"))
        else None,
        "upcoming_start_date": cat_row.get("upcoming_start_date")
        if pd.notna(cat_row.get("upcoming_start_date"))
        else None,
        "upcoming_location": cat_row.get("upcoming_location")
        if pd.notna(cat_row.get("upcoming_location"))
        else None,
    }

    metrics = {
        "event_id": event_id,
        "generated": date.today().isoformat(),
        "definitions": {
            "skill_jj": (
                "West Coast Swing + Newcomer/Novice/Intermediate/Advanced/"
                "All-Star/Champion, points > 0"
            ),
            "new_dancers": (
                "dancers whose first-ever WSDC points row (Skill JJ) falls on "
                "this event date (event_year_and_month)"
            ),
            "wins": "result_standardized = '1' at this event (Skill JJ)",
            "started_here_notable": (
                "first WSDC points at this event; Champion pts since 2009 + "
                "top All-Star pts since 2009"
            ),
            "pairs": (
                "Place-matched Leader+Follower (same place 1-5) in any Skill "
                "Level JJ division at this event"
            ),
            "peer_context": (
                "Among all Skill JJ events; ranks by unique dancers / "
                "first-ever WSDC points at this event / total Skill JJ points / "
                "edition years"
            ),
            "launchpad": (
                "first-ever WSDC Skill JJ points at this event; highest division "
                "and career points share outside"
            ),
            "division_era_mix": "Share of Skill JJ points by division, by era (gaps excluded)",
            "retention": (
                "Return = points in Y and Y+1; editions = distinct years with points here"
            ),
            f"peer_{target['region_key']}": (
                f"Among {target['region_label']} Skill JJ events "
                "(typical_country / mode location)"
            ),
        },
        "catalog": catalog_out,
        "skill_jj_kpi": {
            "unique_dancers": int(ev["dancer_id"].nunique()),
            "total_points": int(ev["event_points"].sum()),
            "result_rows": int(len(ev)),
            "editions_with_results": int(len(years)),
            "wins": wins_n,
            "first_points_here": len(starters),
            "first_points_share_pct": _pct(len(starters), ev["dancer_id"].nunique())
            or 0.0,
            "peak_year_dancers": peak_d["event_year"],
            "peak_dancers": peak_d["unique_dancers"],
            "peak_year_points": peak_p["event_year"],
            "peak_points": peak_p["total_points"],
            "peak_year_new_dancers": peak_n["event_year"],
            "peak_new_dancers": peak_n["new_dancers"],
        },
        "year_gaps": gaps,
        "champ_window_from_year": 2009,
        "timeseries": ts,
        "division_cuts": division_cuts(ev),
        "top5_by_metric": top5_block(ev, names),
        "pairs_as_champ": pairs_block(ev, names),
        "started_here_notable_examples": champ_ex,
        "started_here_notable_champ_since_2009": champ_ex,
        "started_here_notable_allstar_top3_since_2009": as_ex[:3],
        "other_divisions_present": other_divs,
        "header_candidates": [],
        "insights": {
            "peer_context": peer_context,
            "launchpad": launchpad,
            "division_era_mix": division_era_mix(ev, gaps),
            "retention": retention_block(ev, gaps),
        },
    }
    return metrics


def summarize(metrics_list: list[tuple[dict, dict]]) -> str:
    lines = [
        "# Event portrait metrics summary",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Skill JJ = West Coast Swing + Newcomer/Novice/Intermediate/Advanced/"
        "All-Star/Champion, points > 0.",
        "Debut = first Skill JJ points by `event_year_and_month` at this event.",
        "",
    ]
    for target, m in metrics_list:
        pc = m["insights"]["peer_context"]
        rk = target["region_key"]
        reg = pc[rk]
        kpi = m["skill_jj_kpi"]
        cat = m["catalog"]
        lines += [
            f"## {cat['canonical_name']} (event_id={m['event_id']}, {target['slug']})",
            "",
            f"- Location: {cat.get('typical_location')} ({cat.get('typical_country')})",
            f"- Years: {cat['first_edition_year']}–{cat['last_edition_year']} "
            f"({cat['edition_count']} editions)",
            f"- year_gaps: {m['year_gaps'] or 'none'}",
            "",
            "### KPIs (Skill JJ)",
            f"- Unique dancers: **{kpi['unique_dancers']}**",
            f"- Total points: **{kpi['total_points']}**",
            f"- Wins: **{kpi['wins']}**",
            f"- New dancers (first points here): **{kpi['first_points_here']}** "
            f"({kpi['first_points_share_pct']}%)",
            f"- Peak dancers: {kpi['peak_dancers']} ({kpi['peak_year_dancers']})",
            f"- Peak points: {kpi['peak_points']} ({kpi['peak_year_points']})",
            "",
            "### Global ranks (all Skill JJ events)",
            f"- Unique dancers: **#{pc['rank_by_unique_all']}** / {pc['events_total_n']}",
            f"- First points: **#{pc['rank_by_first_points_all']}**",
            f"- Total points: **#{pc['rank_by_total_points_all']}**",
            "",
            f"### Regional ranks ({rk}, n={reg['events_n']})",
            f"- Unique dancers: **#{reg['rank_by_unique']}**",
            f"- First points: **#{reg['rank_by_first_points']}**",
            f"- Total points: **#{reg['rank_by_total_points']}**",
            "",
            "### Top5 by points",
        ]
        for row in m["top5_by_metric"]["points"][:5]:
            lines.append(
                f"- {row['dancer_name']}: {row['points_here']} pts, "
                f"{row['editions']} eds, {row['wins']} wins"
            )
        lines.append("")
        lines.append("### Top5 by wins")
        for row in m["top5_by_metric"]["wins"][:5]:
            lines.append(
                f"- {row['dancer_name']}: {row['wins']} wins, "
                f"{row['points_here']} pts, {row['editions']} eds"
            )
        lines.append("")
        lp = m["insights"]["launchpad"]
        lines.append(
            f"### Launchpad: {lp['starters_n']} starters → "
            f"AS+ {lp['reached_allstar_plus_n']} ({lp['reached_allstar_plus_pct']}%), "
            f"Champ {lp['reached_champion_n']} ({lp['reached_champion_pct']}%)"
        )
        if lp.get("notable_champion_starters"):
            lines.append("Notable Champion starters:")
            for x in lp["notable_champion_starters"][:5]:
                lines.append(
                    f"- {x['dancer_name']} (debut {x['event_year']}): "
                    f"{x['champ_pts']} champ pts since 2009"
                )
        if lp.get("notable_allstar_starters"):
            lines.append("Notable All-Star starters:")
            for x in lp["notable_allstar_starters"][:5]:
                lines.append(
                    f"- {x['dancer_name']} (debut {x['event_year']}): "
                    f"{x['allstar_pts_since_2009']} AS pts since 2009"
                )
        ret = m["insights"]["retention"]
        lines.append("")
        lines.append(
            f"### Retention: 1-edition {ret['one_edition_pct']}%; "
            f"3+ editions {ret['three_plus_editions_pct']}%"
        )
        if ret.get("return_rate_range_pct"):
            lines.append(
                f"- YoY return range: {ret['return_rate_range_pct'][0]}–"
                f"{ret['return_rate_range_pct'][1]}%"
            )
        if ret.get("return_after_gap"):
            g = ret["return_after_gap"]
            lines.append(
                f"- After gap ({g['from_year']}→{g['to_year']}): "
                f"{g.get('returned_after_gap_n')} of {g['base']} "
                f"({g.get('returned_after_gap_pct')}%) — {g.get('note')}"
            )
        lines.append("")
        lines.append("### Timeseries")
        for row in m["timeseries"]:
            lines.append(
                f"- {row['event_year']}: dancers={row['unique_dancers']}, "
                f"points={row['total_points']}, new={row['new_dancers']}"
            )
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    frames = load_frames()
    jj = build_skill_jj(frames["results"], frames["events_wsdc"])
    first_by_event = first_points_by_event(jj)
    peers = peer_table(jj, first_by_event)
    countries = event_country_map(
        frames["catalog"], frames["editions"], jj, frames["locations"]
    )
    names = (
        frames["roles"]
        .assign(dancer_id=lambda d: d["dancer_id"].astype(str))
        .set_index("dancer_id")["dancer_name"]
        .to_dict()
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built: list[tuple[dict, dict]] = []
    print("Discovered event_ids:")
    for target in TARGETS:
        m = build_one(
            target, frames, jj, peers, first_by_event, countries, names
        )
        out_path = OUT_DIR / target["out"]
        out_path.write_text(
            json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        built.append((target, m))
        pc = m["insights"]["peer_context"]
        rk = target["region_key"]
        print(
            f"  {m['event_id']:>4}  {m['catalog']['canonical_name']}"
            f"  gaps={m['year_gaps']}"
            f"  global=({pc['rank_by_unique_all']},"
            f"{pc['rank_by_first_points_all']},{pc['rank_by_total_points_all']})"
            f"  {rk}=({pc[rk]['rank_by_unique']},"
            f"{pc[rk]['rank_by_first_points']},{pc[rk]['rank_by_total_points']})"
            f"  → {out_path.name}"
        )

    summary_path = OUT_DIR / "summary.md"
    summary_path.write_text(summarize(built), encoding="utf-8")
    print(f"\nSummary: {summary_path}")


if __name__ == "__main__":
    main()
