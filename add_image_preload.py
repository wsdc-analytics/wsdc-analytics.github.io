#!/usr/bin/env python3
"""
Скрипт для добавления preload для фоновых изображений заголовков
"""

import re
from pathlib import Path

ARTICLE_CONFIG = {
    'overview_2025.html': 'overview_header_bg.png',
    'overview_2025_en.html': 'overview_header_bg.png',
    'overview_2025_es.html': 'overview_header_bg.png',
    'dancers_2025.html': 'dancers_header_bg.png',
    'dancers_2025_en.html': 'dancers_header_bg.png',
    'dancers_2025_es.html': 'dancers_header_bg.png',
    'dancers_2025_ru.html': 'dancers_header_bg.png',
    'geo_2025.html': 'wsdc_geo_wordcloud.png',
    'geo_2025_en.html': 'wsdc_geo_wordcloud.png',
    'geo_2025_es.html': 'wsdc_geo_wordcloud.png',
    'events_2025.html': 'events_background.png',
    'events_2025_en.html': 'events_background.png',
    'events_2025_es.html': 'events_background.png',
}

def add_image_preload(content, image_name):
    """Добавляет preload для изображения"""
    preload_tag = f'    <link rel="preload" href="{image_name}" as="image" fetchpriority="high">\n'
    
    # Проверяем, есть ли уже preload
    if f'preload.*{image_name}' in content or f'rel="preload".*{image_name}' in content:
        return content
    
    # Ищем место после resource hints или перед Twemoji
    if 'Resource hints' in content or 'resource hints' in content.lower():
        # Добавляем после resource hints
        pattern = r'(<!-- Resource hints[^>]*-->\s*<link[^>]*>)'
        replacement = r'\1\n' + preload_tag
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.DOTALL)
    elif 'preconnect' in content:
        # Добавляем после последнего preconnect/dns-prefetch
        pattern = r'(<link rel="(?:preconnect|dns-prefetch)"[^>]*>\s*)'
        replacement = r'\1' + preload_tag
        content = re.sub(pattern, replacement, content, count=1)
    else:
        # Добавляем перед Twemoji скриптом
        pattern = r'(<!--.*?Twemoji.*?-->\s*<script)'
        replacement = preload_tag + r'\1'
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.DOTALL, count=1)
    
    return content

def process_file(filepath, image_name):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath.name}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Добавляем preload
        content = add_image_preload(content, image_name)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Добавлен preload для {image_name} в {filepath.name}")
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
    
    print("Добавление preload для фоновых изображений...\n")
    
    updated_count = 0
    for filename, image_name in ARTICLE_CONFIG.items():
        filepath = repo_path / filename
        if filepath.exists():
            if process_file(filepath, image_name):
                updated_count += 1
        else:
            print(f"  ⚠ Файл не найден: {filename}")
    
    print(f"\n✓ Обработано файлов: {updated_count}/{len(ARTICLE_CONFIG)}")

if __name__ == '__main__':
    main()
