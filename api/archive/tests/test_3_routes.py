#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5スクレイパーで3ルートをテスト
近距離、中距離、長距離を各1つずつテスト
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5 import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz
import json

def test_3_routes():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🚇 v5スクレイパー 3ルートテスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # テストルート（近距離、中距離、長距離）
    test_routes = [
        {
            'property': 'ルフォンプログレ神田プレミア',
            'origin': '東京都千代田区 神田須田町１丁目２０−１',
            'destination_name': 'Shizenkan University',
            'destination': '東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階',
            'expected_type': '近距離（徒歩または短時間電車）'
        },
        {
            'property': 'ルフォンプログレ神田プレミア',
            'origin': '東京都千代田区 神田須田町１丁目２０−１',
            'destination_name': '早稲田大学',
            'destination': '東京都新宿区西早稲田１丁目６ 11号館',
            'expected_type': '中距離（電車必須）'
        },
        {
            'property': 'ルフォンプログレ神田プレミア', 
            'origin': '東京都千代田区 神田須田町１丁目２０−１',
            'destination_name': '府中オフィス',
            'destination': '東京都府中市住吉町５丁目２２−５',
            'expected_type': '長距離（複数路線利用）'
        }
    ]
    
    scraper = GoogleMapsScraperV5()
    
    try:
        print("\n📌 WebDriver初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了\n")
        
        results = []
        
        for i, route in enumerate(test_routes, 1):
            print("="*80)
            print(f"🔍 テスト {i}/3: {route['destination_name']} ({route['expected_type']})")
            print("-"*80)
            print(f"出発: {route['origin']}")
            print(f"到着: {route['destination'][:50]}...")
            
            result = scraper.scrape_route(
                route['origin'],
                route['destination'],
                route['destination_name'],
                arrival_time
            )
            
            if result.get('success'):
                print(f"\n✅ 取得成功")
                print(f"  総所要時間: {result['travel_time']}分")
                print(f"  ルートタイプ: {result['route_type']}")
                print(f"  料金: ¥{result.get('fare', 'N/A')}")
                print(f"  時刻: {result.get('departure_time', 'N/A')} → {result.get('arrival_time', 'N/A')}")
                
                # 路線情報
                if result.get('train_lines'):
                    print(f"  路線: {', '.join(result['train_lines'])}")
                
                # Place ID
                print(f"\n  Place ID:")
                print(f"    出発: {result['place_ids']['origin']}")
                print(f"    到着: {result['place_ids']['destination']}")
                
                # 全ルート候補
                if result.get('all_routes'):
                    print(f"\n  ルート候補数: {len(result['all_routes'])}個")
                    for j, alt in enumerate(result['all_routes'][:3], 1):
                        print(f"    候補{j}: {alt['travel_time']}分 ({alt['route_type']})")
                        if alt.get('train_lines'):
                            print(f"         路線: {', '.join(alt['train_lines'])}")
                
                # キャッシュ状態
                if result.get('from_cache'):
                    print(f"\n  ⚡ キャッシュから取得")
                
                results.append({
                    'route_name': route['destination_name'],
                    'success': True,
                    'data': {
                        'travel_time': result['travel_time'],
                        'route_type': result['route_type'],
                        'fare': result.get('fare'),
                        'departure_time': result.get('departure_time'),
                        'arrival_time': result.get('arrival_time'),
                        'train_lines': result.get('train_lines', [])
                    }
                })
            else:
                print(f"\n❌ 取得失敗: {result.get('error')}")
                results.append({
                    'route_name': route['destination_name'],
                    'success': False,
                    'error': result.get('error')
                })
            
            print("")  # 空行
        
        # サマリー
        print("="*80)
        print("📊 テスト結果サマリー")
        print("="*80)
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n成功率: {success_count}/3 ({success_count*100/3:.0f}%)")
        
        print("\n【取得結果】")
        for r in results:
            if r['success']:
                data = r['data']
                print(f"  {r['route_name']:20}: {data['travel_time']:3}分 ({data['route_type']})")
                if data['train_lines']:
                    print(f"  {'':20}  路線: {', '.join(data['train_lines'])}")
        
        # 結果をJSON保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/test_3_routes_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 結果を保存: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔧 クリーンアップ中...")
        scraper.close()
        print("✅ 完了")

if __name__ == "__main__":
    test_3_routes()