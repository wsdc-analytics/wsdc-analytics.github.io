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

def get_location_info(loc_id, event_name):
    if loc_id in loc:
        country = loc[loc_id]['country']
        city = loc[loc_id]['city']
        return f"{city}, {country}" if city else country
    elif 'Nordic' in event_name or 'Scandinavia' in event_name:
        return "Stockholm, Sweden"
    return ""

LEVEL_WEIGHTS = {
    'Champions': 3.0, 'All-Stars': 2.0, 'Advanced': 1.5,
    'Intermediate': 1.0, 'Novice': 0.5, 'Newcomer': 0.3
}
LEVEL_ORDER = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']

mentioned = {
    'Igor Pitangui', 'Aleksandra Radziejewska', 'Nicole Ramirez', 
    'Keerigan Rudd', 'Kristen Wallace', 'Zachary Skinner',
    'Charlie Fournier', 'Sebastian Gerwald', 'Alexa Partos', 
    'Fabio Zanardelli', 'Hanna Junk'
}

stats = {}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in LEVEL_WEIGHTS:
            continue
        
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name or dancer_name in mentioned:
            continue
        
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        event_name = row.get('event_name','')
        if not is_european_event(country, event_name):
            continue
        
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        role = row.get('dancer_role','')
        weight = LEVEL_WEIGHTS[comp]
        
        if dancer_name not in stats:
            stats[dancer_name] = {
                'points': 0, 'weighted_points': 0,
                'wins': 0, 'weighted_wins': 0,
                'events': set(), 'competitions': defaultdict(int),
                'points_by_level': defaultdict(float),
                'wins_by_level': defaultdict(int),
                'roles': defaultdict(int),
                'events_data': defaultdict(float),
                'global_points': 0
            }
        
        st = stats[dancer_name]
        
        if pts > 0:
            st['points'] += pts
            st['weighted_points'] += pts * weight
            st['points_by_level'][comp] += pts
            st['events'].add(event_name)
            st['competitions'][comp] += 1
            st['roles'][role] += 1
            st['events_data'][event_name] += pts
        
        if result == '1':
            st['wins'] += 1
            st['weighted_wins'] += weight
            st['wins_by_level'][comp] += 1

# Считаем глобальные поинты
with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in LEVEL_WEIGHTS:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name in stats:
            pts = float(row.get('event_points','0') or 0)
            if pts > 0:
                stats[dancer_name]['global_points'] += pts

# Рассчитываем дополнительные метрики
for name, st in stats.items():
    if st['global_points'] > 0:
        st['european_pct'] = (st['points'] / st['global_points'] * 100)
    else:
        st['european_pct'] = 100 if st['points'] > 0 else 0
    
    # Высшая номинация
    if st['points_by_level']:
        st['highest_level'] = max([l for l in st['points_by_level'].keys()], 
                                  key=lambda x: LEVEL_WEIGHTS.get(x, 0))
    else:
        st['highest_level'] = None
    
    # Количество номинаций с поинтами
    st['num_levels'] = len(st['points_by_level'])
    
    # Прогрессия через номинации (последовательные уровни)
    levels_with_points = sorted([l for l in st['points_by_level'].keys()], 
                               key=lambda x: LEVEL_ORDER.index(x) if x in LEVEL_ORDER else 99)
    st['progression'] = levels_with_points
    st['has_progression'] = len(levels_with_points) >= 2 and all(
        LEVEL_ORDER.index(levels_with_points[i+1]) - LEVEL_ORDER.index(levels_with_points[i]) == 1
        for i in range(len(levels_with_points)-1)
    )
    
    # Специализация (только одна номинация)
    st['specialized'] = len(st['points_by_level']) == 1

# ФИЛЬТРУЕМ: только с поинтами > 0
candidates = {name: st for name, st in stats.items() if st['points'] > 0}

print("="*100)
print("СТРАТЕГИЯ ВЫБОРА: РАЗНООБРАЗНАЯ КАРТИНА ЕВРОПЕЙСКИХ ДОСТИЖЕНИЙ")
print("="*100)

# КАТЕГОРИЯ 1: Лидеры по взвешенным поинтам (высшие номинации)
print("\n1. ЛИДЕРЫ ПО ВЗВЕШЕННЫМ ПОИНТАМ (акцент на высшие номинации):")
sorted_by_weighted = sorted(candidates.items(), key=lambda x: x[1]['weighted_points'], reverse=True)
for i, (name, st) in enumerate(sorted_by_weighted[:5], 1):
    print(f"  {i}. {name:25s} | Weighted: {st['weighted_points']:6.1f} | Raw: {st['points']:5.0f} | Top: {st['highest_level']}")

# КАТЕГОРИЯ 2: Лидеры по взвешенным победам
print("\n2. ЛИДЕРЫ ПО ВЗВЕШЕННЫМ ПОБЕДАМ:")
sorted_by_weighted_wins = sorted(candidates.items(), key=lambda x: x[1]['weighted_wins'], reverse=True)
for i, (name, st) in enumerate(sorted_by_weighted_wins[:5], 1):
    print(f"  {i}. {name:25s} | Weighted wins: {st['weighted_wins']:4.1f} | Wins: {st['wins']} | Top: {st['highest_level']}")

# КАТЕГОРИЯ 3: Лидеры по количеству ивентов
print("\n3. ЛИДЕРЫ ПО КОЛИЧЕСТВУ ИВЕНТОВ:")
sorted_by_events = sorted(candidates.items(), key=lambda x: len(x[1]['events']), reverse=True)
for i, (name, st) in enumerate(sorted_by_events[:5], 1):
    print(f"  {i}. {name:25s} | Events: {len(st['events']):2d} | Points: {st['points']:5.0f} | Top: {st['highest_level']}")

