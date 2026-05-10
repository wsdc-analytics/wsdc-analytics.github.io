#!/usr/bin/env python3
"""Smoke-check critical site files and sitemap links."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_exists(*relative_paths: str) -> None:
    for rel in relative_paths:
        path = ROOT / rel
        if not path.exists():
            fail(f"Missing critical file: {rel}")
    print("[OK] Critical files exist")


def check_sitemap_links() -> None:
    sitemap = ROOT / "sitemap.xml"
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(sitemap)
    locs = [loc.text for loc in tree.findall(".//sm:loc", ns) if loc.text]
    if not locs:
        fail("No URLs found in sitemap.xml")

    missing = []
    for loc in locs:
        parsed = urlparse(loc)
        page = parsed.path.lstrip("/") or "index.html"
        if page == "":
            page = "index.html"
        page_path = ROOT / page
        if not page_path.exists():
            missing.append(page)

    if missing:
        fail(f"Sitemap references missing files: {sorted(set(missing))[:10]}")
    print("[OK] Sitemap links resolve to existing files")


def check_index_data_references() -> None:
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r"static/data/[a-zA-Z0-9_\-]+\.json", index_html)
    missing = [ref for ref in refs if not (ROOT / ref).exists()]
    if missing:
        fail(f"index.html references missing data files: {missing}")
    print("[OK] index.html data references exist")


def main() -> None:
    check_exists(
        "index.html",
        "points-summary.html",
        "sitemap.xml",
        "robots.txt",
        "static/data/articles.json",
        "static/data/points_summaries.json",
    )
    check_sitemap_links()
    check_index_data_references()
    print("[OK] Smoke checks passed.")


if __name__ == "__main__":
    main()
