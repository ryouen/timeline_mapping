#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現在のproperties.jsonのデータ品質を分析
"""

import json
from collections import Counter

def analyze_properties_data():
    # データ読み込み
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("="*80)
    print("📊 properties.json データ品質分析")
    print("="*80)
    
    # 基本統計
    print(f"\n物件数: {len(data['properties'])}")
    
    # 全ルートを収集
    all_routes = []
    for prop in data['properties']:
        for route in prop.get('routes', []):
            route['property_name'] = prop['name']
            all_routes.append(route)
    
    print(f"総ルート数: {len(all_routes)}")
    
    # 異常な徒歩時間を検出
    print("\n【異常な徒歩時間（10分以上）】")
    suspicious_walks = []
    for route in all_routes:
        if route.get('total_walk_time', 0) >= 10:
            suspicious_walks.append({
                'property': route['property_name'],
                'destination': route.get('destination_name', route.get('destination')),
                'walk_time': route.get('total_walk_time'),
                'total_time': route.get('total_time')
            })
    
    for walk in sorted(suspicious_walks, key=lambda x: x['walk_time'], reverse=True)[:10]:
        print(f"  {walk['property'][:20]:20} → {walk['destination']:20}: 徒歩{walk['walk_time']}分 (総{walk['total_time']}分)")
    
    # 駅の使用頻度
    print("\n【使用駅の統計】")
    stations = Counter()
    for route in all_routes:
        if 'details' in route and 'station_used' in route['details']:
            stations[route['details']['station_used']] += 1
    
    for station, count in stations.most_common():
        print(f"  {station}: {count}回")
    
    # 路線の使用頻度
    print("\n【使用路線の統計】")
    lines = Counter()
    for route in all_routes:
        if 'details' in route and 'trains' in route['details']:
            for train in route['details']['trains']:
                if 'line' in train:
                    lines[train['line']] += 1
    
    for line, count in lines.most_common():
        print(f"  {line}: {count}回")
    
    # 同じ経路パターンを検出
    print("\n【重複する経路パターン（駅→駅）】")
    train_patterns = Counter()
    for route in all_routes:
        if 'details' in route and 'trains' in route['details']:
            for train in route['details']['trains']:
                if 'from' in train and 'to' in train:
                    pattern = f"{train['from']}→{train['to']}"
                    train_patterns[pattern] += 1
    
    print("最頻出パターン:")
    for pattern, count in train_patterns.most_common(5):
        print(f"  {pattern}: {count}回")
    
    # 不自然なパターンを検出
    print("\n【不自然な可能性があるパターン】")
    
    # 神田→日本橋が多すぎる場合
    kanda_nihonbashi = train_patterns.get('神田→日本橋', 0)
    if kanda_nihonbashi > len(data['properties']) * 3:  # 物件数×3以上なら異常
        print(f"  ⚠️ '神田→日本橋'が{kanda_nihonbashi}回出現（物件数の{kanda_nihonbashi/len(data['properties']):.1f}倍）")
    
    # 所要時間の分布
    print("\n【所要時間の分布】")
    time_ranges = {
        '0-10分': 0,
        '11-20分': 0,
        '21-30分': 0,
        '31-45分': 0,
        '46-60分': 0,
        '60分以上': 0
    }
    
    for route in all_routes:
        time = route.get('total_time', 0)
        if time <= 10:
            time_ranges['0-10分'] += 1
        elif time <= 20:
            time_ranges['11-20分'] += 1
        elif time <= 30:
            time_ranges['21-30分'] += 1
        elif time <= 45:
            time_ranges['31-45分'] += 1
        elif time <= 60:
            time_ranges['46-60分'] += 1
        else:
            time_ranges['60分以上'] += 1
    
    for range_name, count in time_ranges.items():
        percentage = (count / len(all_routes)) * 100 if all_routes else 0
        print(f"  {range_name}: {count}件 ({percentage:.1f}%)")
    
    # データ品質スコア
    print("\n【データ品質評価】")
    issues = []
    
    # 徒歩時間が異常に長い
    if len(suspicious_walks) > len(all_routes) * 0.1:
        issues.append(f"徒歩時間が10分以上のルートが{len(suspicious_walks)}件（{len(suspicious_walks)/len(all_routes)*100:.1f}%）")
    
    # 同じパターンが多すぎる
    most_common_pattern = train_patterns.most_common(1)[0] if train_patterns else (None, 0)
    if most_common_pattern[1] > len(all_routes) * 0.3:
        issues.append(f"'{most_common_pattern[0]}'パターンが全体の{most_common_pattern[1]/len(all_routes)*100:.1f}%を占める")
    
    if issues:
        print("⚠️ 検出された問題:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ 重大な問題は検出されませんでした")
    
    return {
        'total_properties': len(data['properties']),
        'total_routes': len(all_routes),
        'suspicious_walks': len(suspicious_walks),
        'quality_issues': issues
    }

if __name__ == "__main__":
    result = analyze_properties_data()
    
    print("\n" + "="*80)
    print("💡 推奨事項")
    print("="*80)
    
    if result['suspicious_walks'] > 0:
        print("1. 徒歩時間が異常に長いルートを再取得する必要があります")
    
    if result['quality_issues']:
        print("2. データの多様性が不足している可能性があります")
        print("3. 全ルートを新規に取得し直すことを推奨します")
    else:
        print("データ品質は概ね良好です")