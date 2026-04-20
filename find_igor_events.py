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

igor_events = defaultdict(lambda: {'points':0, 'wins':[], 'competitions':set(), 'city':'', 'country':''})

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            year = int(row.get('event_year','0'))
        except:
            continue
        if year != 2025:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name != 'Igor Pitangui':
            continue
        comp = row.get('event_competition','')
        role = row.get('dancer_role','')
        result = str(row.get('event_result',''))
        points = float(row.get('event_points','0') or 0)
        event_name = row.get('event_name','')
        
        if points <= 0:
            continue
            
        loc_id = row.get('location_id','')
        if loc_id in loc:
            igor_events[event_name]['city'] = loc[loc_id]['city']
            igor_events[event_name]['country'] = loc[loc_id]['country']
        
        igor_events[event_name]['points'] += points
        igor_events[event_name]['competitions'].add(comp)
        
        if result == '1':
            igor_events[event_name]['wins'].append(f"{comp} ({role})")

# Сортируем по поинтам и ищем ивенты с двойными победами
events_sorted = sorted(igor_events.items(), key=lambda x: x[1]['points'], reverse=True)

print("Ивенты Igor Pitangui, отсортированные по поинтам:")
print()
for event_name, data in events_sorted[:10]:
    wins_str = ", ".join(data['wins']) if data['wins'] else "нет побед"
    location = f"{data['city']}, {data['country']}" if data['city'] else data['country']
    print(f"{event_name} ({location}):")
    print(f"  Поинты: {int(data['points'])}")
    print(f"  Победы: {wins_str}")
    print(f"  Номинации: {', '.join(sorted(data['competitions']))}")
    print()

# Ищем ивенты с двумя победами в разных номинациях
print("="*80)
print("Ивенты с двойными победами (Champions + All-Stars):")
print("="*80)
for event_name, data in events_sorted:
    wins = data['wins']
    if len(wins) >= 2:
        has_champions = any('Champions' in w for w in wins)
        has_allstars = any('All-Stars' in w for w in wins)
        if has_champions and has_allstars:
            location = f"{data['city']}, {data['country']}" if data['city'] else data['country']
            print(f"{event_name} ({location}):")
            print(f"  Поинты: {int(data['points'])}")
            print(f"  Победы: {', '.join(wins)}")
            print()
