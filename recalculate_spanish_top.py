import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

# Испанские танцоры по ID
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

# Функция для определения европейских ивентов (с исправлениями)
def is_european_event(country, event_name, loc_id):
    # Специальные случаи:
    # 1. Finnfest - ошибка в стране, но проходит в Финляндии
    if 'finnfest' in event_name.lower():
        return True
    
    # 2. Scandinavian Open - отсутствует локация, но проходит в Стокгольме, Швеция
    if 'scandinavian open' in event_name.lower():
        return True
    
    # 3. Nordic Championships
    if 'nordic' in event_name.lower() or 'scandinavia' in event_name.lower():
        return True
    
    european_countries = {
        'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
        'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
        'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
        'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
    }
    
    return country in european_countries

points = defaultdict(float)
wins = defaultdict(int)
events = defaultdict(set)

# Проверяем, учитываются ли только европейские ивенты или все
# Сначала считаем БЕЗ фильтрации (как в analyze_spanish_dancers.py)
print("Расчет испанского топа:")
print("="*70)

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
        
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        
        event_name = row.get('event_name','')
        
        # ВАЖНО: Проверяем, используется ли фильтрация по европейским ивентам
        # Если да, то применяем исправленную функцию
        # Если нет, то учитываем все ивенты
        
        # Пока считаем ВСЕ ивенты (как в оригинальном скрипте)
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            points[dancer_name] += pts
            events[dancer_name].add(event_name)
        if result == '1':
            wins[dancer_name] += 1

# Топ-10 по каждой метрике
top_points = sorted([(n, p) for n, p in points.items()], key=lambda x: x[1], reverse=True)[:10]
top_wins = sorted([(n, w) for n, w in wins.items() if w > 0], key=lambda x: x[1], reverse=True)[:10]
top_events = sorted([(n, len(e)) for n, e in events.items() if len(e) > 0], key=lambda x: x[1], reverse=True)[:10]

print("\nТоп-10 по поинтам (ВСЕ ивенты):")
for i, (name, pts) in enumerate(top_points, 1):
    print(f"{i}. {name}: {pts:.0f} поинтов ({len(events[name])} ивентов)")

print("\nТоп-10 по победам:")
for i, (name, w) in enumerate(top_wins, 1):
    print(f"{i}. {name}: {w} побед")

print("\nТоп-10 по ивентам:")
for i, (name, evts) in enumerate(top_events, 1):
    print(f"{i}. {name}: {evts} ивентов")

# Проверяем проблемные ивенты
print("\n" + "="*70)
print("Проверка влияния проблемных ивентов:")
problem_events = ['Finnfest', 'Scandinavian Open']
for event in problem_events:
    affected_dancers = []
    for dancer_name in points.keys():
        if event.lower() in ' '.join(events[dancer_name]).lower():
            affected_dancers.append(dancer_name)
    if affected_dancers:
        print(f"\n{event}:")
        for dancer in affected_dancers:
            event_points = 0
            with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('event_year','') == '2025':
                        dancer_id = row.get('dancer_id','')
                        if dancer_id in spanish_ids and dancer_id_to_name.get(dancer_id,'') == dancer:
                            if event.lower() in row.get('event_name','').lower():
                                event_points += float(row.get('event_points','0') or 0)
            print(f"  {dancer}: {event_points:.0f} поинтов")
