#!/usr/bin/env python3
"""
Скрипт для создания трех версий статьи:
1. Русская: Global + European + Russian
2. Английская: Global + European + Sophisticated
3. Испанская: Global + European + Spanish
"""

import re
from pathlib import Path

HTML_FILE = Path('dancers_2025.html')
OUTPUT_DIR = Path('.')

# Читаем исходный файл
print("Чтение исходного файла...")
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим границы секций
def find_section(content, start_marker, end_marker=None):
    """Находит секцию между маркерами"""
    start_pos = content.find(start_marker)
    if start_pos == -1:
        return None
    
    if end_marker:
        # Ищем конец секции
        end_pos = content.find(end_marker, start_pos)
        if end_pos == -1:
            # Если не нашли конец, берем до следующего <hr> или </section>
            end_pos = content.find('<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>', start_pos)
            if end_pos == -1:
                end_pos = content.find('</section>', start_pos)
            if end_pos != -1:
                end_pos += len('</section>')
        else:
            end_pos += len(end_marker)
    else:
        # Берем до конца файла или до следующей секции
        end_pos = len(content)
    
    return content[start_pos:end_pos] if start_pos != -1 else None

# Извлекаем части файла
print("Извлечение секций...")

# Header (до начала article-content)
header_end = content.find('<article class="article-content">')
header = content[:header_end] if header_end != -1 else content[:1000]

# Intro
intro_start = content.find('<div class="intro">')
intro_end = content.find('</div>', intro_start) + len('</div>')
intro = content[intro_start:intro_end] if intro_start != -1 else ""

# Global section
global_section = find_section(content, '<!-- Section 1: Global Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')

# Russian section  
russian_section = find_section(content, '<!-- Section 2: Russian Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')

# Sophisticated section
sophisticated_section = find_section(content, '<!-- Section 3: Sophisticated Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')

# European section
european_section = find_section(content, '<!-- Section 4: European Events Top', '</section>')

# Spanish section
spanish_start = content.find('<section class="section">\n<h2 class="section-title">Топ-10 испанских танцоров</h2>')
spanish_section = None
if spanish_start != -1:
    # Находим конец секции
    spanish_end = content.find('</section>', spanish_start)
    if spanish_end != -1:
        spanish_end += len('</section>')
        spanish_section = content[spanish_start:spanish_end]

# Footer и скрипты (от footer до конца)
footer_start = content.find('<footer class="article-footer">')
footer_and_scripts = content[footer_start:] if footer_start != -1 else ""

# JavaScript данные и функции
js_start = content.find('<script>')
js_end = content.rfind('</script>') + len('</script>')
js_section = content[js_start:js_end] if js_start != -1 and js_end > js_start else ""

print(f"Header: {len(header)} символов")
print(f"Intro: {len(intro)} символов")
print(f"Global: {len(global_section) if global_section else 0} символов")
print(f"Russian: {len(russian_section) if russian_section else 0} символов")
print(f"Sophisticated: {len(sophisticated_section) if sophisticated_section else 0} символов")
print(f"European: {len(european_section) if european_section else 0} символов")
print(f"Spanish: {len(spanish_section) if spanish_section else 0} символов")
print(f"Footer: {len(footer_and_scripts)} символов")

# Создаем русскую версию (Global + European + Russian)
print("\nСоздание русской версии...")
ru_content = header + intro + "\n"
if global_section:
    ru_content += global_section + "\n<hr style=\"border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;\"/>\n"
if european_section:
    ru_content += european_section + "\n<hr style=\"border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;\"/>\n"
if russian_section:
    ru_content += russian_section + "\n"
ru_content += "\n</article>\n" + footer_and_scripts

# Обновляем метаданные для русской версии
ru_content = re.sub(r'<html lang="ru">', '<html lang="ru">', ru_content)
ru_content = re.sub(r'dancers_2025\.html', 'dancers_2025_ru.html', ru_content)

with open(OUTPUT_DIR / 'dancers_2025_ru.html', 'w', encoding='utf-8') as f:
    f.write(ru_content)
print("✅ Русская версия создана: dancers_2025_ru.html")

print("\n⚠️  Английская и испанская версии требуют переводов.")
print("   Создана только русская версия. Переводы нужно добавить вручную.")
