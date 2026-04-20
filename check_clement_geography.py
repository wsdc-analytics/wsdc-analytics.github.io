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

points_by_country = defaultdict(float)
points_by_event_type = defaultdict(float)  # european vs non-european
all_events = []

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
        is_eu = is_european_event(country, event_name, loc_id)
        
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            points_by_country[country] += pts
            if is_eu:
                points_by_event_type['european'] += pts
            else:
                points_by_event_type['non-european'] += pts
            all_events.append({
                'event': event_name,
                'country': country,
                'is_eu': is_eu,
                'points': pts
            })

total_points = sum(points_by_country.values())
eu_points = points_by_event_type['european']
non_eu_points = points_by_event_type['non-european']

print(f"Всего поинтов: {total_points:.0f}")
print(f"Европейские ивенты: {eu_points:.0f} ({eu_points/total_points*100:.1f}%)")
print(f"Неевропейские ивенты: {non_eu_points:.0f} ({non_eu_points/total_points*100:.1f}%)")

print(f"\nПо странам:")
for country, pts in sorted(points_by_country.items(), key=lambda x: x[1], reverse=True):
    print(f"  {country}: {pts:.0f} поинтов ({pts/total_points*100:.1f}%)")

print(f"\nВсе ивенты:")
for event in sorted(all_events, key=lambda x: x['points'], reverse=True):
    print(f"  {event['event']} ({event['country']}): {event['points']:.0f} поинтов ({'EU' if event['is_eu'] else 'non-EU'})")
