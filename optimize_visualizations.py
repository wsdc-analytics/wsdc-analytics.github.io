#!/usr/bin/env python3
"""
Скрипт для оптимизации визуализаций данных во всех статьях
Применяет улучшения: тени для KPI, hover-эффекты, оптимизацию цветов
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

def optimize_data_visualizations(content):
    """Оптимизирует стили визуализаций данных"""
    
    # Заменяем цвета на CSS переменные в data-visualization
    replacements = [
        (r'background:\s*#ffffff\b', 'background: var(--bg-primary)'),
        (r'background:\s*#f7fafc\b', 'background: var(--bg-tertiary)'),
        (r'border:\s*1px solid #e2e8f0\b', 'border: 1px solid var(--border-color)'),
        (r'border-top:\s*1px solid #e2e8f0\b', 'border-top: 1px solid var(--border-color)'),
        (r'border-bottom:\s*1px solid #e2e8f0\b', 'border-bottom: 1px solid var(--border-color)'),
        (r'border-top:\s*2px solid #2d3748\b', 'border-top: 2px solid var(--color-primary)'),
        (r'color:\s*#2d3748\b', 'color: var(--text-primary)'),
        (r'color:\s*#718096\b', 'color: var(--text-tertiary)'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Улучшаем .data-visualization - добавляем border-radius и box-shadow если их нет
    if '.data-visualization {' in content and 'border-radius' not in content.split('.data-visualization {')[1].split('}')[0]:
        content = re.sub(
            r'(\.data-visualization\s*\{[^}]*)(overflow-x:\s*hidden;)',
            r'\1overflow-x: hidden;\n            border-radius: 8px;\n            box-shadow: var(--shadow-sm);',
            content,
            flags=re.DOTALL
        )
    
    # Улучшаем .kpi-card - добавляем улучшенные тени и hover если их нет
    if '.kpi-card {' in content:
        kpi_card_section = re.search(r'\.kpi-card\s*\{[^}]+\}', content, re.DOTALL)
        if kpi_card_section:
            kpi_card = kpi_card_section.group(0)
            if 'border-radius' not in kpi_card:
                kpi_card = kpi_card.replace(
                    'transition:',
                    'border-radius: 6px;\n            transition:'
                )
            if 'box-shadow: var(--shadow-sm)' not in kpi_card:
                kpi_card = kpi_card.replace(
                    'min-height:',
                    'box-shadow: var(--shadow-sm);\n            min-height:'
                )
            content = content.replace(kpi_card_section.group(0), kpi_card)
        
        # Улучшаем .kpi-card:hover
        if '.kpi-card:hover' in content and 'transform' not in content.split('.kpi-card:hover')[1].split('}')[0]:
            content = re.sub(
                r'(\.kpi-card:hover\s*\{[^}]*)(border-color:[^}]*)(\})',
                r'\1\2\n            transform: translateY(-2px);\3',
                content,
                flags=re.DOTALL
            )
    
    # Улучшаем .comparison-table - добавляем border-radius если его нет
    if '.comparison-table {' in content and 'border-radius' not in content.split('.comparison-table {')[1].split('}')[0]:
        content = re.sub(
            r'(\.comparison-table\s*\{[^}]*)(border:\s*1px[^}]*)(\})',
            r'\1\2\n            border-radius: 6px;\n            overflow: hidden;\n            box-shadow: var(--shadow-sm);\3',
            content,
            flags=re.DOTALL
        )
    
    # Улучшаем .comparison-table tbody tr:hover - добавляем визуальный индикатор
    if '.comparison-table tbody tr:hover' in content and 'box-shadow' not in content.split('.comparison-table tbody tr:hover')[1].split('}')[0]:
        content = re.sub(
            r'(\.comparison-table tbody tr:hover\s*\{[^}]*)(background:[^}]*)(\})',
            r'\1\2\n            box-shadow: inset 2px 0 0 var(--color-primary);\3',
            content,
            flags=re.DOTALL
        )
    
    # Улучшаем .bar-row - добавляем hover эффект если его нет
    if '.bar-row {' in content and ':hover' not in content.split('.bar-row {')[0].split('.bar-row:last-child')[0]:
        content = re.sub(
            r'(\.bar-row:last-child\s*\{[^}]+\})',
            r'''.bar-row:hover {
            transform: translateX(2px);
        }

        \1''',
            content
        )
    
    return content

def optimize_header_background(content):
    """Оптимизирует фоновые изображения в заголовках"""
    
    # Добавляем will-change и оптимизацию для .article-header
    if '.article-header {' in content and 'will-change' not in content.split('.article-header {')[1].split('}')[0]:
        content = re.sub(
            r'(\.article-header\s*\{[^}]*)(position:\s*relative;)',
            r'\1\2\n            will-change: transform;\n            background-attachment: scroll;',
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
        
        # Применяем оптимизации
        content = optimize_data_visualizations(content)
        content = optimize_header_background(content)
        
        # Сохраняем только если были изменения
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Оптимизированы визуализации в {filepath.name}")
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
    
    print("Оптимизация визуализаций данных во всех статьях...\n")
    
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
