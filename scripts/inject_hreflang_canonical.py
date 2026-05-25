#!/usr/bin/env python3
"""Inject canonical and hreflang links into multilingual HTML pages."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://wsdc-analytics.github.io"
MARKER = "<!-- SEO: canonical & hreflang -->"

# Keep in sync with static/js/lang-redirect.js
SUPPORTED_BASES = [
    "overview_2025",
    "geo_2025",
    "events_2025",
    "dancers_2025",
    "rules_evolution_2025",
    "rules_catalog",
    "article_secondary_role",
    "article_3year_rule",
    "article_division_transition_time",
]


def lang_urls(base: str) -> dict[str, str]:
    return {
        "ru": f"{SITE}/{base}.html",
        "en": f"{SITE}/{base}_en.html",
        "es": f"{SITE}/{base}_es.html",
    }


def seo_block(canonical: str, urls: dict[str, str]) -> str:
    return (
        f"\n  {MARKER}\n"
        f'  <link rel="canonical" href="{canonical}" />\n'
        f'  <link rel="alternate" hreflang="ru" href="{urls["ru"]}" />\n'
        f'  <link rel="alternate" hreflang="en" href="{urls["en"]}" />\n'
        f'  <link rel="alternate" hreflang="es" href="{urls["es"]}" />\n'
        f'  <link rel="alternate" hreflang="x-default" href="{urls["ru"]}" />\n'
    )


def parse_page(filename: str) -> tuple[str, str] | None:
    """Return (base, canonical_url) for a supported page."""
    name = filename.lower()
    if not name.endswith(".html"):
        return None

    for base in SUPPORTED_BASES:
        urls = lang_urls(base)
        if name == f"{base}.html":
            return base, urls["ru"]
        if name == f"{base}_en.html":
            return base, urls["en"]
        if name == f"{base}_es.html":
            return base, urls["es"]
        if base == "dancers_2025" and name == "dancers_2025_ru.html":
            return base, urls["ru"]
    return None


def remove_existing_block(content: str) -> str:
    if MARKER not in content:
        return content
    pattern = re.compile(
        r"\s*<!-- SEO: canonical & hreflang -->.*?<link rel=\"alternate\" hreflang=\"x-default\"[^>]*/>\s*",
        re.DOTALL,
    )
    return pattern.sub("\n", content)


def inject(content: str, block: str) -> str:
    content = remove_existing_block(content)
    if MARKER in content:
        return content

    match = re.search(r"<meta[^>]*viewport[^>]*>\s*", content, re.IGNORECASE)
    if not match:
        match = re.search(r"<head>\s*", content, re.IGNORECASE)
        if not match:
            raise ValueError("No <head> or viewport meta found")
        pos = match.end()
    else:
        pos = match.end()

    return content[:pos] + block + content[pos:]


def collect_targets() -> list[Path]:
    paths: list[Path] = []
    for base in SUPPORTED_BASES:
        for suffix in ("", "_en", "_es"):
            path = ROOT / f"{base}{suffix}.html"
            if path.exists():
                paths.append(path)
        if base == "dancers_2025":
            ru_alt = ROOT / "dancers_2025_ru.html"
            if ru_alt.exists():
                paths.append(ru_alt)
    return sorted(set(paths))


def main() -> None:
    updated = 0
    for path in collect_targets():
        parsed = parse_page(path.name)
        if not parsed:
            print(f"[SKIP] {path.name}: unsupported name")
            continue

        base, canonical = parsed
        block = seo_block(canonical, lang_urls(base))
        original = path.read_text(encoding="utf-8")
        new_content = inject(original, block)
        if new_content != original:
            path.write_text(new_content, encoding="utf-8")
            updated += 1
            print(f"[OK] {path.name} -> {canonical}")

    print(f"\nUpdated {updated} file(s).")


if __name__ == "__main__":
    main()
