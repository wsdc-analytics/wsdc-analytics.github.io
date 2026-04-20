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

target_name = 'Aleix Figueras'
event_points = defaultdict(float)
event_details = []

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
        
        if dancer_name != target_name:
            continue
        
        event_name = row.get('event_name','')
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            event_points[event_name] += pts
            loc_id = row.get('location_id','')
            country = ''
            city = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
                city = loc[loc_id]['city']
            
            event_details.append({
                'event': event_name,
                'points': pts,
                'comp': comp,
                'result': result,
                'country': country,
                'city': city
            })

if event_points:
    sorted_events = sorted(event_points.items(), key=lambda x: x[1], reverse=True)
    
    print(f"Данные по {target_name} (2025):")
    print("="*70)
    print(f"Всего ивентов с поинтами: {len(event_points)}")
    print(f"Всего поинтов: {sum(event_points.values()):.0f}")
    print(f"\nТоп ивентов по поинтам:")
    for i, (event, points) in enumerate(sorted_events[:5], 1):
        print(f"{i}. {event}: {points:.0f} поинтов")
    
    best_event = sorted_events[0][0]
    best_points = sorted_events[0][1]
    
    print(f"\nСамый успешный ивент: {best_event} - {best_points:.0f} поинтов")
    
    # Показываем детали по самому успешному ивенту
    print(f"\nДетали по ивенту '{best_event}':")
    for detail in event_details:
        if detail['event'] == best_event:
            print(f"  {detail['comp']}: {detail['points']:.0f} поинтов (место: {detail['result']})")
else:
    print(f"{target_name} не найден в данных за 2025 год")
