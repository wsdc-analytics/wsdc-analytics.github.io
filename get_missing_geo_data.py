#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

# Читаем данные
df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)
df_locations = pd.read_csv(LOCATION_FILE, low_memory=False)

# Фильтруем 2025
df_2025 = df_results[df_results['event_year'] == 2025].copy()
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated']
df_skill = df_2025[df_2025['event_competition'].isin(skill_levels)].copy()

df_skill['event_points'] = pd.to_numeric(df_skill['event_points'], errors='coerce')
df_skill = df_skill[df_skill['event_points'].notna() & (df_skill['event_points'] > 0)]

# Соединяем с локациями
df_skill = df_skill.merge(df_locations[['location_id', 'event_country', 'event_city']], on='location_id', how='left')

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

# Танцоры, для которых нужны данные
dancers_needed = [
    'Nicole Ramirez',
    'Igor Pitangui',
    'Aleksandra Radziejewska',
    'Elena Kotelnikova',
    'Daniel Pavlov',
    'Marina Motronenko',
    'Polina Khapaeva'
]

for dancer_name in dancers_needed:
    dancer_data = df_skill[df_skill['dancer_name'] == dancer_name]
    
    if len(dancer_data) == 0:
        print(f"{dancer_name}: Данные не найдены")
        continue
    
    total_points = dancer_data['event_points'].sum()
    total_wins = len(dancer_data[dancer_data['event_result'].astype(str) == '1'])
    
    # Анализ по регионам
    region_stats = dancer_data.groupby('region').agg({
        'event_points': 'sum',
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
        'event_city': 'first',
        'event_country': 'first',
        'region': 'first'
    }).sort_values('event_points', ascending=False)
    
    top_event = None
    top_event_points = 0
    top_event_location = None
    if len(event_stats) > 0:
        top_event = event_stats.index[0]
        top_event_points = int(event_stats.iloc[0]['event_points'])
        city = str(event_stats.iloc[0].get('event_city', 'N/A'))
        country = str(event_stats.iloc[0].get('event_country', 'N/A'))
        top_event_location = f"{city}, {country}"
    
    # Формируем географию
    geo_text = ""
    if top_region:
        geo_text = f"{top_region_pct:.1f}% поинтов набрал(а) на "
        if top_region == 'North America':
            geo_text += "американских ивентах"
        elif top_region == 'Europe':
            geo_text += "европейских ивентах"
        elif top_region == 'Oceania':
            geo_text += "ивентах в Океании"
        elif top_region == 'Asia':
            geo_text += "азиатских ивентах"
        else:
            geo_text += f"ивентах в {top_region}"
        
        if regions_with_wins > 0:
            wins_info = []
            for region, count in wins_by_region.items():
                if region == 'North America':
                    wins_info.append(f"{count} {'побед' if count > 1 else 'победа'} в США")
                elif region == 'Europe':
                    wins_info.append(f"{count} {'побед' if count > 1 else 'победа'} в Европе")
                elif region == 'Oceania':
                    wins_info.append(f"{count} {'побед' if count > 1 else 'победа'} в Океании")
                elif region == 'Asia':
                    wins_info.append(f"{count} {'побед' if count > 1 else 'победа'} в Азии")
                else:
                    wins_info.append(f"{count} {'побед' if count > 1 else 'победа'} в {region}")
            
            if wins_info:
                geo_text += ", " + ", ".join(wins_info)
    
    print(f"{dancer_name}:")
    print(f"  География: {geo_text}")
    if top_event:
        print(f"  Самый успешный ивент: {top_event} ({top_event_location}) с {top_event_points} поинтами")
    print()
