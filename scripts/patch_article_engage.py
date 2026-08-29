#!/usr/bin/env python3
"""Replace legacy article-reactions + article-feedback blocks with data-article-engage mount."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# basename stem (without .html) → (article_id, lang, path_prefix for nested)
# path_prefix empty for root articles; "../../" for events/*

FILES: list[tuple[str, str, str, str]] = [
    # (relative path, article_id, lang, path_prefix)
    ("rules_evolution_2025.html", "rules_evolution_2025_ru", "ru", ""),
    ("rules_evolution_2025_en.html", "rules_evolution_2025_en", "en", ""),
    ("rules_evolution_2025_es.html", "rules_evolution_2025_es", "es", ""),
    ("overview_2025.html", "overview_2025_ru", "ru", ""),
    ("overview_2025_en.html", "overview_2025_en", "en", ""),
    ("overview_2025_es.html", "overview_2025_es", "es", ""),
    ("geo_2025.html", "geo_2025_ru", "ru", ""),
    ("geo_2025_en.html", "geo_2025_en", "en", ""),
    ("geo_2025_es.html", "geo_2025_es", "es", ""),
    ("events_2025.html", "events_2025_ru", "ru", ""),
    ("events_2025_en.html", "events_2025_en", "en", ""),
    ("events_2025_es.html", "events_2025_es", "es", ""),
    ("dancers_2025.html", "dancers_2025_ru", "ru", ""),
    ("dancers_2025_en.html", "dancers_2025_en", "en", ""),
    ("dancers_2025_es.html", "dancers_2025_es", "es", ""),
    ("article_secondary_role.html", "article_secondary_role_ru", "ru", ""),
    ("article_secondary_role_en.html", "article_secondary_role_en", "en", ""),
    ("article_secondary_role_es.html", "article_secondary_role_es", "es", ""),
    ("article_3year_rule.html", "article_3year_rule_ru", "ru", ""),
    ("article_3year_rule_en.html", "article_3year_rule_en", "en", ""),
    ("article_3year_rule_es.html", "article_3year_rule_es", "es", ""),
    ("article_division_transition_time.html", "article_division_transition_ru", "ru", ""),
    ("article_division_transition_time_en.html", "article_division_transition_en", "en", ""),
    ("article_division_transition_time_es.html", "article_division_transition_es", "es", ""),
    ("events/001-arizona-4th-of-july/article_ru.html", "arizona_4th_ru", "ru", "../../"),
    ("events/001-arizona-4th-of-july/article_en.html", "arizona_4th_en", "en", "../../"),
    ("events/001-arizona-4th-of-july/article_es.html", "arizona_4th_es", "es", "../../"),
    ("events/002-uk-wcs-championships/article_ru.html", "uk_wcs_ru", "ru", "../../"),
    ("events/002-uk-wcs-championships/article_en.html", "uk_wcs_en", "en", "../../"),
    ("events/002-uk-wcs-championships/article_es.html", "uk_wcs_es", "es", "../../"),
]

REACTIONS_RE = re.compile(
    r'<section\s+class="article-reactions"[\s\S]*?</section>\s*',
    re.I,
)
FEEDBACK_RE = re.compile(
    r'<section\s+class="article-feedback"[\s\S]*?</section>\s*',
    re.I,
)
# Inline reaction/feedback scripts (common patterns)
FEEDBACK_SCRIPT_RE = re.compile(
    r'<script>\s*//\s*Article feedback[\s\S]*?</script>\s*',
    re.I,
)
REACTIONS_SCRIPT_RE = re.compile(
    r'<script>\s*\(function\s*\(\)\s*\{\s*var\s+REACTIONS_API[\s\S]*?</script>\s*',
    re.I,
)
# Broader: scripts that reference articleFeedbackForm or REACTIONS_API
LEGACY_SCRIPT_RE = re.compile(
    r'<script>(?:(?!</script>)[\s\S])*(?:articleFeedbackForm|REACTIONS_API|lyket-overlay)(?:(?!</script>)[\s\S])*</script>\s*',
    re.I,
)

CHROME_RE = re.compile(
    r'(<div\s+[^>]*data-site-chrome[^>]*)(>)',
    re.I,
)


def engage_block(article_id: str, lang: str, prefix: str) -> str:
    attrs = [
        'class="article-engage"',
        'data-article-engage',
        f'data-article-id="{article_id}"',
        f'data-lang="{lang}"',
    ]
    if prefix:
        attrs.append(f'data-path-prefix="{prefix}"')
    return f'<section {" ".join(attrs)}></section>\n'


def ensure_assets(html: str, prefix: str) -> str:
    css_href = f'{prefix}static/css/article-engage.css?v=20260829a'
    js_href = f'{prefix}static/js/article-engage.js?v=20260829a'
    if "article-engage.css" not in html:
        html = re.sub(
            r'(</head>)',
            f'  <link rel="stylesheet" href="{css_href}">\n\\1',
            html,
            count=1,
            flags=re.I,
        )
    if "article-engage.js" not in html:
        html = re.sub(
            r'(</body>)',
            f'  <script src="{js_href}" defer></script>\n\\1',
            html,
            count=1,
            flags=re.I,
        )
    return html


def patch_chrome(html: str) -> str:
    def repl(m: re.Match[str]) -> str:
        tag = m.group(1)
        if "data-qa-board" in tag:
            return m.group(0)
        # Prefer data-active="articles" when present; else add both
        if 'data-active="' in tag and "data-active=\"articles\"" not in tag:
            # keep existing active for nav highlight if any; articles use fixed chrome often with home
            # Plan: articles use data-qa-board="articles"
            return tag + ' data-qa-board="articles"' + m.group(2)
        if "data-active" not in tag:
            return tag + ' data-active="articles" data-qa-board="articles"' + m.group(2)
        return tag + ' data-qa-board="articles"' + m.group(2)

    return CHROME_RE.sub(repl, html, count=1)


def patch_file(rel: str, article_id: str, lang: str, prefix: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return f"missing {rel}"
    html = path.read_text(encoding="utf-8")
    original = html

    block = engage_block(article_id, lang, prefix)
    had_reactions = bool(REACTIONS_RE.search(html))
    had_feedback = bool(FEEDBACK_RE.search(html))

    if had_reactions and had_feedback:
        html = REACTIONS_RE.sub(block, html, count=1)
        html = FEEDBACK_RE.sub("", html, count=1)
    elif had_reactions:
        html = REACTIONS_RE.sub(block, html, count=1)
    elif had_feedback:
        html = FEEDBACK_RE.sub(block, html, count=1)
    elif "data-article-engage" not in html:
        # Insert before </article> or before footer
        if re.search(r"</article>", html, re.I):
            html = re.sub(r"</article>", block + "</article>", html, count=1, flags=re.I)
        else:
            return f"skip (no mount point) {rel}"

    html = LEGACY_SCRIPT_RE.sub("", html)
    html = ensure_assets(html, prefix)
    html = patch_chrome(html)

    if html == original:
        return f"unchanged {rel}"
    path.write_text(html, encoding="utf-8")
    return f"patched {rel}"


def main() -> int:
    for item in FILES:
        print(patch_file(*item))
    return 0


if __name__ == "__main__":
    sys.exit(main())
