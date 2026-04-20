#!/usr/bin/env python3
"""
Анализ детальной информации о топ-танцорах для создания мини-заметок
Выявление значимых достижений: номинации, распределение побед, активность и т.д.
"""

import pandas as pd
from pathlib import Path
from collections import Counter

# Пути к данным
DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'

print("="*80)
print("📊 АНАЛИЗ ДОСТИЖЕНИЙ ТОП-ТАНЦОРОВ 2025")
print("="*80 + "\n")

# Загрузка данных
df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)

# Создаем словарь имен
dancer_names = {}
for _, row in df_dancers.iterrows():
    dancer_id = str(row.get('dancer_id', ''))
    name = row.get('dancer_name', f"ID {dancer_id}")
    dancer_names[dancer_id] = name

# Skill-level номинации
skill_levels = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']

# Фильтруем 2025 и skill-level
df_2025 = df_results[df_results['event_year'] == 2025].copy()
df_skill = df_2025[df_2025['event_competition'].isin(skill_levels)].copy()
df_skill['event_points'] = pd.to_numeric(df_skill['event_points'], errors='coerce')
df_skill = df_skill[df_skill['event_points'].notna()].copy()
df_skill = df_skill[df_skill['event_points'] > 0].copy()
df_skill['dancer_id'] = df_skill['dancer_id'].astype(str)

# Загружаем топ-10 из CSV
csv_dir = Path('/Users/ania/.cursor/wsdc-analytics-repo')

def analyze_dancer_highlights(metric_type, top_dancers_df, title):
    """Анализирует детальную информацию о топ-танцорах для заметок"""
    print(f"\n{'='*80}")
    print(f"🎯 {title.upper()}")
    print(f"{'='*80}\n")
    
    highlights = []
    
    for idx, row in top_dancers_df.head(10).iterrows():
        dancer_id = str(row['dancer_id'])
        dancer_name = row.get('dancer_name', dancer_names.get(dancer_id, f"ID {dancer_id}"))
        metric_value = row[metric_type]
        
        # Данные о танцоре за 2025
        dancer_data = df_skill[df_skill['dancer_id'] == dancer_id].copy()
        
        if len(dancer_data) == 0:
            continue
        
        # Анализ
        wins = len(dancer_data[(dancer_data['event_result'] == '1') | (dancer_data['event_result'] == 1) | (dancer_data['event_result'] == '1.0')])
        events_count = dancer_data['event_name_id'].nunique()
        competitions = dancer_data['event_competition'].value_counts().to_dict()
        total_results = len(dancer_data)
        
        # Находим номинации, где были победы
        wins_data = dancer_data[(dancer_data['event_result'] == '1') | (dancer_data['event_result'] == 1) | (dancer_data['event_result'] == '1.0')]
        win_competitions = wins_data['event_competition'].value_counts().to_dict() if len(wins_data) > 0 else {}
        
        # Анализ ролей
        roles = dancer_data['event_role'].value_counts().to_dict() if 'event_role' in dancer_data.columns else {}
        
        # Комбинации номинация + роль
        if 'event_role' in dancer_data.columns:
            comp_role = dancer_data.groupby(['event_competition', 'event_role']).size().reset_index(name='count')
            comp_role_dict = {}
            for _, row in comp_role.iterrows():
                comp = row['event_competition']
                role = row['event_role']
                count = row['count']
                if comp not in comp_role_dict:
                    comp_role_dict[comp] = {}
                comp_role_dict[comp][role] = count
        else:
            comp_role_dict = {}
        
        # Победы по номинациям и ролям
        if len(wins_data) > 0 and 'event_role' in wins_data.columns:
            win_comp_role = wins_data.groupby(['event_competition', 'event_role']).size().reset_index(name='wins_count')
            win_comp_role_dict = {}
            for _, row in win_comp_role.iterrows():
                comp = row['event_competition']
                role = row['event_role']
                wins_count = row['wins_count']
                if comp not in win_comp_role_dict:
                    win_comp_role_dict[comp] = {}
                win_comp_role_dict[comp][role] = wins_count
        else:
            win_comp_role_dict = {}
        
        # Создаем заметку в зависимости от метрики
        highlight = {
            'name': dancer_name,
            'metric_value': metric_value,
            'wins': wins,
            'events': events_count,
            'competitions': competitions,
            'win_competitions': win_competitions,
            'total_results': total_results,
            'roles': roles,
            'comp_role': comp_role_dict,
            'win_comp_role': win_comp_role_dict
        }
        
        highlights.append(highlight)
        
        # Выводим детальную информацию для анализа
        print(f"👤 {dancer_name} ({metric_type}: {metric_value})")
        print(f"   • Побед: {wins}")
        print(f"   • Ивентов: {events_count}")
        print(f"   • Всего результатов: {total_results}")
        print(f"   • Роли: {', '.join([f'{k}: {v}' for k, v in roles.items()])}" if roles else "   • Роли: нет данных")
        print(f"   • Номинации: {', '.join(competitions.keys())}")
        if comp_role_dict:
            print(f"   • Номинации и роли:")
            for comp, role_dict in comp_role_dict.items():
                role_str = ', '.join([f"{role} ({count})" for role, count in role_dict.items()])
                print(f"     - {comp}: {role_str}")
        if win_competitions:
            print(f"   • Победы по номинациям: {', '.join([f'{k} ({v})' for k, v in win_competitions.items()])}")
        if win_comp_role_dict:
            print(f"   • Победы по номинациям и ролям:")
            for comp, role_dict in win_comp_role_dict.items():
                role_str = ', '.join([f"{role} ({count})" for role, count in role_dict.items()])
                print(f"     - {comp}: {role_str}")
        print()
    
    return highlights

