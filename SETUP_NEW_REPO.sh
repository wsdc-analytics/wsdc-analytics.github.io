#!/bin/bash
# Скрипт для настройки нового репозитория после его создания на GitHub

cd /Users/ania/.cursor/wsdc-analytics-repo

echo "Проверка файлов..."
ls -la | grep -E "\.html$|\.png$|\.xml$|\.txt$|\.md$"

echo ""
echo "Инициализация Git (если ещё не инициализирован)..."
if [ ! -d .git ]; then
    git init
    git branch -M main
fi

echo ""
echo "Добавление remote..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/wsdc-analitycs/wsdc-analitycs.github.io.git
git remote -v

echo ""
echo "Добавление всех файлов..."
git add .

echo ""
echo "Создание коммита..."
git commit -m "Initial commit: WSDC Analytics articles"

echo ""
echo "Отправка на GitHub..."
echo "ВНИМАНИЕ: Если будет запрошен пароль, используйте Personal Access Token"
git push -u origin main

echo ""
echo "✅ Готово! После этого:"
echo "1. Откройте Settings → Pages в репозитории"
echo "2. Выберите Branch: main, Folder: / (root)"
echo "3. Сохраните"
echo "4. Через 1-2 минуты сайт будет доступен: https://wsdc-analitycs.github.io/"

