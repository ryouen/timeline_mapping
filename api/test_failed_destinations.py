#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
失敗した近距離目的地の再テスト
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta
import json

def test_failed_destinations():
    origin = "東京都千代田区神田須田町1-20-1"
    
    # 失敗した4つの目的地
    failed_destinations = [
        {
            "id": "shizenkan_university",
            "name": "Shizenkan University",
            "address": "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階"
        },
        {
            "id": "tokyo_american_club",
            "name": "東京アメリカンクラブ",
            "address": "東京都中央区日本橋室町３丁目２−１"
        },
        {
            "id": "axle_ochanomizu",
            "name": "axle 御茶ノ水",
            "address": "東京都千代田区神田小川町３丁目２８−５"
        },
        {
            "id": "tokyo_station",
            "name": "東京駅",
            "address": "東京都千代田区丸の内１丁目"
        }
    ]
    
    # 明日の10時到着
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print(f"=== 失敗した近距離目的地の再テスト ===")
    print(f"出発地: {origin}")
    print(f"到着時刻: {arrival_10am.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    results = []
    
    for dest in failed_destinations:
        print(f"\n{dest['name']}:")
        print(f"  住所: {dest['address']}")
        
        result = scrape_route(
            origin, 
            dest['address'], 
            arrival_time=arrival_10am,
            save_debug=True
        )
        
        if result:
            print(f"  ✓ 成功: {result['travel_time']}分")
            print(f"  URL: {result.get('url', 'N/A')}")
            
            # URLを結果に追加
            results.append({
                'id': dest['id'],
                'name': dest['name'],
                'address': dest['address'],
                'travel_time': result['travel_time'],
                'url': build_complete_url(
                    result['origin_details'],
                    result['destination_details'],
                    arrival_time=arrival_10am
                ),
                'route_count': len(result.get('all_routes', [])),
                'status': 'success'
            })
        else:
            print(f"  ✗ 失敗")
            results.append({
                'id': dest['id'],
                'name': dest['name'],
                'address': dest['address'],
                'travel_time': None,
                'url': None,
                'status': 'failed'
            })
    
    # 結果を保存
    output_file = f'/var/www/japandatascience.com/timeline-mapping/api/retest_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'origin': origin,
            'arrival_time': arrival_10am.isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果を保存: {output_file}")
    return results

# URLビルド関数をインポート
from google_maps_scraper_v3 import build_complete_url

if __name__ == "__main__":
    test_failed_destinations()