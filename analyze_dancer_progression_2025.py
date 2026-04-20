#!/usr/bin/env python3
"""
Анализ танцоров, которые прошли несколько последовательных номинаций в 2025 году
(показывает эффективный рост через дивизионы)
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
print("📊 АНАЛИЗ ПРОГРЕССА ТАНЦОРОВ ЧЕРЕЗ НОМИНАЦИИ 2025")
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

# Фильтруем 2025 год и skill-level номинации
print("\n2️⃣  Фильтрация данных за 2025 год...")
df_2025 = df_results[df_results['event_year'] == 2025].copy()
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']
df_skill = df_2025[df_2025['event_competition'].isin(skill_levels)].copy()

# Определяем порядок номинаций
level_order = {
    'Newcomer': 1,
    'Novice': 2,
    'Intermediate': 3,
    'Advanced': 4,
    'All-Stars': 5,
    'Champions': 6
}

# Группируем по танцору и роли, находим уникальные номинации с поинтами
print("\n3️⃣  Анализ прогресса по танцорам...")
dancer_progress = defaultdict(lambda: {'levels': set(), 'role': None, 'points': 0, 'wins': 0, 'events': set()})

for _, row in df_skill.iterrows():
    dancer_id = str(row['dancer_id'])
    competition = row['event_competition']
    role = row.get('event_role', 'unknown')
    points = pd.to_numeric(row.get('event_points', 0), errors='coerce') or 0
    event_result = str(row.get('event_result', ''))
    event_name = row.get('event_name', '')
    
    if points > 0:
        dancer_progress[(dancer_id, role)]['levels'].add(competition)
        dancer_progress[(dancer_id, role)]['role'] = role
        dancer_progress[(dancer_id, role)]['points'] += points
        dancer_progress[(dancer_id, role)]['events'].add(event_name)
        if event_result == '1' or event_result == 1:
            dancer_progress[(dancer_id, role)]['wins'] += 1

# Находим танцоров с последовательными номинациями
def check_consecutive_progression(levels):
    """Проверяет, что номинации идут последовательно"""
    if len(levels) < 2:
        return False
    
    # Сортируем по порядку
    sorted_levels = sorted([level_order.get(l, 99) for l in levels])
    
    # Проверяем, что все уровни идут подряд без пропусков
    for i in range(len(sorted_levels) - 1):
        if sorted_levels[i+1] - sorted_levels[i] != 1:
            return False
    
    return True

progressing_dancers = []

for (dancer_id, role), data in dancer_progress.items():
    levels = data['levels']
    if check_consecutive_progression(levels) and len(levels) >= 2:
        dancer_name = dancer_names.get(dancer_id, f'ID {dancer_id}')
        
        # Получаем названия номинаций в правильном порядке
        sorted_level_names = sorted(levels, key=lambda l: level_order.get(l, 99))
        
        progressing_dancers.append({
            'dancer_id': dancer_id,
            'dancer_name': dancer_name,
            'role': role,
            'levels': sorted_level_names,
            'num_levels': len(levels),
            'points': data['points'],
            'wins': data['wins'],
            'events': len(data['events']),
            'start_level': sorted_level_names[0],
            'end_level': sorted_level_names[-1]
        })

# Сортируем по количеству номинаций и поинтам
progressing_dancers.sort(key=lambda x: (x['num_levels'], x['points']), reverse=True)

print(f"   ✅ Найдено танцоров с последовательным прогрессом: {len(progressing_dancers)}")

# Загружаем топ-10 из CSV файлов
top_points = pd.read_csv(CSV_DIR / 'dancers_top_points_2025.csv')
top_wins = pd.read_csv(CSV_DIR / 'dancers_top_wins_2025.csv')
top_events = pd.read_csv(CSV_DIR / 'dancers_top_events_2025.csv')

top_dancer_ids = set()
top_dancer_ids.update(top_points['dancer_id'].astype(str).tolist())
top_dancer_ids.update(top_wins['dancer_id'].astype(str).tolist())
top_dancer_ids.update(top_events['dancer_id'].astype(str).tolist())

# Фильтруем только тех, кто в топе
top_progressing = [d for d in progressing_dancers if d['dancer_id'] in top_dancer_ids]

print(f"\n4️⃣  Танцоры с прогрессом, попавшие в топы: {len(top_progressing)}")
print("\n" + "="*80)
print("🏆 ТАНЦОРЫ С ПОСЛЕДОВАТЕЛЬНЫМ ПРОГРЕССОМ (В ТОПАХ)")
print("="*80 + "\n")

for i, dancer in enumerate(top_progressing[:15], 1):
    levels_str = ' → '.join(dancer['levels'])
    print(f"{i}. {dancer['dancer_name']} ({dancer['role']})")
    print(f"   Прогресс: {levels_str} ({dancer['num_levels']} номинаций)")
    print(f"   Поинты: {dancer['points']}, Победы: {dancer['wins']}, Ивенты: {dancer['events']}")
    print()

# Сохраняем результаты
output_file = CSV_DIR / 'dancers_progression_2025.csv'
df_progression = pd.DataFrame(top_progressing)
df_progression.to_csv(output_file, index=False)
print(f"✅ Результаты сохранены в {output_file}")

