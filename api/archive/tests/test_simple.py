#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小限のテスト - 1ルートのみ
"""
import sys
import time
from datetime import datetime, timedelta
import pytz

sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

def test_single_route():
    """1ルートのみテスト"""
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    scraper = GoogleMapsScraper()
    try:
        print("🔧 WebDriver初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了")
        
        print("\n📍 テスト: 神田 → Shizenkan University")
        print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')}")
        
        start = time.time()
        result = scraper.scrape_route(
            "東京都千代田区神田須田町1-20-1",
            "東京都中央区日本橋2-5-1髙島屋三井ビルディング17階",
            "Shizenkan University",
            arrival_time
        )
        elapsed = time.time() - start
        
        if result['success']:
            print(f"✅ 成功: {result['travel_time']}分 - {elapsed:.1f}秒")
            print(f"   ルート: {result['route_type']}")
            if result.get('train_lines'):
                print(f"   路線: {', '.join(result['train_lines'])}")
        else:
            print(f"❌ 失敗: {result['error']} - {elapsed:.1f}秒")
            
        return result['success']
        
    finally:
        scraper.close()
        print("\n🔧 クリーンアップ完了")

if __name__ == "__main__":
    success = test_single_route()
    sys.exit(0 if success else 1)