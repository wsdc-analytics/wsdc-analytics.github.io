#!/bin/bash
# Скрипт для обновления remote после переименования репозитория

cd /Users/ania/.cursor/wsdc-analytics-repo
git remote set-url origin https://github.com/wsdc-analitycs/wsdc-analitycs.github.io.git
git remote -v
echo ""
echo "Remote обновлён! Теперь можете делать git push как обычно."

