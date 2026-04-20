import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

skill_levels = {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions','Sophisticated'}

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

russian_dancers = [
    'Elena Kotelnikova',
    'Tatiana Kaneva',
    'Polina Khapaeva',
    'Marina Kondrateva',
    'Anastasiya Yuzhakova',
    'Olga Khvan',
    'Kalaychidi Vladislav',
    'Anton Zverev',
    'Daniel Pavlov',
    'Ekaterina Grigorieva',
    'Marina Motronenko'
]

def is_russian_event(country):
    return country == 'Russia'

def is_european_event(country):
    european = {'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria','Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia','Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'}
    return country in european

stats = {name:{
    'total_points':0,
    'russian_points':0,
    'european_points':0,
    'other_points':0,
    'russian_events':set(),
    'european_events':set(),
    'allstars_points':0,
    'champions_points':0,
    'wins':0,
    'russian_wins':0,
    'european_wins':0,
    'competitions':defaultdict(lambda: {'points':0, 'wins':0})
} for name in russian_dancers}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            year = int(row.get('event_year','0'))
        except:
            continue
        if year != 2025:
            continue
        comp = row.get('event_competition','')
        if comp not in skill_levels:
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name not in stats:
            continue
        country = ''
        city = ''
        loc_id = row.get('location_id','')
        if loc_id in loc:
            country = loc[loc_id]['country']
            city = loc[loc_id]['city']
        
        st = stats[dancer_name]
        st['total_points'] += points
        st['competitions'][comp]['points'] += points
        
        if is_russian_event(country):
            st['russian_points'] += points
            st['russian_events'].add(row.get('event_name',''))
        elif is_european_event(country):
            st['european_points'] += points
            st['european_events'].add(row.get('event_name',''))
        else:
            st['other_points'] += points
        
        if comp == 'All-Stars':
            st['allstars_points'] += points
        elif comp == 'Champions':
            st['champions_points'] += points
        
        if str(row.get('event_result','')) == '1':
            st['wins'] += 1
            st['competitions'][comp]['wins'] += 1
            if is_russian_event(country):
                st['russian_wins'] += 1
            elif is_european_event(country):
                st['european_wins'] += 1

print("Географический анализ российских танцоров:")
print("="*80)
for name, st in sorted(stats.items(), key=lambda x: x[1]['total_points'], reverse=True):
    if st['total_points'] == 0:
        continue
    russian_pct = (st['russian_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0
    european_pct = (st['european_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0
    
    geo_text = ""
    if russian_pct > 0 and european_pct > 0:
        geo_text = f"{russian_pct:.1f}% на российских ивентах ({len(st['russian_events'])} ивентов), {european_pct:.1f}% на европейских ({len(st['european_events'])} ивентов)"
    elif russian_pct > 90:
        geo_text = f"все {st['total_points']:.0f} поинтов на российских ивентах ({len(st['russian_events'])} ивентов) - локальное достижение"
    elif european_pct > 90:
        geo_text = f"{european_pct:.1f}% на европейских ивентах ({len(st['european_events'])} ивентов), что демонстрирует успех на международной арене"
    
    print(f"{name}:")
    print(f"  Всего: {st['total_points']:.0f} поинтов")
    print(f"  География: {geo_text}")
    print(f"  All-Stars: {st['allstars_points']:.0f} поинтов")
    print(f"  Champions: {st['champions_points']:.0f} поинтов")
    print()

print("\n"+"="*80)
print("Лидеры по All-Stars среди российских танцоров:")
print("="*80)
allstars_leaders = sorted([(name, st['allstars_points'], st['total_points']) for name, st in stats.items() if st['allstars_points'] > 0], key=lambda x: x[1], reverse=True)
for name, allstars_pts, total_pts in allstars_leaders[:5]:
    print(f"{name}: {allstars_pts:.0f} поинтов в All-Stars (из {total_pts:.0f} всего)")

