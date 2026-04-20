#!/usr/bin/env python3
"""
Проверка всех значений "New" в статье и сравнение с правильными расчетами
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

REGION_MAP = {
    'United States': 'North America',
    'Canada': 'North America',
    'Mexico': 'North America',
    'United Kingdom': 'Europe',
    'France': 'Europe',
    'Germany': 'Europe',
    'Russia': 'Europe',
    'Poland': 'Europe',
    'Hungary': 'Europe',
    'Sweden': 'Europe',
    'Finland': 'Europe',
    'Norway': 'Europe',
    'Austria': 'Europe',
    'Switzerland': 'Europe',
    'Netherlands': 'Europe',
    'Belgium': 'Europe',
    'Italy': 'Europe',
    'Spain': 'Europe',
    'Czech Republic': 'Europe',
    'Ukraine': 'Europe',
    'Estonia': 'Europe',
    'Latvia': 'Europe',
    'Lithuania': 'Europe',
    'Romania': 'Europe',
    'Ireland': 'Europe',
    'Portugal': 'Europe',
    'Bulgaria': 'Europe',
    'Slovenia': 'Europe',
    'Belarus': 'Europe',
    'Australia': 'Oceania',
    'New Zealand': 'Oceania',
    'Singapore': 'Asia',
    'South Korea': 'Asia',
    'Malaysia': 'Asia',
    'Japan': 'Asia',
    'China': 'Asia',
    'Taiwan': 'Asia',
    'Israel': 'Asia',
    'Turkey': 'Europe',
    'Brazil': 'South America',
    'Argentina': 'South America',
}

# 1. Build Event Location Map
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

# 2. Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025
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

# 3. Определяем локацию ПЕРВЫХ поинтов для новых танцоров
dancer_first_city = {}
dancer_first_state = {}
dancer_first_country = {}

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
        if dancer_id not in dancer_first_state:
            dancer_first_state[dancer_id] = {'state': None, 'month': 13}
        if dancer_id not in dancer_first_country:
            dancer_first_country[dancer_id] = {'country': None, 'month': 13}
        
        if month < dancer_first_city[dancer_id]['month']:
            if city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                dancer_first_city[dancer_id] = {'city_key': city_key, 'month': month}
        
        if month < dancer_first_state[dancer_id]['month']:
            if country == 'United States' and state:
                dancer_first_state[dancer_id] = {'state': state, 'month': month}
        
        if month < dancer_first_country[dancer_id]['month']:
            if country:
                dancer_first_country[dancer_id] = {'country': country, 'month': month}

# 4. Собираем статистику
stats_country = defaultdict(lambda: {'new_dancers_set': set()})
stats_state = defaultdict(lambda: {'new_dancers_set': set()})
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
            is_new_for_state = False
            is_new_for_country = False
            
            if dancer_id in dancer_first_city and dancer_first_city[dancer_id]['city_key']:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                if city_key == dancer_first_city[dancer_id]['city_key']:
                    is_new_for_city = True
            
            if dancer_id in dancer_first_state and dancer_first_state[dancer_id]['state']:
                if country == 'United States' and state == dancer_first_state[dancer_id]['state']:
                    is_new_for_state = True
            
            if dancer_id in dancer_first_country and dancer_first_country[dancer_id]['country']:
                if country == dancer_first_country[dancer_id]['country']:
                    is_new_for_country = True
            
            if is_new_for_city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                stats_city[city_key]['new_dancers_set'].add(dancer_id)
            if is_new_for_state and country == 'United States' and state:
                stats_state[state]['new_dancers_set'].add(dancer_id)
            if is_new_for_country:
                stats_country[country]['new_dancers_set'].add(dancer_id)

# 5. Извлекаем данные из статьи
with open(filename_article, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

article_cities = {}
article_states = {}
article_countries = {}

# Извлекаем данные из таблиц
tables = soup.find_all('table', class_='rank-table')
for table in tables:
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 6:
            name_cell = cells[1]
            # Убираем флаги и лишнее
            name = name_cell.get_text(strip=True)
            # Убираем флаги эмодзи
            for emoji in name_cell.find_all('span', class_='event-flag'):
                name = name.replace(emoji.get_text(strip=True), '').strip()
            
            try:
                events = int(cells[2].get_text(strip=True).replace(',', ''))
                points = int(cells[3].get_text(strip=True).replace(',', ''))
                unique = int(cells[4].get_text(strip=True).replace(',', ''))
                new = int(cells[5].get_text(strip=True).replace(',', ''))
                
                # Определяем тип таблицы по контексту
                if 'Stockholm' in name or 'Budapest' in name or 'Washington' in name or 'Freiburg' in name or 'Kraków' in name or 'Krakow' in name:
                    article_cities[name] = {'events': events, 'points': points, 'unique': unique, 'new': new}
                elif name in ['CA', 'TX', 'FL', 'OR', 'MA', 'IL', 'GA', 'AZ', 'NC', 'DC', 'WA', 'District of Columbia']:
                    article_states[name] = {'events': events, 'points': points, 'unique': unique, 'new': new}
                elif name in ['France', 'Germany', 'Sweden', 'Poland', 'Russia', 'United Kingdom', 'Hungary', 'Canada', 'Finland', 'Spain', 'Austria', 'Italy']:
                    article_countries[name] = {'events': events, 'points': points, 'unique': unique, 'new': new}
            except:
                pass

# 6. Сравниваем
print("="*80)
print("ПРОВЕРКА ЗНАЧЕНИЙ 'NEW' В СТАТЬЕ")
print("="*80)

def normalize_city_name(correct_key, article_name):
    """Нормализует названия для сравнения"""
    # Убираем "United States" из correct_key для сравнения
    correct_short = correct_key.replace(', United States', '').replace('Kraków', 'Krakow')
    article_short = article_name.replace('Kraków', 'Krakow')
    
    # Проверяем частичные совпадения
    if correct_short.split(',')[0].strip().lower() == article_short.split(',')[0].strip().lower():
        return True
    return False

print("\n📊 ГОРОДА:")
print(f"{'Название (статья)':<35} | {'В статье':<8} | {'Правильно':<8} | {'Разница':<8}")
print("-" * 70)
for article_name, article_data in sorted(article_cities.items()):
    article_new = article_data['new']
    
    # Ищем соответствующий ключ в правильных данных
    correct_key = None
    for city_key in stats_city.keys():
        if normalize_city_name(city_key, article_name):
            correct_key = city_key
            break
    
    if correct_key:
        correct_new = len(stats_city[correct_key]['new_dancers_set'])
        if article_new != correct_new:
            diff = correct_new - article_new
            print(f"{article_name:<35} | {article_new:<8} | {correct_new:<8} | {diff:+d}")

print("\n📊 ШТАТЫ США:")
print(f"{'Название':<20} | {'В статье':<8} | {'Правильно':<8} | {'Разница':<8}")
print("-" * 50)
for state_name, article_data in sorted(article_states.items()):
    article_new = article_data['new']
    # Нормализуем название штата
    state_key = state_name
    if state_name == 'District of Columbia':
        state_key = 'DC'
    
    if state_key in stats_state:
        correct_new = len(stats_state[state_key]['new_dancers_set'])
        if article_new != correct_new:
            diff = correct_new - article_new
            print(f"{state_name:<20} | {article_new:<8} | {correct_new:<8} | {diff:+d}")

print("\n📊 СТРАНЫ:")
print(f"{'Название':<20} | {'В статье':<8} | {'Правильно':<8} | {'Разница':<8}")
print("-" * 50)
for country_name, article_data in sorted(article_countries.items()):
    article_new = article_data['new']
    if country_name in stats_country:
        correct_new = len(stats_country[country_name]['new_dancers_set'])
        if article_new != correct_new:
            diff = correct_new - article_new
            print(f"{country_name:<20} | {article_new:<8} | {correct_new:<8} | {diff:+d}")

# 7. Выводим полные данные для проверки
print("\n" + "="*80)
print("ПОЛНЫЕ ДАННЫЕ ДЛЯ ПРОВЕРКИ:")
print("="*80)
print("\nГОРОДА (топ-10):")
city_items = [(k, len(v['new_dancers_set'])) for k, v in stats_city.items()]
city_items.sort(key=lambda x: x[1], reverse=True)
for city_key, new_count in city_items[:10]:
    # Ищем в статье
    article_match = None
    for article_name in article_cities:
        if normalize_city_name(city_key, article_name):
            article_match = article_cities[article_name]['new']
            break
    match_str = f" (в статье: {article_match})" if article_match else " (нет в статье)"
    print(f"  {city_key:<40} -> {new_count:>3} новых{match_str}")

