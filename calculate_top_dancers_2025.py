#!/usr/bin/env python3
"""
Расчет топ-танцоров WSDC 2025 года по трем метрикам:
1. Points - сумма поинтов в skill-level номинациях
2. Wins - количество побед в skill-level номинациях  
3. Events - количество уникальных ивентов с поинтами

Только skill-level номинации: Newcomer, Novice, Intermediate, Advanced, All-Stars, Champions
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Пути к данным
DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'

print("="*80)
print("📊 РАСЧЕТ ТОП-ТАНЦОРОВ WSDC 2025")
print("="*80 + "\n")

# Загрузка данных
print("1️⃣  Загрузка данных...")
df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)

print(f"   ✅ Загружено {len(df_results):,} записей результатов")
print(f"   ✅ Загружено {len(df_dancers):,} записей о танцорах")

# Создаем словарь имен
dancer_names = {}
for _, row in df_dancers.iterrows():
    dancer_id = str(row.get('dancer_id', ''))
    name = row.get('dancer_name', f"ID {dancer_id}")
    dancer_names[dancer_id] = name

print(f"   ✅ Загружено {len(dancer_names):,} имен танцоров")

# Фильтруем 2025 год
print("\n2️⃣  Фильтрация данных за 2025 год...")
df_2025 = df_results[df_results['event_year'] == 2025].copy()
print(f"   ✅ Записей за 2025 год: {len(df_2025):,}")

# Skill-level номинации
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']
df_skill = df_2025[df_2025['event_competition'].isin(skill_levels)].copy()
print(f"   ✅ Skill-level записей за 2025: {len(df_skill):,}")

# Конвертируем поинты в числа
df_skill['event_points'] = pd.to_numeric(df_skill['event_points'], errors='coerce')
df_skill = df_skill[df_skill['event_points'].notna()].copy()
df_skill = df_skill[df_skill['event_points'] > 0].copy()  # Только записи с поинтами > 0

# Конвертируем dancer_id в строку для сопоставления
df_skill['dancer_id'] = df_skill['dancer_id'].astype(str)

print("\n3️⃣  Расчет метрик...")

# 1. TOP BY POINTS - сумма поинтов за 2025
print("\n   📈 Расчет топов по Points...")
points_agg = df_skill.groupby('dancer_id').agg({
    'event_points': 'sum'
}).reset_index()
points_agg.columns = ['dancer_id', 'points_2025']
points_agg = points_agg.sort_values('points_2025', ascending=False)
points_agg['dancer_name'] = points_agg['dancer_id'].map(dancer_names)
points_agg = points_agg[points_agg['dancer_name'].notna()]

# Также считаем total points (за все годы)
df_all = df_results[df_results['event_competition'].isin(skill_levels)].copy()
df_all['event_points'] = pd.to_numeric(df_all['event_points'], errors='coerce')
df_all = df_all[df_all['event_points'].notna()]
df_all = df_all[df_all['event_points'] > 0]
df_all['dancer_id'] = df_all['dancer_id'].astype(str)

points_total = df_all.groupby('dancer_id')['event_points'].sum().reset_index()
points_total.columns = ['dancer_id', 'points_total']
points_total['dancer_id'] = points_total['dancer_id'].astype(str)

points_agg = points_agg.merge(points_total, on='dancer_id', how='left')
points_agg['points_total'] = points_agg['points_total'].fillna(0).astype(int)

print(f"   ✅ Рассчитано топов по Points: {len(points_agg)}")

# 2. TOP BY WINS - количество побед (result = '1' или 'F')
print("\n   🏆 Расчет топов по Wins...")

# Победа = 1 место или F (финал, что обычно означает попадание в финал, но для победы нужно 1)
df_skill['is_win'] = (df_skill['event_result'] == '1') | (df_skill['event_result'] == 1)
wins_agg = df_skill[df_skill['is_win']].groupby('dancer_id').size().reset_index(name='wins_2025')
wins_agg['dancer_id'] = wins_agg['dancer_id'].astype(str)

# Также считаем total wins
df_all_skill = df_results[df_results['event_competition'].isin(skill_levels)].copy()
df_all_skill['is_win'] = (df_all_skill['event_result'] == '1') | (df_all_skill['event_result'] == 1) | (df_all_skill['event_result'] == '1.0')
wins_total = df_all_skill[df_all_skill['is_win']].groupby('dancer_id').size().reset_index(name='wins_total')
wins_total['dancer_id'] = wins_total['dancer_id'].astype(str)

wins_agg = wins_agg.merge(wins_total, on='dancer_id', how='left')
wins_agg['wins_total'] = wins_agg['wins_total'].fillna(0).astype(int)
wins_agg['dancer_name'] = wins_agg['dancer_id'].map(dancer_names)
wins_agg = wins_agg[wins_agg['dancer_name'].notna()]

print(f"   ✅ Рассчитано топов по Wins: {len(wins_agg)}")

# 3. TOP BY EVENTS - количество уникальных ивентов
print("\n   📅 Расчет топов по Events...")
events_agg = df_skill.groupby('dancer_id')['event_name_id'].nunique().reset_index(name='events_2025')
events_agg['dancer_id'] = events_agg['dancer_id'].astype(str)

# Также считаем total events
events_total = df_all.groupby('dancer_id')['event_name_id'].nunique().reset_index(name='events_total')
events_total['dancer_id'] = events_total['dancer_id'].astype(str)

events_agg = events_agg.merge(events_total, on='dancer_id', how='left')
events_agg['events_total'] = events_agg['events_total'].fillna(0).astype(int)
events_agg['dancer_name'] = events_agg['dancer_id'].map(dancer_names)
events_agg = events_agg[events_agg['dancer_name'].notna()]

print(f"   ✅ Рассчитано топов по Events: {len(events_agg)}")

# Выводим топ-10 по каждой метрике
print("\n" + "="*80)
print("🏆 ТОП-10 ТАНЦОРОВ ПО POINTS (2025)")
print("="*80)
print(f"{'Rank':<6} {'Name':<30} {'Points 2025':<12} {'Points Total':<12}")
print("-"*80)
for idx, row in points_agg.head(10).iterrows():
    rank = points_agg.head(10).index.get_loc(idx) + 1
    print(f"{rank:<6} {row['dancer_name']:<30} {int(row['points_2025']):<12} {int(row['points_total']):<12}")

print("\n" + "="*80)
print("🏆 ТОП-10 ТАНЦОРОВ ПО WINS (2025)")
print("="*80)
print(f"{'Rank':<6} {'Name':<30} {'Wins 2025':<12} {'Wins Total':<12}")
print("-"*80)
wins_agg_sorted = wins_agg.sort_values('wins_2025', ascending=False)
for idx, row in wins_agg_sorted.head(10).iterrows():
    rank = wins_agg_sorted.head(10).index.get_loc(idx) + 1
    print(f"{rank:<6} {row['dancer_name']:<30} {int(row['wins_2025']):<12} {int(row['wins_total']):<12}")

print("\n" + "="*80)
print("🏆 ТОП-10 ТАНЦОРОВ ПО EVENTS (2025)")
print("="*80)
print(f"{'Rank':<6} {'Name':<30} {'Events 2025':<12} {'Events Total':<12}")
print("-"*80)
events_agg_sorted = events_agg.sort_values('events_2025', ascending=False)
for idx, row in events_agg_sorted.head(10).iterrows():
    rank = events_agg_sorted.head(10).index.get_loc(idx) + 1
    print(f"{rank:<6} {row['dancer_name']:<30} {int(row['events_2025']):<12} {int(row['events_total']):<12}")

# Сохраняем результаты
output_dir = Path('/Users/ania/.cursor/wsdc-analytics-repo')
points_agg_sorted = points_agg.sort_values('points_2025', ascending=False)
wins_agg_sorted = wins_agg.sort_values('wins_2025', ascending=False)
events_agg_sorted = events_agg.sort_values('events_2025', ascending=False)

points_agg_sorted.to_csv(output_dir / 'dancers_top_points_2025.csv', index=False)
wins_agg_sorted.to_csv(output_dir / 'dancers_top_wins_2025.csv', index=False)
events_agg_sorted.to_csv(output_dir / 'dancers_top_events_2025.csv', index=False)

print("\n✅ Результаты сохранены в CSV файлы:")
print(f"   - {output_dir / 'dancers_top_points_2025.csv'}")
print(f"   - {output_dir / 'dancers_top_wins_2025.csv'}")
print(f"   - {output_dir / 'dancers_top_events_2025.csv'}")

# 4. РОССИЙСКИЕ ТОПЫ
print("\n" + "="*80)
print("🇷🇺 РАСЧЕТ РОССИЙСКИХ ТОПОВ")
print("="*80)

# Загружаем список российских танцоров
russian_ids_file = output_dir / 'russian_dancer_ids.txt'
if russian_ids_file.exists():
    with open(russian_ids_file, 'r') as f:
        russian_ids = set(line.strip() for line in f if line.strip())
    print(f"\n✅ Загружено {len(russian_ids)} ID российских танцоров")
    
    # Фильтруем российских танцоров
    russian_points = points_agg_sorted[points_agg_sorted['dancer_id'].isin(russian_ids)].copy()
    russian_wins = wins_agg_sorted[wins_agg_sorted['dancer_id'].isin(russian_ids)].copy()
    russian_events = events_agg_sorted[events_agg_sorted['dancer_id'].isin(russian_ids)].copy()
    
    # Выводим топ-10 российских танцоров
    print("\n" + "="*80)
    print("🇷🇺 ТОП-10 РОССИЙСКИХ ТАНЦОРОВ ПО POINTS (2025)")
    print("="*80)
    print(f"{'Rank':<6} {'Name':<30} {'Points 2025':<12} {'Points Total':<12}")
    print("-"*80)
    for idx, row in russian_points.head(10).iterrows():
        rank = russian_points.head(10).index.get_loc(idx) + 1
        print(f"{rank:<6} {row['dancer_name']:<30} {int(row['points_2025']):<12} {int(row['points_total']):<12}")
    
    print("\n" + "="*80)
    print("🇷🇺 ТОП-10 РОССИЙСКИХ ТАНЦОРОВ ПО WINS (2025)")
    print("="*80)
    print(f"{'Rank':<6} {'Name':<30} {'Wins 2025':<12} {'Wins Total':<12}")
    print("-"*80)
    for idx, row in russian_wins.head(10).iterrows():
        rank = russian_wins.head(10).index.get_loc(idx) + 1
        print(f"{rank:<6} {row['dancer_name']:<30} {int(row['wins_2025']):<12} {int(row['wins_total']):<12}")
    
    print("\n" + "="*80)
    print("🇷🇺 ТОП-10 РОССИЙСКИХ ТАНЦОРОВ ПО EVENTS (2025)")
    print("="*80)
    print(f"{'Rank':<6} {'Name':<30} {'Events 2025':<12} {'Events Total':<12}")
    print("-"*80)
    for idx, row in russian_events.head(10).iterrows():
        rank = russian_events.head(10).index.get_loc(idx) + 1
        print(f"{rank:<6} {row['dancer_name']:<30} {int(row['events_2025']):<12} {int(row['events_total']):<12}")
    
    # Сохраняем российские топы
    russian_points.to_csv(output_dir / 'russian_dancers_top_points_2025.csv', index=False)
    russian_wins.to_csv(output_dir / 'russian_dancers_top_wins_2025.csv', index=False)
    russian_events.to_csv(output_dir / 'russian_dancers_top_events_2025.csv', index=False)
    
    print("\n✅ Российские топы сохранены в CSV файлы:")
    print(f"   - {output_dir / 'russian_dancers_top_points_2025.csv'}")
    print(f"   - {output_dir / 'russian_dancers_top_wins_2025.csv'}")
    print(f"   - {output_dir / 'russian_dancers_top_events_2025.csv'}")
else:
    print(f"\n⚠️  Файл {russian_ids_file} не найден. Пропускаем расчет российских топов.")

