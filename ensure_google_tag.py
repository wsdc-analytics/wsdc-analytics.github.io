#!/usr/bin/env python3
"""
Скрипт для автоматической проверки и добавления Google Analytics тега
во все HTML статьи в репозитории
"""

import os
import re
from pathlib import Path

GOOGLE_TAG_CODE = '''<!-- Google tag (gtag.js) -->
<script async="" src="https://www.googletagmanager.com/gtag/js?id=G-LMLCY5PE8Z"></script>
<script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-LMLCY5PE8Z');
    </script>'''

GOOGLE_TAG_ID = 'G-LMLCY5PE8Z'

def check_and_add_google_tag(file_path):
    """Проверяет наличие Google Tag в файле и добавляет его, если отсутствует"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие Google Tag
    if GOOGLE_TAG_ID in content:
        return False, "Уже есть Google Tag"
    
    # Проверяем, что это HTML файл со статьей (не index.html, который уже обработан)
    if '</head>' not in content:
        return False, "Не HTML файл или неполный"
    
    # Находим место для вставки - после Schema.org и перед Twemoji/стилями
    # Ищем закрытие </script> от Schema.org или структурированных данных
    schema_pattern = r'(</script>\s*<!--\s*(?:Подключаем|Twemoji|style))'
    match = re.search(schema_pattern, content, re.IGNORECASE | re.MULTILINE)
    
    if match:
        insert_pos = match.start()
        # Находим конец закрывающего тега script
        script_end = content.rfind('</script>', 0, insert_pos) + len('</script>')
        if script_end > 0:
            insert_pos = script_end
    
    # Если не нашли место после Schema.org, вставляем перед </head>
    if not match:
        head_end = content.find('</head>')
        if head_end > 0:
            insert_pos = head_end
        else:
            return False, "Не найдено место для вставки"
    
    # Вставляем Google Tag
    new_content = content[:insert_pos] + '\n' + GOOGLE_TAG_CODE + '\n' + content[insert_pos:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, "Google Tag добавлен"

def main():
    repo_dir = Path(__file__).parent
    html_files = list(repo_dir.glob('*.html'))
    
    print("="*80)
    print("🔍 ПРОВЕРКА И ДОБАВЛЕНИЕ GOOGLE ANALYTICS ТЕГА")
    print("="*80 + "\n")
    
    updated_files = []
    
    for html_file in sorted(html_files):
        print(f"Проверяю: {html_file.name}...")
        try:
            updated, message = check_and_add_google_tag(html_file)
            if updated:
                print(f"  ✅ {message}")
                updated_files.append(html_file.name)
            else:
                print(f"  ℹ️  {message}")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
        print()
    
    if updated_files:
        print(f"✅ Обновлено файлов: {len(updated_files)}")
        print(f"📝 Файлы: {', '.join(updated_files)}")
    else:
        print("✅ Все файлы уже содержат Google Analytics тег!")

if __name__ == '__main__':
    main()

