#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5統合版の簡単なテスト
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5_unified import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz

def simple_test():
    print("="*60)
    print("v5スクレイパー簡単テスト")
    print("="*60)
    
    # テストケース（1件のみ）
    origin = "東京都千代田区神田須田町1-20-1"
    destination = "東京都中央区日本橋2-5-1"
    
    # 明日10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print(f"出発: {origin}")
    print(f"到着: {destination}")
    print(f"時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    print("-"*60)
    
    scraper = GoogleMapsScraperV5()
    
    try:
        print("1. WebDriver初期化中...")
        scraper.setup_driver()
        print("   ✅ 初期化成功")
        
        print("2. ルート検索中...")
        result = scraper.scrape_route(
            origin,
            destination,
            "Shizenkan University",
            arrival_time
        )
        
        if result.get('success'):
            print("   ✅ ルート取得成功")
            print(f"   所要時間: {result['travel_time']}分")
            print(f"   ルートタイプ: {result['route_type']}")
            print(f"   料金: {result.get('fare', 'N/A')}円")
        else:
            print(f"   ❌ ルート取得失敗: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("3. クリーンアップ中...")
        scraper.close()
        print("   ✅ 完了")

if __name__ == "__main__":
    simple_test()