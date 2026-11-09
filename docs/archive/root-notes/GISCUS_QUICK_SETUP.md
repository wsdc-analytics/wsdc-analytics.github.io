# Быстрая настройка Giscus

## Шаг 1: Включить Discussions (2 минуты)

1. Откройте: https://github.com/wsdc-analytics/wsdc-analytics.github.io/settings
2. В разделе "Features" найдите "Discussions"
3. Поставьте галочку ✅
4. Нажмите "Set up discussions"

## Шаг 2: Установить Giscus App (1 минута)

1. Откройте: https://github.com/apps/giscus/installations/new
2. Или: https://github.com/apps/giscus → "Configure" → "Install"
3. Выберите "Only select repositories"
4. Выберите: `wsdc-analytics/wsdc-analytics.github.io`
5. Нажмите "Install"

## Шаг 3: Получить ID (2 минуты)

1. Откройте: https://giscus.app/
2. Заполните:
   - **Repository**: `wsdc-analytics/wsdc-analytics.github.io`
   - **Discussion category**: `General` (или создайте свою)
   - **Mapping**: `Discussion title contains page pathname`
   - **Theme**: `Light`
   - **Language**: `ru` (для RU версии) или `en` (для EN версии)
3. Нажмите "Generate script"
4. Скопируйте значения:
   - `data-repo-id` (например: `R_kgDOKxyz123`)
   - `data-category-id` (например: `DIC_kwDOKxyz123`)

## Шаг 4: Обновить код

После получения ID, нужно заменить в файлах:
- `events_2025.html` (строка с `data-repo-id="REPO_ID"` и `data-category-id="CATEGORY_ID"`)
- `events_2025_en.html` (то же самое)

**Или сообщите мне ID, и я обновлю автоматически!**

## Что получится:

✅ Пользователи смогут комментировать через GitHub аккаунты
✅ Реакции (👍, ❤️, 👎 и т.д.)
✅ Все комментарии хранятся в GitHub Discussions
✅ Бесплатно и без рекламы

