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

  function pickPreferredLanguage() {
    var stored = localStorage.getItem("wsdc-lang");
    if (stored && ["ru", "en", "es"].indexOf(stored) !== -1) {
      return stored;
    }

    var browserLangs = Array.isArray(navigator.languages) && navigator.languages.length
      ? navigator.languages
      : [navigator.language || "en"];

    for (var i = 0; i < browserLangs.length; i += 1) {
      var l = (browserLangs[i] || "").toLowerCase();
      if (l.indexOf("ru") === 0) return "ru";
      if (l.indexOf("es") === 0) return "es";
      if (l.indexOf("en") === 0) return "en";
    }
    return "en";
  }

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

  function redirectIfNeeded() {
    var current = parseCurrent();
    if (!current) return;

    var params = new URLSearchParams(window.location.search);
    // Treat both setlang and lang as explicit user choice.
    // If present, do not run auto language detection redirect.
    var forced = params.get("setlang") || params.get("lang");
    if (forced && ["ru", "en", "es"].indexOf(forced) !== -1) {
      localStorage.setItem("wsdc-lang", forced);
      params.delete("setlang");
      params.delete("lang");
      var cleanQuery = params.toString();
      var forcedTarget = buildTarget(current.base, forced);
      var forcedUrl = forcedTarget + (cleanQuery ? "?" + cleanQuery : "") + window.location.hash;
      if (forcedTarget === current.file && !cleanQuery) return;
      window.location.replace(forcedUrl);
      return;
    }

    var preferred = pickPreferredLanguage();
    if (SUPPORTED[current.base].indexOf(preferred) === -1) return;
    if (preferred === current.currentLang) return;

    var targetFile = buildTarget(current.base, preferred);
    var query = params.toString();
    var targetUrl = targetFile + (query ? "?" + query : "") + window.location.hash;
    window.location.replace(targetUrl);
  }

  try {
    redirectIfNeeded();
  } catch (_e) {
    // Never break page render on redirect helper errors.
  }
})();
