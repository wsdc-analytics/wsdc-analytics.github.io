#!/usr/bin/env python3
"""
Скрипт для обновления JavaScript кода для синхронизации aria-pressed атрибутов
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

def update_language_switcher_js(content):
    """Обновляет JavaScript для обновления aria-pressed в кнопках языка"""
    
    # Паттерн 1: btn.classList.add('active') без aria-pressed
    pattern1 = r'(if\s*\(btn\.dataset\.lang\s*===\s*currentLang\)\s*\{[^}]*btn\.classList\.add\([\'"]active[\'"]\);[^}]*\})\s*else\s*\{[^}]*btn\.disabled\s*=\s*false;[^}]*\})'
    
    replacement1 = r'''if (btn.dataset.lang === currentLang) {
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.disabled = false;
                btn.setAttribute('aria-pressed', 'false');
            }'''
    
    content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
    
    # Паттерн 2: btn.classList.remove/add в цикле
    pattern2 = r'(btn\.classList\.remove\([\'"]active[\'"]\);\s*if\s*\(btn\.dataset\.lang\s*===\s*currentLang\)\s*\{[^}]*btn\.classList\.add\([\'"]active[\'"]\);[^}]*\})'
    
    replacement2 = r'''btn.classList.remove('active');
            btn.setAttribute('aria-pressed', 'false');
            if (btn.dataset.lang === currentLang) {
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            }'''
    
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    # Паттерн 3: для dancers статей с множественными переключателями
    pattern3 = r'(btn\.classList\.add\([\'"]active[\'"]\);\s*\}\s*else\s*\{[^}]*btn\.classList\.remove\([\'"]active[\'"]\);)'
    
    replacement3 = r'''btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-pressed', 'false');'''
    
    content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)
    
    return content

def process_file(filepath):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath.name}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Обновляем JavaScript
        content = update_language_switcher_js(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Обновлен JavaScript в {filepath.name}")
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
    
    print("Обновление ARIA атрибутов в JavaScript...\n")
    
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
