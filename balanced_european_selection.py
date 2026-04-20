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

for name, st in stats.items():
    if st['global_points'] > 0:
        st['european_pct'] = (st['points'] / st['global_points'] * 100)
    else:
        st['european_pct'] = 100 if st['points'] > 0 else 0
    
    if st['points_by_level']:
        st['highest_level'] = max([l for l in st['points_by_level'].keys()], 
                                  key=lambda x: LEVEL_WEIGHTS.get(x, 0))
    else:
        st['highest_level'] = None
    
    levels_with_points = sorted([l for l in st['points_by_level'].keys()], 
                               key=lambda x: LEVEL_ORDER.index(x) if x in LEVEL_ORDER else 99)
    st['progression'] = levels_with_points
    st['has_progression'] = len(levels_with_points) >= 2 and all(
        LEVEL_ORDER.index(levels_with_points[i+1]) - LEVEL_ORDER.index(levels_with_points[i]) == 1
        for i in range(len(levels_with_points)-1)
    ) if len(levels_with_points) >= 2 else False

candidates = {name: st for name, st in stats.items() if st['points'] > 0}

# Топ-10 по поинтам
top_points = sorted(candidates.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
top_points_dict = {name: i+1 for i, (name, _) in enumerate(top_points)}

# Топ-10 по победам
top_wins = sorted([(n, s) for n, s in candidates.items() if s['wins'] > 0], 
                 key=lambda x: x[1]['wins'], reverse=True)[:10]
top_wins_dict = {name: i+1 for i, (name, _) in enumerate(top_wins)}

# Топ-10 по ивентам
top_events = sorted(candidates.items(), key=lambda x: len(x[1]['events']), reverse=True)[:10]
top_events_dict = {name: i+1 for i, (name, _) in enumerate(top_events)}

print("="*100)
print("АНАЛИЗ: ТОП-10 ПО КАЖДОЙ МЕТРИКЕ")
print("="*100)

print("\nТОП-10 ПО ПОИНТАМ:")
for i, (name, st) in enumerate(top_points, 1):
    wins_rank = top_wins_dict.get(name, '-')
    events_rank = top_events_dict.get(name, '-')
    wins_str = str(wins_rank) if isinstance(wins_rank, int) else wins_rank
    events_str = str(events_rank) if isinstance(events_rank, int) else events_rank
    print(f"{i:2d}. {name:25s} | {st['points']:5.0f} pts | Wins rank: {wins_str:>2s} | Events rank: {events_str:>2s} | Top: {st['highest_level']}")

print("\nТОП-10 ПО ПОБЕДАМ:")
for i, (name, st) in enumerate(top_wins, 1):
    points_rank = top_points_dict.get(name, '-')
    events_rank = top_events_dict.get(name, '-')
    points_str = str(points_rank) if isinstance(points_rank, int) else points_rank
    events_str = str(events_rank) if isinstance(events_rank, int) else events_rank
    print(f"{i:2d}. {name:25s} | {st['wins']} wins | Points rank: {points_str:>2s} | Events rank: {events_str:>2s} | Top: {st['highest_level']}")

print("\nТОП-10 ПО ИВЕНТАМ:")
for i, (name, st) in enumerate(top_events, 1):
    points_rank = top_points_dict.get(name, '-')
    wins_rank = top_wins_dict.get(name, '-')
    points_str = str(points_rank) if isinstance(points_rank, int) else points_rank
    wins_str = str(wins_rank) if isinstance(wins_rank, int) else wins_rank
    print(f"{i:2d}. {name:25s} | {len(st['events'])} events | Points rank: {points_str:>2s} | Wins rank: {wins_str:>2s} | Top: {st['highest_level']}")

# Находим танцоров, которые входят хотя бы в один топ-10
in_at_least_one_top = set(top_points_dict.keys()) | set(top_wins_dict.keys()) | set(top_events_dict.keys())

print("\n" + "="*100)
print("ТАНЦОРЫ В ТОП-10 (ХОТЯ БЫ ПО ОДНОЙ МЕТРИКЕ):")
print("="*100)

candidates_in_tops = [(name, st) for name, st in candidates.items() if name in in_at_least_one_top]
candidates_in_tops.sort(key=lambda x: (
    min([top_points_dict.get(x[0], 999), top_wins_dict.get(x[0], 999), top_events_dict.get(x[0], 999)]),
    x[1]['weighted_points'],
    x[1]['points']
))

for name, st in candidates_in_tops:
    p_rank = top_points_dict.get(name, '-')
    w_rank = top_wins_dict.get(name, '-')
    e_rank = top_events_dict.get(name, '-')
    p_str = str(p_rank) if isinstance(p_rank, int) else p_rank
    w_str = str(w_rank) if isinstance(w_rank, int) else w_rank
    e_str = str(e_rank) if isinstance(e_rank, int) else e_rank
    print(f"{name:25s} | Points: {p_str:>2s} ({st['points']:5.0f}) | Wins: {w_str:>2s} ({st['wins']}) | Events: {e_str:>2s} ({len(st['events']):2d}) | Top: {st['highest_level']} | Progression: {st['has_progression']}")

# Выбираем разнообразную выборку из тех, кто в топах
print("\n" + "="*100)
print("РЕКОМЕНДУЕМАЯ СБАЛАНСИРОВАННАЯ ВЫБОРКА:")
print("="*100)
print("Приоритет: топ-10, разнообразие по метрикам, упоминание высших номинаций")

selected = set()
final_list = []

# 1-3: Лидеры по поинтам
for name, st in top_points[:3]:
    if name not in selected:
        selected.add(name)
        final_list.append((name, st, "Top by points"))

# 4-5: Лидеры по победам (если еще не выбраны)
for name, st in top_wins:
    if name not in selected and len(final_list) < 5:
        selected.add(name)
        final_list.append((name, st, "Top by wins"))

# 6: Лидер по ивентам (если еще не выбран)
for name, st in top_events:
    if name not in selected and len(final_list) < 6:
        selected.add(name)
        final_list.append((name, st, "Top by events"))
        break

# 7-8: Из топ-10 по поинтам с интересными особенностями (прогрессия, высшие номинации)
for name, st in top_points[3:]:
    if name not in selected and len(final_list) < 8:
        if st['has_progression'] or st['highest_level'] in ['Champions', 'All-Stars']:
            selected.add(name)
            reason = "Progression" if st['has_progression'] else f"High level: {st['highest_level']}"
            final_list.append((name, st, reason))
            if len(final_list) >= 8:
                break

# 9-10: Дополняем из топ-10 по поинтам
for name, st in top_points:
    if name not in selected and len(final_list) < 10:
        selected.add(name)
        final_list.append((name, st, "Top by points"))
        if len(final_list) >= 10:
            break

print(f"\nФИНАЛЬНЫЙ СПИСОК ({len(final_list)} танцоров):")
for i, (name, st, reason) in enumerate(final_list, 1):
    p_rank = top_points_dict.get(name, '-')
    w_rank = top_wins_dict.get(name, '-')
    e_rank = top_events_dict.get(name, '-')
    p_str = str(p_rank) if isinstance(p_rank, int) else p_rank
    w_str = str(w_rank) if isinstance(w_rank, int) else w_rank
    e_str = str(e_rank) if isinstance(e_rank, int) else e_rank
    print(f"{i:2d}. {name:25s} | P:{p_str:>2s} W:{w_str:>2s} E:{e_str:>2s} | {st['points']:5.0f}pts {st['wins']}w {len(st['events']):2d}e | {reason}")

