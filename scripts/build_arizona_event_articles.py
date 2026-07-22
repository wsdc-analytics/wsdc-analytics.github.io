#!/usr/bin/env python3
"""Build production article_ru/en/es from source_draft_ru.html + i18n.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENT = ROOT / "events" / "001-arizona-4th-of-july"
DRAFT = EVENT / "source_draft_ru.html"
REDIRECT = EVENT / "draft_ru.html"
I18N = EVENT / "i18n.json"
BASE = "https://wsdc-analytics.github.io/events/001-arizona-4th-of-july"
OG_IMAGE = f"{BASE}/assets/hero_fullwidth.png"
STATIC = "../../static"
NS = "articles-events-001-arizona"

EXTRA_CSS = r"""
    .article-header-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      width: 100%;
    }
    .article-header {
      justify-content: flex-start;
    }
    .article-eyebrow {
      margin-top: auto;
    }
    .article-reactions {
      margin: 40px 0 0;
      padding-top: 24px;
      border-top: 1px solid var(--line);
      text-align: right;
      max-width: 100%;
    }
    .article-reactions-label { font-size: 14px; color: var(--muted); margin-bottom: 10px; }
    .article-reactions-buttons { display: flex; flex-wrap: wrap; gap: 20px; justify-content: flex-end; align-items: flex-start; }
    .article-reaction-item { display: inline-flex; align-items: center; gap: 6px; }
    .article-reaction-trigger {
      position: relative; display: inline-flex; align-items: center; justify-content: center;
      cursor: pointer; border: none; background: none; padding: 4px; font-size: inherit; line-height: 1;
      min-width: 2.5rem; min-height: 2.5rem; border-radius: 6px;
    }
    .article-reaction-trigger:hover { background: rgba(45, 55, 72, 0.06); }
    .article-reaction-trigger:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    .article-reaction-emoji { font-size: 1.5rem; line-height: 1; pointer-events: none; font-weight: 600; font-family: inherit; }
    .article-reaction-item.reaction-approve .article-reaction-emoji { color: #16a34a; }
    .article-reaction-item.reaction-neutral .article-reaction-emoji { color: #6b7280; }
    .article-reaction-item.reaction-disapprove .article-reaction-emoji { color: #dc2626; }
    .article-reaction-trigger .lyket-overlay { position: absolute; inset: 0; opacity: 0; overflow: hidden; pointer-events: none; z-index: 0; }
    .article-reaction-count { font-size: 0.95rem; color: var(--muted); min-width: 1.2em; text-align: left; }
    .article-feedback {
      margin-top: 32px;
      padding: 24px 24px 20px;
      border-radius: 12px;
      background: var(--wash);
      border: 1px solid var(--line);
      max-width: 100%;
      text-align: left;
    }
    .article-feedback-title { font-size: 20px; font-weight: 600; margin-bottom: 8px; color: var(--ink); }
    .article-feedback-text { font-size: 14px; color: var(--muted); margin-bottom: 16px; }
    .article-feedback-label { display: block; font-size: 14px; color: var(--muted); margin-bottom: 12px; }
    .article-feedback-input {
      width: 100%; margin-top: 4px; padding: 10px 12px; border-radius: 6px;
      border: 1px solid var(--line); font-family: inherit; font-size: 14px;
      resize: vertical; background: var(--paper);
    }
    .article-feedback-input:focus {
      outline: 2px solid #2563eb; outline-offset: 2px; border-color: #2563eb;
    }
    .article-feedback-button {
      display: inline-flex; align-items: center; justify-content: center;
      padding: 10px 18px; border-radius: 999px; border: none;
      background: #2563eb; color: #fff; font-size: 14px; font-weight: 500;
      cursor: pointer; margin-top: 8px;
    }
    .article-feedback-button:hover { background: #1d4ed8; }
    .article-feedback-button[disabled] { opacity: 0.6; cursor: default; }
    .article-feedback-status { font-size: 13px; margin-top: 8px; color: var(--muted); }
    .skip-link {
      position: absolute; top: -40px; left: 0; background: var(--ink); color: #fff;
      padding: 8px 16px; text-decoration: none; z-index: 100; border-radius: 0 0 4px 0;
      opacity: 0; pointer-events: none;
    }
    .skip-link:focus { top: 0; opacity: 1; pointer-events: auto; }
    @media (max-width: 900px) {
      .article-reactions { text-align: left; }
      .article-reactions-buttons { justify-content: flex-start; }
    }
"""


def head_extras(t: dict) -> str:
    lang = t["lang"]
    page = f"article_{lang}.html"
    url = f"{BASE}/{page}"
    return f"""  <link rel="canonical" href="{url}" />
  <link rel="alternate" hreflang="ru" href="{BASE}/article_ru.html" />
  <link rel="alternate" hreflang="en" href="{BASE}/article_en.html" />
  <link rel="alternate" hreflang="es" href="{BASE}/article_es.html" />
  <link rel="alternate" hreflang="x-default" href="{BASE}/article_ru.html" />
  <meta name="description" content="{esc_attr(t['meta_description'])}">
  <meta name="keywords" content="{esc_attr(t['meta_keywords'])}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://www.googletagmanager.com">
  <link rel="dns-prefetch" href="https://www.googletagmanager.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="preload" href="assets/hero_fullwidth.png" as="image" fetchpriority="high">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{esc_attr(t['og_title'])}">
  <meta property="og:description" content="{esc_attr(t['og_description'])}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{url}">
  <meta name="twitter:title" content="{esc_attr(t['og_title'])}">
  <meta name="twitter:description" content="{esc_attr(t['og_description'])}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <title>{esc_html(t['title'])}</title>
  <link rel="stylesheet" href="{STATIC}/css/tokens.css">
  <link rel="stylesheet" href="{STATIC}/css/site-chrome.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": {json.dumps(t['og_title'], ensure_ascii=False)},
    "description": {json.dumps(t['og_description'], ensure_ascii=False)},
    "url": "{url}",
    "image": "{OG_IMAGE}",
    "datePublished": "2026-07-17",
    "dateModified": "2026-07-21",
    "author": {{ "@type": "Organization", "name": "WSDC Analytics" }},
    "publisher": {{
      "@type": "Organization",
      "name": "WSDC Analytics",
      "logo": {{ "@type": "ImageObject", "url": "https://wsdc-analytics.github.io/events_background.png" }}
    }},
    "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{url}" }}
  }}
  </script>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-LMLCY5PE8Z"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-LMLCY5PE8Z');
  </script>
