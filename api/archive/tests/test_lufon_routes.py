#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ルフォンプログレから9目的地へのルート検索テスト
Place IDを外部から渡してテスト
"""

import sys
import json
import logging
from datetime import datetime, timedelta
import pytz

# パスを追加
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_routes_with_place_ids():
    """Place IDを使用したルート検索テスト"""
    
    # テスト用Place ID（先ほど取得したもの）
    lufon_place_id = "ChIJ2RxO9gKMGGARSvjnp3ocfJg"
    lufon_lat = 35.6949994
    lufon_lon = 139.7711379
    lufon_address = "東京都千代田区神田須田町1-20-1"
    lufon_name = "ルフォンプログレ神田プレミア"
    
    # 目的地のPlace ID
    destinations = [
        {
            "name": "Shizenkan University",
            "address": "東京都中央区日本橋2-5-1",
            "place_id": "ChIJy_fF8PKJGGARr8tJ4FAd9gg"
        },
        {
            "name": "東京アメリカンクラブ",
            "address": "東京都中央区日本橋室町3-2-1",
            "place_id": "ChIJT1l75P-LGGARHl9jRRY1svU"
        },
        {
            "name": "axle御茶ノ水",
            "address": "東京都千代田区神田小川町3-28-5",
            "place_id": "ChIJ2SOIhhqMGGARQ9iwrbH-Pyo"
        },
        {
            "name": "Yawara",
            "address": "東京都渋谷区神宮前1-8-10",
            "place_id": "ChIJQZypWaOMGGAR92ErEJ-hYJ4"
        },
        {
            "name": "神谷町(EE)",
            "address": "東京都港区虎ノ門4-2-6",
            "place_id": "ChIJaVqfzJaLGGARju81iYTB4dQ"
        },
        {
            "name": "早稲田大学",
            "address": "東京都新宿区西早稲田1-6-11",
            "place_id": "ChIJ6a8IHyaNGGARKQZV2dkEKsU"
        },
        {
            "name": "東京駅",
            "address": "東京都千代田区丸の内1丁目",
            "place_id": "ChIJLdASefmLGGARF3Ez6A4i4Q4"
        },
        {
            "name": "羽田空港",
            "address": "東京都大田区羽田空港3-3-2",
            "place_id": "ChIJYQVK7-5jGGAR4lHBGzyAxgM"
        },
        {
            "name": "府中オフィス",
            "address": "東京都府中市住吉町5-22-5",
            "place_id": "ChIJR3AMl5nkGGARCqvDOHEMads"
        }
    ]
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("ルフォンプログレから9目的地へのルート検索テスト")
    print(f"出発地: {lufon_name}")
    print(f"Place ID: {lufon_place_id}")
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    print("="*60)
    
    # スクレイパー初期化
    scraper = GoogleMapsScraper()
    
    try:
        scraper.setup_driver()
        results = []
        success_count = 0
        
        for i, dest in enumerate(destinations, 1):
            print(f"\n[{i}/9] {dest['name']}への経路探索...")
            print(f"  Place ID: {dest['place_id']}")
            
            try:
                # Place IDを渡してルート検索
                result = scraper.scrape_route(
                    lufon_address,
                    dest['address'],
                    dest['name'],
                    arrival_time,
                    origin_place_id=lufon_place_id,
                    dest_place_id=dest['place_id'],
                    origin_lat=lufon_lat,
                    origin_lon=lufon_lon
                )
                
                if result['success']:
                    success_count += 1
                    print(f"  ✅ 成功")
                    print(f"    所要時間: {result['travel_time']}分")
                    print(f"    料金: {result.get('fare', 'N/A')}円")
                    print(f"    ルートタイプ: {result['route_type']}")
                    
                    # 時刻確認
                    if result.get('departure_time') and result.get('arrival_time'):
                        print(f"    時刻: {result['departure_time']} → {result['arrival_time']}")
                    else:
                        print(f"    ⚠️ 時刻情報なし")
                    
                    # 路線情報
                    if result.get('train_lines'):
                        print(f"    路線: {', '.join(result['train_lines'])}")
                else:
                    print(f"  ❌ 失敗: {result.get('error')}")
                
                results.append({
                    'destination': dest['name'],
                    'success': result['success'],
                    'travel_time': result.get('travel_time') if result['success'] else None,
                    'fare': result.get('fare') if result['success'] else None,
                    'has_time': bool(result.get('departure_time')) if result['success'] else False
                })
                
            except Exception as e:
                print(f"  ❌ エラー: {e}")
                results.append({
                    'destination': dest['name'],
                    'success': False,
                    'error': str(e)
                })
        
        # 結果サマリー
        print("\n" + "="*60)
        print("テスト結果サマリー")
        print("="*60)
        print(f"成功: {success_count}/9件")
        
        # 時刻抽出の成功率
        time_success = sum(1 for r in results if r.get('has_time'))
        print(f"時刻抽出成功: {time_success}/9件")
        
        # 平均所要時間
        travel_times = [r['travel_time'] for r in results if r.get('travel_time')]
        if travel_times:
            avg_time = sum(travel_times) / len(travel_times)
            print(f"平均所要時間: {avg_time:.1f}分")
        
        # 結果をJSON保存
        output = {
            'test_timestamp': datetime.now().isoformat(),
            'property': {
                'name': lufon_name,
                'address': lufon_address,
                'place_id': lufon_place_id
            },
            'arrival_time': arrival_time.isoformat(),
            'results': results,
            'summary': {
                'success_count': success_count,
                'time_extraction_count': time_success,
                'average_travel_time': avg_time if travel_times else None
            }
        }
        
        with open('/app/output/japandatascience.com/timeline-mapping/api/test_lufon_routes_results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("\n結果を test_lufon_routes_results.json に保存しました")
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
        print("\nテスト完了")

if __name__ == "__main__":
    test_routes_with_place_ids()