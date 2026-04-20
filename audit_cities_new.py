#!/usr/bin/env python3
"""
Детальная проверка значений "New" для всех городов из статьи
"""

import csv
import sys
from collections import defaultdict
from bs4 import BeautifulSoup

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'
filename_article = '/Users/ania/.cursor/wsdc-analytics-repo/geo_2025.html'

MANUAL_LOCATIONS = {
    'Scandinavian Open': 'Stockholm, Sweden',
    'Scandinavian Open WCS': 'Stockholm, Sweden',
    'Scandinavian Open WCS 2022': 'Stockholm, Sweden',
    'Scandinavian Open WCS "SNOW"': 'Stockholm, Sweden',
}

EVENT_NAME_MAPPING = {
    'Worlds UCWDC': 'UCWDC Country Dance World Championship',
}

# Build Event Location Map
event_geo_map = {}
with open(filename_events, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['name'].strip()
        loc = row.get('location', '').strip()
        if name and loc:
            city, state, country = normalize_location(loc)
            if country:
                event_geo_map[name] = {
                    'city': city,
                    'state': state,
                    'country': country,
                    'raw_loc': loc
                }

for name, loc_str in MANUAL_LOCATIONS.items():
    city, state, country = normalize_location(loc_str)
    event_geo_map[name] = {
        'city': city,
        'state': state,
        'country': country,
        'raw_loc': loc_str
    }

# Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025
dancer_first_year_ever = {}
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        if dancer_id not in dancer_first_year_ever or year < dancer_first_year_ever[dancer_id]:
            dancer_first_year_ever[dancer_id] = year

new_dancers_2025_global = {d for d, y in dancer_first_year_ever.items() if y == 2025}

# Определяем локацию ПЕРВЫХ поинтов для новых танцоров
dancer_first_city = {}

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        dancer_id = row['dancer_id']
        if dancer_id not in new_dancers_2025_global:
            continue
        try:
            points = int(row['event_points'])
        except:
            points = 0
        if points <= 0:
            continue
        
        event_name = row['event_name']
        month = int(row.get('event_month', 1))
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        if not geo:
            continue
        
        city = geo['city']
        state = geo['state']
        country = geo['country']
        
        if dancer_id not in dancer_first_city:
            dancer_first_city[dancer_id] = {'city_key': None, 'month': 13}
        
        if month < dancer_first_city[dancer_id]['month']:
            if city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                dancer_first_city[dancer_id] = {'city_key': city_key, 'month': month}

# Собираем статистику для городов
stats_city = defaultdict(lambda: {'new_dancers_set': set()})

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue

        event_name = row['event_name']
        dancer_id = row['dancer_id']
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        if not geo:
            continue

        city = geo['city']
        state = geo['state']
        country = geo['country']
        
        if dancer_id in new_dancers_2025_global:
            is_new_for_city = False
            
            if dancer_id in dancer_first_city and dancer_first_city[dancer_id]['city_key']:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                if city_key == dancer_first_city[dancer_id]['city_key']:
                    is_new_for_city = True
            
            if is_new_for_city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                stats_city[city_key]['new_dancers_set'].add(dancer_id)

# Извлекаем данные из статьи
with open(filename_article, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

article_cities = {}

# Находим таблицу городов
tables = soup.find_all('table', class_='rank-table')
for table in tables:
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 6:
            name_cell = cells[1]
            name = name_cell.get_text(strip=True)
            # Убираем флаги эмодзи
            for emoji in name_cell.find_all('span', class_='event-flag'):
                name = name.replace(emoji.get_text(strip=True), '').strip()
            
            try:
                events = int(cells[2].get_text(strip=True).replace(',', ''))
                points = int(cells[3].get_text(strip=True).replace(',', ''))
                unique = int(cells[4].get_text(strip=True).replace(',', ''))
                new = int(cells[5].get_text(strip=True).replace(',', ''))
                
                # Проверяем, это город (если содержит известные города или это не штат/страна)
                if any(city_name in name for city_name in ['Stockholm', 'Budapest', 'Washington', 'San Francisco', 'Boston', 'Orlando', 'Atlanta', 'Freiburg', 'Phoenix', 'Kraków', 'Krakow', 'Seattle', 'Portland', 'Denver', 'Austin', 'Chicago', 'Los Angeles', 'New York']):
                    article_cities[name] = {'events': events, 'points': points, 'unique': unique, 'new': new}
            except:
                pass

# Функция нормализации названий для сравнения
def normalize_city_name_for_match(correct_key, article_name):
    """Нормализует названия городов для сравнения"""
    # Убираем "United States" из correct_key
    correct_parts = correct_key.replace(', United States', '').split(',')
    correct_city = correct_parts[0].strip()
    
    # Убираем флаги и нормализуем article_name
    article_city = article_name.split(',')[0].strip()
    
    # Специальные случаи
    city_mapping = {
        'Kraków': 'Krakow',
        'Krakow': 'Kraków',
    }
    
    correct_city_norm = city_mapping.get(correct_city, correct_city)
    article_city_norm = city_mapping.get(article_city, article_city)
    
    # Проверяем совпадение
    if correct_city_norm.lower() == article_city_norm.lower():
        return True
    
    # Проверяем частичные совпадения
    if correct_city.lower() in article_city.lower() or article_city.lower() in correct_city.lower():
        return True
    
    return False

# Сравниваем
print("="*80)
print("ПРОВЕРКА ЗНАЧЕНИЙ 'NEW' ДЛЯ ГОРОДОВ ИЗ СТАТЬИ")
print("="*80)

print(f"\n{'Название (статья)':<35} | {'В статье':<8} | {'Правильно':<8} | {'Разница':<8}")
print("-" * 70)

mismatches = []
for article_name, article_data in sorted(article_cities.items()):
    article_new = article_data['new']
    
    # Ищем соответствующий ключ в правильных данных
    correct_key = None
    correct_new = None
    
    for city_key in stats_city.keys():
        if normalize_city_name_for_match(city_key, article_name):
            correct_key = city_key
            correct_new = len(stats_city[city_key]['new_dancers_set'])
            break
    
    if correct_key:
        if article_new != correct_new:
            diff = correct_new - article_new
            print(f"{article_name:<35} | {article_new:<8} | {correct_new:<8} | {diff:+d}")
            mismatches.append({
                'article_name': article_name,
                'article_new': article_new,
                'correct_key': correct_key,
                'correct_new': correct_new,
                'diff': diff
            })
    else:
        print(f"{article_name:<35} | {article_new:<8} | {'NOT FOUND':<8} | {'?':<8}")

if not mismatches:
    print("\n✅ Все значения 'New' для городов корректны!")
else:
    print(f"\n⚠️  Найдено {len(mismatches)} расхождений")

# Выводим все города из статьи для справки
print("\n" + "="*80)
print("ВСЕ ГОРОДА ИЗ СТАТЬИ:")
print("="*80)
for name, data in sorted(article_cities.items()):
    print(f"  {name:<35} | Events: {data['events']:<3} | Points: {data['points']:<6} | Unique: {data['unique']:<4} | New: {data['new']}")

