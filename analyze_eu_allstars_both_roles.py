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

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    return country in european_countries

# Храним роли для каждого танцора
dancer_roles = defaultdict(set)
dancer_points = defaultdict(float)
dancer_leader_points = defaultdict(float)
dancer_follower_points = defaultdict(float)
dancer_events = defaultdict(set)

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp != 'All-Stars':  # Только All-Stars
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
        
        role = row.get('event_role','').strip().lower()
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            dancer_roles[dancer_name].add(role)
            dancer_points[dancer_name] += pts
            dancer_events[dancer_name].add(event_name)
            
            if role == 'leader':
                dancer_leader_points[dancer_name] += pts
            elif role == 'follower':
                dancer_follower_points[dancer_name] += pts

# Находим танцоров с обеими ролями
both_roles_dancers = []
for dancer_name, roles in dancer_roles.items():
    has_leader = 'leader' in roles
    has_follower = 'follower' in roles
    
    if has_leader and has_follower:
        both_roles_dancers.append({
            'name': dancer_name,
            'total_points': dancer_points[dancer_name],
            'leader_points': dancer_leader_points[dancer_name],
            'follower_points': dancer_follower_points[dancer_name],
            'events': len(dancer_events[dancer_name])
        })

# Сортируем по общему количеству поинтов
both_roles_dancers.sort(key=lambda x: x['total_points'], reverse=True)

print("Танцоры, получавшие поинты за обе роли (Leader и Follower) в All-Stars на европейских ивентах (2025):")
print("="*90)
print(f"{'Имя':<30} {'Всего поинтов':<15} {'Leader':<15} {'Follower':<15} {'Ивентов':<10}")
print("-"*90)

for dancer in both_roles_dancers:
    print(f"{dancer['name']:<30} {dancer['total_points']:<15.0f} {dancer['leader_points']:<15.0f} {dancer['follower_points']:<15.0f} {dancer['events']:<10}")

print(f"\nВсего таких танцоров: {len(both_roles_dancers)}")
