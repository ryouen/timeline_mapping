#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全Place IDを使用してルート検索を実行し、properties.jsonを作成
"""

import json
import sys
import time
from datetime import datetime, timedelta
import pytz

sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

def load_place_ids():
    """Place IDファイルを読み込み"""
    try:
        with open('/app/output/japandatascience.com/timeline-mapping/data/all_place_ids.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ all_place_ids.jsonが見つかりません。batch_place_id_collection.pyを先に実行してください。")
        sys.exit(1)

def load_base_data():
    """基本データを読み込み"""
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties_base.json', 'r', encoding='utf-8') as f:
        properties_data = json.load(f)
    
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        destinations_data = json.load(f)
    
    return properties_data['properties'], destinations_data['destinations']

def search_all_routes():
    """全組み合わせのルート検索"""
    place_ids = load_place_ids()
    properties, destinations = load_base_data()
    
    # 到着時刻（平日朝10時）
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    # 平日になるまで日付を進める
    while tomorrow.weekday() >= 5:  # 5=土曜, 6=日曜
        tomorrow += timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST (平日)")
    
    scraper = GoogleMapsScraper()
    results = {
        'properties': [],
        'generated_at': datetime.now().isoformat(),
        'arrival_time': arrival_time.isoformat()
    }
    
    try:
        # 各物件について処理
        for prop_idx, prop in enumerate(properties, 1):
            prop_name = prop['name']
            
            # Place IDが取得できていない場合はスキップ
            if prop_name not in place_ids['properties']:
                print(f"⚠️ {prop_name}のPlace IDが見つかりません。スキップします。")
                continue
            
            prop_place_info = place_ids['properties'][prop_name]
            
            property_result = {
                'name': prop_name,
                'address': prop['address'],
                'rent': prop.get('rent', ''),
                'place_id': prop_place_info['place_id'],
                'routes': []
            }
            
            print(f"\n{'=' * 60}")
            print(f"[{prop_idx}/{len(properties)}] {prop_name}")
            print(f"{'=' * 60}")
            
            # 各目的地へのルート検索
            for dest_idx, dest in enumerate(destinations, 1):  # 全目的地を処理
                dest_id = dest['id']
                
                # Place IDが取得できていない場合はスキップ
                if dest_id not in place_ids['destinations']:
                    print(f"  ⚠️ {dest['name']}のPlace IDが見つかりません。スキップします。")
                    continue
                
                dest_place_info = place_ids['destinations'][dest_id]
                
                print(f"\n  [{dest_idx}/{len(destinations)}] → {dest['name']}")
                
                try:
                    # ルート検索
                    route_result = scraper.scrape_route(
                        origin_address=prop['address'],
                        dest_address=dest['address'],
                        dest_name=dest['name'],
                        arrival_time=arrival_time,
                        origin_place_id=prop_place_info['place_id'],
                        dest_place_id=dest_place_info['place_id'],
                        origin_lat=prop_place_info.get('lat'),
                        origin_lon=prop_place_info.get('lon'),
                        dest_lat=dest_place_info.get('lat'),
                        dest_lon=dest_place_info.get('lon')
                    )
                    
                    if route_result['success']:
                        route_data = {
                            'destination': dest_id,
                            'destination_name': dest['name'],
                            'total_time': route_result.get('travel_time'),
                            'details': {
                                'wait_time_minutes': route_result.get('wait_time_minutes', 0),
                                'walk_to_station': route_result.get('walk_to_station'),
                                'station_used': route_result.get('station_used'),
                                'trains': route_result.get('trains', []),
                                'walk_from_station': route_result.get('walk_from_station')
                            },
                            'total_walk_time': (route_result.get('walk_to_station', 0) or 0) + 
                                             (route_result.get('walk_from_station', 0) or 0),
                            'fare': route_result.get('fare'),
                            'departure_time': route_result.get('departure_time'),
                            'arrival_time': route_result.get('arrival_time')
                        }
                        property_result['routes'].append(route_data)
                        
                        print(f"    ✅ 成功: {route_result.get('travel_time')}分, {route_result.get('fare')}円")
                    else:
                        print(f"    ❌ 失敗: {route_result.get('error')}")
                    
                    # レート制限対策
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"    ❌ エラー: {e}")
                    continue
            
            results['properties'].append(property_result)
            
            # 進捗を保存
            with open('/app/output/japandatascience.com/timeline-mapping/data/properties_test.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n  ✅ {prop_name}の処理完了: {len(property_result['routes'])}ルート")
        
        print("\n" + "=" * 60)
        print("✅ 全ルート検索完了")
        print(f"  処理物件数: {len(results['properties'])}")
        print(f"  総ルート数: {sum(len(p['routes']) for p in results['properties'])}")
        print("=" * 60)
        
        return results
        
    finally:
        scraper.close()

if __name__ == "__main__":
    search_all_routes()