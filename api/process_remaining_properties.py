#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
未処理3物件のルート情報を取得するスクリプト
"""

import json
import sys
import os
import time
from datetime import datetime, timedelta
import pytz

# google_maps_scraper_v4_complete.pyをインポート
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api/')
from google_maps_scraper_v4_complete import GoogleMapsScraperV4

def process_remaining_properties():
    """未処理3物件を処理"""
    
    # 未処理物件のデータ
    unprocessed_properties = [
        {
            "name": "La Belle 三越前 0702",
            "address": "東京都中央区日本橋本町1丁目",
            "rent": "230,000円"
        },
        {
            "name": "リベルテ月島 604",
            "address": "東京都中央区佃2丁目 12-1",
            "rent": "195,000円"
        },
        {
            "name": "パトリス 神保町 1101号室",
            "address": "東京都千代田区神田神保町二丁目4番64号 パトリス神保町",
            "rent": "330,000円"
        }
    ]
    
    # 目的地データ
    destinations = [
        {"id": "shizenkan_university", "name": "Shizenkan University", "address": "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階"},
        {"id": "tokyo_american_club", "name": "東京アメリカンクラブ", "address": "東京都中央区日本橋室町３丁目２−１"},
        {"id": "axle_ochanomizu", "name": "axle御茶ノ水", "address": "東京都千代田区神田小川町３丁目２８−５"},
        {"id": "yawara", "name": "Yawara", "address": "東京都渋谷区神宮前１丁目８−１０ Ｔｈｅ Ｉｃｅ Ｃｕｂｅｓ 9階"},
        {"id": "kamiyacho_ee", "name": "神谷町(EE)", "address": "東京都港区虎ノ門４丁目２−６ 第二扇屋ビル 1F"},
        {"id": "waseda_university", "name": "早稲田大学", "address": "東京都新宿区西早稲田１丁目６ 11号館"},
        {"id": "tokyo_station", "name": "東京駅", "address": "東京都千代田区丸の内１丁目"},
        {"id": "haneda_airport", "name": "羽田空港", "address": "東京都大田区羽田空港3-3-2"},
        {"id": "fuchu_office", "name": "府中オフィス", "address": "東京都府中市住吉町５丁目２２−５"}
    ]
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("未処理3物件のルート検索開始")
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    print("="*60)
    
    # スクレイパー初期化
    scraper = GoogleMapsScraperV4()
    results = []
    
    try:
        scraper.setup_driver()
        
        for prop_idx, property_data in enumerate(unprocessed_properties, 1):
            print(f"\n[{prop_idx}/3] {property_data['name']}")
            print(f"住所: {property_data['address']}")
            
            property_routes = []
            
            for dest_idx, dest in enumerate(destinations, 1):
                print(f"  [{dest_idx}/9] {dest['name']}... ", end="", flush=True)
                
                result = scraper.scrape_route(
                    origin_address=property_data['address'],
                    dest_address=dest['address'],
                    dest_name=dest['name'],
                    arrival_time=arrival_time
                )
                
                if result['success']:
                    route_data = {
                        "destination": dest['id'],
                        "destination_name": dest['name'],
                        "total_time": result['travel_time'],
                        "details": {
                            "departure_time": result.get('departure_time'),
                            "arrival_time": result.get('arrival_time'),
                            "fare": result.get('fare'),
                            "route_type": result['route_type']
                        },
                        "total_walk_time": 0  # デフォルト値
                    }
                    property_routes.append(route_data)
                    print(f"✅ {result['travel_time']}分")
                else:
                    print(f"❌ 失敗")
                    # エラーでも空のデータを追加
                    property_routes.append({
                        "destination": dest['id'],
                        "destination_name": dest['name'],
                        "total_time": 999,
                        "error": result.get('error', 'Unknown error')
                    })
                
                time.sleep(3)  # レート制限対策
            
            # 物件データとして保存
            results.append({
                "name": property_data['name'],
                "address": property_data['address'],
                "rent": property_data['rent'],
                "routes": property_routes
            })
            
            print(f"✅ {property_data['name']} 完了")
    
    finally:
        scraper.close()
    
    # 結果を保存
    output_file = '/app/output/japandatascience.com/timeline-mapping/data/remaining_properties.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("処理完了！")
    print(f"結果ファイル: {output_file}")
    print("="*60)
    
    return results

if __name__ == "__main__":
    process_remaining_properties()