"""


def esc_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def esc_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chrome_mount(t: dict) -> str:
    lang = t["lang"]
    return f"""  <a href="#main-content" class="skip-link">{esc_html(t['skip_link'])}</a>
  <div
    data-site-chrome
    data-fixed="true"
    data-active="home"
    data-lang="{lang}"
    data-home-href="../../index.html"
    data-path-prefix="../../"
    data-lang-mode="navigate"
    data-lang-ru="article_ru.html"
    data-lang-en="article_en.html"
    data-lang-es="article_es.html"
  ></div>
"""


def reactions_feedback(t: dict) -> str:
    lang = t["lang"]
    aid = f"events_001_arizona_4th_of_july_{lang}"
    return f"""
    <section class="article-reactions" aria-label="{esc_attr(t['reactions_aria'])}">
      <div class="article-reactions-label">{esc_html(t['reactions_label'])}</div>
      <div class="article-reactions-buttons">
        <div class="article-reaction-item reaction-approve">
          <div class="article-reaction-trigger" role="button" tabindex="0" aria-label="{esc_attr(t['react_approve'])}">
            <span class="article-reaction-emoji" aria-hidden="true">✓</span>
            <div class="lyket-overlay" data-lyket-type="like" data-lyket-namespace="{NS}" data-lyket-id="{aid}_positive"></div>
          </div>
          <span class="article-reaction-count" data-lyket-namespace="{NS}" data-lyket-id="{aid}_positive">—</span>
        </div>
        <div class="article-reaction-item reaction-neutral">
          <div class="article-reaction-trigger" role="button" tabindex="0" aria-label="{esc_attr(t['react_neutral'])}">
            <span class="article-reaction-emoji" aria-hidden="true">○</span>
            <div class="lyket-overlay" data-lyket-type="like" data-lyket-namespace="{NS}" data-lyket-id="{aid}_neutral"></div>
          </div>
          <span class="article-reaction-count" data-lyket-namespace="{NS}" data-lyket-id="{aid}_neutral">—</span>
        </div>
        <div class="article-reaction-item reaction-disapprove">
          <div class="article-reaction-trigger" role="button" tabindex="0" aria-label="{esc_attr(t['react_disapprove'])}">
            <span class="article-reaction-emoji" aria-hidden="true">✗</span>
            <div class="lyket-overlay" data-lyket-type="like" data-lyket-namespace="{NS}" data-lyket-id="{aid}_negative"></div>
          </div>
          <span class="article-reaction-count" data-lyket-namespace="{NS}" data-lyket-id="{aid}_negative">—</span>
        </div>
      </div>
    </section>

    <section class="article-feedback" aria-labelledby="feedback-heading">
      <h2 class="article-feedback-title" id="feedback-heading">{esc_html(t['feedback_title'])}</h2>
      <p class="article-feedback-text">{esc_html(t['feedback_text'])}</p>
      <form class="article-feedback-form" id="articleFeedbackForm">
        <label class="article-feedback-label" for="articleFeedbackMessage">{esc_html(t['feedback_message'])}</label>
        <textarea id="articleFeedbackMessage" class="article-feedback-input" rows="4" required></textarea>
        <label class="article-feedback-label" for="articleFeedbackEmail" style="margin-top: 8px;">{esc_html(t['feedback_email'])}</label>
        <input type="email" id="articleFeedbackEmail" class="article-feedback-input" placeholder="you@example.com" autocomplete="email" />
        <button type="submit" class="article-feedback-button" id="articleFeedbackSubmit">{esc_html(t['feedback_submit'])}</button>
        <p class="article-feedback-status" id="articleFeedbackStatus" aria-live="polite"></p>
      </form>
    </section>
