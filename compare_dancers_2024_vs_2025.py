#!/usr/bin/env python3
"""
Сравнение топ-танцоров 2024 и 2025 годов
Выявление пересечений, новых участников и выбывших из топов
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Пути к данным
DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'

print("="*80)
print("📊 СРАВНЕНИЕ ТОП-ТАНЦОРОВ 2024 VS 2025")
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

# Skill-level номинации
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']

# Загрузка российских ID
RUSSIAN_IDS_FILE = Path('/Users/ania/.cursor/wsdc-analytics-repo/russian_dancer_ids.txt')
print(f"\n1️⃣  Загрузка российских ID танцоров...")
if RUSSIAN_IDS_FILE.exists():
    with open(RUSSIAN_IDS_FILE, 'r') as f:
        russian_ids = set(line.strip() for line in f if line.strip())
    print(f"   ✅ Загружено {len(russian_ids)} российских ID")
else:
    print(f"   ⚠️  Файл {RUSSIAN_IDS_FILE} не найден, российские топы не будут рассчитаны")
    russian_ids = set()

def calculate_tops_for_year(year, filter_ids=None):
    """Рассчитывает топы для указанного года"""
    # Фильтруем год
    df_year = df_results[df_results['event_year'] == year].copy()
    df_skill = df_year[df_year['event_competition'].isin(skill_levels)].copy()
    
    # Фильтруем по ID, если указано
    if filter_ids is not None:
        df_skill['dancer_id'] = df_skill['dancer_id'].astype(str)
        df_skill = df_skill[df_skill['dancer_id'].isin(filter_ids)].copy()
    
    # Конвертируем поинты
    df_skill['event_points'] = pd.to_numeric(df_skill['event_points'], errors='coerce')
    df_skill = df_skill[df_skill['event_points'].notna()].copy()
    df_skill = df_skill[df_skill['event_points'] > 0].copy()
    df_skill['dancer_id'] = df_skill['dancer_id'].astype(str)
    
    # 1. TOP BY POINTS
    points_agg = df_skill.groupby('dancer_id')['event_points'].sum().reset_index(name='points')
    points_agg['dancer_id'] = points_agg['dancer_id'].astype(str)
    points_agg['dancer_name'] = points_agg['dancer_id'].map(dancer_names)
    points_agg = points_agg[points_agg['dancer_name'].notna()]
    points_agg = points_agg.sort_values('points', ascending=False)
    points_agg['rank'] = range(1, len(points_agg) + 1)
    
    # 2. TOP BY WINS
    df_skill['is_win'] = (df_skill['event_result'] == '1') | (df_skill['event_result'] == 1) | (df_skill['event_result'] == '1.0')
    wins_agg = df_skill[df_skill['is_win']].groupby('dancer_id').size().reset_index(name='wins')
    wins_agg['dancer_id'] = wins_agg['dancer_id'].astype(str)
    wins_agg['dancer_name'] = wins_agg['dancer_id'].map(dancer_names)
    wins_agg = wins_agg[wins_agg['dancer_name'].notna()]
    wins_agg = wins_agg.sort_values('wins', ascending=False)
    wins_agg['rank'] = range(1, len(wins_agg) + 1)
    
    # 3. TOP BY EVENTS
    events_agg = df_skill.groupby('dancer_id')['event_name_id'].nunique().reset_index(name='events')
    events_agg['dancer_id'] = events_agg['dancer_id'].astype(str)
    events_agg['dancer_name'] = events_agg['dancer_id'].map(dancer_names)
    events_agg = events_agg[events_agg['dancer_name'].notna()]
    events_agg = events_agg.sort_values('events', ascending=False)
    events_agg['rank'] = range(1, len(events_agg) + 1)
    
    return {
        'points': points_agg,
        'wins': wins_agg,
        'events': events_agg
    }

print("\n2️⃣  Расчет топов за 2024 год...")
tops_2024 = calculate_tops_for_year(2024)
print(f"   ✅ Топ по Points: {len(tops_2024['points'])} танцоров")
print(f"   ✅ Топ по Wins: {len(tops_2024['wins'])} танцоров")
print(f"   ✅ Топ по Events: {len(tops_2024['events'])} танцоров")

print("\n3️⃣  Расчет топов за 2025 год...")
tops_2025 = calculate_tops_for_year(2025)
print(f"   ✅ Топ по Points: {len(tops_2025['points'])} танцоров")
print(f"   ✅ Топ по Wins: {len(tops_2025['wins'])} танцоров")
print(f"   ✅ Топ по Events: {len(tops_2025['events'])} танцоров")

print("\n" + "="*80)
print("📈 СРАВНЕНИЕ ТОПОВ")
print("="*80)

def compare_tops(top_2024, top_2025, metric_name):
    """Сравнивает топы за два года"""
    print(f"\n{'='*80}")
    print(f"🏆 {metric_name.upper()} - СРАВНЕНИЕ ТОП-10")
    print(f"{'='*80}")
    
    # Берем топ-10 за каждый год
    top10_2024 = top_2024.head(10).copy()
    top10_2025 = top_2025.head(10).copy()
    
    # Создаем словари для быстрого поиска
    top10_2024_ids = set(top10_2024['dancer_id'].values)
    top10_2025_ids = set(top10_2025['dancer_id'].values)
    
    # Пересечения
    intersection = top10_2024_ids & top10_2025_ids
    
    # Выбывшие (были в 2024, нет в 2025)
    dropped = top10_2024_ids - top10_2025_ids
    
    # Новые (не было в 2024, есть в 2025)
    new_entries = top10_2025_ids - top10_2024_ids
    
    print(f"\n✅ Пересечения (остались в топ-10 оба года): {len(intersection)}")
    if intersection:
        print("\nТанцоры, оставшиеся в топ-10:")
        for dancer_id in intersection:
            name_2024 = top10_2024[top10_2024['dancer_id'] == dancer_id]['dancer_name'].iloc[0]
            rank_2024 = int(top10_2024[top10_2024['dancer_id'] == dancer_id]['rank'].iloc[0])
            value_2024 = top10_2024[top10_2024['dancer_id'] == dancer_id][metric_name].iloc[0]
            
            rank_2025 = int(top10_2025[top10_2025['dancer_id'] == dancer_id]['rank'].iloc[0])
            value_2025 = top10_2025[top10_2025['dancer_id'] == dancer_id][metric_name].iloc[0]
            
            change = rank_2024 - rank_2025  # Положительное = поднялся, отрицательное = опустился
            change_str = f"▲ +{abs(change)}" if change > 0 else (f"▼ {abs(change)}" if change < 0 else "→")
            
            print(f"  • {name_2024}: {rank_2024}-е место ({int(value_2024)}) → {rank_2025}-е место ({int(value_2025)}) {change_str}")
    
    print(f"\n❌ Выбыли из топ-10 (2024 → 2025): {len(dropped)}")
    if dropped:
        print("\nТанцоры, выбывшие из топ-10:")
        for dancer_id in dropped:
            name = top10_2024[top10_2024['dancer_id'] == dancer_id]['dancer_name'].iloc[0]
            rank_2024 = int(top10_2024[top10_2024['dancer_id'] == dancer_id]['rank'].iloc[0])
            value_2024 = top10_2024[top10_2024['dancer_id'] == dancer_id][metric_name].iloc[0]
            
            # Находим их позицию в 2025 (если есть)
            if dancer_id in top_2025['dancer_id'].values:
                rank_2025 = int(top_2025[top_2025['dancer_id'] == dancer_id]['rank'].iloc[0])
                value_2025 = top_2025[top_2025['dancer_id'] == dancer_id][metric_name].iloc[0]
                print(f"  • {name}: {rank_2024}-е место ({int(value_2024)}) в 2024 → {rank_2025}-е место ({int(value_2025)}) в 2025")
            else:
                print(f"  • {name}: {rank_2024}-е место ({int(value_2024)}) в 2024 → не в топе 2025")
    
    print(f"\n🆕 Новые в топ-10 (появились в 2025): {len(new_entries)}")
    if new_entries:
        print("\nНовые танцоры в топ-10:")
        for dancer_id in new_entries:
            name = top10_2025[top10_2025['dancer_id'] == dancer_id]['dancer_name'].iloc[0]
            rank_2025 = int(top10_2025[top10_2025['dancer_id'] == dancer_id]['rank'].iloc[0])
            value_2025 = top10_2025[top10_2025['dancer_id'] == dancer_id][metric_name].iloc[0]
            
            # Находим их позицию в 2024 (если есть)
            if dancer_id in top_2024['dancer_id'].values:
                rank_2024 = int(top_2024[top_2024['dancer_id'] == dancer_id]['rank'].iloc[0])
                value_2024 = top_2024[top_2024['dancer_id'] == dancer_id][metric_name].iloc[0]
                print(f"  • {name}: {rank_2024}-е место ({int(value_2024)}) в 2024 → {rank_2025}-е место ({int(value_2025)}) в 2025 ▲ +{rank_2024 - rank_2025}")
            else:
                print(f"  • {name}: не было в топе 2024 → {rank_2025}-е место ({int(value_2025)}) в 2025 🆕")

# Сравниваем каждую метрику
print("\n" + "="*80)
print("🌍 ГЛОБАЛЬНЫЕ ТОПЫ")
print("="*80)
compare_tops(tops_2024['points'], tops_2025['points'], 'points')
compare_tops(tops_2024['wins'], tops_2025['wins'], 'wins')
compare_tops(tops_2024['events'], tops_2025['events'], 'events')

# Сохраняем результаты для дальнейшего анализа
output_dir = Path('/Users/ania/.cursor/wsdc-analytics-repo')
tops_2024['points'].head(10).to_csv(output_dir / 'dancers_top_points_2024.csv', index=False)
tops_2024['wins'].head(10).to_csv(output_dir / 'dancers_top_wins_2024.csv', index=False)
tops_2024['events'].head(10).to_csv(output_dir / 'dancers_top_events_2024.csv', index=False)

print("\n✅ Результаты сохранены в CSV файлы:")
print(f"   - {output_dir / 'dancers_top_points_2024.csv'}")
print(f"   - {output_dir / 'dancers_top_wins_2024.csv'}")
print(f"   - {output_dir / 'dancers_top_events_2024.csv'}")

# РОССИЙСКИЕ ТОПЫ
if russian_ids:
    print("\n" + "="*80)
    print("🇷🇺 РОССИЙСКИЕ ТОПЫ")
    print("="*80)
    
    print("\n4️⃣  Расчет российских топов за 2024 год...")
    ru_tops_2024 = calculate_tops_for_year(2024, filter_ids=russian_ids)
    print(f"   ✅ Топ по Points: {len(ru_tops_2024['points'])} танцоров")
    print(f"   ✅ Топ по Wins: {len(ru_tops_2024['wins'])} танцоров")
    print(f"   ✅ Топ по Events: {len(ru_tops_2024['events'])} танцоров")
    
    print("\n5️⃣  Расчет российских топов за 2025 год...")
    ru_tops_2025 = calculate_tops_for_year(2025, filter_ids=russian_ids)
    print(f"   ✅ Топ по Points: {len(ru_tops_2025['points'])} танцоров")
    print(f"   ✅ Топ по Wins: {len(ru_tops_2025['wins'])} танцоров")
    print(f"   ✅ Топ по Events: {len(ru_tops_2025['events'])} танцоров")
    
    print("\n" + "="*80)
    print("📈 СРАВНЕНИЕ РОССИЙСКИХ ТОПОВ")
    print("="*80)
    compare_tops(ru_tops_2024['points'], ru_tops_2025['points'], 'points')
    compare_tops(ru_tops_2024['wins'], ru_tops_2025['wins'], 'wins')
    compare_tops(ru_tops_2024['events'], ru_tops_2025['events'], 'events')
    
    # Сохраняем российские топы 2024
    if len(ru_tops_2024['points']) > 0:
        ru_tops_2024['points'].head(10).to_csv(output_dir / 'russian_dancers_top_points_2024.csv', index=False)
        print(f"\n✅ Сохранен: {output_dir / 'russian_dancers_top_points_2024.csv'}")
    if len(ru_tops_2024['wins']) > 0:
        ru_tops_2024['wins'].head(10).to_csv(output_dir / 'russian_dancers_top_wins_2024.csv', index=False)
        print(f"✅ Сохранен: {output_dir / 'russian_dancers_top_wins_2024.csv'}")
    if len(ru_tops_2024['events']) > 0:
        ru_tops_2024['events'].head(10).to_csv(output_dir / 'russian_dancers_top_events_2024.csv', index=False)
        print(f"✅ Сохранен: {output_dir / 'russian_dancers_top_events_2024.csv'}")

