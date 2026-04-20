#!/usr/bin/env python3
"""
Скрипт для исправления skip-link во всех файлах - добавление opacity и pointer-events
"""

import re
from pathlib import Path

ARTICLE_FILES = [
    'index.html',
    'overview_2025.html',
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

def fix_skip_link_styles(content):
    """Исправляет стили skip-link"""
    
    # Добавляем opacity и pointer-events к skip-link
    pattern1 = r'(\.skip-link\s*\{[^}]*)(z-index:\s*\d+;[^}]*)(\})'
    
    def replace_skip_link(match):
        before = match.group(1)
        z_index = match.group(2)
        after = match.group(3)
        
        # Проверяем, есть ли уже opacity
        if 'opacity:' in before + z_index:
            return match.group(0)
        
        return before + z_index + '\n            opacity: 0;\n            pointer-events: none;' + after
    
    content = re.sub(pattern1, replace_skip_link, content, flags=re.DOTALL)
    
    # Обновляем :focus состояние
    pattern2 = r'(\.skip-link:focus\s*\{[^}]*top:\s*0;[^}]*)(\})'
    
    def replace_focus(match):
        before = match.group(1)
        after = match.group(2)
        
        if 'opacity:' in before:
            return match.group(0)
        
        return before + '\n            opacity: 1;\n            pointer-events: auto;' + after
    
    content = re.sub(pattern2, replace_focus, content, flags=re.DOTALL)
    
    # Добавляем position: relative к body если его нет
    if 'body {' in content and 'position: relative' not in content:
        # Ищем body стили и добавляем position: relative
        body_pattern = r'(body\s*\{[^}]*)(-webkit-font-smoothing:[^}]*)(\})'
        def add_position(match):
            before = match.group(1)
            webkit = match.group(2)
            after = match.group(3)
            return before + webkit + '\n            position: relative;' + after
        
        content = re.sub(body_pattern, add_position, content, flags=re.DOTALL)
    
    return content

def process_file(filepath):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath.name}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Исправляем skip-link
        content = fix_skip_link_styles(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Исправлен skip-link в {filepath.name}")
            return True
        else:
            print(f"  - Без изменений {filepath.name}")
            return False
            
    except Exception as e:
        print(f"  ✗ Ошибка при обработке {filepath.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""
    repo_path = Path(__file__).parent
    
    print("Исправление skip-link во всех файлах...\n")
    
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