"""


def reaction_scripts(t: dict) -> str:
    lang = t["lang"]
    article_id = f"events_001_arizona_4th_of_july_{lang}"
    txt = {
        "sending": t["fb_sending"],
        "ok": t["fb_ok"],
        "error": t["fb_error"],
        "validation": t["fb_validation"],
    }
    return f"""
  <script>
(function() {{
  var REACTIONS_API = 'https://wsdc-analytics-github-io.vercel.app';
  function getCountsUrl() {{ return REACTIONS_API ? (REACTIONS_API.replace(/\\/$/, '') + '/api/reactions') : '{STATIC}/data/reactions.json'; }}
  function applyCount(span, n) {{ if (span) span.textContent = typeof n === 'number' && n >= 0 ? n : '—'; }}
  function fetchCounts() {{
    var url = getCountsUrl();
    fetch(url, {{ credentials: 'omit' }}).then(function(r) {{ return r.ok ? r.json() : {{}}; }}).then(function(data) {{
      document.querySelectorAll('.article-reaction-count[data-lyket-namespace][data-lyket-id]').forEach(function(span) {{
        var id = span.getAttribute('data-lyket-id');
        if (id) applyCount(span, (data && typeof data[id] === 'number') ? data[id] : 0);
      }});
    }}).catch(function() {{
      document.querySelectorAll('.article-reaction-count[data-lyket-namespace][data-lyket-id]').forEach(function(span) {{ applyCount(span, 0); }});
    }});
  }}
  function voteReaction(id, countSpan) {{
    if (!id || !countSpan || !REACTIONS_API) return;
    countSpan.setAttribute('aria-busy', 'true');
    countSpan.textContent = '…';
    var base = REACTIONS_API.replace(/\\/$/, '');
    fetch(base + '/api/reactions', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      credentials: 'omit',
      body: JSON.stringify({{ id: id }})
    }}).then(function() {{ fetchCounts(); }}).catch(function() {{ fetchCounts(); }}).finally(function() {{ countSpan.removeAttribute('aria-busy'); }});
  }}
  function initReactionClicks() {{
    document.querySelectorAll('.article-reaction-trigger[role="button"]').forEach(function(trigger) {{
      var overlay = trigger.querySelector('.lyket-overlay');
      var id = overlay && overlay.getAttribute('data-lyket-id');
      var item = trigger.closest('.article-reaction-item');
      var countSpan = item && item.querySelector('.article-reaction-count[data-lyket-namespace][data-lyket-id]');
      if (!id || !countSpan) return;
      trigger.addEventListener('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        voteReaction(id, countSpan);
      }});
    }});
  }}
  function initReactionKeys() {{
    document.querySelectorAll('.article-reaction-trigger[role="button"]').forEach(function(trigger) {{
      trigger.addEventListener('keydown', function(e) {{
        if (e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        trigger.click();
      }});
    }});
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function() {{ fetchCounts(); initReactionClicks(); initReactionKeys(); }});
  else {{ fetchCounts(); initReactionClicks(); initReactionKeys(); }}
}})();
  </script>
  <script>
(function() {{
  var FORM_ID = 'articleFeedbackForm';
  var MESSAGE_ID = 'articleFeedbackMessage';
  var EMAIL_ID = 'articleFeedbackEmail';
  var SUBMIT_ID = 'articleFeedbackSubmit';
  var STATUS_ID = 'articleFeedbackStatus';
  var API_BASE = 'https://wsdc-analytics-github-io.vercel.app';
  var ARTICLE_ID = '{article_id}';
  var TXT = {json.dumps(txt, ensure_ascii=False)};

  function $(id) {{ return document.getElementById(id); }}

  function setStatus(text, isError) {{
    var el = $(STATUS_ID);
    if (!el) return;
    el.textContent = text || '';
    el.style.color = isError ? '#dc2626' : 'var(--muted)';
  }}

  function onSubmit(e) {{
    e.preventDefault();
    var form = $(FORM_ID);
    var msgEl = $(MESSAGE_ID);
    var emailEl = $(EMAIL_ID);
    var btn = $(SUBMIT_ID);
    if (!form || !msgEl || !btn) return;
    var message = msgEl.value.trim();
    var email = emailEl && emailEl.value.trim();
    if (!message || message.length < 5) {{
      setStatus(TXT.validation, true);
      return;
    }}
    btn.disabled = true;
    setStatus(TXT.sending, false);
    fetch(API_BASE.replace(/\\/$/, '') + '/api/contact', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      credentials: 'omit',
      body: JSON.stringify({{
        articleId: ARTICLE_ID,
        articleUrl: window.location.href,
        message: message,
        email: email
      }})
    }}).then(function(r) {{
      if (!r.ok) throw new Error('Request failed');
      return r.json().catch(function() {{ return {{}}; }});
    }}).then(function() {{
      setStatus(TXT.ok, false);
      msgEl.value = '';
    }}).catch(function() {{
      setStatus(TXT.error, true);
    }}).finally(function() {{
      btn.disabled = false;
    }});
  }}

  function init() {{
    var form = $(FORM_ID);
    if (form) form.addEventListener('submit', onSubmit);
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}})();
  </script>
  <script src="{STATIC}/js/site-chrome.js"></script>
