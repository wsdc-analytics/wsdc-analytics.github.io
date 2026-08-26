(function () {
  "use strict";

  const cfg = window.QA_CONFIG || {};
  const SUPABASE_URL = (cfg.supabaseUrl || "").replace(/\/$/, "");
  const ANON = cfg.supabaseAnonKey || "";
  const API_BASE = (cfg.apiBase || "").replace(/\/$/, "");
  const MOD_KEY = "qa_admin_secret_v1";
  const COOLDOWN_KEY = "qa_last_post_ts";
  const COOLDOWN_MS = 20000;

  const els = {
    boards: document.getElementById("qaBoards"),
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
    boards: [],
    boardSlug: "articles",
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

  function fmtDate(iso) {
    try {
      return new Date(iso).toLocaleString("en-GB", {
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
    return { view: "board", boardSlug: state.boardSlug || "articles", threadId: null };
  }

  function goBoard(slug) {
    location.hash = `#board/${slug}`;
  }

  function goThread(id) {
    location.hash = `#thread/${id}`;
  }

  async function sb(path, options = {}) {
    if (!SUPABASE_URL || !ANON) throw new Error("Q&A backend is not configured");
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

  function renderBoards() {
    if (!els.boards) return;
    els.boards.innerHTML = state.boards
      .map((b) => {
        const active = b.slug === state.boardSlug ? " is-active" : "";
        return `<button type="button" class="wsdc-btn wsdc-btn--secondary qa-board-btn${active}" data-board="${esc(
          b.slug
        )}">${esc(b.title)}</button>`;
      })
      .join("");
  }

  async function loadThreads() {
    setListStatus("Loading…");
    const board = state.boards.find((b) => b.slug === state.boardSlug);
    if (!board) {
      els.threadList.innerHTML = `<p class="qa-empty">Unknown board.</p>`;
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
      els.threadList.innerHTML = `<p class="qa-empty">No threads yet. Start one on the right.</p>`;
      return;
    }
    els.threadList.innerHTML = `<ul class="qa-thread-list">${state.threads
      .map((t) => {
        const active = t.id === state.threadId ? " is-active" : "";
        const badges = [
          t.is_pinned ? `<span class="qa-badge is-pin">Pinned</span>` : "",
          t.is_hidden ? `<span class="qa-badge is-hidden">Hidden</span>` : "",
        ]
          .filter(Boolean)
          .join(" ");
        return `<li>
          <button type="button" class="qa-thread-item${active}" data-thread="${esc(t.id)}">
            <div class="qa-thread-title"><span>${esc(t.title)}</span>${badges}</div>
            <div class="qa-thread-meta">${esc(t.author_name)} · ${esc(fmtDate(t.created_at))}</div>
          </button>
        </li>`;
      })
      .join("")}</ul>`;
  }

  async function loadThread(id) {
    setStatus("Loading thread…");
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
      thread = (data.threads || []).find((t) => t.id === id);
    }
    if (!thread) {
      // fallback public fetch if mod list missed it
      const pub = await sb(
        `qa_threads?select=id,board_id,title,author_name,page_url,body,is_hidden,is_pinned,created_at,qa_boards(slug,title)&id=eq.${encodeURIComponent(
          id
        )}&limit=1`
      );
      thread = pub && pub[0];
    }
    if (!thread) throw new Error("Thread not found");

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
    const t = state.thread;
    if (!t || !els.threadPanel) return;
    els.threadPanel.hidden = false;
    els.threadTitle.textContent = t.title;
    const boardTitle =
      (t.qa_boards && t.qa_boards.title) ||
      (state.boards.find((b) => b.id === t.board_id) || {}).title ||
      state.boardSlug;
    els.threadMeta.innerHTML = `${esc(boardTitle)} · by <strong>${esc(t.author_name)}</strong> · ${esc(
      fmtDate(t.created_at)
    )}${t.page_url ? ` · <a href="${esc(t.page_url)}">source</a>` : ""}${
      t.is_pinned ? ' · <span class="qa-badge is-pin">Pinned</span>' : ""
    }${t.is_hidden ? ' · <span class="qa-badge is-hidden">Hidden</span>' : ""}`;

    const opHtml = `<article class="qa-post">
      <div class="qa-post-head"><span class="qa-post-author">${esc(t.author_name)}</span>
      <span>${esc(fmtDate(t.created_at))}</span><span class="qa-badge">OP</span></div>
      <div class="qa-post-body">${esc(t.body)}</div>
    </article>`;

    const replies = (state.posts || [])
      .filter((p) => !p.is_op)
      .map(
        (p) => `<article class="qa-post" data-post-id="${esc(p.id)}">
      <div class="qa-post-head"><span class="qa-post-author">${esc(p.author_name)}</span>
      <span>${esc(fmtDate(p.created_at))}</span>
      ${p.is_hidden ? '<span class="qa-badge is-hidden">Hidden</span>' : ""}
      ${
        state.mod
          ? `<button type="button" class="wsdc-btn wsdc-btn--ghost" data-mod-post="${esc(p.id)}" data-mod-action="${
              p.is_hidden ? "unhide" : "hide"
            }">${p.is_hidden ? "Unhide" : "Hide"}</button>`
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
    if (els.aside) els.aside.hidden = !unlocked;
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
    const t = state.thread;
    els.modActions.innerHTML = `
      <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="hide">${
        t.is_hidden ? "Unhide thread" : "Hide thread"
      }</button>
      <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="pin">${
        t.is_pinned ? "Unpin" : "Pin"
      }</button>
      <button type="button" class="wsdc-btn wsdc-btn--secondary" data-mod-thread="delete">Delete thread</button>
    `;
  }

  async function loadStats() {
    if (!els.stats || !state.mod || !API_BASE) return;
    try {
      const data = await modApi({ action: "stats" });
      const lines = (data.boards || [])
        .map(
          (b) =>
            `<li><strong>${esc(b.title)}</strong>: ${b.visible_threads} visible` +
            (b.hidden_threads ? `, ${b.hidden_threads} hidden` : "") +
            `</li>`
        )
        .join("");
      els.stats.innerHTML = `<div class="qa-stats"><strong>Board counts</strong><ul>${lines}</ul>
        <p>Posts: ${data.posts_total || 0}${
        data.posts_hidden ? ` (${data.posts_hidden} hidden)` : ""
      }</p></div>`;
    } catch (e) {
      els.stats.textContent = e.message || "Stats unavailable";
    }
  }

  async function createThread(form) {
    if (honeypotFilled(form)) return;
    checkCooldown();
    const board = state.boards.find((b) => b.slug === state.boardSlug);
    if (!board) throw new Error("Select a board");

    const title = String(form.title.value || "").trim();
    const author_name = String(form.author_name.value || "").trim();
    const author_email = String(form.author_email.value || "").trim() || null;
    const page_url = String(form.page_url.value || "").trim() || null;
    const body = String(form.body.value || "").trim();

    const rows = await sb("qa_threads", {
      method: "POST",
      body: JSON.stringify({
        board_id: board.id,
        title,
        author_name,
        author_email,
        page_url,
        body,
      }),
    });
    const thread = Array.isArray(rows) ? rows[0] : rows;
    if (!thread || !thread.id) throw new Error("Failed to create thread");

    await sb("qa_posts", {
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
    form.reset();
    goThread(thread.id);
    setStatus("Thread published.", "ok");
  }

  async function createReply(form) {
    if (honeypotFilled(form)) return;
    checkCooldown();
    if (!state.threadId) throw new Error("No thread selected");
    const author_name = String(form.author_name.value || "").trim();
    const author_email = String(form.author_email.value || "").trim() || null;
    const body = String(form.body.value || "").trim();

    await sb("qa_posts", {
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
    setStatus("Reply published.", "ok");
  }

  async function onRoute() {
    const route = parseHash();
    state.boardSlug = route.boardSlug || state.boardSlug || "articles";
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
    els.boards.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-board]");
      if (!btn) return;
      goBoard(btn.getAttribute("data-board"));
    });

    els.threadList.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-thread]");
      if (!btn) return;
      goThread(btn.getAttribute("data-thread"));
    });

    els.newThreadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        setStatus("Publishing…");
        await createThread(e.target);
      } catch (err) {
        setStatus(err.message || "Failed", "error");
      }
    });

    els.replyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        setStatus("Publishing…");
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
        setStatus("Moderator mode on.", "ok");
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
      setStatus("Moderator mode off.");
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
        } else if (act === "delete") {
          const title = state.thread.title || "this thread";
          if (!window.confirm(`Delete thread permanently?\n\n“${title}”\n\nReplies will be removed too.`)) {
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
          setStatus("Thread deleted.", "ok");
          return;
        }
        await onRoute();
        setStatus("Updated.", "ok");
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
        setStatus("Updated.", "ok");
      } catch (err) {
        setStatus(err.message || "Moderation failed", "error");
      }
    });

    window.addEventListener("hashchange", () => {
      onRoute().catch((err) => setStatus(err.message || "Error", "error"));
    });
  }

  async function init() {
    if (!SUPABASE_URL || !ANON) {
      setStatus("Q&A backend is not configured.", "error");
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
