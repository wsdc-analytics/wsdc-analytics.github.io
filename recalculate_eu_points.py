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
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name, loc_id):
    # Explicitly include Finnfest and Scandinavian Open as European
    if 'finnfest' in event_name.lower():
        return True
    if 'scandinavian open' in event_name.lower():
        return True
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
        if not is_european_event(country, event_name, loc_id):
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

print("Топ-10 по поинтам (европейские ивенты, с учетом исправлений):")
print("="*60)
for i, (name, pts) in enumerate(top_points, 1):
    print(f"{i}. {name}: {pts:.0f}")

# Проверка на tied
print("\n" + "="*60)
print("Детальная информация о tied:")
for i, (name, pts) in enumerate(top_points, 1):
    tied_with = []
    for j, (n2, p2) in enumerate(top_points, 1):
        if i != j and abs(p2 - pts) < 0.01:  # Сравнение с учетом возможных ошибок округления
            tied_with.append((j, n2))
    if tied_with:
        print(f"{i}. {name} ({pts:.0f}): tied with {tied_with}")

# Формируем данные для JavaScript
print("\n" + "="*60)
print("JavaScript данные для eu-points:")
print("[")
for i, (name, pts) in enumerate(top_points, 1):
    top3 = i <= 3
    # Проверка на tied
    tied = False
    if i < len(top_points) and abs(top_points[i][1] - pts) < 0.01:
        tied = True
    if i > 1 and abs(top_points[i-2][1] - pts) < 0.01:
        tied = True
    comma = "," if i < len(top_points) else ""
    print(f"                {{rank: {i}, name: '{name}', value: {int(pts)}, top3: {str(top3).lower()}, tied: {str(tied).lower()}}}{comma}")
print("]")