# Анализ для каждой метрики
print("\n1️⃣  ТОП ПО POINTS")
top_points = pd.read_csv(csv_dir / 'dancers_top_points_2025.csv')
points_highlights = analyze_dancer_highlights('points_2025', top_points, 'ТОП ПО POINTS - ВЫДАЮЩИЕСЯ ДОСТИЖЕНИЯ')

print("\n2️⃣  ТОП ПО WINS")
top_wins = pd.read_csv(csv_dir / 'dancers_top_wins_2025.csv')
wins_highlights = analyze_dancer_highlights('wins_2025', top_wins, 'ТОП ПО WINS - ВЫДАЮЩИЕСЯ ДОСТИЖЕНИЯ')

print("\n3️⃣  ТОП ПО EVENTS")
top_events = pd.read_csv(csv_dir / 'dancers_top_events_2025.csv')
events_highlights = analyze_dancer_highlights('events_2025', top_events, 'ТОП ПО EVENTS - ВЫДАЮЩИЕСЯ ДОСТИЖЕНИЯ')

# Российские топы
russian_ids_file = csv_dir / 'russian_dancer_ids.txt'
if russian_ids_file.exists():
    with open(russian_ids_file, 'r') as f:
        russian_ids = set(line.strip() for line in f if line.strip())
    
    print("\n4️⃣  РОССИЙСКИЙ ТОП ПО POINTS")
    ru_top_points = pd.read_csv(csv_dir / 'russian_dancers_top_points_2025.csv')
    ru_points_highlights = analyze_dancer_highlights('points_2025', ru_top_points, 'РОССИЙСКИЙ ТОП ПО POINTS')
    
    print("\n5️⃣  РОССИЙСКИЙ ТОП ПО WINS")
    ru_top_wins = pd.read_csv(csv_dir / 'russian_dancers_top_wins_2025.csv')
    ru_wins_highlights = analyze_dancer_highlights('wins_2025', ru_top_wins, 'РОССИЙСКИЙ ТОП ПО WINS')
    
    print("\n6️⃣  РОССИЙСКИЙ ТОП ПО EVENTS")
    ru_top_events = pd.read_csv(csv_dir / 'russian_dancers_top_events_2025.csv')
    ru_events_highlights = analyze_dancer_highlights('events_2025', ru_top_events, 'РОССИЙСКИЙ ТОП ПО EVENTS')

print("\n✅ Анализ завершен. Теперь можно создать заметки на основе этих данных.")

