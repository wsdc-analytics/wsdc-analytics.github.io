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

skill_levels = {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}

european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland',
    'Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    return country in european_countries

def get_location_info(loc_id, event_name):
    if loc_id in loc:
        country = loc[loc_id]['country']
        city = loc[loc_id]['city']
        return f"{city}, {country}" if city else country
    elif 'Nordic' in event_name or 'Scandinavia' in event_name:
        return "Stockholm, Sweden"
    return ""

# Уже упомянутые танцоры
mentioned = {
    'Igor Pitangui', 'Aleksandra Radziejewska', 'Nicole Ramirez', 
    'Keerigan Rudd', 'Kristen Wallace', 'Zachary Skinner'
}

# Кандидаты из европейского топа
candidates = [
    'Charlie Fournier', 'Alexa Partos', 'Hanna Junk', 'Fabio Zanardelli',
    'Daniel Curl', 'Michael Kuss', 'Melina Voglhuber', 'Sebastian Gerwald',
    'Allan Thivoz', 'Joshua Schubert', 'Christina Landowski'
]

stats = {name: {
    'points': 0, 'wins': 0, 'events': set(), 'competitions': defaultdict(int),
    'roles': defaultdict(int), 'events_data': defaultdict(float),
    'global_points': 0, 'european_points_pct': 0
} for name in candidates}

# Собираем европейские данные
for row in open(RESULTS_FILE, newline='', encoding='utf-8'):
    row_data = {}
    # Простой парсинг, но лучше использовать csv.DictReader
    pass

# Используем DictReader
with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name:
            continue
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        role = row.get('dancer_role','')
        event_name = row.get('event_name','')
        
        # Глобальные поинты
        if comp in skill_levels and pts > 0:
            if dancer_name in stats:
                stats[dancer_name]['global_points'] += pts
        
        # Европейские данные
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        
        if not is_european_event(country, event_name):
            continue
        
        if comp not in skill_levels:
            continue
        
        if dancer_name not in stats:
            continue
        
        if pts > 0:
            st = stats[dancer_name]
            st['points'] += pts
            st['events'].add(event_name)
            st['competitions'][comp] += 1
            st['roles'][role] += 1
            st['events_data'][event_name] += pts
        
        if result == '1':
            stats[dancer_name]['wins'] += 1

# Рассчитываем процент европейских поинтов
for name, st in stats.items():
    if st['global_points'] > 0:
        st['european_points_pct'] = (st['points'] / st['global_points'] * 100)

# Фильтруем и сортируем кандидатов
filtered = [(name, st) for name, st in stats.items() if name not in mentioned and st['points'] > 0]
filtered.sort(key=lambda x: (
    x[1]['points'],  # По поинтам
    x[1]['wins'],    # По победам
    x[1]['european_points_pct']  # По проценту европейских поинтов
), reverse=True)

print("Топ-5 кандидатов для заметок (не упоминались ранее):")
print("="*80)
for i, (name, st) in enumerate(filtered[:8], 1):
    top_event, top_pts = max(st['events_data'].items(), key=lambda x: x[1])
    # Найдем локацию
    top_location = ""
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
                dancer_id = row.get('dancer_id','')
                if dancer_id_to_name.get(dancer_id,'') == name:
                    top_location = get_location_info(row.get('location_id',''), top_event)
                    break
    
    print(f"{i}. {name}:")
    print(f"   Европейские поинты: {st['points']:.0f}")
    print(f"   Глобальные поинты: {st['global_points']:.0f}")
    print(f"   % европейских: {st['european_points_pct']:.1f}%")
    print(f"   Победы: {st['wins']}, Ивенты: {len(st['events'])}")
    print(f"   Номинации: {dict(st['competitions'])}")
    print(f"   Роли: {dict(st['roles'])}")
    print(f"   Топ-ивент: {top_event} ({top_location}) - {int(top_pts)} поинтов")
    print()

