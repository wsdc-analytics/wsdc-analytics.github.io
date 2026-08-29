/**
 * Mount Evolved C site chrome into [data-site-chrome] placeholders.
 *
 * Attributes:
 *   data-active          home | dashboards | points | champions | calendar | articles | qa
 *   data-qa-board        optional board slug override for the Q&A chrome link
 *   data-lang            ru | en | es
 *   data-fixed           "true" for position:fixed (homepage + magazine articles)
 *   data-brand           "logo" (default) | "text"
 *   data-home-href       brand logo link (default index.html) — return home
 *   data-path-prefix     prefix for dashboard / points / champions / calendar / qa hrefs (e.g. "../../" from nested pages)
 *   data-lang-mode       callback | navigate (default callback)
 *   data-lang-ru/en/es   URLs when data-lang-mode=navigate
 *   data-current-dash    filename to mark current dashboard link
 */
(function () {
  "use strict";

  var DASHBOARDS = [
    { href: "dashboard.html", label: "Metrics" },
    { href: "navigator.html", label: "Events Navigator" },
    { href: "rankings.html", label: "Dancer's Ranking" },
    { href: "dancer-profile.html", label: "Dancer Profile" },
    { href: "secondary_role_distribution_dashboard_en.html", label: "Secondary Role Points" },
    { href: "city-clouds.html", label: "Cities Cloud" },
  ];

  function withPathPrefix(root, href) {
    var prefix = root.getAttribute("data-path-prefix") || "";
    if (!prefix || !href) return href;
    if (/^(https?:|mailto:|\/)/i.test(href)) return href;
    return prefix + href;
  }

  var LABELS = {
    dashboards: { ru: "Дашборды", en: "Dashboards", es: "Paneles" },
    points: { ru: "Summary Points", en: "Summary Points", es: "Summary Points" },
    champions: { ru: "New Champions", en: "New Champions", es: "New Champions" },
    calendar: { ru: "Events Calendar", en: "Events Calendar", es: "Events Calendar" },
    contact: { ru: "Контакты", en: "Contacts", es: "Contacto" },
    qa: { ru: "Q&A Hub", en: "Q&A Hub", es: "Q&A Hub" },
    email: { ru: "Написать на email", en: "Send email", es: "Enviar email" },
    facebook: { ru: "Написать в Facebook", en: "Message on Facebook", es: "Escribir en Facebook" },
    home: { ru: "На главную", en: "Back to home", es: "Volver al inicio" },
    dashTip: {
      ru: "Информационные дашборды WSDC",
      en: "WSDC informational dashboards",
      es: "Paneles informativos WSDC",
    },
    pointsTip: {
      ru: "Очки, начисленные по ивентам",
      en: "Points awarded by event",
      es: "Puntos otorgados por evento",
    },
    championsTip: {
      ru: "Хронология переходов Allowed и Required Champions",
      en: "Chronology of Allowed and Required Champions transitions",
      es: "Cronología de transiciones Allowed y Required Champions",
    },
    calendarTip: {
      ru: "Календарь ожидаемых, подтверждённых и hiatus ивентов WSDC",
      en: "Year calendar of expected, confirmed, and hiatus WSDC events",
      es: "Calendario anual de eventos WSDC esperados, confirmados y en hiatus",
    },
  };

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function currentPageName() {
    var path = window.location.pathname || "";
    var parts = path.split("/");
    return parts[parts.length - 1] || "index.html";
  }

  function withLangQuery(href, lang) {
    var base = String(href || "index.html").split("#")[0].split("?")[0];
    if (!base) base = "index.html";
    return base + "?lang=" + lang;
  }

  /** Map chrome context → qa_boards.slug */
  var ACTIVE_TO_QA_BOARD = {
    champions: "new-champions",
    points: "summary-points",
    calendar: "calendar",
    dashboards: "dashboards",
    articles: "articles",
    qa: "other",
    home: "other",
  };

  function resolveQaBoardSlug(root) {
    var override = (root.getAttribute("data-qa-board") || "").trim();
    if (override) return override;
    var active = root.getAttribute("data-active") || "home";
    return ACTIVE_TO_QA_BOARD[active] || "other";
  }

  function qaHubHref(root, lang) {
    var slug = resolveQaBoardSlug(root);
    return withPathPrefix(root, "qa.html") + "?lang=" + lang + "#board/" + encodeURIComponent(slug);
  }

  function syncBackLinks(lang, homeHref) {
    var label = LABELS.home[lang] || LABELS.home.en;
    var href = withLangQuery(homeHref || "index.html", lang);
    document.querySelectorAll("[data-wsdc-back]").forEach(function (el) {
      // Strip any leading arrow; CSS ::before draws it
      el.textContent = label;
      el.setAttribute("href", href);
      if (!el.getAttribute("aria-label")) {
        el.setAttribute("aria-label", label);
      }
    });
  }

  function tipHtml(tipText, tipAttr) {
    return (
      '<button type="button" class="wsdc-chrome__tip" aria-expanded="false" aria-label="' +
      esc(tipText) +
      '">' +
      '<span class="wsdc-chrome__tip-mark" aria-hidden="true">i</span>' +
      '<span class="wsdc-chrome__tip-bubble" role="tooltip" ' +
      tipAttr +
      ">" +
      esc(tipText) +
      "</span>" +
      "</button>"
    );
  }

  function getTipBubble(tip) {
    if (!tip) return null;
    if (tip._chromeBubble && tip._chromeBubble.isConnected) return tip._chromeBubble;
    var bubble = tip.querySelector(".wsdc-chrome__tip-bubble");
    if (bubble) tip._chromeBubble = bubble;
    return bubble || null;
  }

  function clearTipBubblePosition(tip) {
    var bubble = getTipBubble(tip);
    if (!bubble) return;
    bubble.classList.remove("is-ported");
    bubble.style.left = "";
    bubble.style.top = "";
    bubble.style.width = "";
    bubble.style.maxWidth = "";
    bubble.style.transform = "";
    bubble.style.zIndex = "";
    if (tip._chromeBubbleHome && bubble.parentNode !== tip._chromeBubbleHome) {
      tip._chromeBubbleHome.appendChild(bubble);
    }
  }

  function placeTipBubble(tip) {
    var bubble = getTipBubble(tip);
    if (!bubble) return;
    // Narrow / touch: port to body so position:fixed is viewport-relative.
    // (A position:fixed chrome wrap is otherwise the containing block and clips tips.)
    var mobile = window.matchMedia("(max-width: 720px), (hover: none)").matches;
    if (!mobile) {
      clearTipBubblePosition(tip);
      return;
    }
    if (!tip._chromeBubbleHome) tip._chromeBubbleHome = bubble.parentNode || tip;
    if (bubble.parentNode !== document.body) {
      document.body.appendChild(bubble);
    }
    bubble.classList.add("is-ported");

    var pad = 12;
    var gap = 8;
    var maxW = Math.min(280, window.innerWidth - pad * 2);
    bubble.style.maxWidth = maxW + "px";
    bubble.style.width = maxW + "px";
    bubble.style.transform = "none";
    bubble.style.zIndex = "200";

    var tipRect = tip.getBoundingClientRect();
    var bW = bubble.offsetWidth || maxW;
    var bH = bubble.offsetHeight || 48;
    var left = tipRect.left + tipRect.width / 2 - bW / 2;
    left = Math.max(pad, Math.min(left, window.innerWidth - pad - bW));

    var topBelow = tipRect.bottom + gap;
    var topAbove = tipRect.top - gap - bH;
    var top;
    if (topBelow + bH <= window.innerHeight - pad) {
      top = topBelow;
    } else if (topAbove >= pad) {
      top = topAbove;
    } else {
      top = Math.max(pad, Math.min(topBelow, window.innerHeight - pad - bH));
    }

    bubble.style.left = Math.round(left) + "px";
    bubble.style.top = Math.round(top) + "px";
  }

  function releaseAllTipBubbles(root) {
    root.querySelectorAll(".wsdc-chrome__tip").forEach(clearTipBubblePosition);
  }

  function render(root) {
    var active = root.getAttribute("data-active") || "home";
    var lang = root.getAttribute("data-lang") || "en";
    var stored = localStorage.getItem("wsdc-lang");
    if (stored && ["ru", "en", "es"].indexOf(stored) !== -1) {
      lang = stored;
    }
    var fixed = root.getAttribute("data-fixed") === "true";
    var brandMode = root.getAttribute("data-brand") || "logo";
    var homeHref = root.getAttribute("data-home-href") || "index.html";
    var currentDash = root.getAttribute("data-current-dash") || currentPageName();
    var onHome = active === "home" && (currentPageName() === "" || currentPageName() === "index.html");

    var wrapClass = "wsdc-chrome-wrap" + (fixed ? " is-fixed" : "");
    var dashActive = active === "dashboards" ? " is-active" : "";
    var pointsActive = active === "points" ? " is-active" : "";
    var championsActive = active === "champions" ? " is-active" : "";
    var calendarActive = active === "calendar" ? " is-active" : "";
    var homeLabel = LABELS.home[lang] || LABELS.home.en;
    var dashTip = LABELS.dashTip[lang] || LABELS.dashTip.en;
    var pointsTip = LABELS.pointsTip[lang] || LABELS.pointsTip.en;
    var championsTip = LABELS.championsTip[lang] || LABELS.championsTip.en;
    var calendarTip = LABELS.calendarTip[lang] || LABELS.calendarTip.en;

    var brandHtml;
    if (brandMode === "text") {
      brandHtml =
        '<a class="wsdc-chrome__brand" href="' +
        esc(homeHref) +
        '" data-chrome-home aria-label="' +
        esc(homeLabel) +
        '" title="' +
        esc(homeLabel) +
        '">WSDC</a>';
    } else {
      brandHtml =
        '<a class="wsdc-chrome__brand' +
        (onHome ? " is-current-home" : "") +
        '" href="' +
        esc(homeHref) +
        '" id="logoLink" data-chrome-home aria-label="' +
        esc(homeLabel) +
        '" title="' +
        esc(homeLabel) +
        '"><span class="wsdc-chrome__brand-logo"><img src="https://www.worldsdc.com/wp-content/uploads/2019/10/WSDC_WHITE.gif" alt="WSDC" height="22" loading="eager"></span></a>';
    }

    var dashItems = DASHBOARDS.map(function (d) {
      var cur = d.href === currentDash ? " is-current" : "";
      var href = withPathPrefix(root, d.href);
      return (
        '<li role="none"><a href="' +
        esc(href) +
        '" role="menuitem" data-dash-href="' +
        esc(d.href) +
        '" class="' +
        cur.trim() +
        '">' +
        esc(d.label) +
        "</a></li>"
      );
    }).join("");

    var langs = ["ru", "en", "es"]
      .map(function (code) {
        var pressed = code === lang;
        return (
          '<button type="button" class="wsdc-chrome__pill lang-btn' +
          (pressed ? " is-active" : "") +
          '" data-lang="' +
          code +
          '" aria-pressed="' +
          pressed +
          '" aria-label="' +
          (code === "ru" ? "Переключить на русский язык" : code === "es" ? "Cambiar a español" : "Switch to English") +
          '">' +
          code.toUpperCase() +
          "</button>"
        );
      })
      .join("");

    root.innerHTML =
      '<div class="' +
      wrapClass +
      '">' +
      '<nav class="wsdc-chrome" aria-label="Site">' +
      brandHtml +
      '<div class="wsdc-chrome__cluster" data-chrome-nav="dashboards">' +
      tipHtml(dashTip, 'data-chrome-dash-tip') +
      '<div class="wsdc-chrome__dd" data-chrome-dd>' +
      '<button type="button" class="wsdc-chrome__pill' +
      dashActive +
      '" data-chrome-dash-btn aria-expanded="false" aria-haspopup="true" aria-controls="wsdcChromeDashMenu">' +
      '<span data-chrome-dash-label>' +
      esc(LABELS.dashboards[lang] || LABELS.dashboards.en) +
      "</span>" +
      '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2.5 4.5L6 8L9.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
      "</button>" +
      '<ul class="wsdc-chrome__menu" id="wsdcChromeDashMenu" role="menu" data-chrome-dash-menu aria-hidden="true">' +
      dashItems +
      "</ul>" +
      "</div>" +
      "</div>" +
      '<div class="wsdc-chrome__cluster" data-chrome-nav="points">' +
      tipHtml(pointsTip, 'data-chrome-points-tip') +
      '<a class="wsdc-chrome__pill' +
      pointsActive +
      '" href="' +
      esc(withPathPrefix(root, "points-summary.html")) +
      '" id="pointsSummaryBtn">' +
      '<span data-chrome-points-label>' +
      esc(LABELS.points[lang] || LABELS.points.en) +
      "</span>" +
      "</a>" +
      "</div>" +
      '<div class="wsdc-chrome__cluster" data-chrome-nav="champions">' +
      tipHtml(championsTip, 'data-chrome-champions-tip') +
      '<a class="wsdc-chrome__pill' +
      championsActive +
      '" href="' +
      esc(withPathPrefix(root, "champion-news.html")) +
      '" id="championNewsBtn">' +
      '<span data-chrome-champions-label>' +
      esc(LABELS.champions[lang] || LABELS.champions.en) +
      "</span>" +
      "</a>" +
      "</div>" +
      '<div class="wsdc-chrome__cluster" data-chrome-nav="calendar">' +
      tipHtml(calendarTip, 'data-chrome-calendar-tip') +
      '<a class="wsdc-chrome__pill' +
      calendarActive +
      '" href="' +
      esc(withPathPrefix(root, "events-calendar.html")) +
      '" id="eventsCalendarBtn">' +
      '<span data-chrome-calendar-label>' +
      esc(LABELS.calendar[lang] || LABELS.calendar.en) +
      "</span>" +
      "</a>" +
      "</div>" +
      '<div class="wsdc-chrome__spacer" aria-hidden="true"></div>' +
      '<div class="wsdc-chrome__qa" data-chrome-qa>' +
      '<a class="wsdc-chrome__qa-btn' +
      (active === "qa" ? " is-active" : "") +
      '" href="' +
      esc(qaHubHref(root, lang)) +
      '" data-chrome-qa-btn aria-label="' +
      esc(LABELS.qa[lang] || LABELS.qa.en) +
      '" aria-describedby="wsdcChromeQaTip">' +
      '<span class="wsdc-chrome__qa-icon" aria-hidden="true" style="-webkit-mask-image:url(\'' +
      esc(withPathPrefix(root, "static/img/qa-chrome-icon.png")) +
      "');mask-image:url('" +
      esc(withPathPrefix(root, "static/img/qa-chrome-icon.png")) +
      "')" +
      "></span>" +
      "</a>" +
      '<span class="wsdc-chrome__qa-tip" id="wsdcChromeQaTip" role="tooltip" data-chrome-qa-tip>' +
      esc(LABELS.qa[lang] || LABELS.qa.en) +
      "</span>" +
      "</div>" +
      '<div class="wsdc-chrome__contact" data-chrome-contact>' +
      '<button type="button" class="wsdc-chrome__contact-btn" data-chrome-contact-btn aria-label="' +
      esc(LABELS.contact[lang] || LABELS.contact.en) +
      '" aria-expanded="false" aria-haspopup="menu" aria-controls="wsdcChromeContactMenu">' +
      '<svg width="20" height="13" viewBox="0 0 48 32" fill="none" aria-hidden="true"><rect x="2.5" y="2.5" width="43" height="27" rx="2.5" stroke="currentColor" stroke-width="1.75"/><path d="M3.5 7L24 20L44.5 7" stroke="currentColor" stroke-width="1.75"/></svg>' +
      "</button>" +
      '<ul class="wsdc-chrome__contact-menu" id="wsdcChromeContactMenu" role="menu" data-chrome-contact-menu aria-hidden="true">' +
      '<li role="none"><a href="mailto:analytics.wsdc@gmail.com" role="menuitem" data-chrome-email>' +
      esc(LABELS.email[lang] || LABELS.email.en) +
      "</a></li>" +
      '<li role="none"><a href="https://www.facebook.com/share/1EUJKjHCER/" target="_blank" rel="noopener noreferrer" role="menuitem" data-chrome-facebook>' +
      esc(LABELS.facebook[lang] || LABELS.facebook.en) +
      "</a></li>" +
      "</ul>" +
      "</div>" +
      '<div class="wsdc-chrome__langs" role="group" aria-label="Language">' +
      langs +
      "</div>" +
      "</nav>" +
      "</div>";

    bind(root, lang);
  }

  function closeAll(root) {
    var dd = root.querySelector("[data-chrome-dd]");
    var contact = root.querySelector("[data-chrome-contact]");
    var dashBtn = root.querySelector("[data-chrome-dash-btn]");
    var contactBtn = root.querySelector("[data-chrome-contact-btn]");
    var dashMenu = root.querySelector("[data-chrome-dash-menu]");
    var contactMenu = root.querySelector("[data-chrome-contact-menu]");
    if (dd) dd.classList.remove("is-open");
    if (contact) contact.classList.remove("is-open");
    if (dashBtn) dashBtn.setAttribute("aria-expanded", "false");
    if (contactBtn) contactBtn.setAttribute("aria-expanded", "false");
    if (dashMenu) dashMenu.setAttribute("aria-hidden", "true");
    if (contactMenu) contactMenu.setAttribute("aria-hidden", "true");
    root.querySelectorAll(".wsdc-chrome__tip.is-open").forEach(function (tip) {
      tip.classList.remove("is-open");
      tip.setAttribute("aria-expanded", "false");
    });
    releaseAllTipBubbles(root);
  }

  function applyLangLabels(root, lang) {
    root.setAttribute("data-lang", lang);
    var homeLabel = LABELS.home[lang] || LABELS.home.en;
    var homeHref = withLangQuery(root.getAttribute("data-home-href") || "index.html", lang);
    var dashTip = LABELS.dashTip[lang] || LABELS.dashTip.en;
    var pointsTip = LABELS.pointsTip[lang] || LABELS.pointsTip.en;
    var championsTip = LABELS.championsTip[lang] || LABELS.championsTip.en;
    var calendarTip = LABELS.calendarTip[lang] || LABELS.calendarTip.en;

    var dashLabel = root.querySelector("[data-chrome-dash-label]");
    if (dashLabel) dashLabel.textContent = LABELS.dashboards[lang] || LABELS.dashboards.en;
    var pointsLabel = root.querySelector("[data-chrome-points-label]");
    if (pointsLabel) pointsLabel.textContent = LABELS.points[lang] || LABELS.points.en;
    var championsLabel = root.querySelector("[data-chrome-champions-label]");
    if (championsLabel) championsLabel.textContent = LABELS.champions[lang] || LABELS.champions.en;
    var calendarLabel = root.querySelector("[data-chrome-calendar-label]");
    if (calendarLabel) calendarLabel.textContent = LABELS.calendar[lang] || LABELS.calendar.en;
    var contactBtn = root.querySelector("[data-chrome-contact-btn]");
    if (contactBtn) contactBtn.setAttribute("aria-label", LABELS.contact[lang] || LABELS.contact.en);
    var qaBtn = root.querySelector("[data-chrome-qa-btn]");
    if (qaBtn) {
      var qaLabel = LABELS.qa[lang] || LABELS.qa.en;
      qaBtn.setAttribute("href", qaHubHref(root, lang));
      qaBtn.setAttribute("aria-label", qaLabel);
      qaBtn.removeAttribute("title");
      qaBtn.classList.toggle("is-active", (root.getAttribute("data-active") || "") === "qa");
      var icon = qaBtn.querySelector(".wsdc-chrome__qa-icon");
      if (icon) {
        var iconUrl = withPathPrefix(root, "static/img/qa-chrome-icon.png");
        icon.style.webkitMaskImage = "url('" + iconUrl + "')";
        icon.style.maskImage = "url('" + iconUrl + "')";
      }
    }
    var qaTip = root.querySelector("[data-chrome-qa-tip]");
    if (qaTip) qaTip.textContent = LABELS.qa[lang] || LABELS.qa.en;
    var email = root.querySelector("[data-chrome-email]");
    if (email) email.textContent = LABELS.email[lang] || LABELS.email.en;
    var fb = root.querySelector("[data-chrome-facebook]");
    if (fb) fb.textContent = LABELS.facebook[lang] || LABELS.facebook.en;

    root.querySelectorAll("[data-chrome-home]").forEach(function (el) {
      el.setAttribute("href", homeHref);
      el.setAttribute("aria-label", homeLabel);
      el.setAttribute("title", homeLabel);
    });

    syncBackLinks(lang, root.getAttribute("data-home-href") || "index.html");

    var dashTipEl = document.querySelector("[data-chrome-dash-tip]");
    if (dashTipEl) {
      dashTipEl.textContent = dashTip;
      var tipWrap = dashTipEl.closest(".wsdc-chrome__tip") || root.querySelector('[data-chrome-nav="dashboards"] .wsdc-chrome__tip');
      if (tipWrap) tipWrap.setAttribute("aria-label", dashTip);
    }
    var pointsTipEl = document.querySelector("[data-chrome-points-tip]");
    if (pointsTipEl) {
      pointsTipEl.textContent = pointsTip;
      var tipWrap2 = pointsTipEl.closest(".wsdc-chrome__tip") || root.querySelector('[data-chrome-nav="points"] .wsdc-chrome__tip');
      if (tipWrap2) tipWrap2.setAttribute("aria-label", pointsTip);
    }
    var championsTipEl = document.querySelector("[data-chrome-champions-tip]");
    if (championsTipEl) {
      championsTipEl.textContent = championsTip;
      var tipWrap3 = championsTipEl.closest(".wsdc-chrome__tip") || root.querySelector('[data-chrome-nav="champions"] .wsdc-chrome__tip');
      if (tipWrap3) tipWrap3.setAttribute("aria-label", championsTip);
    }
    var calendarTipEl = document.querySelector("[data-chrome-calendar-tip]");
    if (calendarTipEl) {
      calendarTipEl.textContent = calendarTip;
      var tipWrap4 = calendarTipEl.closest(".wsdc-chrome__tip") || root.querySelector('[data-chrome-nav="calendar"] .wsdc-chrome__tip');
      if (tipWrap4) tipWrap4.setAttribute("aria-label", calendarTip);
    }

    root.querySelectorAll(".lang-btn").forEach(function (btn) {
      var on = btn.getAttribute("data-lang") === lang;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function bind(root, initialLang) {
    var dd = root.querySelector("[data-chrome-dd]");
    var dashBtn = root.querySelector("[data-chrome-dash-btn]");
    var contact = root.querySelector("[data-chrome-contact]");
    var contactBtn = root.querySelector("[data-chrome-contact-btn]");
    var dashMenu = root.querySelector("[data-chrome-dash-menu]");
    var contactMenu = root.querySelector("[data-chrome-contact-menu]");
    var ignoreDocClose = false;

    function armIgnoreDocClose() {
      ignoreDocClose = true;
      window.setTimeout(function () {
        ignoreDocClose = false;
      }, 0);
    }

    if (dashBtn && dd) {
      dashBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        armIgnoreDocClose();
        var open = !dd.classList.contains("is-open");
        closeAll(root);
        if (open) {
          dd.classList.add("is-open");
          dashBtn.setAttribute("aria-expanded", "true");
          if (dashMenu) dashMenu.setAttribute("aria-hidden", "false");
        }
      });
    }

    if (contactBtn && contact) {
      contactBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        armIgnoreDocClose();
        var open = !contact.classList.contains("is-open");
        closeAll(root);
        if (open) {
          contact.classList.add("is-open");
          contactBtn.setAttribute("aria-expanded", "true");
          if (contactMenu) contactMenu.setAttribute("aria-hidden", "false");
        }
      });
    }

    root.querySelectorAll(".wsdc-chrome__tip").forEach(function (tip) {
      tip.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        armIgnoreDocClose();
        var open = !tip.classList.contains("is-open");
        closeAll(root);
        if (open) {
          tip.classList.add("is-open");
          tip.setAttribute("aria-expanded", "true");
          window.requestAnimationFrame(function () {
            placeTipBubble(tip);
          });
        }
      });
    });

    document.addEventListener("click", function (e) {
      if (ignoreDocClose) return;
      var t = e.target;
      if (t && t.closest && t.closest(".wsdc-chrome__tip")) return;
      closeAll(root);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAll(root);
    });

    window.addEventListener("resize", function () {
      root.querySelectorAll(".wsdc-chrome__tip.is-open").forEach(placeTipBubble);
    });
    window.addEventListener(
      "scroll",
      function () {
        root.querySelectorAll(".wsdc-chrome__tip.is-open").forEach(placeTipBubble);
      },
      true
    );

    root.querySelectorAll(".lang-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var next = btn.getAttribute("data-lang");
        if (!next) return;
        localStorage.setItem("wsdc-lang", next);
        applyLangLabels(root, next);

        var mode = root.getAttribute("data-lang-mode") || "callback";
        if (mode === "navigate") {
          var url = root.getAttribute("data-lang-" + next);
          if (url) {
            window.location.href = url;
            return;
          }
        }

        if (typeof window.WsdcChrome.onLangChange === "function") {
          window.WsdcChrome.onLangChange(next);
        }

        root.dispatchEvent(
          new CustomEvent("wsdc:langchange", { detail: { lang: next }, bubbles: true })
        );
      });
    });

    applyLangLabels(root, initialLang);
  }

  function mountAll() {
    document.querySelectorAll("[data-site-chrome]").forEach(function (el) {
      if (el.getAttribute("data-chrome-mounted") === "1") return;
      el.setAttribute("data-chrome-mounted", "1");
      render(el);
    });
  }

  var existingOnLangChange =
    window.WsdcChrome && typeof window.WsdcChrome.onLangChange === "function"
      ? window.WsdcChrome.onLangChange
      : null;

  window.WsdcChrome = {
    mount: mountAll,
    applyLangLabels: function (lang) {
      document.querySelectorAll("[data-site-chrome]").forEach(function (el) {
        applyLangLabels(el, lang);
      });
    },
    syncBackLinks: syncBackLinks,
    onLangChange: existingOnLangChange,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll);
  } else {
    mountAll();
  }
})();
