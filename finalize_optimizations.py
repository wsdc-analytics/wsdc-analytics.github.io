#!/usr/bin/env python3
"""
Финальные оптимизации: улучшения для таблиц и производительности
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

def improve_table_styles(content):
    """Улучшает стили таблиц"""
    
    # Улучшаем .comparison-table tbody tr - добавляем transition и cursor
    if '.comparison-table tbody tr:hover' in content:
        # Проверяем, есть ли уже transition для tr
        tr_selector = '.comparison-table tbody tr'
        if tr_selector in content:
            tr_section = re.search(rf'{re.escape(tr_selector)}\s*{{[^}}]*}}', content, re.DOTALL)
            if tr_section and 'transition' not in tr_section.group(0):
                new_tr_style = tr_section.group(0).replace(
                    '{',
                    '{\n            transition: background-color var(--transition-fast), box-shadow var(--transition-fast);\n            cursor: default;'
                )
                content = content.replace(tr_section.group(0), new_tr_style)
        
        # Добавляем улучшения для ячеек при hover
        if '.comparison-table tbody tr:nth-child(even):hover' in content:
            # Проверяем, есть ли уже стили для hover ячеек
            if '.comparison-table tbody tr:hover td.metric-value' not in content:
                insert_point = content.find('.comparison-table tbody tr:nth-child(even):hover')
                if insert_point > 0:
                    # Находим закрывающую скобку этого правила
                    brace_pos = content.find('}', insert_point)
                    if brace_pos > 0:
                        new_styles = '''

        /* Улучшенные hover-эффекты для ячеек таблицы */
        .comparison-table td {
            position: relative;
        }

        .comparison-table tbody tr:hover td.metric-value,
        .comparison-table tbody tr:hover td.metric-change {
            font-weight: 700;
        }'''
                        content = content[:brace_pos+1] + new_styles + content[brace_pos+1:]
    
    return content

def improve_bar_chart_styles(content):
    """Улучшает стили bar charts"""
    
    if '.bar-row:hover' in content and '.bar-row:hover .bar-label' not in content:
        # Добавляем улучшения для label при hover
        hover_section = re.search(r'\.bar-row:hover\s*\{[^}}]*}}', content, re.DOTALL)
        if hover_section:
            insert_pos = content.find(hover_section.group(0)) + len(hover_section.group(0))
            new_styles = '''

        .bar-row:hover .bar-label {
            font-weight: 600;
            color: var(--color-primary);
        }'''
            content = content[:insert_pos] + new_styles + content[insert_pos:]
    
    # Добавляем cursor: default если его нет
    if '.bar-row {' in content and 'cursor' not in content.split('.bar-row {')[1].split('}')[0]:
        content = re.sub(
            r'(\.bar-row\s*\{[^}]*)(padding:[^}]*)(\})',
            r'\1\2\n            cursor: default;\3',
            content,
            flags=re.DOTALL
        )
    
    return content

def process_file(filepath):
    """Обрабатывает один файл"""
    print(f"Обработка {filepath.name}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Применяем улучшения
        content = improve_table_styles(content)
        content = improve_bar_chart_styles(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Улучшены стили в {filepath.name}")
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
    
    print("Финальные оптимизации стилей...\n")
    
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
