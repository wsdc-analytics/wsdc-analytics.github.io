#!/usr/bin/env python3
"""
Комплексный аудит проекта на соответствие лучшим практикам
"""

import re
import os
from collections import defaultdict

issues = defaultdict(list)
warnings = defaultdict(list)
good_practices = defaultdict(list)

def check_html_file(filepath):
    """Проверка HTML файла на best practices"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    
    # 1. DOCTYPE
    if not re.search(r'<!DOCTYPE html>', content, re.IGNORECASE):
        issues[filename].append("❌ Отсутствует <!DOCTYPE html>")
    else:
        good_practices[filename].append("✅ Есть DOCTYPE")
    
    # 2. Lang attribute
    html_tag = re.search(r'<html[^>]*>', content, re.IGNORECASE)
    if html_tag and 'lang=' not in html_tag.group(0):
        issues[filename].append("❌ Отсутствует атрибут lang в теге <html>")
    elif html_tag and 'lang=' in html_tag.group(0):
        good_practices[filename].append("✅ Есть атрибут lang в <html>")
    
    # 3. Viewport meta tag
    if not re.search(r'<meta[^>]*viewport', content, re.IGNORECASE):
        issues[filename].append("❌ Отсутствует meta viewport для mobile")
    else:
        good_practices[filename].append("✅ Есть meta viewport")
    
    # 4. Charset
    if not re.search(r'<meta[^>]*charset', content, re.IGNORECASE):
        issues[filename].append("❌ Отсутствует meta charset")
    else:
        good_practices[filename].append("✅ Есть meta charset")
    
    # 5. Title tag
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if not title_match:
        issues[filename].append("❌ Отсутствует <title>")
    elif len(title_match.group(1).strip()) > 60:
        warnings[filename].append("⚠️  Title слишком длинный (>60 символов)")
    else:
        good_practices[filename].append("✅ Есть <title>")
    
    # 6. Meta description
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
    if not desc_match:
        warnings[filename].append("⚠️  Отсутствует meta description (SEO)")
    elif len(desc_match.group(1)) > 160:
        warnings[filename].append("⚠️  Meta description слишком длинный (>160 символов)")
    else:
        good_practices[filename].append("✅ Есть meta description")
    
    # 7. Open Graph tags
    og_tags = re.findall(r'<meta[^>]*property=["\']og:', content, re.IGNORECASE)
    if len(og_tags) < 3:
        warnings[filename].append(f"⚠️  Мало Open Graph тегов ({len(og_tags)}), рекомендуется минимум 3")
    else:
        good_practices[filename].append(f"✅ Есть Open Graph теги ({len(og_tags)})")
    
    # 8. Structured data (Schema.org)
    if 'application/ld+json' in content:
        good_practices[filename].append("✅ Есть structured data (JSON-LD)")
    else:
        warnings[filename].append("⚠️  Отсутствует structured data (Schema.org)")
    
    # 9. Alt attributes для изображений
    img_tags = re.findall(r'<img[^>]+>', content, re.IGNORECASE)
    img_without_alt = [img for img in img_tags if 'alt=' not in img.lower() and 'role=' not in img.lower()]
    if img_without_alt:
        issues[filename].append(f"❌ Найдено {len(img_without_alt)} изображений без alt (accessibility)")
    if img_tags:
        good_practices[filename].append(f"✅ Проверены изображения ({len(img_tags)} шт.)")
    
    # 10. External links (target="_blank" + rel="noopener")
    ext_links = re.findall(r'<a[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>', content, re.IGNORECASE)
    links_with_target = re.findall(r'<a[^>]*target=["\']_blank["\'][^>]*>', content, re.IGNORECASE)
    links_with_noopener = re.findall(r'<a[^>]*rel=["\'][^"\']*noopener[^"\']*["\'][^>]*>', content, re.IGNORECASE)
    
    if ext_links and len(links_with_target) > 0:
        if len(links_with_noopener) < len(links_with_target):
            warnings[filename].append(f"⚠️  Некоторые внешние ссылки с target='_blank' без rel='noopener' (security)")
        else:
            good_practices[filename].append("✅ Внешние ссылки с rel='noopener'")
    
    # 11. Inline styles (не рекомендуется для больших стилей)
    inline_style_blocks = len(re.findall(r'<style[^>]*>', content, re.IGNORECASE))
    if inline_style_blocks > 1:
        good_practices[filename].append(f"✅ Используются <style> блоки ({inline_style_blocks})")
    
    # 12. Inline scripts (security considerations)
    inline_scripts = len(re.findall(r'<script[^>]*>(?!.*src=)', content, re.IGNORECASE | re.DOTALL))
    if inline_scripts > 0:
        good_practices[filename].append(f"✅ Есть inline scripts ({inline_scripts})")
    
    # 13. Google Analytics
    if 'gtag' in content or 'google-analytics' in content.lower() or 'googletagmanager' in content:
        good_practices[filename].append("✅ Настроен Google Analytics")
    
    # 14. Проверка на устаревшие теги
    deprecated_tags = ['<center>', '<font>', '<marquee>', '<blink>']
    for tag in deprecated_tags:
        if tag in content:
            issues[filename].append(f"❌ Используется устаревший тег: {tag}")
    
    # 15. Проверка на отсутствие закрывающих тегов (базовая)
    open_tags = len(re.findall(r'<(img|br|hr|input|meta|link)[^>]*>', content, re.IGNORECASE))
    # Это нормально для void элементов
    
    # 16. Accessibility: заголовки (h1-h6)
    h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
    if h1_count == 0:
        warnings[filename].append("⚠️  Отсутствует <h1> (SEO/accessibility)")
    elif h1_count > 1:
        warnings[filename].append(f"⚠️  Несколько <h1> тегов ({h1_count}), рекомендуется один")
    else:
        good_practices[filename].append("✅ Есть один <h1>")
    
    # 17. Semantic HTML
    semantic_tags = ['<header>', '<nav>', '<main>', '<article>', '<section>', '<aside>', '<footer>']
    found_semantic = [tag for tag in semantic_tags if tag in content]
    if found_semantic:
        good_practices[filename].append(f"✅ Используются semantic теги: {', '.join([t.replace('<', '').replace('>', '') for t in found_semantic])}")
    
    # 18. ARIA labels (accessibility)
    aria_labels = len(re.findall(r'aria-', content, re.IGNORECASE))
    if aria_labels > 0:
        good_practices[filename].append(f"✅ Используются ARIA атрибуты ({aria_labels})")
    
    return len(issues[filename]), len(warnings[filename]), len(good_practices[filename])

def check_files():
    """Проверка файлов проекта"""
    html_files = [
        'index.html',
        'events_2025.html',
        'events_2025_en.html',
        'geo_2025.html'
    ]
    
    total_issues = 0
    total_warnings = 0
    total_good = 0
    
    for html_file in html_files:
        filepath = os.path.join('/Users/ania/.cursor/wsdc-analytics-repo', html_file)
        if os.path.exists(filepath):
            issues_count, warnings_count, good_count = check_html_file(filepath)
            total_issues += issues_count
            total_warnings += warnings_count
            total_good += good_count
        else:
            print(f"⚠️  Файл {html_file} не найден")
    
    return total_issues, total_warnings, total_good

def check_project_structure():
    """Проверка структуры проекта"""
    repo_path = '/Users/ania/.cursor/wsdc-analytics-repo'
    
    # Проверка robots.txt
    robots_path = os.path.join(repo_path, 'robots.txt')
    if os.path.exists(robots_path):
        good_practices['project'].append("✅ Есть robots.txt")
        with open(robots_path, 'r') as f:
            robots_content = f.read()
            if 'Sitemap:' in robots_content:
                good_practices['project'].append("✅ robots.txt содержит Sitemap")
    else:
        warnings['project'].append("⚠️  Отсутствует robots.txt")
    
    # Проверка sitemap.xml
    sitemap_path = os.path.join(repo_path, 'sitemap.xml')
    if os.path.exists(sitemap_path):
        good_practices['project'].append("✅ Есть sitemap.xml")
    else:
        warnings['project'].append("⚠️  Отсутствует sitemap.xml")
    
    # Проверка README
    readme_path = os.path.join(repo_path, 'README.md')
    if os.path.exists(readme_path):
        good_practices['project'].append("✅ Есть README.md")
    else:
        warnings['project'].append("⚠️  Отсутствует README.md")

def print_report():
    """Вывод отчета"""
    print("=" * 80)
    print("📊 АУДИТ ПРОЕКТА НА СООТВЕТСТВИЕ ЛУЧШИМ ПРАКТИКАМ")
    print("=" * 80)
    print()
    
    # Структура проекта
    check_project_structure()
    
    # Проверка файлов
    total_issues, total_warnings, total_good = check_files()
    
    # Вывод результатов по файлам
    for filename in sorted(set(list(issues.keys()) + list(warnings.keys()) + list(good_practices.keys()))):
        if filename == 'project':
            continue
        
        print(f"\n📄 {filename}")
        print("-" * 80)
        
        if filename in issues:
            for issue in issues[filename]:
                print(f"  {issue}")
        
        if filename in warnings:
            for warning in warnings[filename]:
                print(f"  {warning}")
        
        if filename in good_practices:
            for good in good_practices[filename]:
                print(f"  {good}")
    
    # Общие результаты по проекту
    print(f"\n📦 Структура проекта")
    print("-" * 80)
    if 'project' in good_practices:
        for good in good_practices['project']:
            print(f"  {good}")
    if 'project' in warnings:
        for warning in warnings['project']:
            print(f"  {warning}")
    
    # Итоговая статистика
    print("\n" + "=" * 80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    print(f"  ✅ Хороших практик: {total_good}")
    print(f"  ⚠️  Предупреждений: {total_warnings}")
    print(f"  ❌ Критических проблем: {total_issues}")
    print()
    
    if total_issues == 0 and total_warnings == 0:
        print("🎉 Отлично! Все проверки пройдены успешно!")
    elif total_issues == 0:
        print("✅ Критических проблем нет. Есть рекомендации для улучшения.")
    else:
        print("⚠️  Рекомендуется исправить критические проблемы.")

if __name__ == '__main__':
    print_report()


