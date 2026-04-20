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

# Иерархия номинаций с весами
LEVEL_WEIGHTS = {
    'Champions': 3.0,
    'All-Stars': 2.0,
    'Advanced': 1.5,
    'Intermediate': 1.0,
    'Novice': 0.5,
    'Newcomer': 0.3
}

# Уже упомянутые
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
        weight = LEVEL_WEIGHTS[comp]
        
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

# Рассчитываем процент европейских поинтов
for name, st in stats.items():
    if st['global_points'] > 0:
        st['european_pct'] = (st['points'] / st['global_points'] * 100)
    else:
        st['european_pct'] = 100 if st['points'] > 0 else 0

# Комплексный score (приоритет: взвешенные поинты, затем взвешенные победы, затем количество ивентов)
for name, st in stats.items():
    st['composite_score'] = (
        st['weighted_points'] * 1.0 +      # Взвешенные поинты (главный фактор)
        st['weighted_wins'] * 10.0 +      # Взвешенные победы (важный фактор)
        len(st['events']) * 2.0           # Количество ивентов (дополнительный фактор)
    )

# Сортируем по комплексному score
sorted_dancers = sorted([(n, s) for n, s in stats.items() if s['points'] > 0], 
                       key=lambda x: x[1]['composite_score'], reverse=True)

print("ТОП-15 ЕВРОПЕЙСКИХ ТАНЦОРОВ ПО КОМПЛЕКСНОМУ SCORE")
print("(с учетом иерархии номинаций: Champions=3x, All-Stars=2x, Advanced=1.5x, Intermediate=1x, Novice=0.5x)")
print("="*100)

for i, (name, st) in enumerate(sorted_dancers[:15], 1):
    # Находим топ-ивент
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
    
    # Определяем высшую номинацию
    highest_level = max([l for l in st['points_by_level'].keys()], 
                       key=lambda x: LEVEL_WEIGHTS.get(x, 0)) if st['points_by_level'] else 'N/A'
    
    print(f"\n{i:2d}. {name}")
    print(f"    Комплексный score: {st['composite_score']:.1f}")
    print(f"    Поинты: {st['points']:.0f} (взвешенные: {st['weighted_points']:.1f})")
    print(f"    Победы: {st['wins']} (взвешенные: {st['weighted_wins']:.1f})")
    print(f"    Ивенты: {len(st['events'])}")
    print(f"    % европейских: {st['european_pct']:.1f}%")
    print(f"    Высшая номинация: {highest_level}")
    print(f"    Поинты по номинациям: {dict(st['points_by_level'])}")
    print(f"    Победы по номинациям: {dict(st['wins_by_level'])}")
    if top_event:
        print(f"    Топ-ивент: {top_event} ({top_location}) - {int(top_pts)} поинтов")

print("\n" + "="*100)
print("РЕКОМЕНДУЕМЫЕ ТОП-10 ДЛЯ ЗАМЕТОК:")
print("="*100)
for i, (name, st) in enumerate(sorted_dancers[:10], 1):
    highest = max([l for l in st['points_by_level'].keys()], 
                 key=lambda x: LEVEL_WEIGHTS.get(x, 0)) if st['points_by_level'] else 'N/A'
    print(f"{i:2d}. {name:25s} | Score: {st['composite_score']:6.1f} | {st['points']:5.0f} pts | {st['wins']} wins | {len(st['events'])} events | Top: {highest}")

