#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import json

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)
df_locations = pd.read_csv(LOCATION_FILE, low_memory=False)

# Фильтруем 2025 и skill-level
df_2025 = df_results[df_results['event_year'] == 2025].copy()
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated']
df_skill = df_2025[df_2025['event_competition'].isin(skill_levels)].copy()

df_skill['event_points'] = pd.to_numeric(df_skill['event_points'], errors='coerce')
df_skill = df_skill[df_skill['event_points'].notna() & (df_skill['event_points'] > 0)]

# Соединяем с локациями
df_skill = df_skill.merge(df_locations[['location_id', 'event_country', 'event_city', 'event_state']], 
                          on='location_id', how='left')

# Определяем регионы
def get_region(country):
    if pd.isna(country):
        return 'Unknown'
    country_str = str(country).strip()
    
    european_countries = ['United Kingdom', 'France', 'Germany', 'Spain', 'Italy', 'Netherlands', 
                          'Poland', 'Sweden', 'Denmark', 'Norway', 'Finland', 'Belgium', 'Switzerland',
                          'Austria', 'Portugal', 'Greece', 'Ireland', 'Czech Republic', 'Hungary',
                          'Romania', 'Croatia', 'Slovenia', 'Estonia', 'Latvia', 'Lithuania',
                          'Russia', 'Ukraine', 'Belarus', 'Bulgaria', 'Serbia']
    
    if country_str == 'United States' or country_str == 'Canada':
        return 'North America'
    elif country_str in european_countries:
        return 'Europe'
    elif country_str in ['Australia', 'New Zealand']:
        return 'Oceania'
    elif country_str in ['Japan', 'South Korea', 'China', 'Singapore', 'Thailand', 'Malaysia',
                         'Philippines', 'Indonesia', 'Taiwan', 'Republic of Korea']:
        return 'Asia'
    elif country_str in ['Brazil', 'Argentina', 'Mexico', 'Chile', 'Colombia']:
        return 'Latin America'
    else:
        return 'Other'

df_skill['region'] = df_skill['event_country'].apply(get_region)

# Соединяем с именами
df_skill['dancer_id'] = df_skill['dancer_id'].astype(str)
df_dancers['dancer_id'] = df_dancers['dancer_id'].astype(str)
df_skill = df_skill.merge(df_dancers[['dancer_id', 'dancer_name']], on='dancer_id', how='left')

# Читаем все топы
tops_dir = Path('.')
csv_files = [
    'dancers_top_points_2025.csv',
    'dancers_top_wins_2025.csv',
    'dancers_top_events_2025.csv',
    'russian_dancers_top_points_2025.csv',
    'russian_dancers_top_wins_2025.csv',
    'russian_dancers_top_events_2025.csv',
    'sophisticated_top_points_2025.csv',
    'sophisticated_top_wins_2025.csv',
    'sophisticated_top_events_2025.csv'
]

all_dancer_names = set()
for csv_file in csv_files:
    file_path = tops_dir / csv_file
    if file_path.exists():
        df = pd.read_csv(file_path)
        if 'dancer_name' in df.columns:
            all_dancer_names.update(df['dancer_name'].tolist())

# Анализируем каждого танцора
results = {}

