#!/usr/bin/env python3
"""
Скрипт для применения улучшений дизайна ко всем HTML файлам статей.
Применяет: CSS custom properties, улучшение контраста, ARIA-метки, оптимизацию загрузки.
"""

import re
import os
from pathlib import Path

# Список файлов для обработки
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

def apply_css_variables(content):
    """Добавляет CSS custom properties в начало стилей"""
    css_vars = """        :root {
            /* Основные цвета */
            --color-primary: #2d3748;
            --color-primary-dark: #1a202c;
            --color-primary-light: #4a5568;
            
            /* Фоны */
            --bg-primary: #ffffff;
            --bg-secondary: #fafafa;
            --bg-tertiary: #f7fafc;
            
            /* Текст - улучшенный контраст */
            --text-primary: #2d3748;
            --text-secondary: #4a5568;
            --text-tertiary: #718096;
            
            /* Границы */
            --border-color: #e5e5e5;
            --border-color-hover: #cbd5e0;
            
            /* Тени */
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
            
            /* Переходы */
            --transition-fast: 0.15s ease;
            --transition-base: 0.2s ease;
            --transition-slow: 0.3s ease;
        }

"""
    
    # Добавляем skip link стили
    skip_link_css = """        /* Skip link для доступности */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: var(--color-primary);
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            z-index: 100;
            border-radius: 0 0 4px 0;
        }
        .skip-link:focus {
            top: 0;
        }

"""
    
    # Ищем начало <style> и добавляем переменные после него
    if '<style>' in content:
        # Добавляем переменные после <style>
        content = content.replace('<style>', '<style>\n' + css_vars + skip_link_css, 1)
    
    return content

def replace_colors(content):
    """Заменяет хардкод цвета на CSS переменные"""
    replacements = [
        (r'color:\s*#666\b', 'color: var(--text-secondary)'),
        (r'color:\s*#2d3748\b', 'color: var(--text-primary)'),
        (r'background-color:\s*#ffffff\b', 'background-color: var(--bg-primary)'),
        (r'background-color:\s*#fafafa\b', 'background-color: var(--bg-secondary)'),
        (r'background-color:\s*#f7fafc\b', 'background-color: var(--bg-tertiary)'),
        (r'border:\s*1px solid #e5e5e5\b', 'border: 1px solid var(--border-color)'),
        (r'border-top:\s*1px solid #e5e5e5\b', 'border-top: 1px solid var(--border-color)'),
        (r'border-bottom:\s*1px solid #e5e5e5\b', 'border-bottom: 1px solid var(--border-color)'),
        (r'border-top:\s*2px solid #2d3748\b', 'border-top: 2px solid var(--color-primary)'),
        (r'border-left:\s*3px solid #2d3748\b', 'border-left: 3px solid var(--color-primary)'),
        (r'border-left:\s*4px solid #2d3748\b', 'border-left: 4px solid var(--color-primary)'),
        (r'background:\s*#2d3748\b', 'background: var(--color-primary)'),
        (r'transition:\s*all 0\.2s ease\b', 'transition: all var(--transition-base)'),
        (r'transition:\s*opacity 0\.2s ease\b', 'transition: opacity var(--transition-base)'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def add_resource_hints(content):
    """Добавляет resource hints перед Twemoji скриптом"""
    resource_hints = """    <!-- Resource hints для оптимизации производительности -->
    <link rel="preconnect" href="https://unpkg.com">
    <link rel="dns-prefetch" href="https://unpkg.com">
    
"""
    
    # Ищем Twemoji скрипт и добавляем hints перед ним
    if 'twemoji' in content.lower() and 'preconnect' not in content:
        content = re.sub(
            r'(<!--.*?Twemoji.*?-->\s*<script[^>]*twemoji[^>]*>)',
            resource_hints + r'\1',
            content,
            flags=re.IGNORECASE | re.DOTALL
        )
        # Добавляем defer к Twemoji
        content = re.sub(
            r'(<script[^>]*twemoji[^>]*)(>)',
            r'\1 defer\2',
            content,
            flags=re.IGNORECASE
        )
    
    return content

def add_skip_link(content):
    """Добавляет skip link в начало body"""
    skip_link = '<a href="#main-content" class="skip-link">Перейти к содержимому</a>\n    '
    
    if '<body>' in content and 'skip-link' not in content:
        content = content.replace('<body>', '<body>\n    ' + skip_link, 1)
    
    return content

def add_main_tag(content):
    """Добавляет <main> тег вокруг article-content"""
    if '<article class="article-content">' in content and '<main' not in content:
        content = content.replace(
            '<article class="article-content">',
            '<main id="main-content">\n        <article class="article-content">',
            1
        )
        # Закрываем main перед закрытием article или перед footer
        if '</article>' in content:
            content = re.sub(
                r'(</article>)(\s*</div>|\s*<footer)',
                r'\1\n        </main>\2',
                content,
                count=1
            )
    
    return content

def add_aria_labels(content):
    """Добавляет ARIA-метки для кнопок языка"""
    # Улучшаем кнопки языка
    lang_button_pattern = r'(<button[^>]*data-lang="([^"]+)"[^>]*class="[^"]*lang-btn[^"]*"[^>]*>)([^<]+)(</button>)'
    
    def replace_lang_button(match):
        full_tag = match.group(0)
        lang = match.group(2)
        text = match.group(3)
        
        # Определяем aria-label в зависимости от языка
        aria_labels = {
            'ru': 'Переключить на русский язык',
            'en': 'Switch to English',
            'es': 'Cambiar a español'
        }
        aria_label = aria_labels.get(lang, f'Switch to {lang.upper()}')
        
        # Проверяем, есть ли уже aria-label
        if 'aria-label' not in full_tag:
            # Добавляем aria-label и aria-pressed
            if 'active' in full_tag:
                aria_pressed = 'true'
            else:
                aria_pressed = 'false'
            
            # Вставляем атрибуты перед закрывающей скобкой открывающего тега
            new_tag = re.sub(
                r'(>)([^<]+</button>)',
                f' aria-label="{aria_label}" aria-pressed="{aria_pressed}">\\2',
                full_tag
            )
            return new_tag
        
        return full_tag
    
    content = re.sub(lang_button_pattern, replace_lang_button, content)
    
    # Добавляем role="group" к language-switcher
    content = re.sub(
        r'(<div[^>]*class="[^"]*language-switcher[^"]*"[^>]*)>',
        r'\1 role="group" aria-label="Выбор языка">',
        content
    )
    
    return content

def improve_button_styles(content):
    """Улучшает стили кнопок с focus состояниями"""
    # Добавляем focus стили для language-switcher buttons
    if '.language-switcher-article button' in content and ':focus' not in content:
        # Ищем блок стилей для кнопок и добавляем focus
        content = re.sub(
            r'(\.language-switcher-article button\.active\s*\{[^}]+\})',
            r'''.language-switcher-article button:focus {
            outline: 2px solid white;
            outline-offset: 2px;
        }

        \1''',
            content
        )
    
    return content

def process_file(filepath):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Применяем все улучшения
        content = apply_css_variables(content)
        content = replace_colors(content)
        content = add_resource_hints(content)
        content = add_skip_link(content)
        content = add_main_tag(content)
        content = add_aria_labels(content)
        content = improve_button_styles(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Обновлен {filepath}")
            return True
        else:
            print(f"  - Без изменений {filepath}")
            return False
            
    except Exception as e:
        print(f"  ✗ Ошибка при обработке {filepath}: {e}")
        return False

def main():
    """Главная функция"""
    repo_path = Path(__file__).parent
    
    print("Применение улучшений дизайна к статьям...\n")
    
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
