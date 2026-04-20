#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'

df_results = pd.read_csv(RESULTS_FILE, low_memory=False)
df_dancers = pd.read_csv(DANCERS_FILE, low_memory=False)

# Фильтруем 2025 и sophisticated
df_2025 = df_results[df_results['event_year'] == 2025].copy()
df_soph = df_2025[df_2025['event_competition'] == 'Sophisticated'].copy()

df_soph['event_points'] = pd.to_numeric(df_soph['event_points'], errors='coerce')
df_soph = df_soph[df_soph['event_points'].notna() & (df_soph['event_points'] > 0)]

# Группируем по танцорам
agg_data = df_soph.groupby('dancer_id').agg({
    'event_points': 'sum',
    'event_name': 'nunique',
    'event_result': lambda x: len(x[x.astype(str) == '1'])
}).reset_index()

agg_data.columns = ['dancer_id', 'points', 'events', 'wins']

# Соединяем с именами
agg_data['dancer_id'] = agg_data['dancer_id'].astype(str)
df_dancers['dancer_id'] = df_dancers['dancer_id'].astype(str)
agg_data = agg_data.merge(df_dancers[['dancer_id', 'dancer_name']], on='dancer_id', how='left')

# Сортируем по каждой метрике и получаем топ-10
output_dir = Path(__file__).parent

for metric in ['points', 'wins', 'events']:
    top = agg_data.nlargest(10, metric)[['dancer_name', metric]].copy()
    top.columns = ['dancer_name', metric]
    top_file = output_dir / f'sophisticated_top_{metric}_2025.csv'
    top.to_csv(top_file, index=False)
    print(f'Сохранил {top_file}: {len(top)} записей')

