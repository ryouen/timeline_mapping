#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合版google_maps_scraper.pyのテスト
1物件（神田）から最初の3目的地へのルート取得
"""

import sys
import os
import time
from datetime import datetime, timedelta
import pytz

# パスを追加
sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from json_data_loader import JsonDataLoader

def test_single_property():
    """1物件から3目的地へのルート取得テスト"""
    
    # データ読み込み
    data_loader = JsonDataLoader()
    properties = data_loader.get_all_properties()
    destinations = data_loader.get_all_destinations()
    
    if not properties or not destinations:
        print("❌ データの読み込みに失敗")
        return
    
    # 最初の物件と最初の3目的地を使用
    test_property = properties[0]
    test_destinations = destinations[:3]
    
    # 到着時刻設定（明日10:00）
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print(f"📍 テスト物件: {test_property['name']}")
    print(f"   住所: {test_property['address']}")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 60)
    
    scraper = GoogleMapsScraper()
    success_count = 0
    fail_count = 0
    
    try:
        scraper.setup_driver()
        
        for i, dest in enumerate(test_destinations, 1):
            print(f"\n[{i}/3] {dest['name']}へのルート検索...")
            start_time = time.time()
            
            result = scraper.scrape_route(
                test_property['address'],
                dest['address'],
                dest['name'],
                arrival_time
            )
            
            elapsed = time.time() - start_time
            
            if result['success']:
                success_count += 1
                print(f"✅ 成功: {result['travel_time']}分 ({result['route_type']}) - {elapsed:.1f}秒")
                if result.get('train_lines'):
                    print(f"   路線: {', '.join(result['train_lines'])}")
                if result.get('fare'):
                    print(f"   運賃: ¥{result['fare']}")
            else:
                fail_count += 1
                print(f"❌ 失敗: {result['error']} - {elapsed:.1f}秒")
    
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    finally:
        scraper.close()
        print("\n" + "=" * 60)
        print(f"📊 結果: 成功 {success_count}/3, 失敗 {fail_count}/3")
        
        if success_count == 3:
            print("🎉 統合版のテストが完全に成功しました！")
            return True
        elif success_count > 0:
            print("⚠️ 部分的に成功しました")
            return False
        else:
            print("❌ テストが失敗しました")
            return False

if __name__ == "__main__":
    success = test_single_property()
    sys.exit(0 if success else 1)