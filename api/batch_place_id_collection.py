#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
properties_base.jsonとdestinations.jsonから全Place IDを一括取得
"""

import json
import sys
import time
from datetime import datetime
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

def load_json_files():
    """JSONファイルを読み込み"""
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties_base.json', 'r', encoding='utf-8') as f:
        properties_data = json.load(f)
    
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        destinations_data = json.load(f)
    
    return properties_data['properties'], destinations_data['destinations']

def collect_all_place_ids():
    """全物件と全目的地のPlace IDを収集"""
    properties, destinations = load_json_files()
    
    # 既知のPlace IDを事前定義
    known_place_ids = {
        'destinations': {
            'shizenkan_university': 'ChIJGWlcqP6LGGARddFD1M78MhU',
            'tokyo_station': 'ChIJ-S9lbaOLGGAR0DW0TS3vFZY',
            'waseda_university': 'ChIJm-AJt2CMGGARWGdPPySdXEE',
            'fuchu_office': 'ChIJR3AMl5nkGGARCqvDOHEMads',
            'axle_ochanomizu': 'ChIJLfSUhXSMGGARUy6iU79r3_I',
            'yawara': 'ChIJ3WLQGb2MGGARHj2TsjYz3Ao',
            'tokyo_american_club': 'ChIJW9Ziq42LGGARUCLpfDPgR7Y',
            'roppongi_itchome': 'ChIJ1byqJ5WLGGAR9s0K3sJYats',
            'narita_airport': 'ChIJvYiCaYbyImAR37wW7J_Tcds',
            'haneda_airport': 'ChIJgz93XJ6LGGAR48l5YKtFWzk',
            'andaz_tokyo': 'ChIJ25zuXJKLGGARLWCdqPGlcxg'
        },
        'properties': {
            'ルフォンプログレ神田プレミア': 'ChIJ2RxO9gKMGGARSvjnp3ocfJg'
        }
    }
    
    scraper = GoogleMapsScraper()
    place_ids = {
        'properties': {},
        'destinations': {},
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # 物件のPlace IDを取得
        print("=" * 60)
        print("物件のPlace ID取得")
        print("=" * 60)
        
        for i, prop in enumerate(properties, 1):  # 全物件を処理
            print(f"\n[{i}/{len(properties)}] {prop['name']}")
            print(f"  住所: {prop['address']}")
            
            # 既知のPlace IDがある場合は使用
            if prop['name'] in known_place_ids.get('properties', {}):
                place_id = known_place_ids['properties'][prop['name']]
                place_ids['properties'][prop['name']] = {
                    'address': prop['address'],
                    'place_id': place_id,
                    'lat': None,
                    'lon': None
                }
                print(f"  ✅ Place ID (既知): {place_id}")
            else:
                result = scraper.get_place_id(prop['address'], prop['name'])
                
                if result and result.get('place_id'):
                    place_ids['properties'][prop['name']] = {
                        'address': prop['address'],
                        'place_id': result['place_id'],
                        'lat': result.get('lat'),
                        'lon': result.get('lon')
                    }
                    print(f"  ✅ Place ID: {result['place_id']}")
                else:
                    print(f"  ❌ Place ID取得失敗")
            
            time.sleep(2)  # レート制限対策
        
        # 目的地のPlace IDを取得
        print("\n" + "=" * 60)
        print("目的地のPlace ID取得")
        print("=" * 60)
        
        for i, dest in enumerate(destinations, 1):
            print(f"\n[{i}/{len(destinations)}] {dest['name']}")
            print(f"  住所: {dest['address']}")
            
            # 既知のPlace IDがある場合は使用
            if dest['id'] in known_place_ids.get('destinations', {}):
                place_id = known_place_ids['destinations'][dest['id']]
                place_ids['destinations'][dest['id']] = {
                    'name': dest['name'],
                    'address': dest['address'],
                    'place_id': place_id,
                    'lat': None,
                    'lon': None
                }
                print(f"  ✅ Place ID (既知): {place_id}")
            else:
                # 駅や空港は名前で検索
                if any(keyword in dest['name'] for keyword in ['駅', '空港', 'Station', 'Airport']):
                    result = scraper.get_place_id(dest['address'], dest['name'])
                else:
                    result = scraper.get_place_id(dest['address'])
                
                if result and result.get('place_id'):
                    place_ids['destinations'][dest['id']] = {
                        'name': dest['name'],
                        'address': dest['address'],
                        'place_id': result['place_id'],
                        'lat': result.get('lat'),
                        'lon': result.get('lon')
                    }
                    print(f"  ✅ Place ID: {result['place_id']}")
                else:
                    print(f"  ❌ Place ID取得失敗")
            
            time.sleep(2)  # レート制限対策
        
        # 結果を保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/all_place_ids.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(place_ids, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print(f"✅ Place ID収集完了")
        print(f"  物件: {len(place_ids['properties'])}件")
        print(f"  目的地: {len(place_ids['destinations'])}件")
        print(f"  保存先: {output_file}")
        print("=" * 60)
        
        return place_ids
        
    finally:
        scraper.close()

if __name__ == "__main__":
    collect_all_place_ids()