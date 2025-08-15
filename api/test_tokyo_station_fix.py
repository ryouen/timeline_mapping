#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
東京駅ルート修正テスト
徒歩区間問題を解決するため、より具体的な地点指定を試す
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta, timezone
import json

def test_tokyo_station_variations():
    """東京駅への異なるアプローチをテスト"""
    
    origin = "東京都千代田区神田須田町1-20-1"  # ルフォンプログレ
    
    # 複数の東京駅指定方法を試す
    destinations = [
        {
            "name": "東京駅（丸の内）- 元の指定",
            "address": "東京都千代田区丸の内１丁目"
        },
        {
            "name": "東京駅 - 駅名直接指定",
            "address": "東京駅"
        },
        {
            "name": "東京駅丸の内北口",
            "address": "東京駅丸の内北口"
        },
        {
            "name": "東京駅八重洲口",
            "address": "東京駅八重洲口"
        },
        {
            "name": "大丸東京店（東京駅直結）",
            "address": "東京都千代田区丸の内1-9-1 大丸東京店"
        },
        {
            "name": "JR東京駅",
            "address": "JR東京駅"
        }
    ]
    
    # 明日10時到着
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00
    
    print("=" * 60)
    print("東京駅ルート修正テスト - 異なる地点指定方法の比較")
    print(f"出発地: {origin}")
    print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
    print("=" * 60)
    
    results = []
    
    for i, dest in enumerate(destinations, 1):
        print(f"\n[{i}/{len(destinations)}] {dest['name']}")
        print(f"  住所: {dest['address']}")
        
        try:
            result = scrape_route(
                origin,
                dest['address'],
                arrival_time=arrival_10am,
                save_debug=False  # デバッグファイルは最小限に
            )
            
            if result:
                # 最短ルートの詳細を取得
                shortest_route = min(result['all_routes'], key=lambda r: r['total_time'])
                
                # 車ルートかどうかを判定
                is_car = False
                route_text = shortest_route.get('raw_text', '')
                if any(word in route_text for word in ['中央通り', '国道', '都道', '号線', '車で']):
                    is_car = True
                
                # 公共交通機関の指標があるか
                has_transit = any(word in route_text for word in ['駅', '線', '電車', 'バス', '徒歩', '乗換'])
                
                print(f"  ✓ 所要時間: {result['travel_time']}分")
                print(f"  ✓ ルートタイプ: {'🚗 車ルート' if is_car else '🚇 公共交通機関'}")
                if shortest_route.get('trains'):
                    print(f"  ✓ 経路詳細: {', '.join(shortest_route['trains'][:3])}")
                print(f"  ✓ URL: {result.get('url', 'N/A')[:100]}...")
                
                results.append({
                    'destination': dest['name'],
                    'address': dest['address'],
                    'travel_time': result['travel_time'],
                    'is_car': is_car,
                    'has_transit': has_transit,
                    'route_details': shortest_route.get('trains', []),
                    'url': result.get('url'),
                    'coordinates': {
                        'lat': result['destination_details'].get('lat'),
                        'lng': result['destination_details'].get('lng')
                    }
                })
            else:
                print(f"  ✗ スクレイピング失敗")
                results.append({
                    'destination': dest['name'],
                    'address': dest['address'],
                    'error': 'Failed to scrape'
                })
                
        except Exception as e:
            print(f"  ✗ エラー: {e}")
            results.append({
                'destination': dest['name'],
                'address': dest['address'],
                'error': str(e)
            })
    
    # 結果のサマリー
    print("\n" + "=" * 60)
    print("結果サマリー")
    print("=" * 60)
    
    transit_results = [r for r in results if not r.get('is_car', True) and not r.get('error')]
    car_results = [r for r in results if r.get('is_car', False)]
    failed_results = [r for r in results if r.get('error')]
    
    if transit_results:
        print(f"\n✅ 公共交通機関として取得成功: {len(transit_results)}件")
        for r in transit_results:
            print(f"  - {r['destination']}: {r['travel_time']}分")
            if r.get('coordinates'):
                print(f"    座標: {r['coordinates']['lat']}, {r['coordinates']['lng']}")
    
    if car_results:
        print(f"\n❌ 車ルートとして取得: {len(car_results)}件")
        for r in car_results:
            print(f"  - {r['destination']}: {r['travel_time']}分")
    
    if failed_results:
        print(f"\n⚠️ 取得失敗: {len(failed_results)}件")
        for r in failed_results:
            print(f"  - {r['destination']}: {r.get('error', 'Unknown error')}")
    
    # 推奨する解決策
    if transit_results:
        best = min(transit_results, key=lambda x: x['travel_time'])
        print(f"\n🎯 推奨: 「{best['address']}」を使用")
        print(f"  理由: 公共交通機関として{best['travel_time']}分で取得可能")
        
        # JSONファイルに保存
        with open('/app/output/japandatascience.com/timeline-mapping/api/tokyo_station_fix_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'tested_at': datetime.now().isoformat(),
                'origin': origin,
                'results': results,
                'recommendation': {
                    'use_address': best['address'],
                    'travel_time': best['travel_time'],
                    'coordinates': best.get('coordinates')
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"\n結果をtokyo_station_fix_results.jsonに保存しました")

if __name__ == "__main__":
    test_tokyo_station_variations()