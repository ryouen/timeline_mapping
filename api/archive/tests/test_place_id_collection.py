#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID収集テスト - ルフォンプログレのみ
"""

import sys
import json
import time
import re
import logging
from urllib.parse import quote
from selenium import webdriver

# パスを追加
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from collect_place_ids import PlaceIdCollector

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_lufon():
    """ルフォンプログレのPlace ID取得テスト"""
    
    collector = PlaceIdCollector()
    
    try:
        collector.setup_driver()
        
        # ルフォンプログレの情報
        test_property = {
            "name": "ルフォンプログレ神田プレミア",
            "address": "東京都千代田区神田須田町1-20-1"
        }
        
        print("\n" + "="*60)
        print("Place ID収集テスト - ルフォンプログレ")
        print("="*60)
        
        # Place ID取得
        result = collector.extract_place_id(test_property['address'], test_property['name'])
        
        print(f"\n物件: {test_property['name']}")
        print(f"住所: {test_property['address']}")
        print(f"正規化住所: {result['normalized_address']}")
        print(f"\n結果:")
        print(f"  Place ID: {result['place_id']}")
        print(f"  形式: {result['place_id_format']}")
        print(f"  緯度: {result['lat']}")
        print(f"  経度: {result['lon']}")
        
        if result['place_id']:
            print(f"\n✅ Place ID取得成功！")
            
            # 9つの目的地も取得
            print("\n" + "="*60)
            print("9つの目的地のPlace ID取得")
            print("="*60)
            
            # destinations.json読み込み
            with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
                destinations_data = json.load(f)
            
            dest_results = []
            for i, dest in enumerate(destinations_data['destinations'], 1):
                print(f"\n[{i}/9] {dest['name']}")
                dest_result = collector.extract_place_id(dest['address'], dest['name'])
                
                status = "✓" if dest_result['place_id'] else "✗"
                print(f"  {status} Place ID: {dest_result['place_id']}")
                print(f"    形式: {dest_result['place_id_format']}")
                
                dest_results.append({
                    'name': dest['name'],
                    'place_id': dest_result['place_id'],
                    'format': dest_result['place_id_format']
                })
                
                # レート制限対策
                time.sleep(1)
            
            # 結果サマリー
            print("\n" + "="*60)
            print("結果サマリー")
            print("="*60)
            
            # ChIJ形式の数をカウント
            chij_count = sum(1 for r in dest_results if r['format'] == 'ChIJ')
            ox_count = sum(1 for r in dest_results if r['format'] == '0x')
            none_count = sum(1 for r in dest_results if not r['place_id'])
            
            print(f"ChIJ形式: {chij_count}件")
            print(f"0x形式: {ox_count}件")
            print(f"取得失敗: {none_count}件")
            
            # テスト結果をJSON保存
            test_result = {
                'property': {
                    'name': test_property['name'],
                    'address': test_property['address'],
                    'place_id': result['place_id'],
                    'format': result['place_id_format'],
                    'lat': result['lat'],
                    'lon': result['lon']
                },
                'destinations': dest_results,
                'summary': {
                    'chij_count': chij_count,
                    'ox_count': ox_count,
                    'failed_count': none_count
                }
            }
            
            with open('/app/output/japandatascience.com/timeline-mapping/api/test_place_id_results.json', 'w', encoding='utf-8') as f:
                json.dump(test_result, f, ensure_ascii=False, indent=2)
            
            print("\n結果を test_place_id_results.json に保存しました")
            
        else:
            print(f"\n❌ Place ID取得失敗")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()

if __name__ == "__main__":
    test_lufon()