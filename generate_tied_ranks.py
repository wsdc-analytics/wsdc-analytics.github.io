import pandas as pd

def generate_ranks_with_ties(df, value_col, name_col='dancer_name', max_results=None):
    """Генерирует ранги с учетом одинаковых значений (ties)"""
    result = []
    current_rank = 1
    i = 0
    
    while i < len(df):
        value = df.iloc[i][value_col]
        
        # Находим все строки с таким же значением
        same_value_mask = df[value_col] == value
        same_value_df = df[same_value_mask]
        
        # Добавляем всех с таким значением
        for _, row in same_value_df.iterrows():
            is_top3 = current_rank <= 3
            result.append({
                'rank': current_rank,
                'name': row[name_col],
                'value': int(row[value_col]),
                'top3': is_top3,
                'tied_count': len(same_value_df)
            })
        
        # Переходим к следующему уникальному значению
        i += len(same_value_df)
        current_rank += len(same_value_df)
        
        if max_results and len(result) >= max_results:
            break
    
    return result

# Загружаем данные
ru_wins = pd.read_csv('russian_dancers_top_wins_2025.csv').sort_values('wins_2025', ascending=False)
ru_points = pd.read_csv('russian_dancers_top_points_2025.csv').sort_values('points_2025', ascending=False)
ru_events = pd.read_csv('russian_dancers_top_events_2025.csv').sort_values('events_2025', ascending=False)

global_wins = pd.read_csv('dancers_top_wins_2025.csv').sort_values('wins_2025', ascending=False)
global_points = pd.read_csv('dancers_top_points_2025.csv').sort_values('points_2025', ascending=False)
global_events = pd.read_csv('dancers_top_events_2025.csv').sort_values('events_2025', ascending=False)

print("=== RUSSIAN WINS ===")
ru_wins_ranks = generate_ranks_with_ties(ru_wins, 'wins_2025', 'dancer_name')
print(f"Всего записей с учетом ties: {len(ru_wins_ranks)}")
for item in ru_wins_ranks[:15]:
    print(f"{{rank: {item['rank']}, name: '{item['name']}', value: {item['value']}, top3: {item['top3']}}},\n", end='')

print("\n=== RUSSIAN EVENTS ===")
ru_events_ranks = generate_ranks_with_ties(ru_events, 'events_2025', 'dancer_name')
print(f"Всего записей с учетом ties: {len(ru_events_ranks)}")
for item in ru_events_ranks[:12]:
    print(f"{{rank: {item['rank']}, name: '{item['name']}', value: {item['value']}, top3: {item['top3']}}},\n", end='')

print("\n=== GLOBAL WINS ===")
global_wins_ranks = generate_ranks_with_ties(global_wins, 'wins_2025', 'dancer_name')
print(f"Всего записей с учетом ties: {len(global_wins_ranks)}")
for item in global_wins_ranks[:20]:
    print(f"{{rank: {item['rank']}, name: '{item['name']}', value: {item['value']}, top3: {item['top3']}}},\n", end='')

