// Данные статей по языкам
const articlesByLang = {
    ru: [
        {
            title: "WSDC 2025: Города и регионы",
            language: "RU",
            description: "География WCS 2025: от городов до регионов, баланс сил и карта активности.",
            url: "geo_2025.html",
            keywords: "география, города, регионы, страны, штаты, WSDC, 2025, анализ",
            datePublished: "2026-01-07",
            category: "География"
        },
        {
            title: "WSDC 2025: Ивенты",
            language: "RU",
            description: "Изменения в глобальном топе и региональные тренды.",
            url: "events_2025.html",
            keywords: "ивенты, рейтинг, поинты, новички, Европа, США, WSDC, 2025, анализ ивентов",
            datePublished: "2026-01-02",
            category: "Ивенты"
        }
    ],
    en: [
        {
            title: "WSDC 2025: Cities and Regions",
            language: "EN",
            description: "WCS Geography 2025: from cities to regions, balance of power and activity map.",
            url: "geo_2025_en.html",
            keywords: "geography, cities, regions, countries, states, WSDC, 2025, analysis",
            datePublished: "2026-01-07",
            category: "Geography"
        },
        {
            title: "WSDC 2025: Events",
            language: "EN",
            description: "Changes in the global top and regional trends.",
            url: "events_2025_en.html",
            keywords: "events, rankings, points, new dancers, Europe, United States, WSDC, 2025, analysis",
            datePublished: "2026-01-02",
            category: "Events"
        }
    ],
    es: [
        {
            title: "WSDC 2025: Ciudades y Regiones",
            language: "ES",
            description: "Geografía WCS 2025: de ciudades a regiones, balance de poder y mapa de actividad.",
            url: "geo_2025_es.html",
            keywords: "geografía, ciudades, regiones, países, estados, WSDC, 2025, análisis",
            datePublished: "2026-01-07",
            category: "Geografía"
        },
        {
            title: "WSDC 2025: Eventos",
            language: "ES",
            description: "Cambios en el top global y tendencias regionales.",
            url: "events_2025_es.html",
            keywords: "eventos, rankings, puntos, nuevos bailarines, Europa, Estados Unidos, WSDC, 2025, análisis",
            datePublished: "2026-01-02",
            category: "Eventos"
        }
    ]
};

// Все статьи для поиска (объединенный массив)
const allArticles = Object.values(articlesByLang).flat();

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const articlesGrid = document.getElementById('articlesGrid');
const langButtons = document.querySelectorAll('.lang-btn');

// Определение языка: URL параметр > localStorage > браузер > RU по умолчанию
function getCurrentLanguage() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get('lang');
    if (urlLang && ['ru', 'en', 'es'].includes(urlLang)) {
        return urlLang;
    }
    
    const storedLang = localStorage.getItem('wsdc-lang');
    if (storedLang && ['ru', 'en', 'es'].includes(storedLang)) {
        return storedLang;
    }
    
    const browserLang = navigator.language || navigator.userLanguage;
    if (browserLang.startsWith('ru')) return 'ru';
    if (browserLang.startsWith('en')) return 'en';
    if (browserLang.startsWith('es')) return 'es';
    
    return 'ru'; // По умолчанию
}

// Сохранение выбора языка
function setLanguage(lang) {
    localStorage.setItem('wsdc-lang', lang);
    const url = new URL(window.location);
    url.searchParams.set('lang', lang);
    window.history.replaceState({}, '', url);
    updateLanguage(lang);
}

