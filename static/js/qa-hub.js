(function () {
  "use strict";

  const cfg = window.QA_CONFIG || {};
  const SUPABASE_URL = (cfg.supabaseUrl || "").replace(/\/$/, "");
  const ANON = cfg.supabaseAnonKey || "";
  const API_BASE = (cfg.apiBase || "").replace(/\/$/, "");
  const MOD_KEY = "qa_admin_secret_v1";
  const COOLDOWN_KEY = "qa_last_post_ts";
  const COOLDOWN_MS = 20000;
  const I18n = window.QaI18n || null;

  function langFromQuery() {
    try {
      const q = new URLSearchParams(location.search).get("lang");
      if (q && I18n) return I18n.normalizeLang(q);
      if (q === "ru" || q === "es" || q === "en") return q;
    } catch {
      /* ignore */
    }
    const stored = localStorage.getItem("wsdc-lang");
    if (stored === "ru" || stored === "es" || stored === "en") return stored;
    return "en";
  }

  function t(key) {
    if (I18n) return I18n.t(state.lang, key);
    return key;
  }

  function localizedBoardTitle(slug, fallback) {
    if (I18n) return I18n.boardTitle(state.lang, slug, fallback);
    return fallback || slug;
  }

  const els = {
    boards: null,
    composeBoard: document.getElementById("qaComposeBoard"),
    optionalDetails: document.getElementById("qaOptionalDetails"),
    threadList: document.getElementById("qaThreadList"),
    threadPanel: document.getElementById("qaThreadPanel"),
    threadTitle: document.getElementById("qaThreadTitle"),
    threadMeta: document.getElementById("qaThreadMeta"),
    posts: document.getElementById("qaPosts"),
    newThreadForm: document.getElementById("qaNewThreadForm"),
    replyForm: document.getElementById("qaReplyForm"),
    status: document.getElementById("qaStatus"),
    listStatus: document.getElementById("qaListStatus"),
    modBar: document.getElementById("qaModBar"),
    modUnlock: document.getElementById("qaModUnlock"),
    modSecret: document.getElementById("qaModSecret"),
    modLock: document.getElementById("qaModLock"),
    modActions: document.getElementById("qaModActions"),
    stats: document.getElementById("qaStats"),
    aside: document.getElementById("qaAside"),
  };

  const state = {
    lang: langFromQuery(),
    boards: [],
    boardSlug: "other",
    threads: [],
    threadId: null,
    thread: null,
    posts: [],
    mod: Boolean(localStorage.getItem(MOD_KEY)),
  };

  function setStatus(msg, kind) {
    if (!els.status) return;
    els.status.textContent = msg || "";
    els.status.classList.toggle("is-error", kind === "error");
    els.status.classList.toggle("is-ok", kind === "ok");
  }

  function setListStatus(msg) {
    if (els.listStatus) els.listStatus.textContent = msg || "";
  }

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function safeHttpsUrl(raw) {
    const s = String(raw || "").trim();
    if (!s || s.length > 500) return null;
    try {
      const u = new URL(s);
      if (u.protocol !== "https:") return null;
      return u.href;
    } catch {
      return null;
    }
  }

  function fmtDate(iso) {
    try {
      const locale =
        state.lang === "ru" ? "ru-RU" : state.lang === "es" ? "es-ES" : "en-GB";
      return new Date(iso).toLocaleString(locale, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso || "";
    }
  }

  function parseHash() {
    const raw = (location.hash || "").replace(/^#\/?/, "");
    const parts = raw.split("/").filter(Boolean);
    if (parts[0] === "thread" && parts[1]) {
      return { view: "thread", threadId: parts[1], boardSlug: state.boardSlug };
    }
    if (parts[0] === "board" && parts[1]) {
      return { view: "board", boardSlug: parts[1], threadId: null };
    }
    return { view: "board", boardSlug: state.boardSlug || "other", threadId: null };
  }

  function goBoard(slug) {
    location.hash = `#board/${slug}`;
  }

  function goThread(id) {
    location.hash = `#thread/${id}`;
  }

  function setHubLang(lang) {
    const next = I18n ? I18n.normalizeLang(lang) : lang === "ru" || lang === "es" ? lang : "en";
    state.lang = next;
    localStorage.setItem("wsdc-lang", next);
    const url = new URL(location.href);
    url.searchParams.set("lang", next);
    history.replaceState(null, "", url.pathname + url.search + url.hash);
    if (I18n) I18n.applyStatic(next);
    const chrome = document.querySelector("[data-site-chrome]");
    if (chrome) chrome.setAttribute("data-lang", next);
    renderBoards();
    if (state.thread) renderThread();
    else renderThreads();
    if (state.mod) loadStats();
  }

  function applyLang() {
    state.lang = langFromQuery();
    localStorage.setItem("wsdc-lang", state.lang);
    if (I18n) I18n.applyStatic(state.lang);
    const chrome = document.querySelector("[data-site-chrome]");
    if (chrome) {
      chrome.setAttribute("data-lang", state.lang);
      if (window.WsdcChrome && typeof window.WsdcChrome.applyLangLabels === "function") {
        window.WsdcChrome.applyLangLabels(state.lang);
      }
    }
  }

  function applyPrefillFromQuery() {
    try {
      const params = new URLSearchParams(location.search);
      const pageUrl = params.get("page_url");
      const titleHint = params.get("title");
      if (!els.newThreadForm) return;
      if (pageUrl) {
        const safe = safeHttpsUrl(pageUrl) || pageUrl;
        const input = els.newThreadForm.querySelector('[name="page_url"]');
        if (input) {
          input.value = safe;
          if (els.optionalDetails) els.optionalDetails.open = true;
        }
      }
      if (titleHint) {
        const titleInput = els.newThreadForm.querySelector('[name="title"]');
        if (titleInput && !titleInput.value) {
          titleInput.value = String(titleHint).slice(0, 160);
        }
      }
    } catch {
      /* ignore */
    }
  }

  async function sb(path, options = {}) {
    if (!SUPABASE_URL || !ANON) throw new Error(t("notConfigured"));
    const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
      ...options,
      headers: {
        apikey: ANON,
        Authorization: `Bearer ${ANON}`,
        "Content-Type": "application/json",
        Prefer: options.prefer || "return=representation",
        ...(options.headers || {}),
      },
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }
    if (!res.ok) {
      const msg =
        (data && data.message) ||
        (data && data.error_description) ||
        (typeof data === "string" ? data : "Request failed");
      throw new Error(msg);
    }
    return data;
  }

  async function modApi(payload) {
    if (!API_BASE) throw new Error("Moderation API is not configured (apiBase)");
    const secret = localStorage.getItem(MOD_KEY) || "";
    const res = await fetch(`${API_BASE}/api/qa-mod`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-qa-admin-secret": secret,
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data.message || data.error || "Moderation failed";
      throw new Error(detail);
    }
    return data;
  }

  async function notify(payload) {
    if (!API_BASE) return;
    try {
      await fetch(`${API_BASE}/api/qa-notify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch {
      /* soft-fail */
    }
  }

  function checkCooldown() {
    const last = Number(localStorage.getItem(COOLDOWN_KEY) || 0);
    const wait = COOLDOWN_MS - (Date.now() - last);
    if (wait > 0) throw new Error(`Please wait ${Math.ceil(wait / 1000)}s before posting again`);
  }

  function markPosted() {
    localStorage.setItem(COOLDOWN_KEY, String(Date.now()));
  }

  function honeypotFilled(form) {
    const hp = form.querySelector('[name="website"]');
    return hp && String(hp.value || "").trim() !== "";
  }

  async function loadBoards() {
    const rows = await sb("qa_boards?select=id,slug,title,sort_order&order=sort_order.asc");
    state.boards = rows || [];
    renderBoards();
  }

  function renderComposeBoardSelect() {
    if (!els.composeBoard) return;
    els.composeBoard.innerHTML = state.boards
      .map((b) => {
        const label = localizedBoardTitle(b.slug, b.title);
        const sel = b.slug === state.boardSlug ? " selected" : "";
        return `<option value="${esc(b.slug)}"${sel}>${esc(label)}</option>`;
      })
      .join("");
  }

  function renderBoards() {
    if (!state.boardSlug && state.boards[0]) state.boardSlug = state.boards[0].slug;
    renderComposeBoardSelect();
  }

  async function loadThreads() {
    setListStatus(t("loading"));
    const board = state.boards.find((b) => b.slug === state.boardSlug);
    if (!board) {
      els.threadList.innerHTML = `<p class="qa-empty">${esc(t("unknownBoard"))}</p>`;
      setListStatus("");
      return;
    }

    if (state.mod && API_BASE) {
      try {
        const data = await modApi({ action: "list_threads", board_slug: state.boardSlug });
        state.threads = data.threads || [];
      } catch (e) {
        state.threads = await sb(
          `qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,created_at&board_id=eq.${board.id}&order=is_pinned.desc,created_at.desc&limit=80`
        );
      }
    } else {
      state.threads = await sb(
        `qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,created_at&board_id=eq.${board.id}&order=is_pinned.desc,created_at.desc&limit=80`
      );
    }
    renderThreads();
    setListStatus("");
  }

  function renderThreads() {
    if (!els.threadList) return;
    if (!state.threads.length) {
      els.threadList.innerHTML = `<p class="qa-empty">${esc(t("empty"))}</p>`;
      return;
    }
    els.threadList.innerHTML = `<ul class="qa-thread-list">${state.threads
      .map((row) => {
        const active = row.id === state.threadId ? " is-active" : "";
        const badges = [
          row.is_pinned ? `<span class="wsdc-pill is-accent">${esc(t("pin"))}</span>` : "",
          row.is_hidden ? `<span class="wsdc-pill qa-pill-hidden">${esc(t("hidden"))}</span>` : "",
        ]
          .filter(Boolean)
          .join(" ");
        return `<li>
          <button type="button" class="qa-thread-item${active}" data-thread="${esc(row.id)}">
            <div class="qa-thread-title"><span>${esc(row.title)}</span>${badges}</div>
            <div class="qa-thread-meta"><span class="qa-thread-author">${esc(row.author_name)}</span><span class="qa-time">${esc(fmtDate(row.created_at))}</span></div>
          </button>
        </li>`;
      })
      .join("")}</ul>`;
  }

  async function loadThread(id) {
    setStatus(t("loadingThread"));
    const rows = state.mod && API_BASE
      ? null
      : await sb(
          `qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,created_at,qa_boards(slug,title)&id=eq.${encodeURIComponent(
            id
          )}&limit=1`
        );

    let thread = rows && rows[0];
    if (!thread && state.mod && API_BASE) {
      const data = await modApi({ action: "list_threads" });
      thread = (data.threads || []).find((row) => row.id === id);
    }
    if (!thread) {
      const pub = await sb(
        `qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,created_at,qa_boards(slug,title)&id=eq.${encodeURIComponent(
          id
        )}&limit=1`
      );
      thread = pub && pub[0];
    }
    if (!thread) throw new Error(t("threadNotFound"));

    state.thread = thread;
    state.threadId = thread.id;
    if (thread.qa_boards && thread.qa_boards.slug) {
      state.boardSlug = thread.qa_boards.slug;
    }

    const posts = await sb(
      `qa_posts?select=id,thread_id,author_name,body,is_hidden,is_op,created_at&thread_id=eq.${encodeURIComponent(
        id
      )}&order=created_at.asc`
    );
    state.posts = posts || [];
    renderThread();
    renderBoards();
    renderThreads();
    setStatus("");
  }

  function renderThread() {
    const thr = state.thread;
    if (!thr || !els.threadPanel) return;
    els.threadPanel.hidden = false;
    els.threadTitle.textContent = thr.title;
    const slug =
      (thr.qa_boards && thr.qa_boards.slug) ||
      (state.boards.find((b) => b.id === thr.board_id) || {}).slug ||
      state.boardSlug;
    const boardTitle = localizedBoardTitle(
      slug,
      (thr.qa_boards && thr.qa_boards.title) || state.boardSlug
    );
    els.threadMeta.innerHTML = `${esc(boardTitle)} · ${esc(t("by"))} <strong>${esc(thr.author_name)}</strong> · <span class="qa-time">${esc(
      fmtDate(thr.created_at)
    )}</span>${(() => {
      const href = safeHttpsUrl(thr.page_url);
      return href
        ? ` · <a href="${esc(href)}" rel="noopener noreferrer" target="_blank">${esc(t("source"))}</a>`
        : "";
    })()}${
      thr.is_pinned ? ` · <span class="wsdc-pill is-accent">${esc(t("pin"))}</span>` : ""
    }${thr.is_hidden ? ` · <span class="wsdc-pill qa-pill-hidden">${esc(t("hidden"))}</span>` : ""}`;

    const opHtml = `<article class="qa-post qa-post--op">
      <div class="qa-post-head"><span class="qa-post-author">${esc(thr.author_name)}</span>
      <span class="qa-time">${esc(fmtDate(thr.created_at))}</span><span class="wsdc-pill">OP</span></div>
      <div class="qa-post-body">${esc(thr.body)}</div>
    </article>`;

    const replies = (state.posts || [])
      .filter((p) => !p.is_op)
      .map(
        (p) => `<article class="qa-post qa-post--reply" data-post-id="${esc(p.id)}">
      <div class="qa-post-head"><span class="qa-post-author">${esc(p.author_name)}</span>
      <span class="qa-time">${esc(fmtDate(p.created_at))}</span>
      ${p.is_hidden ? `<span class="wsdc-pill qa-pill-hidden">${esc(t("hidden"))}</span>` : ""}
      ${
        state.mod
          ? `<button type="button" class="wsdc-btn wsdc-btn--ghost" data-mod-post="${esc(p.id)}" data-mod-action="${
              p.is_hidden ? "unhide" : "hide"
            }">${esc(p.is_hidden ? t("unhidePost") : t("hidePost"))}</button>`
          : ""
      }
      </div>
      <div class="qa-post-body">${esc(p.body)}</div>
    </article>`
      )
      .join("");

    els.posts.innerHTML = opHtml + replies;
    els.replyForm.hidden = false;
    renderModActions();
  }

  function renderModBar() {
    if (!els.modBar) return;
    const unlocked = state.mod;
    els.modUnlock.hidden = unlocked;
    els.modLock.hidden = !unlocked;
    els.modActions.hidden = !unlocked || !state.threadId;
    if (els.aside) {
      els.aside.hidden = !unlocked;
      if (!unlocked) els.aside.open = false;
    }
    if (!unlocked) els.modBar.open = false;
  }

  function renderModActions() {
    if (!els.modActions || !state.thread) {
      if (els.modActions) els.modActions.hidden = true;
      return;
    }
    if (!state.mod) {
      els.modActions.hidden = true;
      return;
    }
    els.modActions.hidden = false;
    const thr = state.thread;
    const currentSlug =
      (thr.qa_boards && thr.qa_boards.slug) ||
      (state.boards.find((b) => b.id === thr.board_id) || {}).slug ||
      state.boardSlug;
    const options = state.boards
      .map((b) => {
        const label = localizedBoardTitle(b.slug, b.title);
        const sel = b.slug === currentSlug ? " selected" : "";
        return `<option value="${esc(b.slug)}"${sel}>${esc(label)}</option>`;
      })
      .join("");
    els.modActions.innerHTML = `
      <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="hide">${esc(
        thr.is_hidden ? t("unhideThread") : t("hideThread")
      )}</button>
      <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="pin">${esc(
        thr.is_pinned ? t("unpin") : t("pin")
      )}</button>
      <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="delete">${esc(
        t("deleteThread")
      )}</button>
      <div class="qa-mod-move">
        <label class="qa-mod-label" for="qaModMoveBoard">${esc(t("moveBoard"))}</label>
        <select class="wsdc-field" id="qaModMoveBoard">${options}</select>
        <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="move">${esc(
          t("move")
        )}</button>
      </div>
    `;
  }

  async function loadStats() {
    if (!els.stats || !state.mod || !API_BASE) return;
    try {
      const data = await modApi({ action: "stats" });
      const lines = (data.boards || [])
        .map((b) => {
          const title = localizedBoardTitle(b.slug, b.title);
          return (
            `<li><strong>${esc(title)}</strong>: ${b.visible_threads} ${esc(t("visible"))}` +
            (b.hidden_threads ? `, ${b.hidden_threads} ${esc(t("hidden"))}` : "") +
            `</li>`
          );
        })
        .join("");
      els.stats.innerHTML = `<strong>${esc(t("boardCounts"))}</strong><ul>${lines}</ul>
        <p>${esc(t("posts"))}: ${data.posts_total || 0}${
        data.posts_hidden ? ` (${data.posts_hidden} ${esc(t("hidden"))})` : ""
      }</p>`;
    } catch (e) {
      els.stats.textContent = e.message || t("statsUnavailable");
    }
  }

  async function createThread(form) {
    if (honeypotFilled(form)) return;
    checkCooldown();
    const formSlug =
      (form.board_slug && form.board_slug.value) || state.boardSlug;
    const board = state.boards.find((b) => b.slug === formSlug);
    if (!board) throw new Error(t("selectBoard"));

    const title = String(form.title.value || "").trim();
    const author_name = String(form.author_name.value || "").trim();
    const author_email = String(form.author_email.value || "").trim() || null;
    const page_url_raw = String(form.page_url.value || "").trim();
    const page_url = page_url_raw ? safeHttpsUrl(page_url_raw) : null;
    if (page_url_raw && !page_url) throw new Error(t("pageUrlHttps"));
    const body = String(form.body.value || "").trim();

    const rows = await sb(
      "qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,created_at",
      {
        method: "POST",
        body: JSON.stringify({
          board_id: board.id,
          title,
          author_name,
          author_email,
          page_url,
          body,
        }),
      }
    );
    const thread = Array.isArray(rows) ? rows[0] : rows;
    if (!thread || !thread.id) throw new Error(t("createFailed"));

    await sb("qa_posts?select=id,thread_id,author_name,body,is_hidden,is_op,created_at", {
      method: "POST",
      body: JSON.stringify({
        thread_id: thread.id,
        author_name,
        author_email,
        body,
        is_op: true,
      }),
    });

    markPosted();
    await notify({
      kind: "thread",
      board: board.slug,
      title,
      author_name,
      thread_id: thread.id,
      preview: body,
    });
    state.boardSlug = board.slug;
    form.reset();
    renderComposeBoardSelect();
    goThread(thread.id);
    setStatus(t("threadPublished"), "ok");
  }

  async function createReply(form) {
    if (honeypotFilled(form)) return;
    checkCooldown();
    if (!state.threadId) throw new Error(t("noThread"));
    const author_name = String(form.author_name.value || "").trim();
    const author_email = String(form.author_email.value || "").trim() || null;
    const body = String(form.body.value || "").trim();

    await sb("qa_posts?select=id,thread_id,author_name,body,is_hidden,is_op,created_at", {
      method: "POST",
      body: JSON.stringify({
        thread_id: state.threadId,
        author_name,
        author_email,
        body,
        is_op: false,
      }),
    });

    markPosted();
    await notify({
      kind: "reply",
      board: state.boardSlug,
      title: state.thread && state.thread.title,
      author_name,
      thread_id: state.threadId,
      preview: body,
    });
    form.reset();
    await loadThread(state.threadId);
    setStatus(t("replyPublished"), "ok");
  }

  async function onRoute() {
    const route = parseHash();
    state.boardSlug = route.boardSlug || state.boardSlug || "other";
    renderBoards();
    renderModBar();

    if (route.view === "thread") {
      await loadThreads();
      await loadThread(route.threadId);
    } else {
      state.threadId = null;
      state.thread = null;
      state.posts = [];
      if (els.threadPanel) els.threadPanel.hidden = true;
      if (els.replyForm) els.replyForm.hidden = true;
      await loadThreads();
      setStatus("");
    }
    if (state.mod) await loadStats();
  }

  function wire() {
    if (els.composeBoard) {
      els.composeBoard.addEventListener("change", () => {
        const slug = els.composeBoard.value;
        if (slug && slug !== state.boardSlug) goBoard(slug);
      });
    }

    els.threadList.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-thread]");
      if (!btn) return;
      goThread(btn.getAttribute("data-thread"));
    });

    els.newThreadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        setStatus(t("publishing"));
        await createThread(e.target);
      } catch (err) {
        setStatus(err.message || "Failed", "error");
      }
    });

    els.replyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        setStatus(t("publishing"));
        await createReply(e.target);
      } catch (err) {
        setStatus(err.message || "Failed", "error");
      }
    });

    document.getElementById("qaModUnlockBtn").addEventListener("click", async () => {
      const secret = String(els.modSecret.value || "").trim();
      if (!secret) return;
      localStorage.setItem(MOD_KEY, secret);
      state.mod = true;
      els.modSecret.value = "";
      renderModBar();
      try {
        await modApi({ action: "stats" });
        setStatus(t("modOn"), "ok");
        await onRoute();
      } catch (err) {
        localStorage.removeItem(MOD_KEY);
        state.mod = false;
        renderModBar();
        setStatus(err.message || "Invalid secret / API", "error");
      }
    });

    els.modLock.addEventListener("click", () => {
      localStorage.removeItem(MOD_KEY);
      state.mod = false;
      renderModBar();
      setStatus(t("modOff"));
      onRoute();
    });

    els.modActions.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-mod-thread]");
      if (!btn || !state.thread) return;
      const act = btn.getAttribute("data-mod-thread");
      try {
        if (act === "hide") {
          await modApi({
            action: state.thread.is_hidden ? "unhide" : "hide",
            type: "thread",
            id: state.thread.id,
          });
        } else if (act === "pin") {
          await modApi({
            action: state.thread.is_pinned ? "unpin" : "pin",
            type: "thread",
            id: state.thread.id,
          });
        } else if (act === "move") {
          const select = els.modActions.querySelector("#qaModMoveBoard");
          const boardSlug = select && select.value;
          if (!boardSlug) return;
          await modApi({
            action: "move",
            type: "thread",
            id: state.thread.id,
            board_slug: boardSlug,
          });
          state.boardSlug = boardSlug;
        } else if (act === "delete") {
          const title = state.thread.title || "this thread";
          if (
            !window.confirm(
              `${t("deleteConfirm")}\n\n“${title}”\n\n${t("deleteConfirmReplies")}`
            )
          ) {
            return;
          }
          const boardSlug = state.boardSlug;
          await modApi({
            action: "delete",
            type: "thread",
            id: state.thread.id,
          });
          state.threadId = null;
          state.thread = null;
          location.hash = `#board/${boardSlug}`;
          setStatus(t("threadDeleted"), "ok");
          return;
        }
        await onRoute();
        setStatus(t("updated"), "ok");
      } catch (err) {
        setStatus(err.message || "Moderation failed", "error");
      }
    });

    els.posts.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-mod-post]");
      if (!btn) return;
      try {
        await modApi({
          action: btn.getAttribute("data-mod-action"),
          type: "post",
          id: btn.getAttribute("data-mod-post"),
        });
        await loadThread(state.threadId);
        setStatus(t("updated"), "ok");
      } catch (err) {
        setStatus(err.message || "Moderation failed", "error");
      }
    });

    window.addEventListener("hashchange", () => {
      onRoute().catch((err) => setStatus(err.message || "Error", "error"));
    });

    function onChromeLang(lang) {
      if (!lang) return;
      setHubLang(lang);
    }

    window.WsdcChrome = window.WsdcChrome || {};
    const prevLang = window.WsdcChrome.onLangChange;
    window.WsdcChrome.onLangChange = function (lang) {
      if (typeof prevLang === "function") prevLang(lang);
      onChromeLang(lang);
    };

    document.addEventListener("wsdc:langchange", (e) => {
      const lang = e && e.detail && e.detail.lang;
      if (lang) onChromeLang(lang);
    });
  }

  async function init() {
    applyLang();
    applyPrefillFromQuery();
    if (!SUPABASE_URL || !ANON) {
      setStatus(t("notConfigured"), "error");
      return;
    }
    wire();
    renderModBar();
    await loadBoards();
    if (!location.hash) location.hash = `#board/${state.boardSlug}`;
    else await onRoute();
  }

  init().catch((err) => setStatus(err.message || "Failed to start", "error"));
})();