for dancer_name in sorted(all_dancer_names):
    dancer_data = df_skill[df_skill['dancer_name'] == dancer_name]
    
    if len(dancer_data) == 0:
        continue
    
    dancer_id = dancer_data['dancer_id'].iloc[0]
    total_points = dancer_data['event_points'].sum()
    total_wins = len(dancer_data[dancer_data['event_result'].astype(str) == '1'])
    total_events = dancer_data['event_name'].nunique()
    
    # Анализ по регионам
    region_stats = dancer_data.groupby('region').agg({
        'event_points': 'sum',
        'event_name': 'nunique',
        'event_result': lambda x: len(x[x.astype(str) == '1'])
    }).sort_values('event_points', ascending=False)
    
    regions_with_points = len(region_stats)
    top_region = region_stats.index[0] if len(region_stats) > 0 else None
    top_region_pct = (region_stats.iloc[0]['event_points'] / total_points * 100) if total_points > 0 and len(region_stats) > 0 else 0
    
    # Победы по регионам
    wins_data = dancer_data[dancer_data['event_result'].astype(str) == '1']
    wins_by_region = wins_data.groupby('region').size().to_dict() if len(wins_data) > 0 else {}
    regions_with_wins = len(wins_by_region)
    
    # Топ ивент
    event_stats = dancer_data.groupby('event_name').agg({
        'event_points': 'sum',
        'event_country': 'first',
        'event_city': 'first',
        'region': 'first'
    }).sort_values('event_points', ascending=False)
    
    top_event = None
    top_event_points = 0
    top_event_location = None
    if len(event_stats) > 0:
        top_event = event_stats.index[0]
        top_event_points = event_stats.iloc[0]['event_points']
        city = event_stats.iloc[0].get('event_city', 'N/A')
        country = event_stats.iloc[0].get('event_country', 'N/A')
        region = event_stats.iloc[0].get('region', 'N/A')
        top_event_location = f"{city}, {country}, {region}"
    
    # Определяем интересные инсайты
    insights = []
    
    # Международность (3+ региона с поинтами)
    if regions_with_points >= 3:
        insights.append(f"международная активность: поинты на ивентах в {regions_with_points} регионах")
    
    # Победы в нескольких регионах
    if regions_with_wins >= 2:
        insights.append(f"победы в {regions_with_wins} регионах")
    
    # Сильная региональная специализация (>90% в одном регионе)
    if top_region_pct >= 90:
        insights.append(f"сильная специализация на {top_region} регионе ({top_region_pct:.1f}% поинтов)")
    
    # Топ ивент с высоким количеством поинтов
    if top_event_points >= 20:
        insights.append(f"самый успешный ивент: {top_event} ({top_event_location}) с {top_event_points} поинтами")
    
    results[dancer_name] = {
        'dancer_id': dancer_id,
        'total_points': total_points,
        'total_wins': total_wins,
        'total_events': total_events,
        'regions_count': regions_with_points,
        'top_region': top_region,
        'top_region_pct': top_region_pct,
        'wins_regions_count': regions_with_wins,
        'wins_by_region': wins_by_region,
        'top_event': top_event,
        'top_event_points': top_event_points,
        'top_event_location': top_event_location,
        'region_stats': region_stats.to_dict('index') if len(region_stats) > 0 else {},
        'insights': insights
    }

# Выводим результаты с интересными инсайтами
print("=" * 100)
print("ГЕОГРАФИЧЕСКИЙ АНАЛИЗ ВСЕХ ТАНЦОРОВ ИЗ ТОПОВ")
print("=" * 100)

# Сортируем по количеству интересных инсайтов
dancers_with_insights = [(name, data) for name, data in results.items() if len(data['insights']) > 0]
dancers_with_insights.sort(key=lambda x: (len(x[1]['insights']), x[1]['total_points']), reverse=True)

print(f"\nТанцоры с интересными географическими инсайтами ({len(dancers_with_insights)}):")
print()

for dancer_name, data in dancers_with_insights:
    print(f"{dancer_name}")
    print(f"  Всего: {data['total_points']} поинтов, {data['total_wins']} побед, {data['total_events']} ивентов")
    print(f"  Инсайты:")
    for insight in data['insights']:
        print(f"    - {insight}")
    print()

# Также выводим полный список для справки
print("=" * 100)
print("ПОЛНЫЙ СПИСОК (включая без инсайтов):")
print("=" * 100)

for dancer_name, data in sorted(results.items()):
    print(f"{dancer_name}: {data['total_points']} поинтов, {data['total_wins']} побед, {data['total_events']} ивентов, {data['regions_count']} регионов")
    if data['top_region']:
        print(f"  Топ регион: {data['top_region']} ({data['top_region_pct']:.1f}%)")
    if data['top_event']:
        print(f"  Топ ивент: {data['top_event']} ({data['top_event_location']}) - {data['top_event_points']} поинтов")
    print()