"""


def replace_body_copy(html: str, t: dict) -> str:
    """Replace RU draft body blocks with localized copy (structure preserved)."""
    # Header
    html = re.sub(
        r'<div class="article-eyebrow">.*?</div>',
        f'<div class="article-eyebrow">{esc_html(t["eyebrow"])}</div>',
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<p class="article-subtitle">.*?</p>',
        f'<p class="article-subtitle">{esc_html(t["subtitle"])}</p>',
        html,
        count=1,
        flags=re.S,
    )

    # Series ledes (three consecutive)
    ledes = re.findall(r'<p class="series-lede">.*?</p>', html, flags=re.S)
    if len(ledes) >= 3:
        html = html.replace(
            ledes[0],
            f'<p class="series-lede">\n      {esc_html(t["series_lede_1"])}\n    </p>',
            1,
        )
        html = html.replace(
            ledes[1],
            f'<p class="series-lede">\n      {esc_html(t["series_lede_2"])}\n    </p>',
            1,
        )
        html = html.replace(
            ledes[2],
            f'<p class="series-lede">\n      {t["series_lede_3_html"]}\n    </p>',
            1,
        )

    intros = re.findall(r'<p class="intro">.*?</p>', html, flags=re.S)
    if len(intros) >= 2:
        html = html.replace(
            intros[0],
            f'<p class="intro">\n      {esc_html(t["intro_1"])}\n    </p>',
            1,
        )
        html = html.replace(
            intros[1],
            f'<p class="intro">\n      {esc_html(t["intro_2"])}\n    </p>',
            1,
        )

    html = re.sub(
        r'<summary>.*?</summary>',
        f'<summary>{esc_html(t["links_summary"])}</summary>',
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace("Сайт ивента:", f'{t["link_event"]}:', 1)
    html = html.replace("Сайт клуба:", f'{t["link_club"]}:', 1)
    html = html.replace("Площадка проведения:", f'{t["link_venue"]}:', 1)

    # Snapshot labels — careful ordered replacements
    html = re.sub(
        r'(<div class="snapshot-item">\s*<div class="snapshot-label">)Издания(</div>)',
        rf'\1{esc_html(t["snap_editions"])}\2',
        html,
        count=1,
    )
    html = html.replace(
        "топ-1 среди всех ивентов", esc_html(t["snap_editions_note"]), 1
    )

    # Dancers block (first Танцоры with tooltip after editions)
    html = re.sub(
        r'aria-label="Пояснение: уникальные танцоры с поинтами на этом ивенте"',
        f'aria-label="{esc_attr(t["snap_dancers_aria"])}"',
        html,
        count=1,
    )
    html = html.replace(
        "Количество уникальных танцоров, которые когда-либо получали поинты на этом ивенте в Skill Level номинациях.",
        esc_html(t["snap_dancers_tip"]),
        1,
    )
    html = html.replace("топ-6 среди всех ивентов", esc_html(t["snap_dancers_note"]), 1)

    html = re.sub(
        r'aria-label="Пояснение: первые поинты WSDC на этом ивенте в Skill Level номинациях"',
        f'aria-label="{esc_attr(t["snap_new_aria"])}"',
        html,
        count=1,
    )
    html = html.replace(
        "Количество танцоров, получивших свои первые поинты WSDC на этом ивенте в Skill Level номинациях.",
        esc_html(t["snap_new_tip"]),
        1,
    )
    html = html.replace("топ-13 среди всех ивентов", esc_html(t["snap_new_note"]), 1)

    html = re.sub(
        r'aria-label="Пояснение: сумма Skill-Level поинтов на этом ивенте"',
        f'aria-label="{esc_attr(t["snap_points_aria"])}"',
        html,
        count=1,
    )
    html = html.replace(
        "Количество поинтов, набранных на ивенте всеми танцорами в Skill-Level номинациях.",
        esc_html(t["snap_points_tip"]),
        1,
    )
    html = html.replace("топ-8 среди всех ивентов", esc_html(t["snap_points_note"]), 1)

    # Label text nodes inside snapshot (after tooltips already replaced)
    # Replace snapshot labels carefully by unique context
    html = re.sub(
        r'(<div class="snapshot-label">\s*)Танцоры(\s*<span class="snapshot-info">)',
        rf'\1{esc_html(t["snap_dancers"])}\2',
        html,
        count=1,
    )
    html = re.sub(
        r'(<div class="snapshot-label">\s*)Новые танцоры(\s*<span class="snapshot-info">)',
        rf'\1{esc_html(t["snap_new"])}\2',
        html,
        count=1,
    )
    html = re.sub(
        r'(<div class="snapshot-label">\s*)Поинты(\s*<span class="snapshot-info">)',
        rf'\1{esc_html(t["snap_points"])}\2',
        html,
        count=1,
    )

    def section(title_id: str, title_key: str, html_: str) -> str:
        return re.sub(
            rf'(<h2 class="section-title" id="{title_id}">).*?(</h2>)',
            rf'\1{esc_html(t[title_key])}\2',
            html_,
            count=1,
            flags=re.S,
        )

    html = section("peer-title", "peer_title", html)
    html = section("traj-title", "traj_title", html)
    html = section("launch-title", "launch_title", html)
    html = section("ret-title", "ret_title", html)
    html = section("people-title", "people_title", html)
    html = section("closing-title", "closing_title", html)

    # Paragraphs inside sections — replace by unique RU substrings
    pairs = [
        (
            "Удивительно, но ивент с самой долгой историей не лидирует почти ни по одной ключевой метрике.\n        По танцорам с поинтами он 6-й (1364), по новым танцорам 13-й (245), по сумме поинтов Skill Level 8-й (8284).",
            t["peer_p1"],
        ),
        (
            "Одна из причин: отказ от номинации Newcomer с 1998 года (с мимолётным возвращением номинации в 2009).",
            t["peer_p2"],
        ),
        (
            "Ивент не отличается плавностью роста: были резкие взлёты (1998, 2007) и падения (2011, 2018),\n        плюс пропуск 2020-2021. При этом 2026 уже близко к историческим пикам по танцорам и поинтам.",
            t["traj_p1"],
        ),
        (
            "Максимумы по новым танцорам остались в 1990-х. Сейчас эта метрика заметно скромнее других ивентов.",
            t["traj_p2"],
        ),
        (
            "Для примерно каждого пятого танцора с поинтами на этом ивенте (245 из 1364, около 18%)\n        4TH of July Convention стал первой записью в реестре WSDC.",
            t["launch_p1"],
        ),
        (
            "Большинство стартовавших здесь сейчас остаются в Novice-Advanced: примерно треть в Novice,\n        по четверти имеют право выступать в Intermediate и Advanced. До All-Star и выше доходит\n        примерно каждый восьмой, до Champion каждый пятнадцатый.",
            t["launch_p2"],
        ),
        (
            "Среди тех, кто дошёл до Champion, есть и танцоры, включённые в зал славы WSDC,\n        и те, кто на виду сейчас:",
            t["launch_p3"],
        ),
        (
            "Большинство танцоров с поинтами на этом ивенте отметились в реестре только один раз: 63% (865 из 1364), набрав при этом 39,4% всех Skill Level поинтов.\n        Ниже: как распределяются танцоры с большим количеством успешных участий и какая доля поинтов у этих групп.",
            t["ret_p1"],
        ),
        (
            "Год к году картина другая: приблизительно 25% танцоров с поинтами в одном году снова набирает\n        поинты в следующем году. Это показывает, насколько постоянный состав получает поинты на ивенте.\n        Пик пришёлся на 2015: 40,7% от тех, кто получил поинты в 2014.",
            t["ret_p2"],
        ),
        (
            "Лидером Финикса за всю историю является Robert Royston: у него больше всех поинтов,\n        успешных участий и побед на этом ивенте.",
            t["people_p1"],
        ),
        (
            "По поинтам следом идут Michael Kielbasa (45) и Melissa Rutz (43).\n        Больше всего успешных участий: по 11 у Robert Royston и Benji Schwimmer;\n        они же лидируют по победам (по 4).",
            t["people_p2"],
        ),
        (
            "Чаще всего в финалах совпадали и получали поинты Robert Royston и Torri Zzaoui\n        (три финала, одна победа). Ещё по одной совместной победе при двух финалах\n        у Robert Royston и Brandi Tobias, Kyle Redd и Deborah Szekely, Benji Schwimmer и Laureen Baldovi,\n        Billy Smuck и Sheena Shirley, Bret Navarre и Kristen Parker.\n        PJ Turner и Melissa Rutz дважды совпадали в финале, но не побеждали.",
            t["people_p3"],
        ),
    ]
    for old, new in pairs:
        if old not in html:
            raise SystemExit(f"Missing RU block for replace:\n{old[:80]}...")
        html = html.replace(old, esc_html(new), 1)

    html = re.sub(
        r'<p class="closing">.*?</p>',
        f'<p class="closing">\n        {esc_html(t["closing"])}\n      </p>',
        html,
        count=1,
        flags=re.S,
    )

    # Name list / hof
    for key, ru in [
        ("hof_wayne", "Wayne Bott: первые поинты в 1992, Hall of Fame WSDC 2009"),
        ("hof_martin", "Martin Parker: 1993, Hall of Fame WSDC 2015"),
        ("hof_katie", "Katie Schneider: 2000"),
        ("hof_heidi", "Heidi Groskreutz: 2000"),
        ("hof_cameo", "Cameo Cross: 2007"),
        ("hof_mackenzie", "Mackenzie Keister: 2022"),
        ("hof_others", "и другие."),
    ]:
        html = html.replace(ru, esc_html(t[key]), 1)

    # Aria / toggles / captions
    html = html.replace(
        'aria-label="Метрика сравнения ивентов"',
        f'aria-label="{esc_attr(t["peer_toggles_aria"])}"',
        1,
    )
    html = html.replace(
        'aria-label="Ивенты по выбранной метрике"',
        f'aria-label="{esc_attr(t["peer_bars_aria"])}"',
        1,
    )
    html = html.replace(
        'aria-label="Метрика траектории"',
        f'aria-label="{esc_attr(t["traj_toggles_aria"])}"',
        1,
    )
    html = html.replace(
        'aria-label="Траектория метрики по годам"',
        f'aria-label="{esc_attr(t["traj_aria"])}"',
        1,
    )
    html = html.replace(
        "Наведите на точку: год, значение и изменение к предыдущему году.",
        esc_html(t["traj_caption"]),
        1,
    )
    html = html.replace(
        'aria-label="Высший дивизион стартовавших здесь"',
        f'aria-label="{esc_attr(t["launch_bars_aria"])}"',
        1,
    )
    html = html.replace(
        'aria-label="Число успешных участий на танцора"',
        f'aria-label="{esc_attr(t["ret_bars_aria"])}"',
        1,
    )
    html = html.replace(
        'aria-label="Доля повторного набора поинтов год к году"',
        f'aria-label="{esc_attr(t["ret_chart_aria"])}"',
        1,
    )
    html = html.replace(
        "Доля танцоров с поинтами в году Y, которые снова набрали поинты в Y+1 (1991-2026).",
        esc_html(t["ret_caption"]),
        1,
    )
    html = html.replace(
        'aria-label="Метрика топ-5"',
        f'aria-label="{esc_attr(t["people_toggles_aria"])}"',
        1,
    )
    html = html.replace(
        'aria-label="Топ-5 танцоров"',
        f'aria-label="{esc_attr(t["people_bars_aria"])}"',
        1,
    )

    # Toggle button labels — peer then traj then people
    # peer: Танцоры, Новые танцоры, Поинты
    # traj: Танцоры, Поинты, Новые танцоры
    # people: Поинты, Участия, Победы
    def replace_toggle_block(html_: str, block_id: str, labels: list[str]) -> str:
        pattern = rf'(<div class="metric-toggles" id="{block_id}"[^>]*>)(.*?)(</div>)'
        m = re.search(pattern, html_, flags=re.S)
        if not m:
            raise SystemExit(f"toggle block {block_id} not found")
        block = m.group(2)
        buttons = re.findall(r"(<button[^>]*>)(.*?)(</button>)", block, flags=re.S)
        if len(buttons) != len(labels):
            raise SystemExit(f"{block_id}: expected {len(labels)} buttons, got {len(buttons)}")
        new_block = block
        for (pre, _old, post), lab in zip(buttons, labels):
            new_block = new_block.replace(
                f"{pre}{_old}{post}", f"{pre}{esc_html(lab)}{post}", 1
            )
        return html_[: m.start()] + m.group(1) + new_block + m.group(3) + html_[m.end() :]

    html = replace_toggle_block(
        html, "peerToggles", [t["btn_dancers"], t["btn_new"], t["btn_points"]]
    )
    html = replace_toggle_block(
        html, "trajToggles", [t["btn_dancers"], t["btn_points"], t["btn_new"]]
    )
    html = replace_toggle_block(
        html, "peopleToggles", [t["btn_points"], t["btn_editions"], t["btn_wins"]]
    )

    # Footer
    html = re.sub(
        r'<footer class="article-footer">.*?</footer>',
        f'<footer class="article-footer">\n    {t["footer_html"]}\n  </footer>',
        html,
        count=1,
        flags=re.S,
    )
    return html


def patch_js_i18n(html: str, t: dict) -> str:
    """Inject locale strings into chart/render JS."""
    dec = t["pct_decimal"]
    of_ = t["js_of"]

    # Locale constants at top of IIFE (used by multiple renderers)
    marker = "  const M = JSON.parse(document.getElementById(\"event-metrics\").textContent);\n  const gaps = new Set(M.year_gaps || []);"
    inject = (
        marker
        + f"\n  const PCT_DEC = {json.dumps(dec)};\n"
        + f"  const OF_WORD = {json.dumps(of_, ensure_ascii=False)};\n"
        + "  const fmtPctLoc = (v) => String(v).replace(\".\", PCT_DEC);"
    )
    if marker not in html:
        raise SystemExit("metrics/gaps marker not found")
    html = html.replace(marker, inject, 1)

    # Launch KPIs
    old_launch = '''    document.getElementById("launchKpis").innerHTML = [
      ["Новые танцоры", L.starters_n, ""],
      ["Дошли до All-Star+", `${String(L.reached_allstar_plus_pct).replace(".", ",")}%`, `${L.reached_allstar_plus_n} из ${L.starters_n}`],
      ["Дошли до Champion", `${String(L.reached_champion_pct).replace(".", ",")}%`, `${L.reached_champion_n} из ${L.starters_n}`]
    ].map(([lab, val, note]) =>'''
    new_launch = f'''    document.getElementById("launchKpis").innerHTML = [
      [{json.dumps(t["js_new_dancers"], ensure_ascii=False)}, L.starters_n, ""],
      [{json.dumps(t["js_reached_as"], ensure_ascii=False)}, `${{fmtPctLoc(L.reached_allstar_plus_pct)}}%`, `${{L.reached_allstar_plus_n}} ${{OF_WORD}} ${{L.starters_n}}`],
      [{json.dumps(t["js_reached_champ"], ensure_ascii=False)}, `${{fmtPctLoc(L.reached_champion_pct)}}%`, `${{L.reached_champion_n}} ${{OF_WORD}} ${{L.starters_n}}`]
    ].map(([lab, val, note]) =>'''
    if old_launch not in html:
        raise SystemExit("launch KPI JS block not found")
    html = html.replace(old_launch, new_launch, 1)

    # Retention participation labels
    old_part = '''    const participationLabel = (editions) => {
      if (editions === 1) return "1 успешное участие";
      if (editions === "5+") return "5+ успешных участий";
      const n = Number(editions);
      if (n >= 2 && n <= 4) return `${n} успешных участия`;
      return `${editions} успешных участий`;
    };
    const fmtPct = (v) => String(v).replace(".", ",");
    document.getElementById("retBars").innerHTML = low.map((h) => {
      const w = ((100 * h.dancers) / max).toFixed(1);
      const peoplePct = h.dancers_share_pct != null
        ? h.dancers_share_pct
        : Math.round((1000 * h.dancers) / base) / 10;
      const pointsPct = h.points_share_pct;
      const valueText = pointsPct != null
        ? `${h.dancers} · ${fmtPct(peoplePct)}% танцоров набрали ${fmtPct(pointsPct)}% поинтов`
        : `${h.dancers} · ${fmtPct(peoplePct)}% танцоров`;'''

    part1 = json.dumps(t["js_part_1"], ensure_ascii=False)
    part5 = json.dumps(t["js_part_5plus"], ensure_ascii=False)
    part_n = json.dumps(t["js_part_n"], ensure_ascii=False)
    part_many = json.dumps(t["js_part_n_many"], ensure_ascii=False)
    dp = json.dumps(t["js_dancers_points"], ensure_ascii=False)
    do_ = json.dumps(t["js_dancers_only"], ensure_ascii=False)

    new_part = f'''    const participationLabel = (editions) => {{
      if (editions === 1) return {part1};
      if (editions === "5+") return {part5};
      const n = Number(editions);
      if (n >= 2 && n <= 4) return {part_n}.replace("{{n}}", String(n));
      return {part_many}.replace("{{n}}", String(editions));
    }};
    const fmtPct = (v) => String(v).replace(".", PCT_DEC);
    document.getElementById("retBars").innerHTML = low.map((h) => {{
      const w = ((100 * h.dancers) / max).toFixed(1);
      const peoplePct = h.dancers_share_pct != null
        ? h.dancers_share_pct
        : Math.round((1000 * h.dancers) / base) / 10;
      const pointsPct = h.points_share_pct;
      const valueText = pointsPct != null
        ? {dp}.replace("{{dancers}}", String(h.dancers)).replace("{{peoplePct}}", fmtPct(peoplePct)).replace("{{pointsPct}}", fmtPct(pointsPct))
        : {do_}.replace("{{dancers}}", String(h.dancers)).replace("{{peoplePct}}", fmtPct(peoplePct));'''
    if old_part not in html:
        raise SystemExit("retention JS block not found")
    html = html.replace(old_part, new_part, 1)

    # Return tip "из"
    html = html.replace(
        "${s.returned} из ${s.base}",
        "${s.returned} ${OF_WORD} ${s.base}",
        1,
    )
    html = html.replace(
        'const rate = String(s.value).replace(".", ",");',
        "const rate = String(s.value).replace('.', PCT_DEC);",
        1,
    )

    # YoY format
    old_yoy = '''  function formatYoy(pct) {
    if (pct == null || !Number.isFinite(pct)) return null;
    const rounded = Math.round(pct);
    if (rounded === 0) return { text: "0% год к году", cls: "is-flat" };
    const sign = rounded > 0 ? "+" : "−";
    return { text: `${sign}${Math.abs(rounded)}% год к году`, cls: rounded > 0 ? "is-up" : "is-down" };
  }'''
    flat = json.dumps(t["js_yoy_flat"], ensure_ascii=False)
    up = json.dumps(t["js_yoy_up"], ensure_ascii=False)
    down = json.dumps(t["js_yoy_down"], ensure_ascii=False)
    new_yoy = f'''  function formatYoy(pct) {{
    if (pct == null || !Number.isFinite(pct)) return null;
    const rounded = Math.round(pct);
    if (rounded === 0) return {{ text: {flat}, cls: "is-flat" }};
    if (rounded > 0) return {{ text: {up}.replace("{{n}}", String(Math.abs(rounded))), cls: "is-up" }};
    return {{ text: {down}.replace("{{n}}", String(Math.abs(rounded))), cls: "is-down" }};
  }}'''
    if old_yoy not in html:
        raise SystemExit("formatYoy not found")
    html = html.replace(old_yoy, new_yoy, 1)

    html = html.replace(
        'const pct = (Math.round((1000 * d.n) / base) / 10).toFixed(1).replace(".", ",");',
        "const pct = fmtPctLoc((Math.round((1000 * d.n) / base) / 10).toFixed(1));",
        1,
    )
    return html


def build_one(lang: str, draft: str, i18n: dict) -> str:
    t = i18n[lang]
    html = draft

    # Replace entire head meta/title block up to fonts/style
    html = re.sub(
        r"<html lang=\"ru\">",
        f'<html lang="{lang}">',
        html,
        count=1,
    )
    # Remove old draft head meta/title/fonts — keep style block
    html = re.sub(
        r"<head>\s*<meta charset=\"UTF-8\">.*?<style>",
        "<head>\n  <meta charset=\"UTF-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        + head_extras(t)
        + "  <style>",
        html,
        count=1,
        flags=re.S,
    )

    # Keep draft justify; article-shell left-align is overridden after the link below.
    JUSTIFY_OVERRIDE = f"""  <link rel="stylesheet" href="{STATIC}/css/article-shell.css">
  <style>
    /* Event portraits: restore width justification (shell defaults to left). */
    .article-rail,
    .article-rail p,
    .article-rail .intro,
    .article-rail .series-lede,
    .article-rail .closing,
    .article-rail .footnote,
    .article-content .data-note,
    .article-footer .data-note {{
      text-align: justify;
      text-justify: inter-word;
      hyphens: none;
      -webkit-hyphens: none;
      -ms-hyphens: none;
    }}
    .article-rail .section-title,
    .article-rail .snapshot,
    .article-rail .insight-kpis,
    .article-rail .bar-chart,
    .article-rail .hbar-meta,
    .article-rail .metric-toggles,
    .article-rail .name-list,
    .article-rail .chart-caption,
    .article-rail .article-links,
    .article-rail .article-reactions,
    .article-rail .article-feedback {{
      text-align: left;
    }}
    /* Drop magazine H2 rail — flush left with body column */
    .article-rail .section-title,
    .article-rail h2.section-title,
    .article-content .section-title,
    .article-feedback-title {{
      border-left: none;
      padding-left: 0;
      margin-left: 0;
    }}
    /* Keep series teal: shell remaps --accent to brand gray */
    :root {{
      --accent: #0f766e;
    }}
    .hbar.is-focus .hbar-fill {{
      background: #0f766e;
    }}
    .hbar.is-focus .hbar-meta,
    .hbar.is-focus .hbar-value {{
      color: #0f766e;
    }}
  </style>
