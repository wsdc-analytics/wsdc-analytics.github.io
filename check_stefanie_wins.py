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

top_wins = sorted([(n, w) for n, w in wins.items() if w > 0], key=lambda x: x[1], reverse=True)[:10]

print("Топ-10 по победам на европейских ивентах (2025):")
print("="*70)
for i, (name, num_wins) in enumerate(top_wins, 1):
    num_points = points[name]
    num_events = len(events[name])
    print(f"{i}. {name}: {num_wins} побед ({num_points:.0f} поинтов, {num_events} ивентов)")

# Проверяем конкретно Stefanie Tschom
target_name = 'Stefanie Tschom'
if target_name in wins:
    print(f"\n{target_name}:")
    print(f"  Побед: {wins[target_name]}")
    print(f"  Поинтов: {points[target_name]:.0f}")
    print(f"  Ивентов: {len(events[target_name])}")
    
    # Находим ее место
    for i, (name, num_wins) in enumerate(top_wins, 1):
        if name == target_name:
            print(f"  Место в топе: {i}")
            break
    else:
        print(f"  Место в топе: не в топ-10")
else:
    print(f"\n{target_name}: не найдена в данных")

print("\n" + "="*70)
print("JavaScript данные для eu-wins:")
print("[")
rank = 1
for i, (name, value) in enumerate(top_wins):
    tied = (i > 0 and top_wins[i-1][1] == value) or (i < len(top_wins)-1 and top_wins[i+1][1] == value)
    top3 = rank <= 3
    comma = "," if i < len(top_wins) - 1 else ""
    print(f"                {{rank: {rank}, name: '{name}', value: {value}, top3: {str(top3).lower()}, tied: {str(tied).lower()}}}{comma}")
    if i < len(top_wins) - 1 and top_wins[i+1][1] != value:
        rank = i + 2
print("]")
