/**
 * Shared article engage block: 👍/👎 + Q&A Hub CTA.
 *
 * Mount:
 *   <section data-article-engage data-article-id="rules_evolution_2025_ru" data-lang="ru"></section>
 *   <link rel="stylesheet" href="static/css/article-engage.css">
 *   <script src="static/js/article-engage.js" defer></script>
 *
 * Optional: data-api-base, data-qa-href, data-path-prefix
 */
(function () {
  "use strict";

  var VOTER_KEY = "wsdc_reaction_voter_v1";
  var COOKIE_NAME = "wsdc_rk";
  var DEFAULT_API = "https://wsdc-analytics-github-io.vercel.app";

  var COPY = {
    en: {
      rate: "Was this useful?",
      up: "Helpful",
      down: "Not helpful",
      cta:
        "Questions, corrections, or ideas? Ask in the Q&A Hub — no account needed.",
      link: "Open Q&A Hub",
    },
    ru: {
      rate: "Была ли статья полезной?",
      up: "Полезно",
      down: "Не полезно",
      cta:
        "Есть вопросы, уточнения или замечания? Задайте их в Q&A Hub — без регистрации.",
      link: "Перейти в Q&A Hub",
    },
    es: {
      rate: "¿Te resultó útil?",
      up: "Útil",
      down: "No útil",
      cta:
        "¿Preguntas, correcciones o ideas? Escríbelas en el Q&A Hub — sin cuenta.",
      link: "Abrir Q&A Hub",
    },
  };

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function uuidLite() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "v-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
  }

  function readCookie(name) {
    var m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : "";
  }

  function writeCookie(name, value) {
    var maxAge = 60 * 60 * 24 * 400;
    document.cookie =
      name +
      "=" +
      encodeURIComponent(value) +
      "; path=/; max-age=" +
      maxAge +
      "; SameSite=Lax";
  }

  function getVoterKey() {
    var fromLs = "";
    try {
      fromLs = localStorage.getItem(VOTER_KEY) || "";
    } catch {
      /* ignore */
    }
    var fromCookie = readCookie(COOKIE_NAME);
    var key = fromLs || fromCookie || uuidLite();
    if (!/^[a-z0-9-]{8,80}$/i.test(key)) key = uuidLite();
    try {
      localStorage.setItem(VOTER_KEY, key);
    } catch {
      /* ignore */
    }
    writeCookie(COOKIE_NAME, key);
    return key;
  }

  function langOf(el) {
    var lang = (el.getAttribute("data-lang") || document.documentElement.lang || "en").toLowerCase();
    if (lang.indexOf("ru") === 0) return "ru";
    if (lang.indexOf("es") === 0) return "es";
    return "en";
  }

  function apiBase(el) {
    var raw = el.getAttribute("data-api-base") || DEFAULT_API;
    return String(raw).replace(/\/$/, "");
  }

  function qaHref(el, lang) {
    var prefix = el.getAttribute("data-path-prefix") || "";
    var custom = el.getAttribute("data-qa-href");
    var pageUrl = location.href.split("#")[0].split("?")[0];
    if (custom) return custom;
    var title = document.title.replace(/\s*\|\s*WSDC Analytics\s*$/i, "").trim();
    var params = new URLSearchParams();
    params.set("lang", lang);
    params.set("page_url", pageUrl);
    if (title) params.set("title", title.slice(0, 120));
    return prefix + "qa.html?" + params.toString() + "#board/articles";
  }

  function render(el, counts) {
    var lang = langOf(el);
    var c = COPY[lang] || COPY.en;
    var articleId = el.getAttribute("data-article-id") || "";
    var data = (counts && counts[articleId]) || { up: 0, down: 0, mine: null };
    var upActive = data.mine === "up" ? " is-active" : "";
    var downActive = data.mine === "down" ? " is-active" : "";

    el.innerHTML =
      '<div class="article-engage__row">' +
      '<p class="article-engage__label">' +
      esc(c.rate) +
      "</p>" +
      '<div class="article-engage__thumbs">' +
      '<button type="button" class="article-engage__btn' +
      upActive +
      '" data-value="up" aria-pressed="' +
      (data.mine === "up" ? "true" : "false") +
      '" aria-label="' +
      esc(c.up) +
      '"><span aria-hidden="true">👍</span><span>' +
      esc(c.up) +
      '</span><span class="article-engage__count" data-count="up">' +
      esc(String(data.up || 0)) +
      "</span></button>" +
      '<button type="button" class="article-engage__btn' +
      downActive +
      '" data-value="down" aria-pressed="' +
      (data.mine === "down" ? "true" : "false") +
      '" aria-label="' +
      esc(c.down) +
      '"><span aria-hidden="true">👎</span><span>' +
      esc(c.down) +
      '</span><span class="article-engage__count" data-count="down">' +
      esc(String(data.down || 0)) +
      "</span></button>" +
      "</div></div>" +
      '<p class="article-engage__cta">' +
      esc(c.cta) +
      ' <a href="' +
      esc(qaHref(el, lang)) +
      '">' +
      esc(c.link) +
      "</a></p>";
  }

  function applyCounts(el, data) {
    var articleId = el.getAttribute("data-article-id") || "";
    var row = data[articleId] || data;
    el.querySelectorAll(".article-engage__btn").forEach(function (btn) {
      var v = btn.getAttribute("data-value");
      var on = row.mine === v;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var up = el.querySelector('[data-count="up"]');
    var down = el.querySelector('[data-count="down"]');
    if (up) up.textContent = String(row.up || 0);
    if (down) down.textContent = String(row.down || 0);
  }

  async function fetchCounts(el, ids, voterKey) {
    var url =
      apiBase(el) +
      "/api/reactions?ids=" +
      encodeURIComponent(ids.join(",")) +
      "&voter_key=" +
      encodeURIComponent(voterKey);
    var res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load reactions");
    return res.json();
  }

  async function postVote(el, articleId, value, voterKey) {
    var res = await fetch(apiBase(el) + "/api/reactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        article_id: articleId,
        value: value,
        voter_key: voterKey,
      }),
    });
    var data = await res.json().catch(function () {
      return {};
    });
    if (!res.ok) throw new Error(data.error || "Vote failed");
    return data;
  }

  function bind(el, voterKey) {
    el.addEventListener("click", function (e) {
      var btn = e.target.closest(".article-engage__btn");
      if (!btn || !el.contains(btn)) return;
      var articleId = el.getAttribute("data-article-id");
      if (!articleId) return;
      var next = btn.getAttribute("data-value");
      var current = btn.classList.contains("is-active") ? next : null;
      var value = current === next ? null : next;
      btn.disabled = true;
      postVote(el, articleId, value, voterKey)
        .then(function (data) {
          applyCounts(el, data);
        })
        .catch(function () {
          /* keep previous UI */
        })
        .finally(function () {
          btn.disabled = false;
        });
    });
  }

  async function mountOne(el, voterKey, sharedCounts) {
    var articleId = el.getAttribute("data-article-id");
    if (!articleId) return;
    var counts = sharedCounts || {};
    if (!sharedCounts) {
      try {
        counts = await fetchCounts(el, [articleId], voterKey);
      } catch {
        counts = {};
      }
    }
    render(el, counts);
    bind(el, voterKey);
  }

  async function mountAll() {
    var nodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-article-engage]")
    );
    if (!nodes.length) return;
    var voterKey = getVoterKey();
    var ids = nodes
      .map(function (el) {
        return el.getAttribute("data-article-id");
      })
      .filter(Boolean);
    var counts = {};
    try {
      counts = await fetchCounts(nodes[0], ids, voterKey);
    } catch {
      counts = {};
    }
    nodes.forEach(function (el) {
      mountOne(el, voterKey, counts);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll);
  } else {
    mountAll();
  }

  window.ArticleEngage = { mount: mountAll };
})();
