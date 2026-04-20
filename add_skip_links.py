#!/usr/bin/env python3
"""
Скрипт для добавления skip-link во все HTML файлы статей
"""

import re
from pathlib import Path

ARTICLE_FILES = [
    'overview_2025_en.html',
    'overview_2025_es.html',
    'dancers_2025.html',
    'dancers_2025_en.html',
    'dancers_2025_es.html',
    'dancers_2025_ru.html',
    'geo_2025.html',
    'geo_2025_en.html',
    'geo_2025_es.html',
    'events_2025.html',
    'events_2025_en.html',
    'events_2025_es.html',
]

def add_skip_link(content):
    """Добавляет skip-link после <body>"""
    skip_link = '<a href="#main-content" class="skip-link">Перейти к содержимому</a>\n    '
    
    # Проверяем, есть ли уже skip-link
    if 'skip-link' in content and '<a href="#main-content" class="skip-link">' in content:
        return content
    
    # Добавляем skip-link после <body>
    if '<body>' in content:
        content = content.replace('<body>', '<body>\n    ' + skip_link, 1)
    
    return content

def process_file(filepath):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath.name}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Добавляем skip-link
        content = add_skip_link(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Добавлен skip-link в {filepath.name}")
            return True
        else:
            print(f"  - Без изменений {filepath.name}")
            return False
            
    except Exception as e:
        print(f"  ✗ Ошибка при обработке {filepath.name}: {e}")
        return False

def main():
    """Главная функция"""
    repo_path = Path(__file__).parent
    
    print("Добавление skip-link во все статьи...\n")
    
    updated_count = 0
    for filename in ARTICLE_FILES:
        filepath = repo_path / filename
        if filepath.exists():
            if process_file(filepath):
                updated_count += 1
        else:
            print(f"  ⚠ Файл не найден: {filename}")
    
    print(f"\n✓ Обработано файлов: {updated_count}/{len(ARTICLE_FILES)}")

if __name__ == '__main__':
    main()
