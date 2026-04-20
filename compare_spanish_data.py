import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

spanish_ids = {
    '24950', '23919', '24385', '18215', '18987', '8203', '23975', '11874',
    '20779', '26638', '19474', '21512', '19732', '12767', '24328', '25231',
    '24621', '24626', '22481', '26336', '20978', '12372', '14916', '18751'
}

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

# Данные из HTML (текущие)
html_data = {
    'points': [
        ('Julien Espagnet', 65), ('Fran Vidal', 50), ('Alvaro Hilario Garcia', 47),
        ('Margarita Perepelkina', 29), ('Aleix Figueras', 28), ('Cristina Marino', 27),
        ('Miquel Menendez', 23), ('Alena Muñoz Sánchez', 18), ('Laura llacuna', 18)
    ],
    'events': [
        ('Alvaro Hilario Garcia', 16), ('Fran Vidal', 11), ('Miquel Menendez', 10),
        ('Julien Espagnet', 8), ('Margarita Perepelkina', 6), ('Aleix Figueras', 6),
        ('Alena Belousova', 6), ('Ivan Jorquera Martine', 4), ('Laura llacuna', 4),
        ('Cristina Marino', 4)
    ]
}

# Пересчитываем
points = defaultdict(float)
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
        if dancer_id not in spanish_ids:
            continue
        
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name:
            continue
        
        pts = float(row.get('event_points','0') or 0)
        event_name = row.get('event_name','')
        
        if pts > 0:
            points[dancer_name] += pts
            events[dancer_name].add(event_name)

# Сравниваем
print("Сравнение данных:")
print("="*70)

print("\nПо поинтам:")
recalc_points = sorted([(n, p) for n, p in points.items()], key=lambda x: x[1], reverse=True)[:10]
for i, (name, pts) in enumerate(recalc_points, 1):
    html_pts = next((p for n, p in html_data['points'] if n == name), None)
    if html_pts is None:
        print(f"  {i}. {name}: {pts:.0f} (в HTML отсутствует)")
    elif abs(html_pts - pts) > 0.1:
        print(f"  {i}. {name}: {pts:.0f} (в HTML: {html_pts:.0f}) ⚠ РАЗНИЦА!")
    else:
        print(f"  {i}. {name}: {pts:.0f} ✓")

print("\nПо ивентам:")
recalc_events = sorted([(n, len(e)) for n, e in events.items() if len(e) > 0], key=lambda x: x[1], reverse=True)[:10]
for i, (name, evts) in enumerate(recalc_events, 1):
    html_evts = next((e for n, e in html_data['events'] if n == name), None)
    if html_evts is None:
        print(f"  {i}. {name}: {evts} (в HTML отсутствует)")
    elif html_evts != evts:
        print(f"  {i}. {name}: {evts} (в HTML: {html_evts}) ⚠ РАЗНИЦА!")
    else:
        print(f"  {i}. {name}: {evts} ✓")