# КАТЕГОРИЯ 4: Прогрессия через номинации
print("\n4. ПРОГРЕССИЯ ЧЕРЕЗ НОМИНАЦИИ (2+ последовательных уровня):")
progression_candidates = [(n, s) for n, s in candidates.items() if s['has_progression']]
progression_candidates.sort(key=lambda x: (len(x[1]['progression']), x[1]['points']), reverse=True)
for i, (name, st) in enumerate(progression_candidates[:5], 1):
    prog_str = ' → '.join(st['progression'])
    print(f"  {i}. {name:25s} | {prog_str} | Points: {st['points']:5.0f}")

# КАТЕГОРИЯ 5: Специализация в одной номинации (особенно высшей)
print("\n5. СПЕЦИАЛИЗАЦИЯ В ВЫСШИХ НОМИНАЦИЯХ (только All-Stars/Champions):")
specialized_high = [(n, s) for n, s in candidates.items() 
                   if s['specialized'] and s['highest_level'] in ['All-Stars', 'Champions']]
specialized_high.sort(key=lambda x: (LEVEL_WEIGHTS.get(x[1]['highest_level'], 0), x[1]['points']), reverse=True)
for i, (name, st) in enumerate(specialized_high[:5], 1):
    level = st['highest_level']
    print(f"  {i}. {name:25s} | {level:12s} | {st['points']:5.0f} pts | {st['wins']} wins | {len(st['events'])} events")

# КАТЕГОРИЯ 6: Высокие результаты в средних номинациях (Novice, Intermediate)
print("\n6. ВЫСОКИЕ РЕЗУЛЬТАТЫ В СРЕДНИХ НОМИНАЦИЯХ (Novice, Intermediate):")
mid_level_high = [(n, s) for n, s in candidates.items() 
                  if 'Novice' in s['points_by_level'] or 'Intermediate' in s['points_by_level']]
mid_level_high.sort(key=lambda x: (
    max([s['points_by_level'].get('Novice', 0) + s['points_by_level'].get('Intermediate', 0) for s in [x[1]]]),
    x[1]['points']
), reverse=True)
for i, (name, st) in enumerate(mid_level_high[:5], 1):
    levels_str = ', '.join([f"{l}: {int(v)}" for l, v in st['points_by_level'].items() if l in ['Novice', 'Intermediate']])
    print(f"  {i}. {name:25s} | {levels_str} | Total: {st['points']:5.0f}")

print("\n" + "="*100)
print("РЕКОМЕНДУЕМАЯ ДИВЕРСИФИЦИРОВАННАЯ ВЫБОРКА (10 ТАНЦОРОВ):")
print("="*100)

selected = set()
final_list = []

# 1-2: Топ по взвешенным поинтам (высшие номинации)
for name, st in sorted_by_weighted:
    if name not in selected and len(final_list) < 2:
        selected.add(name)
        final_list.append((name, st, "Leader by weighted points"))

# 3-4: Топ по взвешенным победам
for name, st in sorted_by_weighted_wins:
    if name not in selected and len(final_list) < 4:
        selected.add(name)
        final_list.append((name, st, "Leader by weighted wins"))

# 5: Лидер по ивентам (если еще не выбран)
for name, st in sorted_by_events:
    if name not in selected and len(final_list) < 5:
        selected.add(name)
        final_list.append((name, st, "Leader by events"))
        break

# 6-7: Прогрессия через номинации
for name, st in progression_candidates:
    if name not in selected and len(final_list) < 7:
        selected.add(name)
        final_list.append((name, st, f"Progression: {' → '.join(st['progression'])}"))
        if len(final_list) >= 7:
            break

# 8-9: Специализация в высших номинациях
for name, st in specialized_high:
    if name not in selected and len(final_list) < 9:
        selected.add(name)
        final_list.append((name, st, f"Specialized in {st['highest_level']}"))
        if len(final_list) >= 9:
            break

# 10: Высокие результаты в средних номинациях
for name, st in mid_level_high:
    if name not in selected and len(final_list) < 10:
        selected.add(name)
        mid_levels = [l for l in st['points_by_level'].keys() if l in ['Novice', 'Intermediate']]
        final_list.append((name, st, f"High results in {', '.join(mid_levels)}"))
        break

# Если не хватает до 10, дополняем по взвешенным поинтам
for name, st in sorted_by_weighted:
    if name not in selected and len(final_list) < 10:
        selected.add(name)
        final_list.append((name, st, "High weighted points"))

print("\nФИНАЛЬНЫЙ СПИСОК:")
for i, (name, st, reason) in enumerate(final_list, 1):
    top_event, top_pts = max(st['events_data'].items(), key=lambda x: x[1]) if st['events_data'] else ('', 0)
    top_location = ""
    if top_event:
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
                    dancer_id = row.get('dancer_id','')
                    if dancer_id_to_name.get(dancer_id,'') == name:
                        top_location = get_location_info(row.get('location_id',''), top_event)
                        break
    
    print(f"\n{i:2d}. {name}")
    print(f"    Причина выбора: {reason}")
    print(f"    Поинты: {st['points']:.0f} (взвешенные: {st['weighted_points']:.1f})")
    print(f"    Победы: {st['wins']} (взвешенные: {st['weighted_wins']:.1f})")
    print(f"    Ивенты: {len(st['events'])}")
    print(f"    Высшая номинация: {st['highest_level']}")
    print(f"    Поинты по номинациям: {dict(st['points_by_level'])}")
    print(f"    Победы по номинациям: {dict(st['wins_by_level'])}")
    print(f"    % европейских: {st['european_pct']:.1f}%")
    if top_event:
        print(f"    Топ-ивент: {top_event} ({top_location}) - {int(top_pts)} поинтов")

