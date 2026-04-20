#!/usr/bin/env python3
"""
Проверка синхронизации всех данных между тремя языковыми версиями
"""

from bs4 import BeautifulSoup
import re

files = {
    'ru': '/Users/ania/.cursor/wsdc-analytics-repo/geo_2025.html',
    'en': '/Users/ania/.cursor/wsdc-analytics-repo/geo_2025_en.html',
    'es': '/Users/ania/.cursor/wsdc-analytics-repo/geo_2025_es.html'
}

def extract_table_data(soup, lang):
    """Извлекает данные из всех таблиц"""
    tables = soup.find_all('table', class_='rank-table')
    all_data = []
    
    for table in tables:
        rows = table.find_all('tr')[1:]  # Пропускаем заголовок
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                name = cells[1].get_text(strip=True)
                # Убираем флаги
                for emoji in cells[1].find_all('span', class_='event-flag'):
                    name = name.replace(emoji.get_text(strip=True), '').strip()
                # Убираем NEW и другие маркеры
                name = re.sub(r'\s*🆕\s*NEW\s*', '', name)
                name = re.sub(r'<[^>]+>', '', name)  # Убираем HTML теги
                
                try:
                    events = int(cells[2].get_text(strip=True).replace(',', ''))
                    points = int(cells[3].get_text(strip=True).replace(',', ''))
                    unique = int(cells[4].get_text(strip=True).replace(',', ''))
                    new = int(cells[5].get_text(strip=True).replace(',', ''))
                    
                    all_data.append({
                        'name': name,
                        'events': events,
                        'points': points,
                        'unique': unique,
                        'new': new
                    })
                except:
                    pass
    
    return all_data

def extract_text_numbers(soup):
    """Извлекает числа из текста статьи"""
    text = soup.get_text()
    # Ищем числа в контексте (например, "4280", "176 человек")
    numbers = []
    # Паттерны для поиска чисел в контексте метрик
    patterns = [
        r'(\d{1,3}(?:[,\s]\d{3})*)\s*(?:поинт|point|punto)',
        r'(\d{1,3}(?:[,\s]\d{3})*)\s*(?:уникальн|unique|único)',
        r'(\d{1,3}(?:[,\s]\d{3})*)\s*(?:нов|new|nuevo)',
        r'(\d{1,3}(?:[,\s]\d{3})*)\s*(?:ивент|event|evento)',
    ]
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            num_str = match.group(1).replace(',', '').replace(' ', '')
            try:
                numbers.append(int(num_str))
            except:
                pass
    return numbers

print("="*80)
print("ПРОВЕРКА СИНХРОНИЗАЦИИ ВСЕХ ВЕРСИЙ")
print("="*80)

all_data = {}
for lang, filepath in files.items():
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        all_data[lang] = extract_table_data(soup, lang)

# Группируем по именам (нормализуем названия)
def normalize_name(name):
    """Нормализует название для сравнения"""
    # Убираем лишние пробелы
    name = ' '.join(name.split())
    # Нормализуем известные варианты
    name_mapping = {
        'Washington, DC': 'Washington',
        'District of Columbia': 'DC',
        'Kraków': 'Krakow',
        'Krakow': 'Krakow',
    }
    for k, v in name_mapping.items():
        if k in name:
            return v
    return name.split(',')[0].strip() if ',' in name else name.strip()

# Группируем данные
grouped = {}
for lang, data_list in all_data.items():
    for item in data_list:
        key = normalize_name(item['name'])
        if key not in grouped:
            grouped[key] = {}
        if lang not in grouped[key]:
            grouped[key][lang] = []
        grouped[key][lang].append(item)

# Проверяем расхождения
print("\n📊 РАСХОЖДЕНИЯ В ТАБЛИЦАХ:")
print("="*80)

mismatches = []
for key, versions in sorted(grouped.items()):
    # Проверяем, что во всех версиях есть одинаковое количество записей
    counts = {lang: len(data) for lang, data in versions.items()}
    if len(set(counts.values())) > 1:
        print(f"\n⚠️  {key}: разное количество записей {counts}")
        continue
    
    # Для каждой записи проверяем значения
    for i in range(counts['ru'] if 'ru' in counts else 0):
        values = {}
        for lang in ['ru', 'en', 'es']:
            if lang in versions and i < len(versions[lang]):
                values[lang] = versions[lang][i]
        
        if len(values) < 3:
            continue
        
        ru_val = values['ru']
        en_val = values['en']
        es_val = values['es']
        
        # Проверяем каждое поле
        for field in ['events', 'points', 'unique', 'new']:
            ru_f = ru_val.get(field)
            en_f = en_val.get(field)
            es_f = es_val.get(field)
            
            if ru_f != en_f or ru_f != es_f or en_f != es_f:
                mismatch_key = f"{key}_{i}_{field}"
                if mismatch_key not in mismatches:
                    mismatches.append(mismatch_key)
                    print(f"\n  {key} (запись {i+1}), поле {field}:")
                    print(f"    RU: {ru_f}")
                    print(f"    EN: {en_f}")
                    print(f"    ES: {es_f}")

if not mismatches:
    print("✅ Все данные в таблицах синхронизированы!")
else:
    print(f"\n⚠️  Найдено {len(mismatches)} расхождений")

# Проверяем ключевые числа в тексте
print("\n" + "="*80)
print("ПРОВЕРКА КЛЮЧЕВЫХ ЧИСЕЛ В ТЕКСТЕ:")
print("="*80)

key_numbers = {
    'Germany/Germania/Германия': [176, 163],  # new, в сравнении с France
    'Sweden/Suecia/Швеция': [111],  # new
    'France/Francia/Франция': [4280, 600, 163],  # points, unique, new
}

for key_pattern, expected_values in key_numbers.items():
    print(f"\n{key_pattern}:")
    for lang, filepath in files.items():
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            text = soup.get_text()
            # Ищем числа рядом с названием страны
            for val in expected_values:
                pattern = rf'{re.escape(key_pattern.split("/")[0 if lang=="en" else (1 if lang=="es" else 2)])}.*?{val}|{val}.*?{re.escape(key_pattern.split("/")[0 if lang=="en" else (1 if lang=="es" else 2)])}'
                if re.search(pattern, text, re.IGNORECASE):
                    print(f"  {lang.upper()}: ✓ {val} найден")
                else:
                    print(f"  {lang.upper()}: ✗ {val} НЕ найден")

