import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

# Испанские танцоры по ID
spanish_ids = {
    '24950', '23919', '24385', '18215', '18987', '8203', '23975', '11874',
    '20779', '26638', '19474', '21512', '19732', '12767', '24328', '25231',
    '24621', '24626', '22481', '26336', '20978', '12372', '14916', '18751'
}

dancer_id_to_name = {}
name_to_id = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id = row.get('dancer_id', '')
        dancer_name = row.get('dancer_name', '')
        dancer_id_to_name[dancer_id] = dancer_name
        if dancer_id in spanish_ids:
            name_to_id[dancer_name] = dancer_id

# Проверка какие ID нашлись
print("Найденные танцоры:")
for dancer_id, dancer_name in dancer_id_to_name.items():
    if dancer_id in spanish_ids:
        print(f"  {dancer_id}: {dancer_name}")

loc = {}
with open(LOCATION_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        loc[row['location_id']] = {
            'country': row.get('event_country',''),
            'city': row.get('event_city','')
        }

def get_location_info(loc_id, event_name):
    if loc_id in loc:
        country = loc[loc_id]['country']
        city = loc[loc_id]['city']
        return f"{city}, {country}" if city else country
    elif 'Nordic' in event_name or 'Scandinavia' in event_name:
        return "Stockholm, Sweden"
    return ""

LEVEL_ORDER = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']

stats = defaultdict(lambda: {
    'points': 0, 'wins': 0, 'events': set(),
    'points_by_level': defaultdict(float), 'wins_by_level': defaultdict(int),
    'competitions': defaultdict(int), 'roles': defaultdict(int),
    'events_data': defaultdict(float), 'global_points': 0
})

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}:
            continue
        
        dancer_id = row.get('dancer_id','')
        if dancer_id not in spanish_ids:
            continue
        
        dancer_name = dancer_id_to_name.get(dancer_id, '')
        if not dancer_name:
            continue
        
        # Глобальные поинты
        pts = float(row.get('event_points','0') or 0)
        if pts > 0:
            stats[dancer_name]['global_points'] += pts
        
        result = str(row.get('event_result',''))
        role = row.get('dancer_role','')
        event_name = row.get('event_name','')
        loc_id = row.get('location_id','')
        
        if pts > 0:
            stats[dancer_name]['points'] += pts
            stats[dancer_name]['points_by_level'][comp] += pts
            stats[dancer_name]['events'].add(event_name)
            stats[dancer_name]['competitions'][comp] += 1
            stats[dancer_name]['roles'][role] += 1
            stats[dancer_name]['events_data'][event_name] += pts
            
            # Для географии
            location = get_location_info(loc_id, event_name)
            if location:
                if 'location_data' not in stats[dancer_name]:
                    stats[dancer_name]['location_data'] = defaultdict(float)
                stats[dancer_name]['location_data'][location] += pts
        
        if result == '1':
            stats[dancer_name]['wins'] += 1
            stats[dancer_name]['wins_by_level'][comp] += 1

# Топ-10 по каждой метрике
top_points = sorted(stats.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
top_wins = sorted(stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:10]
top_events = sorted(stats.items(), key=lambda x: len(x[1]['events']), reverse=True)[:10]

print("\n" + "="*70)
print("ТОП-10 ПО ПОИНТАМ (испанские танцоры):")
print("="*70)
for i, (name, data) in enumerate(top_points, 1):
    print(f"{i:2d}. {name:35s} | {data['points']:5.0f} pts")

print("\n" + "="*70)
print("ТОП-10 ПО ПОБЕДАМ (испанские танцоры):")
print("="*70)
for i, (name, data) in enumerate(top_wins, 1):
    if data['wins'] > 0:
        print(f"{i:2d}. {name:35s} | {data['wins']:2d} wins")

print("\n" + "="*70)
print("ТОП-10 ПО ИВЕНТАМ (испанские танцоры):")
print("="*70)
for i, (name, data) in enumerate(top_events, 1):
    print(f"{i:2d}. {name:35s} | {len(data['events']):2d} events")

# Детальная информация для каждого в топ-10 по поинтам
print("\n" + "="*70)
print("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ (топ-10 по поинтам):")
print("="*70)
for name, data in top_points:
    highest = max([l for l in data['points_by_level'].keys()], 
                 key=lambda x: LEVEL_ORDER.index(x) if x in LEVEL_ORDER else 99) if data['points_by_level'] else 'N/A'
    
    levels_with_points = sorted([l for l in data['points_by_level'].keys()], 
                               key=lambda x: LEVEL_ORDER.index(x) if x in LEVEL_ORDER else 99)
    has_progression = len(levels_with_points) >= 2 and all(
        LEVEL_ORDER.index(levels_with_points[i+1]) - LEVEL_ORDER.index(levels_with_points[i]) == 1
        for i in range(len(levels_with_points)-1)
    ) if len(levels_with_points) >= 2 else False
    
    top_event, top_pts = max(data['events_data'].items(), key=lambda x: x[1]) if data['events_data'] else ('', 0)
    top_location = ""
    for loc_name, loc_pts in data.get('location_data', {}).items():
        if loc_pts == top_pts:
            top_location = loc_name
            break
    
    if not top_location and top_event:
        # Найдем локацию из event_name
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
                    dancer_id = row.get('dancer_id','')
                    if dancer_id in spanish_ids and dancer_id_to_name.get(dancer_id,'') == name:
                        top_location = get_location_info(row.get('location_id',''), top_event)
                        break
    
    print(f"\n{name}:")
    print(f"  Поинты: {data['points']:.0f}")
    print(f"  Победы: {data['wins']}")
    print(f"  Ивенты: {len(data['events'])}")
    print(f"  Высшая номинация: {highest}")
    print(f"  Поинты по номинациям: {dict(data['points_by_level'])}")
    print(f"  Победы по номинациям: {dict(data['wins_by_level'])}")
    print(f"  Прогрессия: {has_progression} ({' → '.join(levels_with_points) if levels_with_points else 'N/A'})")
    print(f"  Топ-ивент: {top_event} ({top_location}) - {int(top_pts)} поинтов")
    if 'location_data' in data:
        spanish_pts = sum([pts for loc_name, pts in data['location_data'].items() if 'Spain' in loc_name])
        print(f"  География: {spanish_pts/data['points']*100:.1f}% в Испании" if data['points'] > 0 else "  География: N/A")

