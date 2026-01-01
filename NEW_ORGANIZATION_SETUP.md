# Настройка новой организации с правильным названием

## Шаг 1: Создание новой организации

1. Перейдите на GitHub и откройте: https://github.com/settings/organizations
2. Или перейдите: Ваш профиль → Settings → Organizations → New organization
3. Название организации: **`wsdc-analytics`** (с "analytics")
4. План: **Free**
5. Email: ваш email
6. Нажмите **"Create organization"**

## Шаг 2: Создание репозитория

1. В новой организации нажмите **"New repository"**
2. Название репозитория: **`wsdc-analytics.github.io`** (обязательно точно так!)
3. Описание: "Data-driven insights on West Coast Swing competitive scene"
4. Выберите **Public**
5. **НЕ** добавляйте README, .gitignore или лицензию
6. Нажмите **"Create repository"**

## Шаг 3: Загрузка файлов

После создания репозитория выполните команды:

```bash
cd /Users/ania/.cursor/wsdc-analytics-repo

# Очистка старого git (если есть)
rm -rf .git

# Инициализация нового репозитория
git init
git branch -M main

# Добавление remote
git remote add origin https://github.com/wsdc-analytics/wsdc-analytics.github.io.git

# Добавление всех файлов
git add .

# Коммит
git commit -m "Initial commit: WSDC Analytics articles"

# Отправка на GitHub
git push -u origin main
```

## Шаг 4: Настройка GitHub Pages

1. Откройте: https://github.com/wsdc-analytics/wsdc-analytics.github.io/settings/pages
2. В разделе **"Build and deployment"**:
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/ (root)`
3. Нажмите **Save**

## Шаг 5: Готово!

Через 1-2 минуты сайт будет доступен по адресу:
**https://wsdc-analytics.github.io/**

## Обновление файлов

После создания новой организации нужно обновить:
- ✅ `sitemap.xml` - обновить URLs
- ✅ `robots.txt` - обновить URL sitemap
- ✅ Все ссылки в документации

Эти изменения будут сделаны автоматически после создания новой организации.

