# Инструкции по настройке репозитория wsdc-analytics.github.io

## Шаг 1: Создание организации на GitHub

1. Перейдите на GitHub и войдите в свой аккаунт
2. Нажмите на иконку профиля в правом верхнем углу
3. Выберите **"Settings"** → **"Organizations"** → **"New organization"**
4. Выберите план **"Free"**
5. Название организации: **`wsdc-analytics`**
6. Email: ваш email
7. Нажмите **"Create organization"**

## Шаг 2: Создание репозитория

1. В созданной организации нажмите **"New repository"**
2. Название репозитория: **`wsdc-analytics.github.io`** (обязательно точно так!)
3. Описание: "Data-driven insights on West Coast Swing competitive scene"
4. Выберите **Public**
5. **НЕ** добавляйте README, .gitignore или лицензию (файлы уже готовы)
6. Нажмите **"Create repository"**

## Шаг 3: Настройка локального репозитория

Выполните следующие команды в терминале:

```bash
# Перейдите в папку с подготовленными файлами
cd /Users/ania/.cursor/wsdc-analytics-repo

# Инициализируйте Git репозиторий
git init

# Добавьте все файлы
git add .

# Сделайте первый коммит
git commit -m "Initial commit: WSDC Analytics articles"

# Добавьте remote (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/wsdc-analytics/wsdc-analytics.github.io.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Отправьте файлы на GitHub
git push -u origin main
```

## Шаг 4: Включение GitHub Pages

1. Перейдите в настройки репозитория: **Settings** → **Pages**
2. В разделе **"Source"** выберите:
   - Branch: **`main`**
   - Folder: **`/ (root)`**
3. Нажмите **"Save"**

## Шаг 5: Проверка

Через 1-2 минуты ваш сайт будет доступен по адресу:
**https://wsdc-analytics.github.io**

## Структура файлов

```
wsdc-analytics-repo/
├── index.html              # Главная страница с навигацией
├── events_2025.html        # Статья про ивенты (RU)
├── events_2025_en.html      # Статья про ивенты (EN)
├── geo_2025.html           # Статья про географию (RU)
├── events_background.png   # Фоновое изображение для заголовков
├── README.md               # Описание проекта
└── SETUP_INSTRUCTIONS.md   # Эти инструкции
```

## Дальнейшие шаги

После публикации вы можете:
- Добавлять новые статьи в папку репозитория
- Обновлять `index.html` для добавления ссылок на новые статьи
- Использовать GitHub Issues для отслеживания задач
- Настроить Google Analytics для отслеживания посещений (опционально)

## Настройка Google Analytics (опционально)

Если хотите отслеживать посещения:

1. Создайте аккаунт в Google Analytics
2. Получите Tracking ID (формат: `G-XXXXXXXXXX`)
3. Добавьте в `<head>` каждого HTML файла:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## Проблемы?

Если что-то не работает:
- Проверьте, что репозиторий называется точно `wsdc-analytics.github.io`
- Убедитесь, что GitHub Pages включен в настройках
- Подождите 2-3 минуты после включения Pages (нужно время на деплой)
- Проверьте, что все файлы закоммичены и запушены

