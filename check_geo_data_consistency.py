#!/usr/bin/env python3
"""
Проверка согласованности данных между таблицами в geo_2025.html
"""

import csv
import re
from collections import defaultdict

def load_geo_data():
    """Загрузка данных из CSV файлов"""
    # Здесь нужно загрузить данные из ваших CSV файлов
    # Пока используем паттерн поиска по файлам
    
    states_data = {}
    regions_data = {}
    
    # Попробуем найти файлы с данными
    try:
        with open('dancers_results_info.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Логика обработки данных
                pass
    except FileNotFoundError:
        print("CSV файлы не найдены, нужно указать путь к данным")
    
    return states_data, regions_data

def extract_table_data_from_html(html_file):
    """Извлекает данные из HTML таблиц"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим региональную таблицу
    regional_table = re.search(r'Регион.*?</table>', content, re.DOTALL)
    # Находим таблицу штатов США
    states_table = re.search(r'Штат.*?</table>', content, re.DOTALL)
    
    regional_data = {}
    states_data = {}
    
    # Извлекаем данные из региональной таблицы
    if regional_table:
        rows = re.findall(r'<tr>.*?</tr>', regional_table.group(), re.DOTALL)
        for row in rows:
            # Ищем название региона
            region_match = re.search(r'<td[^>]*>([^<]+(?:USA|France|Germany|Sweden|Poland|Russia|United Kingdom|Hungary|Florida))[^<]*)</td>', row)
            if not region_match:
                continue
            
            region_name = region_match.group(1).strip()
            # Извлекаем числа
            numbers = re.findall(r'<td[^>]*>([0-9,]+)</td>', row)
            if len(numbers) >= 4:
                regional_data[region_name] = {
                    'events': numbers[0].replace(',', ''),
                    'points': numbers[1].replace(',', ''),
                    'unique': numbers[2].replace(',', ''),
                    'new': numbers[3].replace(',', '')
                }
    
    # Извлекаем данные из таблицы штатов
    if states_table:
        rows = re.findall(r'<tr>.*?</tr>', states_table.group(), re.DOTALL)
        for row in rows:
            state_match = re.search(r'<td[^>]*>([A-Za-z ]+)</td>', row)
            if not state_match:
                continue
            
            state_name = state_match.group(1).strip()
            numbers = re.findall(r'<td[^>]*>([0-9,]+)</td>', row)
            if len(numbers) >= 4:
                states_data[state_name] = {
                    'events': numbers[0].replace(',', ''),
                    'points': numbers[1].replace(',', ''),
                    'unique': numbers[2].replace(',', ''),
                    'new': numbers[3].replace(',', '')
                }
    
    return regional_data, states_data

# Проверяем данные
html_file = 'geo_2025.html'
regional_data, states_data = extract_table_data_from_html(html_file)

print("=== РЕГИОНАЛЬНАЯ ТАБЛИЦА ===")
for region, data in regional_data.items():
    if 'Florida' in region or 'Oregon' in region or 'Massachusetts' in region:
        print(f"{region}: Points={data['points']}, New={data['new']}")

print("\n=== ТАБЛИЦА ШТАТОВ США ===")
for state, data in states_data.items():
    if state in ['Florida', 'Oregon', 'Massachusetts']:
        print(f"{state}: Points={data['points']}, New={data['new']}")

print("\n=== СРАВНЕНИЕ ===")
if 'Florida' in regional_data.get('Florida, USA', {}):
    reg_fl = regional_data.get('Florida, USA', {})
    states_fl = states_data.get('Florida', {})
    if reg_fl.get('new') != states_fl.get('new'):
        print(f"⚠️ Florida New не совпадает: региональная={reg_fl.get('new')}, штаты={states_fl.get('new')}")