// Обновление интерфейса при смене языка
function updateLanguage(lang) {
    // Обновление активной кнопки
    langButtons.forEach(btn => {
        if (btn.dataset.lang === lang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Обновление placeholder поиска
    const placeholders = {
        ru: 'Поиск статей...',
        en: 'Search articles...',
        es: 'Buscar artículos...'
    };
    if (searchInput) {
        searchInput.placeholder = placeholders[lang] || placeholders.en;
    }

    // Обновление подзаголовка
    const subtitles = {
        ru: 'Статистика, исследования и аналитика West Coast Swing',
        en: 'West Coast Swing: Statistics, Research & Analytics',
        es: 'West Coast Swing: Estadísticas, Investigación y Análisis'
    };
    const subtitleElement = document.getElementById('subtitle');
    if (subtitleElement) {
        subtitleElement.textContent = subtitles[lang] || subtitles.en;
    }

    // Фильтрация и отображение статей
    const articles = articlesByLang[lang] || [];
    displayArticles(articles, lang);
}

// Форматирование даты по языку
function formatDate(dateString, lang) {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    
    const day = date.getDate();
    const monthNames = {
        ru: ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 
             'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'],
        en: ['January', 'February', 'March', 'April', 'May', 'June',
             'July', 'August', 'September', 'October', 'November', 'December'],
        es: ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    };
    
    const month = monthNames[lang] ? monthNames[lang][date.getMonth()] : monthNames.en[date.getMonth()];
    const year = date.getFullYear();
    
    // Форматы: RU: "2 января 2025", EN: "January 2, 2025", ES: "2 de enero de 2025"
    if (lang === 'ru') {
        return `${day} ${month} ${year}`;
    } else if (lang === 'es') {
        return `${day} de ${month} de ${year}`;
    } else {
        return `${month} ${day}, ${year}`;
    }
}

// Отображение статей
function displayArticles(articles, lang) {
    if (articles.length === 0) {
        const noArticlesText = {
            ru: 'Статьи на этом языке пока недоступны.',
            en: 'Articles in this language are not available yet.',
            es: 'Los artículos en este idioma aún no están disponibles.'
        };
        articlesGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">${noArticlesText[lang] || noArticlesText.en}</div>`;
        return;
    }

    // Сортировка статей от новых к старым (по дате публикации)
    const sortedArticles = [...articles].sort((a, b) => {
        const dateA = a.datePublished ? new Date(a.datePublished) : new Date(0);
        const dateB = b.datePublished ? new Date(b.datePublished) : new Date(0);
        return dateB - dateA; // Более новые статьи первыми
    });

    let html = '';
    sortedArticles.forEach(article => {
        const formattedDate = article.datePublished ? formatDate(article.datePublished, lang) : '';
        const metaText = formattedDate && article.category 
            ? `${formattedDate} • ${article.category}`
            : (article.category || '');
        
        html += `
            <a href="${article.url}?lang=${lang}" class="article-card">
                <div class="meta">${metaText}</div>
                <h2>${article.title}</h2>
                <p>${article.description}</p>
            </a>
        `;
    });
    articlesGrid.innerHTML = html;
}

// Инициализация языка при загрузке
const currentLang = getCurrentLanguage();
updateLanguage(currentLang);

// Обработчики переключения языка
langButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        if (!btn.disabled) {
            setLanguage(btn.dataset.lang);
        }
    });
});

function normalizeText(text) {
    return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function searchArticles(query) {
    if (!query || query.trim() === '') {
        searchResults.classList.add('hidden');
        articlesGrid.style.display = 'grid';
        // Восстановить статьи текущего языка
        const currentLang = getCurrentLanguage();
        updateLanguage(currentLang);
        return;
    }

    const normalizedQuery = normalizeText(query);
    const currentLang = getCurrentLanguage();
    // Искать только в статьях текущего языка
    const articlesToSearch = articlesByLang[currentLang] || [];
    const results = articlesToSearch.filter(article => {
        const titleMatch = normalizeText(article.title).includes(normalizedQuery);
        const descMatch = normalizeText(article.description).includes(normalizedQuery);
        const keywordsMatch = normalizeText(article.keywords).includes(normalizedQuery);
        return titleMatch || descMatch || keywordsMatch;
    });

    displayResults(results, query);
}

function displayResults(results, query) {
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">No articles found for "' + query + '"</div>';
        searchResults.classList.remove('hidden');
        articlesGrid.style.display = 'none';
        return;
    }

    let html = '';
    const currentLang = getCurrentLanguage();
    results.forEach(article => {
        html += `
            <a href="${article.url}?lang=${currentLang}" class="search-result-item" style="text-decoration: none; color: inherit; display: block;">
                <h3>${article.title}</h3>
                <p>${article.description}</p>
            </a>
        `;
    });

    searchResults.innerHTML = html;
    searchResults.classList.remove('hidden');
    articlesGrid.style.display = 'none';
}

// Обработчик поиска
let searchTimeout;
const searchInputEl = document.getElementById('searchInput');
if (searchInputEl) {
    searchInputEl.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchArticles(e.target.value);
        }, 300);
    });

    // Показать все статьи при очистке поиска
    searchInputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInputEl.value = '';
            searchResults.classList.add('hidden');
            articlesGrid.style.display = 'grid';
        }
    });
}
