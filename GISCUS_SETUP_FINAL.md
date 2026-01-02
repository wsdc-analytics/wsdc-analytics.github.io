# Настройка Giscus - Пошаговая инструкция

## Шаг 1: Включить Discussions в репозитории

По официальной документации GitHub, нужно:

1. Откройте репозиторий: https://github.com/wsdc-analytics/wsdc-analytics.github.io
2. Нажмите **"Settings"** (вкладка вверху)
3. В **левом боковом меню** найдите раздел **"General"** (обычно первый пункт)
4. В основном контенте справа прокрутите **вниз** до раздела **"Features"**
5. Найдите чекбокс **"Discussions"** и поставьте галочку ✅
6. Сохраните (если нужно)

**Если раздела "Features" нет в General:**

### Альтернативный способ 1: Через прямую ссылку
Попробуйте открыть напрямую:
https://github.com/wsdc-analytics/wsdc-analytics.github.io/discussions

GitHub автоматически предложит включить Discussions.

### Альтернативный способ 2: Через создание первого Discussion
1. Откройте репозиторий
2. Найдите вкладку **"Discussions"** в верхнем меню (рядом с Pull requests, Actions)
3. Если вкладки нет, нажмите на **"..."** (три точки) рядом с "Insights"
4. В выпадающем меню выберите "Discussions"
5. GitHub предложит включить - нажмите кнопку

---

## Шаг 2: Установить Giscus App

1. Перейдите: https://github.com/apps/giscus
2. Нажмите зеленую кнопку **"Configure"** или **"Install"**
3. Выберите **"Only select repositories"**
4. В выпадающем списке найдите: `wsdc-analytics/wsdc-analytics.github.io`
5. Нажмите **"Install"** или **"Save"**

---

## Шаг 3: Получить ID для кода

1. Перейдите: https://giscus.app/
2. Заполните форму:
   - **Repository**: `wsdc-analytics/wsdc-analytics.github.io`
   - **Discussion category**: Выберите `General` (или создайте свою)
   - **Mapping**: `Discussion title contains page pathname`
   - **Theme**: `Light`
   - **Language**: `ru` (для русской статьи) или `en` (для английской)
3. Нажмите **"Generate script"** или просто прокрутите вниз
4. Скопируйте значения из сгенерированного кода:
   - `data-repo-id="..."` - это REPO_ID
   - `data-category-id="..."` - это CATEGORY_ID

**Пример:**
```
data-repo-id="R_kgDOKxyz123"
data-category-id="DIC_kwDOKxyz123"
```

---

## Шаг 4: Обновить код (сообщите ID - я обновлю автоматически!)

После получения ID, сообщите мне:
- `data-repo-id` (REPO_ID)
- `data-category-id` (CATEGORY_ID)

Я обновлю файлы `events_2025.html` и `events_2025_en.html` автоматически.

---

## Проверка

После всех шагов:
1. Откройте статью на сайте
2. Прокрутите вниз до секции "Комментарии"
3. Должен появиться виджет Giscus

Если что-то не работает - проверьте консоль браузера (F12) на наличие ошибок.

