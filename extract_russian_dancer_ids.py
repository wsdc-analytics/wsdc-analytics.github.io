#!/usr/bin/env python3
"""
Извлечение ID российских танцоров из divisions.json.gz
"""

import requests
import gzip
import json

print("Загрузка и анализ divisions.json.gz...")

url = "https://raw.githubusercontent.com/apushkarev/apushkarev.github.io/master/wsdc/divisions.json.gz"
response = requests.get(url, stream=True)

if response.status_code != 200:
    print(f"❌ Ошибка загрузки: {response.status_code}")
    exit(1)

# Распаковываем gzip
data = gzip.decompress(response.content)
divisions_data = json.loads(data.decode('utf-8'))

print(f"✅ Файл загружен и распакован")

# Извлекаем все уникальные wscid
russian_dancer_ids = set()

def extract_ids(obj):
    """Рекурсивно извлекает wscid/dancer_wsdcid из структуры"""
    if isinstance(obj, dict):
        # Проверяем ключи, которые могут содержать ID
        if 'dancer_wsdcid' in obj:
            russian_dancer_ids.add(str(obj['dancer_wsdcid']))
        if 'wscid' in obj:
            russian_dancer_ids.add(str(obj['wscid']))
        if 'dancer' in obj and isinstance(obj['dancer'], dict):
            if 'wscid' in obj['dancer']:
                russian_dancer_ids.add(str(obj['dancer']['wscid']))
        # Рекурсивно обходим все значения
        for value in obj.values():
            extract_ids(value)
    elif isinstance(obj, list):
        for item in obj:
            extract_ids(item)

extract_ids(divisions_data)

print(f"\n✅ Найдено уникальных ID: {len(russian_dancer_ids)}")

# Показываем первые 30 для проверки
print("\nПервые 30 ID:")
for i, dancer_id in enumerate(sorted(russian_dancer_ids, key=int)[:30]):
    print(f"  {i+1}. {dancer_id}")

# Сохраняем в файл
output_file = 'russian_dancer_ids.txt'
with open(output_file, 'w') as f:
    for dancer_id in sorted(russian_dancer_ids, key=int):
        f.write(f"{dancer_id}\n")

print(f"\n✅ Все ID сохранены в {output_file}")
print(f"Всего уникальных ID: {len(russian_dancer_ids)}")

