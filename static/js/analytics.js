/**
 * Shared GA4 loader with Consent Mode v2 + light custom events.
 * Measurement ID: G-LMLCY5PE8Z
 *
 * Usage: <script src="static/js/analytics.js" defer></script>
 * Optionally set window.__WSDC_PAGE_TYPE__ = 'calendar'|'dashboard'|'article'|…
 * before this script (or via data-page-type on <html>).
 */
(function () {
  var MEASUREMENT_ID = "G-LMLCY5PE8Z";
  var CONSENT_KEY = "wsdc_ga_consent_v1";

  function pageType() {
    if (window.__WSDC_PAGE_TYPE__) return String(window.__WSDC_PAGE_TYPE__);
    var html = document.documentElement;
    if (html && html.getAttribute("data-page-type")) {
      return html.getAttribute("data-page-type");
    }
    var path = (location.pathname || "/").toLowerCase();
    if (path.indexOf("events-calendar") >= 0) return "calendar";
    if (path.indexOf("champion-news") >= 0) return "champion_news";
    if (path.indexOf("points-summary") >= 0) return "points_summary";
    if (path.indexOf("rankings") >= 0 || path.indexOf("dashboard") >= 0 || path.indexOf("navigator") >= 0 || path.indexOf("dancer-profile") >= 0 || path.indexOf("city-clouds") >= 0 || path.indexOf("secondary_role") >= 0 || path.indexOf("time_in_division") >= 0) {
      return "dashboard";
    }
    if (path.indexOf("article") >= 0 || path.indexOf("/events/") >= 0) return "article";
    if (path === "/" || path.indexOf("index") >= 0) return "home";
    return "other";
  }

  function lang() {
    var html = document.documentElement;
    var dl = html && html.getAttribute("data-lang");
    if (dl) return dl;
    return (html && html.lang) || "en";
  }

  function loadGtag(granted) {
    window.dataLayer = window.dataLayer || [];
    function gtag() {
      window.dataLayer.push(arguments);
    }
    window.gtag = gtag;

    gtag("consent", "default", {
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      analytics_storage: granted ? "granted" : "denied",
      functionality_storage: "granted",
      security_storage: "granted",
      wait_for_update: 500,
    });

    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
    document.head.appendChild(s);

    gtag("js", new Date());
    gtag("config", MEASUREMENT_ID, {
      anonymize_ip: true,
      send_page_view: true,
      page_type: pageType(),
      language: lang(),
    });
  }

  function setConsent(granted) {
    try {
      localStorage.setItem(CONSENT_KEY, granted ? "granted" : "denied");
    } catch (e) {}
    if (window.gtag) {
      window.gtag("consent", "update", {
        analytics_storage: granted ? "granted" : "denied",
      });
    } else {
      loadGtag(granted);
    }
    var banner = document.getElementById("wsdc-consent-banner");
    if (banner) banner.remove();
  }

  function showBanner() {
    if (document.getElementById("wsdc-consent-banner")) return;
    var el = document.createElement("div");
    el.id = "wsdc-consent-banner";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-live", "polite");
    el.style.cssText =
      "position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#111;color:#fff;" +
      "padding:12px 16px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;" +
      "justify-content:space-between;font:14px/1.4 DM Sans,system-ui,sans-serif;box-shadow:0 -4px 16px rgba(0,0,0,.2)";
    el.innerHTML =
      '<p style="margin:0;max-width:52rem">We use privacy-minded analytics (Google Analytics) to understand which pages help dancers. You can accept or decline.</p>' +
      '<div style="display:flex;gap:8px">' +
      '<button type="button" data-consent="denied" style="background:transparent;color:#fff;border:1px solid #888;border-radius:6px;padding:8px 12px;cursor:pointer">Decline</button>' +
      '<button type="button" data-consent="granted" style="background:#fff;color:#111;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;font-weight:600">Accept</button>' +
      "</div>";
    el.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-consent]");
      if (!btn) return;
      setConsent(btn.getAttribute("data-consent") === "granted");
    });
    document.body.appendChild(el);
  }

  function track(name, params) {
    if (typeof window.gtag !== "function") return;
    var payload = params || {};
    payload.page_type = payload.page_type || pageType();
    payload.language = payload.language || lang();
    window.gtag("event", name, payload);
  }
  window.wsdcTrack = track;

  function wireCustomEvents() {
    document.addEventListener(
      "click",
      function (ev) {
        var a = ev.target.closest("a[href]");
        if (!a) return;
        var href = a.getAttribute("href") || "";
        if (/^https?:\/\//i.test(href) && href.indexOf(location.host) === -1) {
          track("outbound_click", { link_url: href.slice(0, 200) });
        }
        if (a.closest("[data-chrome-nav]")) {
          track("nav_click", { nav: a.closest("[data-chrome-nav]").getAttribute("data-chrome-nav") });
        }
      },
      true
    );

    document.addEventListener(
      "change",
      function (ev) {
        var t = ev.target;
        if (!t) return;
        if (t.matches("[data-cal-filter], select[data-filter], .cal-filter select")) {
          track("calendar_filter", { filter_id: t.id || t.name || t.getAttribute("data-cal-filter") || "unknown" });
        }
      },
      true
    );

    document.addEventListener(
      "click",
      function (ev) {
        var langBtn = ev.target.closest("[data-lang-switch], .wsdc-chrome__langs button");
        if (langBtn) {
          track("language_switch", { to: langBtn.getAttribute("data-lang") || langBtn.textContent });
        }
      },
      true
    );

    // Article scroll depth 75%
    var fired75 = false;
    window.addEventListener(
      "scroll",
      function () {
        if (fired75 || pageType() !== "article") return;
        var doc = document.documentElement;
        var max = doc.scrollHeight - window.innerHeight;
        if (max <= 0) return;
        if (window.scrollY / max >= 0.75) {
          fired75 = true;
          track("article_read_75");
        }
      },
      { passive: true }
    );
  }

  function init() {
    var stored = null;
    try {
      stored = localStorage.getItem(CONSENT_KEY);
    } catch (e) {}
    if (stored === "granted") {
      loadGtag(true);
    } else if (stored === "denied") {
      loadGtag(false);
    } else {
      loadGtag(false);
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", showBanner);
      } else {
        showBanner();
      }
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", wireCustomEvents);
    } else {
      wireCustomEvents();
    }
  }

  init();
})();
