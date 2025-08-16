#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shizenkanルートのテスト - 車ルート除外確認
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta
import json

def test_shizenkan():
    """Shizenkanへのルートをテスト（公共交通機関のみ）"""
    
    # ルフォンプログレの情報
    origin = "東京都千代田区神田須田町1-20-1"
    destination = "東京都中央区日本橋２丁目１６−３"  # Shizenkan University
    
    # 明日の10時到着
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("=" * 60)
    print("Shizenkanルートテスト - 公共交通機関のみ")
    print(f"出発地: {origin}")
    print(f"目的地: {destination}")
    print(f"到着時刻: {arrival_10am.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # スクレイピング実行
    result = scrape_route(origin, destination, arrival_time=arrival_10am, save_debug=True)
    
    if result:
        print(f"\n✓ スクレイピング成功")
        print(f"URL: {result['url']}")
        print(f"\n場所情報:")
        print(f"  出発地 Place ID: {result['origin_details'].get('place_id', 'なし')}")
        print(f"  目的地 Place ID: {result['destination_details'].get('place_id', 'なし')}")
        
        print(f"\n最短所要時間: {result['travel_time']}分")
        
        print(f"\nすべてのルート（公共交通機関のみ）:")
        for i, route in enumerate(result['all_routes']):
            route_type = ""
            if route.get('is_walking_only'):
                route_type = " (徒歩のみ)"
            elif route.get('has_train'):
                route_type = " (電車/バス)"
            else:
                route_type = " (公共交通)"
                
            print(f"  ルート{i+1}: {route['total_time']}分{route_type}")
            if route['trains']:
                print(f"    経路: {' → '.join(route['trains'][:3])}")
            
            # 最短ルートの詳細を表示
            shortest = min(result['all_routes'], key=lambda r: r['total_time'])
            if route == shortest:
                print(f"    ★ これが選択されたルートです")
                if route['total_time'] == 6:
                    print(f"    ⚠️  6分のルートが選択されています - 車ルートの可能性")
                elif route['total_time'] == 7:
                    print(f"    ✓ 7分のルート - ゴールデンデータと一致")
    else:
        print("\n✗ スクレイピング失敗")
        print("公共交通機関のルートが見つかりませんでした")

if __name__ == "__main__":
    test_shizenkan()