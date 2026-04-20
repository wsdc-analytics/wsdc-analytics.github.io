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

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    european = {'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland',
    'Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'}
    return country in european

mentioned = {
    'Igor Pitangui', 'Aleksandra Radziejewska', 'Nicole Ramirez', 
    'Keerigan Rudd', 'Kristen Wallace', 'Zachary Skinner',
    'Charlie Fournier', 'Sebastian Gerwald', 'Alexa Partos', 
    'Fabio Zanardelli', 'Hanna Junk'
}

# Все кандидаты из европейского топа по разным метрикам
all_candidates = [
    'Daniel Curl', 'Michael Kuss', 'Melina Voglhuber',
    'Allan Thivoz', 'Joshua Schubert', 'Christina Landowski',
    'Alvaro Hilario Garcia', 'Stefanie Tschom', 'Florian Hamm',
    'Camille Picano', 'Attila Kobori', 'Aymeline Felmy', 'Tobias Gerwald'
]

stats = {}

for target in all_candidates:
    if target in mentioned:
        continue
    
    stats[target] = {
        'points': 0, 'wins': 0, 'events': set(), 'competitions': defaultdict(int),
        'roles': defaultdict(int), 'events_data': defaultdict(float),
        'global_points': 0
    }
    
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') != '2025':
                continue
            comp = row.get('event_competition','')
            dancer_id = row.get('dancer_id','')
            dancer_name = dancer_id_to_name.get(dancer_id,'')
            if dancer_name != target:
                continue
            
            pts = float(row.get('event_points','0') or 0)
            result = str(row.get('event_result',''))
            role = row.get('dancer_role','')
            event_name = row.get('event_name','')
            
            # Глобальные поинты
            if comp in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'} and pts > 0:
                stats[target]['global_points'] += pts
            
            # Европейские данные
            loc_id = row.get('location_id','')
            country = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
            
            if not is_european_event(country, event_name):
                continue
            
            if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}:
                continue
            
            if pts > 0:
                stats[target]['points'] += pts
                stats[target]['events'].add(event_name)
                stats[target]['competitions'][comp] += 1
                stats[target]['roles'][role] += 1
                stats[target]['events_data'][event_name] += pts
            if result == '1':
                stats[target]['wins'] += 1
    
    if stats[target]['global_points'] > 0:
        stats[target]['european_pct'] = (stats[target]['points'] / stats[target]['global_points'] * 100)
    else:
        stats[target]['european_pct'] = 100 if stats[target]['points'] > 0 else 0

# Анализируем по разным критериям
print("АНАЛИЗ КАНДИДАТОВ ПО РАЗНЫМ КРИТЕРИЯМ:")
print("="*80)

# 1. Топ по поинтам
print("\n1. ТОП ПО ПОИНТАМ (европейские):")
sorted_by_points = sorted([(n, s) for n, s in stats.items() if s['points'] > 0], 
                         key=lambda x: x[1]['points'], reverse=True)
for i, (name, st) in enumerate(sorted_by_points[:10], 1):
    print(f"{i:2d}. {name:25s} | {st['points']:5.0f} поинтов | {st['wins']} побед | {len(st['events'])} ивентов")

# 2. Топ по победам
print("\n2. ТОП ПО ПОБЕДАМ:")
sorted_by_wins = sorted([(n, s) for n, s in stats.items() if s['wins'] > 0], 
                       key=lambda x: (x[1]['wins'], x[1]['points']), reverse=True)
for i, (name, st) in enumerate(sorted_by_wins[:10], 1):
    print(f"{i:2d}. {name:25s} | {st['wins']} побед | {st['points']:5.0f} поинтов | {len(st['events'])} ивентов")

# 3. Топ по количеству ивентов
print("\n3. ТОП ПО КОЛИЧЕСТВУ ИВЕНТОВ:")
sorted_by_events = sorted([(n, s) for n, s in stats.items() if len(s['events']) > 0], 
                         key=lambda x: (len(x[1]['events']), x[1]['points']), reverse=True)
for i, (name, st) in enumerate(sorted_by_events[:10], 1):
    print(f"{i:2d}. {name:25s} | {len(st['events'])} ивентов | {st['points']:5.0f} поинтов | {st['wins']} побед")

# 4. Топ по проценту европейских поинтов (100% Европа)
print("\n4. ТАНЦОРЫ С 100% ЕВРОПЕЙСКИХ ПОИНТОВ:")
european_only = [(n, s) for n, s in stats.items() if s['european_pct'] == 100 and s['points'] > 0]
european_only.sort(key=lambda x: x[1]['points'], reverse=True)
for i, (name, st) in enumerate(european_only[:10], 1):
    print(f"{i:2d}. {name:25s} | {st['points']:5.0f} поинтов | {st['wins']} побед | {len(st['events'])} ивентов")

# 5. Уникальные достижения
print("\n5. УНИКАЛЬНЫЕ ДОСТИЖЕНИЯ:")
print("   - Специализация в одной номинации (All-Stars/Champions):")
for name, st in sorted_by_points:
    comps = dict(st['competitions'])
    if len(comps) == 1 and ('All-Stars' in comps or 'Champions' in comps):
        comp_name = list(comps.keys())[0]
        print(f"     {name:25s} - {comp_name} ({comps[comp_name]} выступлений)")

print("\n   - Прогрессия через несколько номинаций:")
for name, st in sorted_by_points:
    comps = sorted([c for c in st['competitions'].keys() if st['competitions'][c] > 0])
    level_order = ['Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions']
    comps_sorted = sorted(comps, key=lambda x: level_order.index(x) if x in level_order else 99)
    if len(comps_sorted) >= 3:
        print(f"     {name:25s} - {' → '.join(comps_sorted)} ({len(comps_sorted)} номинаций)")

print("\n" + "="*80)
print("МОЯ ВЫБОРКА:")
print("  Daniel Curl, Florian Hamm, Camille Picano")
print("\nЧТО МОГЛО ВЛИЯТЬ:")
for name in ['Daniel Curl', 'Florian Hamm', 'Camille Picano']:
    if name in stats:
        st = stats[name]
        print(f"\n{name}:")
        print(f"  - Поинты: {st['points']:.0f} (позиция в топе по поинтам: {sorted_by_points.index((name, st))+1})")
        print(f"  - Победы: {st['wins']} (позиция в топе по победам: {sorted_by_wins.index((name, st))+1 if (name, st) in sorted_by_wins else 'N/A'})")
        print(f"  - Ивенты: {len(st['events'])} (позиция в топе по ивентам: {sorted_by_events.index((name, st))+1})")
        print(f"  - % европейских: {st['european_pct']:.1f}%")
        print(f"  - Номинации: {dict(st['competitions'])}")

