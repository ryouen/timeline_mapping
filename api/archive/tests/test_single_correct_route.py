#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONローダーを使用した単一ルートテスト
最初の物件から最初の目的地のみ
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5_optimized import GoogleMapsScraperV5Optimized
from json_data_loader import JsonDataLoader
from datetime import datetime, timedelta
import pytz

def test_single_route():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🔒 単一ルートテスト（正しいデータ使用）")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # JSONローダーを初期化
    loader = JsonDataLoader()
    
    # 最初の物件と最初の目的地を取得
    first_property = loader.get_property_by_index(0)
    first_destination = loader.get_all_destinations()[0]
    
    print(f"\n物件: {first_property['name']}")
    print(f"  住所: {first_property['address']}")
    
    print(f"\n目的地: {first_destination['name']}")
    print(f"  住所: {first_destination['address']}")
    
    scraper = GoogleMapsScraperV5Optimized()
    
    try:
        print("\n初期化中...")
        scraper.setup_driver()
        
        print("ルート検索開始...")
        result = scraper.scrape_route(
            first_property['address'],  # JSONから読み込んだまま使用
            first_destination['address'],  # JSONから読み込んだまま使用
            first_destination['name'],
            arrival_time
        )
        
        if result.get('success'):
            print(f"\n✅ 成功")
            print(f"  所要時間: {result['travel_time']}分")
            print(f"  ルートタイプ: {result['route_type']}")
            if result.get('train_lines'):
                print(f"  路線: {', '.join(result['train_lines'])}")
            if result.get('fare'):
                print(f"  料金: ¥{result['fare']}")
            
            # 詳細なルート情報
            departure_time = arrival_time - timedelta(minutes=result['travel_time'])
            print(f"\n【ルート詳細】")
            print(f"  {departure_time.strftime('%H:%M')} 出発: {first_property['name']}")
            if result.get('train_lines'):
                print(f"  ↓ 徒歩")
                print(f"  ↓ {' → '.join(result['train_lines'])}")
                print(f"  ↓ 徒歩")
            else:
                print(f"  ↓ {result['route_type']}")
            print(f"  {arrival_time.strftime('%H:%M')} 到着: {first_destination['name']}")
            
        else:
            print(f"\n❌ 失敗: {result.get('error')}")
            
    finally:
        scraper.close()
        print("\n✅ 終了")

if __name__ == "__main__":
    test_single_route()