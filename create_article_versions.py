#!/usr/bin/env python3
"""
Скрипт для создания трех версий статьи:
1. Русская: Global + European + Russian
2. Английская: Global + European + Sophisticated
3. Испанская: Global + European + Spanish
"""

import re
from pathlib import Path

HTML_FILE = Path('/Users/ania/.cursor/wsdc-analytics-repo/dancers_2025.html')

# Читаем исходный файл
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим границы секций
def find_section_boundaries(content):
    """Находит начало и конец каждой секции"""
    sections = {}
    
    # Section 1: Global Top (начинается с <!-- Section 1)
    # Section 2: Russian Top (начинается с <!-- Section 2)
    # Section 3: Sophisticated Top (начинается с <!-- Section 3)
    # Section 4: European Top (начинается с <!-- Section 4)
    # Section 5: Spanish Top (начинается с <section class="section"> после European)
    # Section 6: US Top (начинается с <!-- Section 6)
    
    patterns = {
        'intro': (r'<div class="intro">', r'</div>'),
        'global': (r'<!-- Section 1: Global Top', r'<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>'),
        'russian': (r'<!-- Section 2: Russian Top', r'<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>'),
        'sophisticated': (r'<!-- Section 3: Sophisticated Top', r'<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>'),
        'european': (r'<!-- Section 4: European Events Top', r'</section>'),
        'spanish': (r'<section class="section">\s*<h2 class="section-title">Топ-10 испанских танцоров</h2>', r'</section>'),
        'us': (r'<!-- Section 6: US Events Top', r'</section>'),
    }
    
    for name, (start_pattern, end_pattern) in patterns.items():
        start_match = re.search(start_pattern, content, re.DOTALL)
        if start_match:
            start_pos = start_match.start()
            # Ищем конец секции после начала
            remaining = content[start_pos:]
            end_match = re.search(end_pattern, remaining, re.DOTALL)
            if end_match:
                end_pos = start_pos + end_match.end()
                sections[name] = (start_pos, end_pos)
            else:
                # Если не нашли конец, берем до следующей секции или конца файла
                sections[name] = (start_pos, len(content))
    
    return sections

# Находим JavaScript данные
def find_js_data(content):
    """Находит JavaScript данные для каждой секции"""
    js_data = {}
    
    patterns = {
        'global': r"const globalMetricData = \{([^}]+)\};",
        'russian': r"const ruMetricData = \{([^}]+)\};",
        'sophisticated': r"const sophisticatedMetricData = \{([^}]+)\};",
        'european': r"const euMetricData = \{([^}]+)\};",
        'spanish': r"const esMetricData = \{([^}]+)\};",
        'us': r"const usMetricData = \{([^}]+)\};",
    }
    
    for name, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            js_data[name] = match.group(0)
    
    return js_data

# Находим функции переключения метрик
def find_metric_functions(content):
    """Находит функции переключения метрик"""
    functions = {}
    
    patterns = {
        'global': r'function switchGlobalMetric[^}]+}',
        'russian': r'function switchRuMetric[^}]+}',
        'sophisticated': r'function switchSophisticatedMetric[^}]+}',
        'european': r'function switchEuMetric[^}]+}',
        'spanish': r'function switchEsMetric[^}]+}',
        'us': r'function switchUsMetric[^}]+}',
    }
    
    for name, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            functions[name] = match.group(0)
    
    return functions

print("Анализ структуры файла...")
sections = find_section_boundaries(content)
js_data = find_js_data(content)
functions = find_metric_functions(content)

print(f"Найдено секций: {list(sections.keys())}")
print(f"Найдено JS данных: {list(js_data.keys())}")
print(f"Найдено функций: {list(functions.keys())}")

# Теперь создадим версии файлов
# Это будет сложная задача, требующая ручной работы с переводами
