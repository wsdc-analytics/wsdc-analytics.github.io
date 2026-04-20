import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'

dancer_id_to_name = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id_to_name[row['dancer_id']] = row.get('dancer_name','')

target_name = 'Chloe Winzar'
event_points = defaultdict(float)
total_points = 0
events = set()
wins = 0

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
        
        event_name = row.get('event_name','')
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            event_points[event_name] += pts
            total_points += pts
            events.add(event_name)
        if result == '1':
            wins += 1

if event_points:
    sorted_events = sorted(event_points.items(), key=lambda x: x[1], reverse=True)
    
    print(f"Данные по {target_name} в Sophisticated (2025):")
    print("="*70)
    print(f"Всего поинтов: {total_points:.0f}")
    print(f"Всего ивентов: {len(events)}")
    print(f"Побед: {wins}")
    print(f"\nТоп ивентов по поинтам:")
    for i, (event, points) in enumerate(sorted_events[:5], 1):
        print(f"{i}. {event}: {points:.0f} поинтов")
    
    best_event = sorted_events[0][0]
    best_points = sorted_events[0][1]
    print(f"\nСамый успешный ивент: {best_event} - {best_points:.0f} поинтов")
else:
    print(f"{target_name} не найден в данных Sophisticated за 2025 год")
