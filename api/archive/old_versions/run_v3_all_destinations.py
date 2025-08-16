#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3スクレイパーで全目的地のルート情報を取得
ルフォンプログレから10時到着で検索
"""

import json
import os
from datetime import datetime, timedelta
import sys

# v3スクレイパーをインポート
from google_maps_scraper_v3 import scrape_route

def load_destinations():
    """destinations.jsonを読み込む"""
    dest_file = '/app/output/japandatascience.com/timeline-mapping/data/destinations.json'
    with open(dest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

def main():
    # ルフォンプログレの住所
    origin = "東京都千代田区神田須田町1-20-1"
    
    # 明日の10時到着
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # 目的地を読み込む
    destinations = load_destinations()
    
    print(f"=== v3スクレイパーによる全目的地ルート検索 ===")
    print(f"出発地: {origin}")
    print(f"到着時刻: {arrival_10am.strftime('%Y-%m-%d %H:%M')}")
    print(f"目的地数: {len(destinations)}")
    print("=" * 50)
    
    results = []
    success_count = 0
    
    for i, dest in enumerate(destinations, 1):
        dest_name = dest['name']
        dest_address = dest['address']
        dest_id = dest['id']
        
        print(f"\n[{i}/{len(destinations)}] {dest_name}")
        print(f"  住所: {dest_address}")
        
        try:
            # v3で検索
            result = scrape_route(
                origin, 
                dest_address, 
                arrival_time=arrival_10am,
                save_debug=False  # デバッグファイルは保存しない
            )
            
            if result and result.get('travel_time'):
                print(f"  ✓ 成功: {result['travel_time']}分")
                
                # 結果を保存
                route_data = {
                    'destination_id': dest_id,
                    'destination_name': dest_name,
                    'destination_address': dest_address,
                    'travel_time': result['travel_time'],
                    'scraped_at': result.get('scraped_at'),
                    'route_count': len(result.get('all_routes', [])),
                    'origin_coords': {
                        'lat': result['origin_details'].get('lat'),
                        'lng': result['origin_details'].get('lng')
                    },
                    'destination_coords': {
                        'lat': result['destination_details'].get('lat'),
                        'lng': result['destination_details'].get('lng')
                    }
                }
                results.append(route_data)
                success_count += 1
            else:
                print(f"  ✗ 失敗: ルート情報を取得できませんでした")
                results.append({
                    'destination_id': dest_id,
                    'destination_name': dest_name,
                    'destination_address': dest_address,
                    'travel_time': None,
                    'error': 'No route found'
                })
                
        except Exception as e:
            print(f"  ✗ エラー: {str(e)}")
            results.append({
                'destination_id': dest_id,
                'destination_name': dest_name,
                'destination_address': dest_address,
                'travel_time': None,
                'error': str(e)
            })
    
    # 結果をファイルに保存
    output_file = f'/app/output/japandatascience.com/timeline-mapping/api/v3_all_destinations_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'origin': origin,
            'arrival_time': arrival_10am.isoformat(),
            'total_destinations': len(destinations),
            'successful': success_count,
            'failed': len(destinations) - success_count,
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"完了!")
    print(f"成功: {success_count}/{len(destinations)}")
    print(f"結果ファイル: {output_file}")
    
    # 簡易サマリーを表示
    print("\n=== 結果サマリー ===")
    for r in results:
        if r.get('travel_time'):
            print(f"{r['destination_name']}: {r['travel_time']}分")
        else:
            print(f"{r['destination_name']}: 失敗 ({r.get('error', 'Unknown error')})")

if __name__ == "__main__":
    main()