#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
早稲田大学ルートでクリック操作の効果をテスト
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5 import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz

def test_waseda_with_click():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🎓 早稲田大学ルート - クリック操作効果テスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    origin = '東京都千代田区神田須田町1-20-1'
    destination = '東京都新宿区西早稲田1-6-11'
    
    scraper = GoogleMapsScraperV5()
    
    try:
        print("\n📌 初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了\n")
        
        print("テスト: 早稲田大学（クリック操作あり）")
        print("-"*60)
        
        result = scraper.scrape_route(
            origin,
            destination,
            '早稲田大学',
            arrival_time
        )
        
        if result.get('success'):
            print(f"\n✅ 取得成功")
            print(f"  所要時間: {result['travel_time']}分")
            print(f"  ルートタイプ: {result['route_type']}")
            print(f"  料金: ¥{result.get('fare', 'N/A')}")
            print(f"  時刻: {result.get('departure_time', 'N/A')} → {result.get('arrival_time', 'N/A')}")
            
            if result.get('train_lines'):
                print(f"  路線: {', '.join(result['train_lines'])}")
            
            print(f"\n  全ルート候補:")
            for i, route in enumerate(result.get('all_routes', []), 1):
                print(f"    {i}. {route['travel_time']}分 ({route['route_type']})")
                if route.get('train_lines'):
                    print(f"       路線: {', '.join(route['train_lines'])}")
                if route.get('fare'):
                    print(f"       料金: ¥{route['fare']}")
                print(f"       詳細: {route.get('summary', '')[:80]}...")
            
            # 正しい公共交通機関ルートが取得できているか確認
            correct_route = False
            for route in result.get('all_routes', []):
                if '東西線' in str(route.get('train_lines', [])) or '銀座線' in str(route.get('train_lines', [])):
                    correct_route = True
                    print(f"\n  ✅ 正しい電車ルートを検出: {route['travel_time']}分")
                    break
            
            if not correct_route:
                print(f"\n  ⚠️ 電車ルートが検出できていません")
                
        else:
            print(f"\n❌ 取得失敗: {result.get('error')}")
            
    finally:
        scraper.close()
        print("\n✅ 終了")

if __name__ == "__main__":
    test_waseda_with_click()