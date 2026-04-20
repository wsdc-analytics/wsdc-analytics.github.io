#!/usr/bin/env python3
"""
Анализ танцоров с наибольшим количеством поинтов в Champions и All-Stars
(отдельно по ролям)
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

# Пути к данным
DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
CSV_DIR = Path('/Users/ania/.cursor/wsdc-analytics-repo')

print("="*80)
print("📊 АНАЛИЗ ЛИДЕРОВ ПО ПОИНТАМ В CHAMPIONS И ALL-STARS 2025")
print("="*80 + "\n")

# Загрузка данных
print("1️⃣  Загрузка данных...")
df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)

# Создаем словарь имен
dancer_names = {}
for _, row in df_dancers.iterrows():
    dancer_id = str(row.get('dancer_id', ''))
    name = row.get('dancer_name', f"ID {dancer_id}")
    dancer_names[dancer_id] = name

# Фильтруем 2025 год
df_2025 = df_results[df_results['event_year'] == 2025].copy()

# Загружаем топ-10 из CSV
top_points = pd.read_csv(CSV_DIR / 'dancers_top_points_2025.csv')
top_points_ids = set(top_points['dancer_id'].astype(str).head(10).tolist())

print("\n2️⃣  Анализ Champions...")
df_champions = df_2025[
    (df_2025['event_competition'] == 'Champions') &
    (df_2025['event_points'].notna()) &
    (pd.to_numeric(df_2025['event_points'], errors='coerce') > 0)
].copy()
df_champions['event_points'] = pd.to_numeric(df_champions['event_points'], errors='coerce')

champions_by_role = defaultdict(lambda: {'points': 0, 'wins': 0, 'events': set()})

for _, row in df_champions.iterrows():
    dancer_id = str(row['dancer_id'])
    role = row.get('event_role', 'unknown')
    points = row['event_points'] or 0
    event_result = str(row.get('event_result', ''))
    event_name = row.get('event_name', '')
    
    if points > 0:
        key = (dancer_id, role)
        champions_by_role[key]['points'] += points
        champions_by_role[key]['events'].add(event_name)
        if event_result == '1' or event_result == 1:
            champions_by_role[key]['wins'] += 1

champions_list = []
for (dancer_id, role), data in champions_by_role.items():
    champions_list.append({
        'dancer_id': dancer_id,
        'dancer_name': dancer_names.get(dancer_id, f'ID {dancer_id}'),
        'role': role,
        'points': data['points'],
        'wins': data['wins'],
        'events': len(data['events']),
        'in_top10': dancer_id in top_points_ids
    })

champions_list.sort(key=lambda x: x['points'], reverse=True)

print(f"\n🏆 ТОП-10 ПО ПОИНТАМ В CHAMPIONS (все роли):")
for i, dancer in enumerate(champions_list[:10], 1):
    top_mark = " ⭐ В ТОП-10" if dancer['in_top10'] else ""
    print(f"{i}. {dancer['dancer_name']} ({dancer['role']}): {dancer['points']} поинтов, {dancer['wins']} побед, {dancer['events']} ивентов{top_mark}")

print("\n3️⃣  Анализ All-Stars...")
df_allstars = df_2025[
    (df_2025['event_competition'] == 'All-Stars') &
    (df_2025['event_points'].notna()) &
    (pd.to_numeric(df_2025['event_points'], errors='coerce') > 0)
].copy()
df_allstars['event_points'] = pd.to_numeric(df_allstars['event_points'], errors='coerce')

allstars_by_role = defaultdict(lambda: {'points': 0, 'wins': 0, 'events': set()})

for _, row in df_allstars.iterrows():
    dancer_id = str(row['dancer_id'])
    role = row.get('event_role', 'unknown')
    points = row['event_points'] or 0
    event_result = str(row.get('event_result', ''))
    event_name = row.get('event_name', '')
    
    if points > 0:
        key = (dancer_id, role)
        allstars_by_role[key]['points'] += points
        allstars_by_role[key]['events'].add(event_name)
        if event_result == '1' or event_result == 1:
            allstars_by_role[key]['wins'] += 1

allstars_list = []
for (dancer_id, role), data in allstars_by_role.items():
    allstars_list.append({
        'dancer_id': dancer_id,
        'dancer_name': dancer_names.get(dancer_id, f'ID {dancer_id}'),
        'role': role,
        'points': data['points'],
        'wins': data['wins'],
        'events': len(data['events']),
        'in_top10': dancer_id in top_points_ids
    })

allstars_list.sort(key=lambda x: x['points'], reverse=True)

print(f"\n🏆 ТОП-10 ПО ПОИНТАМ В ALL-STARS (все роли):")
for i, dancer in enumerate(allstars_list[:10], 1):
    top_mark = " ⭐ В ТОП-10" if dancer['in_top10'] else ""
    print(f"{i}. {dancer['dancer_name']} ({dancer['role']}): {dancer['points']} поинтов, {dancer['wins']} побед, {dancer['events']} ивентов{top_mark}")

print("\n4️⃣  Танцоры из топ-10 с наибольшими поинтами в Champions:")
champions_in_top = [d for d in champions_list if d['in_top10']]
champions_in_top.sort(key=lambda x: x['points'], reverse=True)
for dancer in champions_in_top[:5]:
    print(f"   {dancer['dancer_name']} ({dancer['role']}): {dancer['points']} поинтов в Champions")

print("\n5️⃣  Танцоры из топ-10 с наибольшими поинтами в All-Stars:")
allstars_in_top = [d for d in allstars_list if d['in_top10']]
allstars_in_top.sort(key=lambda x: x['points'], reverse=True)
for dancer in allstars_in_top[:5]:
    print(f"   {dancer['dancer_name']} ({dancer['role']}): {dancer['points']} поинтов в All-Stars")

