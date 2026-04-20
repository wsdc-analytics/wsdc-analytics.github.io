import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

dancer_id_to_name = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id_to_name[row['dancer_id']] = row.get('dancer_name','')

loc = {}
with open(LOCATION_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        loc[row['location_id']] = {
            'country': row.get('event_country',''),
            'city': row.get('event_city','')
        }

european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name, loc_id):
    # Специальные случаи:
    # 1. Finnfest - ошибка в стране, но проходит в Финляндии
    if 'finnfest' in event_name.lower():
        return True
    
    # 2. Scandinavian Open - отсутствует локация, но проходит в Стокгольме, Швеция
    if 'scandinavian open' in event_name.lower():
        return True
    
    # 3. Nordic Championships
    if 'nordic' in event_name.lower() or 'scandinavia' in event_name.lower():
        return True
    
    return country in european_countries

points = defaultdict(float)
wins = defaultdict(int)
events = defaultdict(set)

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name:
            continue
        
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        
        event_name = row.get('event_name','')
        if not is_european_event(country, event_name, loc_id):
            continue
        
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            points[dancer_name] += pts
            events[dancer_name].add(event_name)
        if result == '1':
            wins[dancer_name] += 1

# Топ-10 по ивентам
top_events = sorted([(n, len(e)) for n, e in events.items() if len(e) > 0], key=lambda x: x[1], reverse=True)[:10]

print("Топ-10 по количеству ивентов с поинтами на европейских ивентах (2025):")
print("="*70)
for i, (name, evts) in enumerate(top_events, 1):
    pts = points[name]
    w = wins[name]
    print(f"{i}. {name}: {evts} ивентов ({pts:.0f} поинтов, {w} побед)")

print("\n" + "="*70)
print("JavaScript данные для eu-events:")
print("[")
for i, (name, evts) in enumerate(top_events, 1):
    top3 = i <= 3
    # Проверка на tied
    tied = False
    if i < len(top_events) and top_events[i][1] == evts:
        tied = True
    if i > 1 and top_events[i-2][1] == evts:
        tied = True
    comma = "," if i < len(top_events) else ""
    print(f"                {{rank: {i}, name: '{name}', value: {evts}, top3: {str(top3).lower()}, tied: {str(tied).lower()}}}{comma}")
print("]")