</head>"""

    # Inject extra CSS before </style>, then shell + justify override
    html = html.replace(
        "  </style>\n</head>",
        EXTRA_CSS + "  </style>\n" + JUSTIFY_OVERRIDE,
        1,
    )

    # Body: chrome + back link
    html = html.replace(
        "<body>\n\n<div class=\"magazine-container\">",
        "<body>\n" + chrome_mount(t) + "\n<div class=\"wsdc-chrome-page-pad magazine-container\">",
        1,
    )
    html = html.replace(
        '  <header class="article-header">\n    <div class="article-header-media"',
        f'  <header class="article-header">\n    <div class="article-header-top">\n      <a class="wsdc-back is-on-hero" href="../../index.html?lang={lang}" data-wsdc-back id="backLink">{esc_html(t["back_home"])}</a>\n    </div>\n    <div class="article-header-media"',
        1,
    )
    html = html.replace(
        '<main class="article-content">',
        '<main id="main-content" class="article-content">',
        1,
    )

    html = replace_body_copy(html, t)

    # Insert reactions/feedback before footer
    html = html.replace(
        '    </div>\n  </main>\n\n  <footer class="article-footer">',
        "    " + reactions_feedback(t) + "\n    </div>\n  </main>\n\n  <footer class=\"article-footer\">",
        1,
    )

    html = patch_js_i18n(html, t)
    # Scripts before </body>
    html = html.replace("</body>", reaction_scripts(t) + "\n</body>", 1)
    return html


def main() -> None:
    draft = DRAFT.read_text(encoding="utf-8")
    i18n = json.loads(I18N.read_text(encoding="utf-8"))
    for lang in ("ru", "en", "es"):
        out = EVENT / f"article_{lang}.html"
        out.write_text(build_one(lang, draft, i18n), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")

    # Redirect old draft URL
    REDIRECT.write_text(
        """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=article_ru.html">
  <link rel="canonical" href="https://wsdc-analytics.github.io/events/001-arizona-4th-of-july/article_ru.html">
  <title>Redirect…</title>
  <script>location.replace("article_ru.html" + location.search + location.hash);</script>
</head>
<body>
  <p><a href="article_ru.html">article_ru.html</a></p>
</body>
</html>
""",
        encoding="utf-8",
    )
    print("draft_ru.html → redirect to article_ru.html")


if __name__ == "__main__":
    main()
