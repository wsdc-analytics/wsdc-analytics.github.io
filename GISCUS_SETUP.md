# Настройка Giscus для комментариев

## Шаг 1: Включить Discussions в репозитории

1. Откройте: https://github.com/wsdc-analytics/wsdc-analytics.github.io/settings
2. Прокрутите до раздела "Features"
3. Включите "Discussions" (галочка)
4. Нажмите "Set up discussions"

## Шаг 2: Установить Giscus App

1. Перейдите: https://github.com/apps/giscus
2. Нажмите "Configure" или "Install"
3. Выберите "Only select repositories"
4. Выберите репозиторий: `wsdc-analytics/wsdc-analytics.github.io`
5. Нажмите "Install"

## Шаг 3: Получить настройки

1. Перейдите: https://giscus.app/
2. Заполните форму:
   - **Repository**: `wsdc-analytics/wsdc-analytics.github.io`
   - **Discussion category**: Выберите категорию (можно создать "General" или "Announcements")
   - **Mapping**: "Discussion title contains page pathname" (рекомендуется)
   - **Theme**: "Light" (или другой по выбору)
   - **Language**: "ru" для русской версии, "en" для английской
3. Нажмите "Generate script"
4. Скопируйте значения:
   - `data-repo`
   - `data-repo-id`
   - `data-category`
   - `data-category-id`
   - `data-mapping`
   - `data-theme`
   - `data-lang`

## Шаг 4: Обновить код в HTML файлах

После получения настроек, нужно обновить код в:
- `events_2025.html`
- `events_2025_en.html`

Код уже добавлен в файлы, нужно только заменить значения атрибутов `data-*` на полученные из giscus.app

## Альтернативный способ (быстрый)

Если хотите использовать значения по умолчанию, можно использовать базовую конфигурацию, которая будет работать после установки app и включения Discussions.

