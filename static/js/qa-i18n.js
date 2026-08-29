/**
 * Q&A Hub UI strings (en / ru / es). Threads stay language-mixed; only chrome copy is localized.
 */
(function (global) {
  "use strict";

  var STRINGS = {
    en: {
      docTitle: "Q&A Hub | WSDC Analytics",
      back: "Back to home",
      title: "Q&A Hub",
      subtitle:
        "Ask about articles, dashboards, points, champions, or the site. No accounts — just a display name. Posts appear immediately. Write in the language you prefer.",
      threads: "Threads",
      board: "Board",
      boardOptions: "Board options",
      empty: "No threads yet. Start one on the right.",
      unknownBoard: "Unknown board.",
      loading: "Loading…",
      loadingThread: "Loading thread…",
      composeTitle: "New thread",
      composeLede: "Posts to the selected board. You can change the board anytime.",
      labelTitle: "Title",
      phTitle: "Short question title",
      labelName: "Your name",
      phName: "Display name",
      labelMessage: "Message",
      phMessage: "Context, what you tried, what is unclear…",
      optional: "Optional details",
      labelEmail: "Email",
      emailHint: "(not shown publicly)",
      phEmail: "you@example.com",
      labelPage: "Related page",
      phPage: "https://wsdc-analytics.github.io/…",
      publish: "Publish thread",
      reply: "Reply",
      phReply: "Write a reply…",
      emailHintShort: "(not shown)",
      postReply: "Post reply",
      boardStats: "Board stats",
      mod: "Moderator",
      secret: "Secret",
      unlock: "Unlock",
      lock: "Lock",
      hideThread: "Hide thread",
      unhideThread: "Unhide thread",
      pin: "Pin",
      unpin: "Unpin",
      deleteThread: "Delete thread",
      moveBoard: "Move to board",
      move: "Move",
      publishing: "Publishing…",
      threadPublished: "Thread published.",
      replyPublished: "Reply published.",
      threadDeleted: "Thread deleted.",
      updated: "Updated.",
      modOn: "Moderator mode on.",
      modOff: "Moderator mode off.",
      notConfigured: "Q&A backend is not configured.",
      selectBoard: "Select a board",
      noThread: "No thread selected",
      source: "source",
      by: "by",
      hidePost: "Hide",
      unhidePost: "Unhide",
      boardCounts: "Board counts",
      posts: "Posts",
      visible: "visible",
      hidden: "hidden",
      statsUnlock: "Unlock moderator mode to load counts.",
      statsUnavailable: "Stats unavailable",
      deleteConfirm: "Delete thread permanently?",
      deleteConfirmReplies: "Replies will be removed too.",
      pageUrlHttps: "Related page URL must be https://",
      createFailed: "Failed to create thread",
      threadNotFound: "Thread not found",
      boards: {
        articles: "Articles",
        dashboards: "Dashboards",
        "summary-points": "Summary Points",
        "new-champions": "New Champions",
        calendar: "Calendar",
        other: "Other",
      },
    },
    ru: {
      docTitle: "Q&A Hub | WSDC Analytics",
      back: "На главную",
      title: "Q&A Hub",
      subtitle:
        "Вопросы по статьям, дашбордам, очкам, чемпионам и сайту. Без аккаунтов — только отображаемое имя. Посты появляются сразу. Пишите на удобном языке.",
      threads: "Треды",
      board: "Доска",
      boardOptions: "Доски",
      empty: "Пока нет тредов. Начните справа.",
      unknownBoard: "Неизвестная доска.",
      loading: "Загрузка…",
      loadingThread: "Загрузка треда…",
      composeTitle: "Новый тред",
      composeLede: "Публикуется на выбранной доске. Доску можно сменить.",
      labelTitle: "Заголовок",
      phTitle: "Короткий вопрос",
      labelName: "Ваше имя",
      phName: "Отображаемое имя",
      labelMessage: "Сообщение",
      phMessage: "Контекст, что пробовали, что непонятно…",
      optional: "Дополнительно",
      labelEmail: "Email",
      emailHint: "(не показывается публично)",
      phEmail: "you@example.com",
      labelPage: "Связанная страница",
      phPage: "https://wsdc-analytics.github.io/…",
      publish: "Опубликовать",
      reply: "Ответ",
      phReply: "Напишите ответ…",
      emailHintShort: "(не показывается)",
      postReply: "Отправить ответ",
      boardStats: "Статистика досок",
      mod: "Модератор",
      secret: "Секрет",
      unlock: "Разблокировать",
      lock: "Заблокировать",
      hideThread: "Скрыть тред",
      unhideThread: "Показать тред",
      pin: "Закрепить",
      unpin: "Открепить",
      deleteThread: "Удалить тред",
      moveBoard: "Перенести на доску",
      move: "Перенести",
      publishing: "Публикация…",
      threadPublished: "Тред опубликован.",
      replyPublished: "Ответ опубликован.",
      threadDeleted: "Тред удалён.",
      updated: "Обновлено.",
      modOn: "Режим модератора включён.",
      modOff: "Режим модератора выключен.",
      notConfigured: "Бэкенд Q&A не настроен.",
      selectBoard: "Выберите доску",
      noThread: "Тред не выбран",
      source: "источник",
      by: "от",
      hidePost: "Скрыть",
      unhidePost: "Показать",
      boardCounts: "Счётчики досок",
      posts: "Посты",
      visible: "видимых",
      hidden: "скрытых",
      statsUnlock: "Разблокируйте модератора, чтобы загрузить счётчики.",
      statsUnavailable: "Статистика недоступна",
      deleteConfirm: "Удалить тред навсегда?",
      deleteConfirmReplies: "Ответы тоже будут удалены.",
      pageUrlHttps: "URL страницы должен быть https://",
      createFailed: "Не удалось создать тред",
      threadNotFound: "Тред не найден",
      boards: {
        articles: "Статьи",
        dashboards: "Дашборды",
        "summary-points": "Summary Points",
        "new-champions": "New Champions",
        calendar: "Календарь",
        other: "Другое",
      },
    },
    es: {
      docTitle: "Q&A Hub | WSDC Analytics",
      back: "Volver al inicio",
      title: "Q&A Hub",
      subtitle:
        "Pregunta sobre artículos, paneles, puntos, champions o el sitio. Sin cuentas: solo un nombre visible. Las publicaciones aparecen al instante. Escribe en el idioma que prefieras.",
      threads: "Hilos",
      board: "Tablero",
      boardOptions: "Tableros",
      empty: "Aún no hay hilos. Empieza a la derecha.",
      unknownBoard: "Tablero desconocido.",
      loading: "Cargando…",
      loadingThread: "Cargando hilo…",
      composeTitle: "Nuevo hilo",
      composeLede: "Se publica en el tablero seleccionado. Puedes cambiarlo.",
      labelTitle: "Título",
      phTitle: "Pregunta breve",
      labelName: "Tu nombre",
      phName: "Nombre visible",
      labelMessage: "Mensaje",
      phMessage: "Contexto, qué probaste, qué no está claro…",
      optional: "Detalles opcionales",
      labelEmail: "Email",
      emailHint: "(no se muestra públicamente)",
      phEmail: "you@example.com",
      labelPage: "Página relacionada",
      phPage: "https://wsdc-analytics.github.io/…",
      publish: "Publicar hilo",
      reply: "Respuesta",
      phReply: "Escribe una respuesta…",
      emailHintShort: "(no se muestra)",
      postReply: "Publicar respuesta",
      boardStats: "Estadísticas",
      mod: "Moderador",
      secret: "Secreto",
      unlock: "Desbloquear",
      lock: "Bloquear",
      hideThread: "Ocultar hilo",
      unhideThread: "Mostrar hilo",
      pin: "Fijar",
      unpin: "Desfijar",
      deleteThread: "Eliminar hilo",
      moveBoard: "Mover a tablero",
      move: "Mover",
      publishing: "Publicando…",
      threadPublished: "Hilo publicado.",
      replyPublished: "Respuesta publicada.",
      threadDeleted: "Hilo eliminado.",
      updated: "Actualizado.",
      modOn: "Modo moderador activado.",
      modOff: "Modo moderador desactivado.",
      notConfigured: "El backend de Q&A no está configurado.",
      selectBoard: "Selecciona un tablero",
      noThread: "Ningún hilo seleccionado",
      source: "fuente",
      by: "por",
      hidePost: "Ocultar",
      unhidePost: "Mostrar",
      boardCounts: "Conteos por tablero",
      posts: "Publicaciones",
      visible: "visibles",
      hidden: "ocultos",
      statsUnlock: "Desbloquea el moderador para cargar conteos.",
      statsUnavailable: "Estadísticas no disponibles",
      deleteConfirm: "¿Eliminar el hilo permanentemente?",
      deleteConfirmReplies: "Las respuestas también se eliminarán.",
      pageUrlHttps: "La URL debe ser https://",
      createFailed: "No se pudo crear el hilo",
      threadNotFound: "Hilo no encontrado",
      boards: {
        articles: "Artículos",
        dashboards: "Paneles",
        "summary-points": "Summary Points",
        "new-champions": "New Champions",
        calendar: "Calendario",
        other: "Otros",
      },
    },
  };

  function normalizeLang(lang) {
    var l = String(lang || "en").toLowerCase();
    if (l === "ru" || l === "es" || l === "en") return l;
    return "en";
  }

  function t(lang, key) {
    var pack = STRINGS[normalizeLang(lang)] || STRINGS.en;
    if (Object.prototype.hasOwnProperty.call(pack, key)) return pack[key];
    return STRINGS.en[key] || key;
  }

  function boardTitle(lang, slug, fallback) {
    var pack = STRINGS[normalizeLang(lang)] || STRINGS.en;
    var map = pack.boards || STRINGS.en.boards;
    return (map && map[slug]) || fallback || slug;
  }

  function applyStatic(lang) {
    var L = STRINGS[normalizeLang(lang)] || STRINGS.en;
    document.documentElement.lang = normalizeLang(lang);
    document.title = L.docTitle;
    document.querySelectorAll("[data-qa-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-qa-i18n");
      if (!key || L[key] == null || typeof L[key] === "object") return;
      el.textContent = L[key];
    });
    document.querySelectorAll("[data-qa-i18n-html]").forEach(function (el) {
      var key = el.getAttribute("data-qa-i18n-html");
      if (!key || L[key] == null) return;
      el.innerHTML = L[key];
    });
    document.querySelectorAll("[data-qa-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-qa-i18n-placeholder");
      if (!key || L[key] == null) return;
      el.setAttribute("placeholder", L[key]);
    });
    document.querySelectorAll("[data-qa-i18n-aria]").forEach(function (el) {
      var key = el.getAttribute("data-qa-i18n-aria");
      if (!key || L[key] == null) return;
      el.setAttribute("aria-label", L[key]);
    });
  }

  global.QaI18n = {
    STRINGS: STRINGS,
    normalizeLang: normalizeLang,
    t: t,
    boardTitle: boardTitle,
    applyStatic: applyStatic,
  };
})(typeof window !== "undefined" ? window : globalThis);
