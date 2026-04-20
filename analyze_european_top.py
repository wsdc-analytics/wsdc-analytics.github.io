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

skill_levels = {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}

european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland',
    'Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name):
    # Специальная обработка для Nordic Championships
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
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
        if comp not in skill_levels:
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
        if not is_european_event(country, event_name):
            continue
        
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            points[dancer_name] += pts
            events[dancer_name].add(event_name)
        if result == '1':
            wins[dancer_name] += 1

# Топ-10 по поинтам
top_points = sorted([(n, p) for n, p in points.items()], key=lambda x: x[1], reverse=True)[:10]
# Топ-10 по победам
top_wins = sorted([(n, w) for n, w in wins.items() if w > 0], key=lambda x: x[1], reverse=True)[:10]
# Топ-10 по ивентам
top_events = sorted([(n, len(e)) for n, e in events.items() if len(e) > 0], key=lambda x: x[1], reverse=True)[:10]

print("Топ-10 по поинтам (европейские ивенты):")
for i, (name, pts) in enumerate(top_points, 1):
    print(f"{i}. {name}: {pts:.0f}")

print("\nТоп-10 по победам:")
for i, (name, w) in enumerate(top_wins, 1):
    print(f"{i}. {name}: {w}")

print("\nТоп-10 по ивентам:")
for i, (name, e) in enumerate(top_events, 1):
    print(f"{i}. {name}: {e}")

# Формируем данные для JavaScript
print("\n" + "="*60)
print("JavaScript данные для eu-points:")
print("[")
for i, (name, pts) in enumerate(top_points, 1):
    top3 = i <= 3
    # Проверка на tied (следующий имеет такое же значение)
    tied = i < len(top_points) and top_points[i][1] == pts
    if i > 1 and top_points[i-2][1] == pts:
        tied = True
    comma = "," if i < len(top_points) else ""
    print(f"                {{rank: {i}, name: '{name}', value: {int(pts)}, top3: {str(top3).lower()}, tied: {str(tied).lower()}}}{comma}")

