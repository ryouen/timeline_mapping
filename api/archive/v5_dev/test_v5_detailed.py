#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5スクレイパーで実際のルートを詳細に取得して表示
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5_final import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz
import json

def test_routes_detailed():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🚇 Google Maps v5 ルート詳細取得テスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # テストする主要ルート
    test_routes = [
        {
            'name': 'Shizenkan University',
            'destination': '東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階'
        },
        {
            'name': '東京アメリカンクラブ',
            'destination': '東京都中央区日本橋室町３丁目２−１'
        },
        {
            'name': 'axle御茶ノ水',
            'destination': '東京都千代田区神田小川町３丁目２８−５'
        },
        {
            'name': '早稲田大学',
            'destination': '東京都新宿区西早稲田１丁目６ 11号館'
        },
        {
            'name': '府中オフィス',
            'destination': '東京都府中市住吉町５丁目２２−５'
        }
    ]
    
    # 出発地（ルフォンプログレ神田プレミア）
    origin = '東京都千代田区神田須田町1-20-1'
    
    scraper = GoogleMapsScraperV5()
    
    try:
        scraper.setup_driver()
        
        results = []
        
        for i, route in enumerate(test_routes, 1):
            print(f"\n{'='*80}")
            print(f"📍 ルート {i}: {route['name']}")
            print(f"   出発: {origin}")
            print(f"   到着: {route['destination']}")
            print("-"*80)
            
            result = scraper.scrape_route(
                origin,
                route['destination'],
                route['name'],
                arrival_time
            )
            
            if result.get('success'):
                print(f"✅ 取得成功")
                print(f"\n【基本情報】")
                print(f"  総所要時間: {result['travel_time']}分")
                print(f"  ルートタイプ: {result['route_type']}")
                print(f"  料金: ¥{result.get('fare', 'N/A')}")
                print(f"  出発時刻: {result.get('departure_time', 'N/A')}")
                print(f"  到着時刻: {result.get('arrival_time', 'N/A')}")
                
                print(f"\n【Place ID】")
                print(f"  出発地: {result['place_ids']['origin']}")
                print(f"  目的地: {result['place_ids']['destination']}")
                
                # 全ルート候補を表示
                if result.get('all_routes'):
                    print(f"\n【ルート候補】")
                    for j, alt_route in enumerate(result['all_routes'], 1):
                        print(f"  候補{j}: {alt_route['travel_time']}分 ({alt_route['route_type']}) ")
                        if alt_route.get('fare'):
                            print(f"        料金: ¥{alt_route['fare']}")
                        if alt_route.get('departure_time'):
                            print(f"        {alt_route['departure_time']} → {alt_route.get('arrival_time', 'N/A')}")
                        print(f"        詳細: {alt_route['summary'][:50]}...")
                
                results.append({
                    'name': route['name'],
                    'success': True,
                    'data': result
                })
            else:
                print(f"❌ 取得失敗: {result.get('error')}")
                results.append({
                    'name': route['name'],
                    'success': False,
                    'error': result.get('error')
                })
                
        # サマリー表示
        print(f"\n{'='*80}")
        print("📊 取得結果サマリー")
        print("="*80)
        
        success_count = sum(1 for r in results if r['success'])
        print(f"成功: {success_count}/{len(results)}")
        
        print("\n【所要時間一覧】")
        for r in results:
            if r['success']:
                print(f"  {r['name']:20}: {r['data']['travel_time']:3}分 ({r['data']['route_type']})")
        
        # 結果をJSONに保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/v5_test_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 詳細結果を保存: {output_file}")
        
    finally:
        scraper.close()

if __name__ == "__main__":
    test_routes_detailed()