import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'
OUTPUT_DIR = Path('/Users/ania/.cursor/wsdc-analytics-repo')

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

def is_us_event(country, event_name):
    """Проверяет, является ли ивент американским (США)"""
    # Проверяем страну
    if country == 'United States':
        return True
    # Дополнительная проверка для некоторых ивентов, которые могут быть помечены иначе
    # но проводились в США
    us_keywords = ['USA', 'US', 'United States']
    if any(keyword in event_name for keyword in us_keywords):
        return True
    return False

points = defaultdict(float)
wins = defaultdict(int)
events = defaultdict(set)
dancer_ids = {}

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
        if not is_us_event(country, event_name):
            continue
        
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            points[dancer_name] += pts
            events[dancer_name].add(event_name)
            dancer_ids[dancer_name] = dancer_id
        if result == '1':
            wins[dancer_name] += 1

# Топ-10 по поинтам
top_points = sorted([(n, p) for n, p in points.items()], key=lambda x: x[1], reverse=True)[:10]
# Топ-10 по победам
top_wins = sorted([(n, w) for n, w in wins.items() if w > 0], key=lambda x: x[1], reverse=True)[:10]
# Топ-10 по ивентам
top_events = sorted([(n, len(e)) for n, e in events.items() if len(e) > 0], key=lambda x: x[1], reverse=True)[:10]

def format_js_data(data, metric_name):
    """Форматирует данные для JavaScript с правильным расчетом рангов и tied"""
    result = []
    prev_value = None
    rank = 1
    
    for i, (name, value) in enumerate(data):
        # Проверяем tied - если значение такое же как у предыдущего или следующего
        tied = False
        if i > 0 and data[i-1][1] == value:
            tied = True
        if i < len(data) - 1 and data[i+1][1] == value:
            tied = True
        
        top3 = rank <= 3
        
        result.append({
            'rank': rank,
            'name': name,
            'value': int(value),
            'top3': top3,
            'tied': tied
        })
        
        # Обновляем rank для следующего элемента
        if i < len(data) - 1 and data[i+1][1] != value:
            rank = i + 2
    
    return result

# Форматируем данные для JavaScript
points_data = format_js_data(top_points, 'points')
wins_data = format_js_data(top_wins, 'wins')
events_data = format_js_data(top_events, 'events')

# Выводим результаты
print("Топ-10 по поинтам (американские ивенты):")
for i, (name, pts) in enumerate(top_points, 1):
    print(f"{i}. {name}: {pts:.0f}")

print("\nТоп-10 по победам:")
for i, (name, w) in enumerate(top_wins, 1):
    print(f"{i}. {name}: {w}")

print("\nТоп-10 по ивентам:")
for i, (name, e) in enumerate(top_events, 1):
    print(f"{i}. {name}: {e}")

# Сохраняем CSV файлы
# Points CSV
with open(OUTPUT_DIR / 'us_dancers_top_points_2025.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['dancer_id', 'points_2025', 'dancer_name', 'points_total'])
    for name, pts in top_points:
        dancer_id = dancer_ids.get(name, '')
        # Для points_total используем общий total points (нужно будет получить из основного файла)
        writer.writerow([dancer_id, int(pts), name, int(pts)])

# Wins CSV
with open(OUTPUT_DIR / 'us_dancers_top_wins_2025.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['dancer_id', 'wins_2025', 'dancer_name', 'wins_total'])
    for name, w in top_wins:
        dancer_id = dancer_ids.get(name, '')
        writer.writerow([dancer_id, w, name, w])

# Events CSV
with open(OUTPUT_DIR / 'us_dancers_top_events_2025.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['dancer_id', 'events_2025', 'dancer_name', 'events_total'])
    for name, e in top_events:
        dancer_id = dancer_ids.get(name, '')
        writer.writerow([dancer_id, e, name, e])

print("\n" + "="*60)
print("JavaScript данные для HTML:")
print("\n'us-points': [")
for i, item in enumerate(points_data):
    comma = "," if i < len(points_data) - 1 else ""
    print(f"                {{rank: {item['rank']}, name: '{item['name']}', value: {item['value']}, top3: {str(item['top3']).lower()}, tied: {str(item['tied']).lower()}}}{comma}")
print("],")

print("\n'us-wins': [")
for i, item in enumerate(wins_data):
    comma = "," if i < len(wins_data) - 1 else ""
    print(f"                {{rank: {item['rank']}, name: '{item['name']}', value: {item['value']}, top3: {str(item['top3']).lower()}, tied: {str(item['tied']).lower()}}}{comma}")
print("],")

print("\n'us-events': [")
for i, item in enumerate(events_data):
    comma = "," if i < len(events_data) - 1 else ""
    print(f"                {{rank: {item['rank']}, name: '{item['name']}', value: {item['value']}, top3: {str(item['top3']).lower()}, tied: {str(item['tied']).lower()}}}{comma}")
print("],")
