(function () {
  var SUPPORTED = {
    overview_2025: ["ru", "en", "es"],
    geo_2025: ["ru", "en", "es"],
    events_2025: ["ru", "en", "es"],
    dancers_2025: ["ru", "en", "es"],
    rules_evolution_2025: ["ru", "en", "es"],
    rules_catalog: ["ru", "en", "es"],
    article_secondary_role: ["ru", "en", "es"],
    article_3year_rule: ["ru", "en", "es"],
    article_division_transition_time: ["ru", "en", "es"]
  };

  function parseCurrent() {
    var file = (window.location.pathname.split("/").pop() || "").toLowerCase();
    var match = file.match(/^(.*?)(?:_(en|es|ru))?\.html$/);
    if (!match) return null;

    var base = match[1];
    var suffix = match[2] || null;
    if (!SUPPORTED[base]) return null;

    var currentLang = suffix || "ru";
    if (base === "dancers_2025" && file === "dancers_2025_ru.html") {
      currentLang = "ru";
    }

    return { base: base, file: file, currentLang: currentLang };
  }

  function buildTarget(base, lang) {
    if (lang === "ru") return base + ".html";
    return base + "_" + lang + ".html";
  }

  /**
   * Strip setlang/lang from the URL without a navigation.
   * location.replace() here is reported by Google as "Page with redirect".
   */
  function stripLangQueryInPlace(params) {
    params.delete("setlang");
    params.delete("lang");
    var cleanQuery = params.toString();
    var next =
      window.location.pathname +
      (cleanQuery ? "?" + cleanQuery : "") +
      window.location.hash;
    var current =
      window.location.pathname + window.location.search + window.location.hash;
    if (next === current) return;
    if (window.history && typeof window.history.replaceState === "function") {
      window.history.replaceState(null, "", next);
    }
  }

  function redirectIfNeeded() {
    var current = parseCurrent();
    if (!current) return;

    var params = new URLSearchParams(window.location.search);
    // Explicit user/language choice only (?lang= / ?setlang=).
    // Do not auto-redirect from Accept-Language or localStorage — that makes
    // sitemap language URLs (e.g. *_es.html) look like redirects to Googlebot.
    var forced = params.get("setlang") || params.get("lang");
    if (!(forced && ["ru", "en", "es"].indexOf(forced) !== -1)) return;

    localStorage.setItem("wsdc-lang", forced);
    var forcedTarget = buildTarget(current.base, forced);

    if (forcedTarget === current.file) {
      stripLangQueryInPlace(params);
      return;
    }

    params.delete("setlang");
    params.delete("lang");
    var cleanQuery = params.toString();
    var forcedUrl =
      forcedTarget + (cleanQuery ? "?" + cleanQuery : "") + window.location.hash;
    window.location.replace(forcedUrl);
  }

  try {
    redirectIfNeeded();
  } catch (_e) {
    // Never break page render on redirect helper errors.
  }
})();
