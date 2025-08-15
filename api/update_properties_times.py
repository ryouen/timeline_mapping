#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
properties.jsonの所要時間を更新
v3スクレイパーの結果に基づいて、ルフォンプログレ神田プレミアの所要時間を更新
"""

import json

def update_properties():
    # v3スクレイパーの結果（v3_results_summary.htmlから）
    new_times = {
        "shizenkan_university": 7,    # 変更なし
        "tokyo_american_club": 7,      # 変更なし
        "axle_ochanomizu": 13,        # 8 → 13
        "yawara": 33,                  # 34 → 33
        "kamiyacho_ee": 18,            # 23 → 18
        "waseda_university": 31,       # 35 → 31
        "fuchu_office": 62,            # 48 → 62
        "tokyo_station": 9,            # 11 → 9（注：車ルート）
        "haneda_airport": 29           # 55 → 29
    }
    
    # properties.jsonを読み込む
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 最初のプロパティ（ルフォンプログレ神田プレミア）のルートを更新
    if data['properties'] and len(data['properties']) > 0:
        property = data['properties'][0]
        
        if property['name'] == "ルフォンプログレ神田プレミア":
            print(f"更新対象プロパティ: {property['name']}")
            print(f"住所: {property['address']}")
            print("\n所要時間の更新:")
            
            # 各ルートの所要時間を更新
            for route in property['routes']:
                dest_id = route['destination']
                old_time = route['total_time']
                
                if dest_id in new_times:
                    new_time = new_times[dest_id]
                    route['total_time'] = new_time
                    
                    if old_time != new_time:
                        print(f"  {route['destination_name']}: {old_time}分 → {new_time}分")
                    else:
                        print(f"  {route['destination_name']}: {old_time}分 (変更なし)")
                        
                    # 東京駅の特記事項
                    if dest_id == "tokyo_station":
                        print(f"    注意: 車ルートとして検出されています（要改善）")
    
    # バックアップを作成
    from datetime import datetime
    backup_filename = f'/app/output/japandatascience.com/timeline-mapping/data/properties_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_filename, 'w', encoding='utf-8') as f:
        with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    print(f"\nバックアップ作成: {backup_filename}")
    
    # 更新したデータを保存
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\nproperties.json を更新しました")
    print("\n=== 更新後の所要時間一覧 ===")
    for route in data['properties'][0]['routes']:
        print(f"{route['destination_name']:20} : {route['total_time']:3}分")

if __name__ == "__main__":
    update_properties()