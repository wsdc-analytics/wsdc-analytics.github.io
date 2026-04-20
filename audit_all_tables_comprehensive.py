#!/usr/bin/env python3
"""
Комплексная проверка всех таблиц с правильной логикой:
- Новые танцоры учитываются, если они получили первые поинты ВООБЩЕ в 2025
- Локация первых поинтов определяется по ВСЕМ номинациям (включая Sophisticated/Masters)
- Новый танцор считается "новым" для локации, где он получил первые поинты (любая номинация)
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

print("="*80)
print("КОМПЛЕКСНАЯ ПРОВЕРКА ВСЕХ ТАБЛИЦ")
print("Логика: Новые танцоры = получили первые поинты ВООБЩЕ в 2025 (все номинации)")
print("="*80)

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

# 2. Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025 (ВСЕ номинации)
print("\n📊 Шаг 1: Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025...")
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
print(f"  Танцоров, которые получили первые поинты ВООБЩЕ в 2025: {len(new_dancers_2025_global)}")

# 3. Определяем локацию ПЕРВЫХ поинтов для новых танцоров (ВСЕ номинации)
print("📊 Шаг 2: Определяем локацию ПЕРВЫХ поинтов (все номинации)...")
dancer_first_city = {}
dancer_first_state = {}
dancer_first_country = {}

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        # Включаем ВСЕ номинации для определения локации первых поинтов
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
        
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        if not geo:
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

print(f"  Определено локаций для {len(dancer_first_city)} танцоров")

# 4. Собираем статистику (skill-level для поинтов, но новые учитываем по всем номинациям)
print("📊 Шаг 3: Собираем статистику...")
stats_country = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
})
stats_state = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
})
stats_city = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set(),
    'display_name': '', 'country': ''
})

# Обрабатываем skill-level поинты
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue

        event_name = row['event_name']
        dancer_id = row['dancer_id']
        points = int(row['event_points'])
        
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        if not geo:
            geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        if not geo:
            continue

        city = geo['city']
        state = geo['state']
        country = geo['country']
        region = REGION_MAP.get(country, 'Other')

        # Обновляем статистику
        def update_stats(d, key, pts, did, evt, extra_meta=None):
            d[key]['points'] += pts
            d[key]['events_set'].add(evt)
            d[key]['dancers_set'].add(did)
            if extra_meta:
                for k, v in extra_meta.items():
                    d[key][k] = v

        update_stats(stats_country, country, points, dancer_id, event_name)
        if country == 'United States' and state:
            update_stats(stats_state, state, points, dancer_id, event_name)
        city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
        update_stats(stats_city, city_key, points, dancer_id, event_name,
                     {'display_name': city_key, 'country': country})

# 5. Добавляем новых танцоров (по локации первых поинтов - все номинации)
print("📊 Шаг 4: Добавляем новых танцоров (по локации первых поинтов - все номинации)...")
for dancer_id in new_dancers_2025_global:
    # Для города
    if dancer_id in dancer_first_city and dancer_first_city[dancer_id]['city_key']:
        city_key = dancer_first_city[dancer_id]['city_key']
        if city_key not in stats_city:
            parts = city_key.split(', ')
            country = parts[-1] if len(parts) > 1 else ''
            stats_city[city_key] = {
                'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set(),
                'display_name': city_key, 'country': country
            }
        stats_city[city_key]['new_dancers_set'].add(dancer_id)
    
    # Для штата
    if dancer_id in dancer_first_state and dancer_first_state[dancer_id]['state']:
        state = dancer_first_state[dancer_id]['state']
        if state not in stats_state:
            stats_state[state] = {
                'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
            }
        stats_state[state]['new_dancers_set'].add(dancer_id)
    
    # Для страны
    if dancer_id in dancer_first_country and dancer_first_country[dancer_id]['country']:
        country = dancer_first_country[dancer_id]['country']
        if country not in stats_country:
            stats_country[country] = {
                'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
            }
        stats_country[country]['new_dancers_set'].add(dancer_id)

# 6. Извлекаем данные из статьи
print("📊 Шаг 5: Извлекаем данные из статьи...")
with open(filename_article, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

article_cities = {}
article_states = {}
article_countries = {}

tables = soup.find_all('table', class_='rank-table')
for table in tables:
    rows = table.find_all('tr')[1:]
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 6:
            name_cell = cells[1]
            name = name_cell.get_text(strip=True)
            for emoji in name_cell.find_all('span', class_='event-flag'):
                name = name.replace(emoji.get_text(strip=True), '').strip()
            
            try:
                events = int(cells[2].get_text(strip=True).replace(',', ''))
                points = int(cells[3].get_text(strip=True).replace(',', ''))
                unique = int(cells[4].get_text(strip=True).replace(',', ''))
                new = int(cells[5].get_text(strip=True).replace(',', ''))
                
                if any(city_name in name for city_name in ['Stockholm', 'Budapest', 'Washington', 'San Francisco', 'Boston', 'Orlando', 'Atlanta', 'Freiburg', 'Phoenix', 'Kraków', 'Krakow', 'Seattle']):
                    article_cities[name] = {'new': new}
                elif name in ['CA', 'TX', 'FL', 'OR', 'MA', 'IL', 'GA', 'AZ', 'NC', 'DC', 'WA', 'District of Columbia']:
                    state_key = 'DC' if name == 'District of Columbia' else name
                    article_states[state_key] = {'new': new}
                elif name in ['France', 'Germany', 'Sweden', 'Poland', 'Russia', 'United Kingdom', 'Hungary', 'Canada', 'Finland', 'Spain', 'Austria', 'Italy']:
                    article_countries[name] = {'new': new}
            except:
                pass

# 7. Сравниваем
print("\n" + "="*80)
print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
print("="*80)

def normalize_city_name_for_match(correct_key, article_name):
    correct_parts = correct_key.replace(', United States', '').split(',')
    correct_city = correct_parts[0].strip()
    article_city = article_name.split(',')[0].strip()
    city_mapping = {'Kraków': 'Krakow', 'Krakow': 'Kraków'}
    correct_city_norm = city_mapping.get(correct_city, correct_city)
    article_city_norm = city_mapping.get(article_city, article_city)
    if correct_city_norm.lower() == article_city_norm.lower():
        return True
    if correct_city.lower() in article_city.lower() or article_city.lower() in correct_city.lower():
        return True
    return False

print("\n📊 ГОРОДА:")
mismatches_cities = []
city_items = [(k, len(v['new_dancers_set'])) for k, v in stats_city.items()]
city_items.sort(key=lambda x: x[1], reverse=True)
for city_key, correct_new in city_items[:15]:
    # Ищем в статье
    found = False
    for article_name, article_data in article_cities.items():
        if normalize_city_name_for_match(city_key, article_name):
            article_new = article_data['new']
            if article_new != correct_new:
                print(f"  {article_name:<35} | Статья: {article_new:<4} | Правильно: {correct_new:<4} | Разница: {correct_new - article_new:+d}")
                mismatches_cities.append((article_name, article_new, correct_new))
            found = True
            break

print("\n📊 ШТАТЫ США:")
mismatches_states = []
state_items = [(k, len(v['new_dancers_set'])) for k, v in stats_state.items()]
state_items.sort(key=lambda x: x[1], reverse=True)
for state_key, correct_new in state_items[:15]:
    if state_key in article_states:
        article_new = article_states[state_key]['new']
        if article_new != correct_new:
            print(f"  {state_key:<20} | Статья: {article_new:<4} | Правильно: {correct_new:<4} | Разница: {correct_new - article_new:+d}")
            mismatches_states.append((state_key, article_new, correct_new))

print("\n📊 СТРАНЫ:")
mismatches_countries = []
country_items = [(k, len(v['new_dancers_set'])) for k, v in stats_country.items()]
country_items.sort(key=lambda x: x[1], reverse=True)
for country_key, correct_new in country_items[:15]:
    if country_key in article_countries:
        article_new = article_countries[country_key]['new']
        if article_new != correct_new:
            print(f"  {country_key:<20} | Статья: {article_new:<4} | Правильно: {correct_new:<4} | Разница: {correct_new - article_new:+d}")
            mismatches_countries.append((country_key, article_new, correct_new))

total_mismatches = len(mismatches_cities) + len(mismatches_states) + len(mismatches_countries)
if total_mismatches == 0:
    print("\n✅ Все значения 'New' корректны!")
else:
    print(f"\n⚠️  Найдено {total_mismatches} расхождений")

