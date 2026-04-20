#!/usr/bin/env python3
"""
Скрипт для добавления ARIA-меток к кнопкам переключения языка
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

def add_aria_to_buttons(content):
    """Добавляет ARIA-метки к кнопкам языка"""
    
    # Определяем aria-label в зависимости от языка кнопки
    def get_aria_label(lang):
        labels = {
            'ru': 'Переключить на русский язык',
            'en': 'Switch to English',
            'es': 'Cambiar a español'
        }
        return labels.get(lang, f'Switch to {lang.upper()}')
    
    # Заменяем кнопки без aria-label
    def replace_button(match):
        full_tag = match.group(0)
        lang = match.group(1)
        is_active = 'active' in full_tag
        
        # Если уже есть aria-label, не трогаем
        if 'aria-label' in full_tag:
            return full_tag
        
        # Определяем aria-pressed
        aria_pressed = 'true' if is_active else 'false'
        aria_label = get_aria_label(lang)
        
        # Добавляем атрибуты перед закрывающей скобкой
        new_tag = re.sub(
            r'(data-lang="[^"]+")(\s*>)',
            f'\\1 aria-label="{aria_label}" aria-pressed="{aria_pressed}"\\2',
            full_tag
        )
        return new_tag
    
    # Паттерн для кнопок языка
    pattern = r'<button\s+class="[^"]*lang-btn-article[^"]*"\s+data-lang="(ru|en|es)"[^>]*>'
    content = re.sub(pattern, replace_button, content)
    
    return content

def process_file(filepath):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath.name}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Добавляем ARIA-метки
        content = add_aria_to_buttons(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Добавлены ARIA-метки в {filepath.name}")
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
    
    print("Добавление ARIA-меток к кнопкам языка...\n")
    
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
