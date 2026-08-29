/**
 * Article thumbs: 👍 / 👎 + counts (right-aligned under article).
 *
 * Mount:
 *   <section data-article-engage data-article-id="…" data-lang="ru"></section>
 */
(function () {
  "use strict";

  var VOTER_KEY = "wsdc_reaction_voter_v1";
  var COOKIE_NAME = "wsdc_rk";
  var DEFAULT_API = "https://wsdc-analytics-github-io.vercel.app";

  var LABELS = {
    en: { up: "Helpful", down: "Not helpful" },
    ru: { up: "Полезно", down: "Не полезно" },
    es: { up: "Útil", down: "No útil" },
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
    var secure = location.protocol === "https:" ? "; Secure" : "";
    document.cookie =
      name +
      "=" +
      encodeURIComponent(value) +
      "; path=/; max-age=" +
      60 * 60 * 24 * 400 +
      "; SameSite=Lax" +
      secure;
  }

  function isValidArticleId(id) {
    return typeof id === "string" && /^[a-z0-9][a-z0-9_-]{1,120}$/i.test(id);
  }

  function apiBase(el) {
    var raw = String(el.getAttribute("data-api-base") || DEFAULT_API).replace(/\/$/, "");
    if (/^https:\/\/wsdc-analytics-github-io\.vercel\.app$/i.test(raw)) return raw;
    if (/^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(raw)) return raw;
    return DEFAULT_API;
  }

  function getVoterKey() {
    var fromLs = "";
    try {
      fromLs = localStorage.getItem(VOTER_KEY) || "";
    } catch {
      /* ignore */
    }
    var key = fromLs || readCookie(COOKIE_NAME) || uuidLite();
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

  function emptyRow() {
    return { up: 0, down: 0, mine: null };
  }

  function render(el, counts) {
    var lang = langOf(el);
    var labels = LABELS[lang] || LABELS.en;
    var articleId = el.getAttribute("data-article-id") || "";
    var data = (counts && counts[articleId]) || emptyRow();
    el.innerHTML =
      '<div class="article-engage__thumbs" role="group" aria-label="Reactions">' +
      '<button type="button" class="article-engage__btn' +
      (data.mine === "up" ? " is-active" : "") +
      '" data-value="up" aria-pressed="' +
      (data.mine === "up" ? "true" : "false") +
      '" aria-label="' +
      esc(labels.up) +
      '"><span class="article-engage__emoji" aria-hidden="true">👍</span>' +
      '<span class="article-engage__count" data-count="up">' +
      esc(String(data.up || 0)) +
      "</span></button>" +
      '<button type="button" class="article-engage__btn' +
      (data.mine === "down" ? " is-active" : "") +
      '" data-value="down" aria-pressed="' +
      (data.mine === "down" ? "true" : "false") +
      '" aria-label="' +
      esc(labels.down) +
      '"><span class="article-engage__emoji" aria-hidden="true">👎</span>' +
      '<span class="article-engage__count" data-count="down">' +
      esc(String(data.down || 0)) +
      "</span></button>" +
      "</div>";
    el._counts = {
      up: Number(data.up) || 0,
      down: Number(data.down) || 0,
      mine: data.mine || null,
    };
  }

  function applyCounts(el, row) {
    var data = {
      up: Number(row.up) || 0,
      down: Number(row.down) || 0,
      mine: row.mine || null,
    };
    el._counts = data;
    el.querySelectorAll(".article-engage__btn").forEach(function (btn) {
      var v = btn.getAttribute("data-value");
      var on = data.mine === v;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var up = el.querySelector('[data-count="up"]');
    var down = el.querySelector('[data-count="down"]');
    if (up) up.textContent = String(data.up);
    if (down) down.textContent = String(data.down);
  }

  function optimisticToggle(prev, next) {
    var up = prev.up;
    var down = prev.down;
    var mine = prev.mine;
    if (mine === "up") up = Math.max(0, up - 1);
    if (mine === "down") down = Math.max(0, down - 1);
    if (next === "up") up += 1;
    if (next === "down") down += 1;
    return { up: up, down: down, mine: next };
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
    if (el._engageBound) return;
    el._engageBound = true;
    el.addEventListener("click", function (e) {
      var btn = e.target.closest(".article-engage__btn");
      if (!btn || !el.contains(btn)) return;
      e.preventDefault();
      var articleId = el.getAttribute("data-article-id");
      if (!isValidArticleId(articleId) || el._voting) return;
      var next = btn.getAttribute("data-value");
      var prev = el._counts || emptyRow();
      var value = prev.mine === next ? null : next;
      var optimistic = optimisticToggle(prev, value);
      applyCounts(el, optimistic);
      el._voting = true;
      postVote(el, articleId, value, voterKey)
        .then(function (data) {
          applyCounts(el, data);
        })
        .catch(function (err) {
          applyCounts(el, prev);
          if (typeof console !== "undefined" && console.warn) {
            console.warn("[article-engage] vote failed", err && err.message ? err.message : err);
          }
        })
        .finally(function () {
          el._voting = false;
        });
    });
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
      .filter(isValidArticleId);
    var counts = {};
    try {
      counts = await fetchCounts(nodes[0], ids, voterKey);
    } catch {
      counts = {};
    }
    nodes.forEach(function (el) {
      render(el, counts);
      bind(el, voterKey);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll);
  } else {
    mountAll();
  }

  window.ArticleEngage = { mount: mountAll };
})();
