# Reactions API (собственный счётчик)

Счётчик реакций (✓ / ○ / ✗) без Lyket: данные в репозитории, обновление через serverless.

## Поведение

- **Без API** (`REACTIONS_API = ''`): счётчики читаются из `static/data/reactions.json` (относительный путь), голосование не выполняется.
- **С API**: в статьях задаётся `REACTIONS_API = 'https://<your-vercel-app>.vercel.app'`. GET — загрузка счётчиков, POST — инкремент по `id`.

## Деплой API (Vercel)

1. Подключите репозиторий к Vercel, корень проекта — корень репо.
2. В настройках проекта → Environment Variables задайте:
   - `GITHUB_TOKEN` — Personal Access Token с правом `contents: write` для этого репо.
   - `GITHUB_REPO` — `owner/repo` (например `username/wsdc-analytics-repo`).
   - `GITHUB_BRANCH` — ветка с контентом (по умолчанию `main`).
3. После деплоя в каждой статье замените пустое значение на URL приложения:
   ```javascript
   var REACTIONS_API = 'https://wsdc-analytics-repo.vercel.app';
   ```

## Эндпоинты

- `GET /api/reactions` — JSON счётчиков `{ "<id>": number, ... }` (из raw GitHub или кэша).
- `POST /api/reactions` — тело `{ "id": "<reaction_id>" }`; инкремент в `static/data/reactions.json` и коммит в репо через GitHub API.

Файл данных: `static/data/reactions.json`. Список всех `id` соответствует атрибутам `data-lyket-id` в статьях.
