import csv
import re
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'
HTML_FILE = Path('/Users/ania/.cursor/wsdc-analytics-repo/dancers_2025.html')

# Загружаем данные
dancer_id_to_name = {}
name_to_dancer_id = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id = row['dancer_id']
        dancer_name = row.get('dancer_name','')
        dancer_id_to_name[dancer_id] = dancer_name
        if dancer_name:
            name_to_dancer_id[dancer_name] = dancer_id

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
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

us_states = {
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
    'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
    'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
    'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico',
    'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
    'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
}

def is_european_event(country, event_name, loc_id):
    if 'finnfest' in event_name.lower():
        return True
    if 'scandinavian open' in event_name.lower():
        return True
    if 'nordic' in event_name.lower() or 'scandinavia' in event_name.lower():
        return True
    return country in european_countries

def is_us_event(country, event_name):
    if country == 'United States':
        return True
    if 'SwingCouver' in event_name or 'The Open' in event_name or 'USA Grand Nationals' in event_name:
        return True
    return False

def is_russian_event(country):
    return country == 'Russia' or country == 'Russian Federation'

def is_spanish_event(country):
    return country == 'Spain'

# Читаем HTML и находим все highlight блоки
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Находим все блоки highlight-insight
pattern = r'<div class="highlight-insight"[^>]*>.*?<p><strong>([^<]+)</strong>.*?<strong>География:</strong>\s*([^<]+)</p>'
matches = re.findall(pattern, html_content, re.DOTALL)

print("Проверка географии для всех танцоров:")
print("="*80)

issues = []
checked = set()

for dancer_name_raw, geo_text in matches:
    dancer_name = dancer_name_raw.strip()
    
    # Пропускаем если это не имя танцора (слишком короткое или содержит служебные слова)
    if not dancer_name or len(dancer_name) < 3 or 'Самый' in dancer_name or 'География' in dancer_name:
        continue
    
    if dancer_name in checked:
        continue
    checked.add(dancer_name)
    
    dancer_id = name_to_dancer_id.get(dancer_name)
    if not dancer_id:
        # Пробуем найти похожее имя
        for name, did in name_to_dancer_id.items():
            if dancer_name.lower() == name.lower():
                dancer_id = did
                dancer_name = name
                break
    
    if not dancer_id:
        print(f"\n⚠️  Не найден dancer_id для: {dancer_name}")
        continue
    
    # Считаем реальную географию
    points_by_region = defaultdict(float)
    total_points = 0
    
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') != '2025':
                continue
            if row.get('dancer_id','') != dancer_id:
                continue
            
            comp = row.get('event_competition','')
            if comp not in skill_levels:
                continue
            
            loc_id = row.get('location_id','')
            country = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
            
            event_name = row.get('event_name','')
            pts = float(row.get('event_points','0') or 0)
            
            if pts > 0:
                total_points += pts
                
                if is_european_event(country, event_name, loc_id):
                    points_by_region['european'] += pts
                elif is_us_event(country, event_name):
                    points_by_region['us'] += pts
                elif is_russian_event(country):
                    points_by_region['russian'] += pts
                elif is_spanish_event(country):
                    points_by_region['spanish'] += pts
                else:
                    points_by_region['other'] += pts
    
    if total_points == 0:
        print(f"\n⚠️  {dancer_name}: нет поинтов в 2025")
        continue
    
    # Формируем описание реальной географии
    geo_parts = []
    if points_by_region['european'] > 0:
        pct = points_by_region['european'] / total_points * 100
        if abs(pct - 100) < 0.1:
            geo_parts.append("все поинты набрал(а) на европейских ивентах")
        else:
            geo_parts.append(f"{pct:.1f}% поинтов набрал(а) на европейских ивентах")
    
    if points_by_region['us'] > 0:
        pct = points_by_region['us'] / total_points * 100
        geo_parts.append(f"{pct:.1f}% на американских ивентах")
    
    if points_by_region['russian'] > 0:
        pct = points_by_region['russian'] / total_points * 100
        geo_parts.append(f"{pct:.1f}% на российских ивентах")
    
    if points_by_region['spanish'] > 0:
        pct = points_by_region['spanish'] / total_points * 100
        geo_parts.append(f"{pct:.1f}% на испанских ивентах")
    
    if points_by_region['other'] > 0:
        pct = points_by_region['other'] / total_points * 100
        geo_parts.append(f"{pct:.1f}% на других ивентах")
    
    real_geo = ", ".join(geo_parts)
    stated_geo = geo_text.strip()
    
    # Проверяем соответствие
    print(f"\n{dancer_name}:")
    print(f"  Заявлено: {stated_geo}")
    print(f"  Реально:   {real_geo}")
    
    # Проверка на "все поинты" когда это не так
    if "все поинты" in stated_geo.lower() and "европейских" in stated_geo.lower():
        if abs(points_by_region['european'] / total_points - 1.0) > 0.01:
            issues.append((dancer_name, stated_geo, real_geo))
            print(f"  ⚠️  НЕСООТВЕТСТВИЕ: заявлено 'все поинты на европейских', но реально не 100%!")
    elif "все поинты" in stated_geo.lower() and "американских" in stated_geo.lower():
        if abs(points_by_region['us'] / total_points - 1.0) > 0.01:
            issues.append((dancer_name, stated_geo, real_geo))
            print(f"  ⚠️  НЕСООТВЕТСТВИЕ: заявлено 'все поинты на американских', но реально не 100%!")

if issues:
    print("\n" + "="*80)
    print("НАЙДЕНЫ ПРОБЛЕМЫ:")
    for dancer, stated, real in issues:
        print(f"\n{dancer}:")
        print(f"  Заявлено: {stated}")
        print(f"  Должно быть: {real}")
else:
    print("\n" + "="*80)
    print("✅ Все проверки пройдены!")
