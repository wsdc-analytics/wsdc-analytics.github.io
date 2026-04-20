import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

dancer_id_to_name = {}
name_to_dancer_id = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id = row['dancer_id']
        dancer_name = row.get('dancer_name','')
        dancer_id_to_name[dancer_id] = dancer_name
        if dancer_name:
            name_to_dancer_id[dancer_name] = dancer_id

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
    if 'finnfest' in event_name.lower():
        return True
    if 'scandinavian open' in event_name.lower():
        return True
    if 'nordic' in event_name.lower() or 'scandinavia' in event_name.lower():
        return True
    return country in european_countries

dancer_name = 'Clement Turpain'
dancer_id = name_to_dancer_id.get(dancer_name)

if not dancer_id:
    print(f"Не найден dancer_id для {dancer_name}")
    exit(1)

print(f"Данные для {dancer_name} (dancer_id: {dancer_id})")
print("="*70)

points_by_event = defaultdict(float)
points_by_comp = defaultdict(float)
points_by_role = defaultdict(float)
wins_by_comp = defaultdict(int)
wins_by_role = defaultdict(int)
events_set = set()
event_details = []

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        if row.get('dancer_id','') != dancer_id:
            continue
        
        comp = row.get('event_competition','')
        if comp not in skill_levels:
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
        role = row.get('event_role','')
        
        if pts > 0:
            points_by_event[event_name] += pts
            points_by_comp[comp] += pts
            points_by_role[role] += pts
            events_set.add(event_name)
            event_details.append({
                'event': event_name,
                'comp': comp,
                'role': role,
                'points': pts,
                'result': result,
                'country': country
            })
        
        if result == '1':
            wins_by_comp[comp] += 1
            wins_by_role[role] += 1

total_points = sum(points_by_event.values())
total_wins = sum(wins_by_comp.values())
total_events = len(events_set)

print(f"\nОбщая статистика:")
print(f"  Всего поинтов: {total_points:.0f}")
print(f"  Всего побед: {total_wins}")
print(f"  Всего ивентов: {total_events}")

print(f"\nПо номинациям:")
for comp in sorted(points_by_comp.keys(), key=lambda x: points_by_comp[x], reverse=True):
    print(f"  {comp}: {points_by_comp[comp]:.0f} поинтов, {wins_by_comp[comp]} побед")

print(f"\nПо ролям:")
for role in sorted(points_by_role.keys(), key=lambda x: points_by_role[x], reverse=True):
    print(f"  {role}: {points_by_role[role]:.0f} поинтов, {wins_by_role[role]} побед")

print(f"\nТоп ивенты по поинтам:")
top_events = sorted(points_by_event.items(), key=lambda x: x[1], reverse=True)[:5]
for event, pts in top_events:
    print(f"  {event}: {pts:.0f} поинтов")

print(f"\nВсе ивенты с деталями:")
for detail in sorted(event_details, key=lambda x: x['points'], reverse=True):
    print(f"  {detail['event']} ({detail['country']}): {detail['comp']} {detail['role']} - {detail['points']:.0f} поинтов (место: {detail['result']})")
