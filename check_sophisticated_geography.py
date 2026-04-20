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

target_dancers = [
    'Chloe Winzar', 'Haley Hauglum', 'Marine Monin', 'Stanley Seguy', 
    'Jerome Fernandez', 'Jerome Tangha'
]

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
    if country == 'Polska':
        return True
    return country in european_countries

def is_us_event(country):
    return country == 'United States'

for target_name in target_dancers:
    all_points = 0
    eu_points = 0
    us_points = 0
    other_points = 0
    eu_events = set()
    us_events = set()
    other_events = set()
    all_events = set()

    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') != '2025':
                continue
            
            comp = row.get('event_competition','')
            if comp != 'Sophisticated':
                continue
            
            dancer_id = row.get('dancer_id','')
            dancer_name = dancer_id_to_name.get(dancer_id,'')
            
            if dancer_name != target_name:
                continue
            
            loc_id = row.get('location_id','')
            country = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
            
            event_name = row.get('event_name','')
            pts = float(row.get('event_points','0') or 0)
            
            if pts > 0:
                all_points += pts
                all_events.add(event_name)
                
                if is_european_event(country, event_name, loc_id):
                    eu_points += pts
                    eu_events.add(event_name)
                elif is_us_event(country):
                    us_points += pts
                    us_events.add(event_name)
                else:
                    other_points += pts
                    other_events.add(event_name)

    if all_points > 0:
        print(f"\n{target_name}:")
        print(f"  Всего поинтов: {all_points:.0f}")
        print(f"  Всего ивентов: {len(all_events)}")
        print(f"  Европа: {eu_points:.0f} поинтов ({eu_points/all_points*100:.1f}%), {len(eu_events)} ивентов")
        print(f"  США: {us_points:.0f} поинтов ({us_points/all_points*100:.1f}%), {len(us_events)} ивентов")
        if other_points > 0:
            print(f"  Другие: {other_points:.0f} поинтов ({other_points/all_points*100:.1f}%), {len(other_events)} ивентов")
        
        # Формируем строку географии
        geo_parts = []
        if eu_points > 0:
            geo_parts.append(f"{eu_points/all_points*100:.1f}% на европейских ивентах")
        if us_points > 0:
            geo_parts.append(f"{us_points/all_points*100:.1f}% на американских ивентах")
        if other_points > 0:
            geo_parts.append(f"{other_points/all_points*100:.1f}% на других ивентах")
        
        print(f"  География строка: {', '.join(geo_parts)}")
