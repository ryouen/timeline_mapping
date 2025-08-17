#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
単一ルートテスト: ルフォンプログレ → 府中オフィス
"""

import sys
import json
from datetime import datetime, timedelta
import pytz

sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

def test_single_route():
    """単一ルートのテスト"""
    
    # 到着時刻（平日朝10時）
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    while tomorrow.weekday() >= 5:
        tomorrow += timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    
    # テストデータ
    origin = {
        'name': 'ルフォンプログレ神田プレミア',
        'address': '東京都千代田区神田須田町1-20-1',
        'place_id': 'ChIJ2RxO9gKMGGARSvjnp3ocfJg'
    }
    
    dest = {
        'name': '府中オフィス',
        'address': '東京都府中市住吉町５丁目２２−５',
        'place_id': 'ChIJR3AMl5nkGGARCqvDOHEMads'
    }
    
    print(f"\n出発地: {origin['name']}")
    print(f"目的地: {dest['name']}")
    
    scraper = GoogleMapsScraper()
    
    try:
        print("\n検索開始...")
        result = scraper.scrape_route(
            origin_address=origin['address'],
            dest_address=dest['address'],
            dest_name=dest['name'],
            arrival_time=arrival_time,
            origin_place_id=origin['place_id'],
            dest_place_id=dest['place_id']
        )
        
        if result['success']:
            print("\n✅ ルート取得成功!")
            print(f"  所要時間: {result.get('travel_time')}分")
            print(f"  料金: {result.get('fare')}円")
            print(f"  出発時刻: {result.get('departure_time')}")
            print(f"  到着時刻: {result.get('arrival_time')}")
            print(f"  駅まで: {result.get('walk_to_station')}分")
            print(f"  駅から: {result.get('walk_from_station')}分")
            print(f"  使用駅: {result.get('station_used')}")
            print(f"  電車: {len(result.get('trains', []))}本")
            
            # 結果を保存
            with open('/app/output/japandatascience.com/timeline-mapping/data/single_route_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print("\n結果を single_route_result.json に保存しました")
        else:
            print(f"\n❌ ルート取得失敗: {result.get('error')}")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    test_single_route()