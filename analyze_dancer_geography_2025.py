#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)
df_locations = pd.read_csv(LOCATION_FILE, low_memory=False)

# Фильтруем 2025 и skill-level
df_2025 = df_results[df_results['event_year'] == 2025].copy()
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']
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
    
    # Европа
    european_countries = ['United Kingdom', 'France', 'Germany', 'Spain', 'Italy', 'Netherlands', 
                          'Poland', 'Sweden', 'Denmark', 'Norway', 'Finland', 'Belgium', 'Switzerland',
                          'Austria', 'Portugal', 'Greece', 'Ireland', 'Czech Republic', 'Hungary',
                          'Romania', 'Croatia', 'Slovenia', 'Estonia', 'Latvia', 'Lithuania',
                          'Russia', 'Ukraine', 'Belarus', 'Bulgaria', 'Serbia']
    
    # США и Канада
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

# Топ-10 по поинтам для анализа
top_points = df_skill.groupby('dancer_id').agg({
    'event_points': 'sum'
}).reset_index().nlargest(10, 'event_points')

print("=" * 80)
print("ГЕОГРАФИЧЕСКИЙ АНАЛИЗ ТОП-10 ТАНЦОРОВ ПО ПОИНТАМ")
print("=" * 80)

for _, top_dancer in top_points.iterrows():
    dancer_id = top_dancer['dancer_id']
    dancer_data = df_skill[df_skill['dancer_id'] == dancer_id]
    dancer_name = dancer_data['dancer_name'].iloc[0] if len(dancer_data) > 0 else f'ID: {dancer_id}'
    
    total_points = dancer_data['event_points'].sum()
    total_wins = len(dancer_data[dancer_data['event_result'].astype(str) == '1'])
    total_events = dancer_data['event_name'].nunique()
    
    print(f"\n{dancer_name} (ID: {dancer_id})")
    print(f"  Всего: {total_points} поинтов, {total_wins} побед, {total_events} ивентов")
    
    # Анализ по регионам
    region_stats = dancer_data.groupby('region').agg({
        'event_points': 'sum',
        'event_name': 'nunique',
        'event_result': lambda x: len(x[x.astype(str) == '1'])
    }).sort_values('event_points', ascending=False)
    
    print(f"\n  По регионам:")
    for region, row in region_stats.iterrows():
        region_wins = len(dancer_data[
            (dancer_data['region'] == region) & 
            (dancer_data['event_result'].astype(str) == '1')
        ])
        region_events = dancer_data[dancer_data['region'] == region]['event_name'].nunique()
        pct_points = (row['event_points'] / total_points * 100) if total_points > 0 else 0
        print(f"    {region}: {row['event_points']} поинтов ({pct_points:.1f}%), "
              f"{region_wins} побед, {region_events} ивентов")
    
    # Топ-3 ивента по поинтам
    event_stats = dancer_data.groupby('event_name').agg({
        'event_points': 'sum',
        'event_country': 'first',
        'event_city': 'first',
        'region': 'first',
        'event_result': lambda x: len(x[x.astype(str) == '1'])
    }).sort_values('event_points', ascending=False).head(3)
    
    print(f"\n  Топ-3 ивента по поинтам:")
    for event_name, row in event_stats.iterrows():
        event_wins = len(dancer_data[
            (dancer_data['event_name'] == event_name) & 
            (dancer_data['event_result'].astype(str) == '1')
        ])
        city = row.get('event_city', 'N/A')
        country = row.get('event_country', 'N/A')
        region = row.get('region', 'N/A')
        print(f"    {event_name} ({city}, {country}, {region}): "
              f"{row['event_points']} поинтов, {event_wins} побед")
    
    # Победы по регионам
    wins_data = dancer_data[dancer_data['event_result'].astype(str) == '1']
    if len(wins_data) > 0:
        wins_by_region = wins_data.groupby('region').size().sort_values(ascending=False)
        print(f"\n  Победы по регионам:")
        for region, count in wins_by_region.items():
            region_wins = wins_data[wins_data['region'] == region]
            print(f"    {region}: {count} побед")
            for _, win in region_wins.iterrows():
                event_name = win.get('event_name', 'N/A')
                city = win.get('event_city', 'N/A')
                country = win.get('event_country', 'N/A')
                role = win.get('event_role', 'N/A')
                print(f"      - {event_name} ({city}, {country}) - {role}")

print("\n" + "=" * 80)

