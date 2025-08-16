#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ルフォンプログレから3目的地へのルート検索テスト（簡易版）
"""

import sys
import json
import logging
from datetime import datetime, timedelta
import pytz

sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_3_routes():
    """3つの目的地のみテスト"""
    
    # ルフォンプログレ
    lufon = {
        "address": "東京都千代田区神田須田町1-20-1",
        "place_id": "ChIJ2RxO9gKMGGARSvjnp3ocfJg"
    }
    
    # 3目的地のみ
    destinations = [
        {
            "name": "Shizenkan University",
            "address": "東京都中央区日本橋2-5-1",
            "place_id": "ChIJy_fF8PKJGGARr8tJ4FAd9gg"
        },
        {
            "name": "東京駅",
            "address": "東京都千代田区丸の内1丁目",
            "place_id": "ChIJLdASefmLGGARF3Ez6A4i4Q4"
        },
        {
            "name": "早稲田大学",
            "address": "東京都新宿区西早稲田1-6-11",
            "place_id": "ChIJ6a8IHyaNGGARKQZV2dkEKsU"
        }
    ]
    
    # 明日10時
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("簡易テスト: ルフォンプログレから3目的地")
    print("="*60)
    
    scraper = GoogleMapsScraper()
    
    try:
        scraper.setup_driver()
        
        for i, dest in enumerate(destinations, 1):
            print(f"\n[{i}/3] {dest['name']}")
            
            result = scraper.scrape_route(
                lufon['address'],
                dest['address'],
                dest['name'],
                arrival_time,
                origin_place_id=lufon['place_id'],
                dest_place_id=dest['place_id']
            )
            
            if result['success']:
                print(f"  ✅ 成功")
                print(f"  所要時間: {result['travel_time']}分")
                print(f"  料金: {result.get('fare', 'N/A')}円")
                
                # 時刻確認
                if result.get('departure_time'):
                    print(f"  時刻: {result['departure_time']} → {result['arrival_time']}")
                else:
                    print(f"  ⚠️ 時刻抽出失敗")
                
                # Place ID確認
                if result.get('place_ids'):
                    origin_id = result['place_ids'].get('origin', '')[:20]
                    dest_id = result['place_ids'].get('destination', '')[:20]
                    print(f"  Place ID使用: {origin_id}... → {dest_id}...")
            else:
                print(f"  ❌ 失敗: {result.get('error')}")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()

if __name__ == "__main__":
    test_3_routes()