#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版v5で3ルートをクイックテスト
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5 import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz
import json
import time

def test_quick_3routes():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🚇 修正版v5スクレイパー 3ルートテスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # テストルート
    test_routes = [
        {
            'name': 'Shizenkan（近距離）',
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都中央区日本橋2-5-1'
        },
        {
            'name': '早稲田大学（中距離）',
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都新宿区西早稲田1-6-11'
        },
        {
            'name': '府中（長距離）',
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都府中市住吉町5-22-5'
        }
    ]
    
    scraper = GoogleMapsScraperV5()
    
    try:
        print("\n📌 初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了\n")
        
        results = []
        
        for i, route in enumerate(test_routes, 1):
            print(f"[{i}/3] {route['name']}")
            
            start_time = time.time()
            
            result = scraper.scrape_route(
                route['origin'],
                route['destination'],
                route['name'],
                arrival_time
            )
            
            elapsed = time.time() - start_time
            
            if result.get('success'):
                print(f"  ✅ 成功 ({elapsed:.1f}秒)")
                print(f"    {result['travel_time']}分 ({result['route_type']})")
                if result.get('train_lines'):
                    print(f"    路線: {', '.join(result['train_lines'])}")
                print(f"    料金: ¥{result.get('fare', 'N/A')}")
                
                results.append({
                    'name': route['name'],
                    'success': True,
                    'time': result['travel_time'],
                    'type': result['route_type'],
                    'lines': result.get('train_lines', []),
                    'fare': result.get('fare'),
                    'elapsed_seconds': elapsed
                })
            else:
                print(f"  ❌ 失敗: {result.get('error')}")
                results.append({
                    'name': route['name'],
                    'success': False,
                    'error': result.get('error'),
                    'elapsed_seconds': elapsed
                })
            
            print()
        
        # サマリー
        print("="*80)
        print("📊 結果サマリー")
        print("="*80)
        
        total_time = sum(r['elapsed_seconds'] for r in results)
        success_count = sum(1 for r in results if r['success'])
        
        print(f"\n成功率: {success_count}/3")
        print(f"総処理時間: {total_time:.1f}秒 (平均: {total_time/3:.1f}秒/ルート)")
        
        print("\n【取得データ】")
        for r in results:
            if r['success']:
                print(f"  {r['name']:30}: {r['time']:3}分 ({r['type']})")
                if r['lines']:
                    print(f"  {'':30}  路線: {', '.join(r['lines'])}")
        
        # 保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/test_quick_3routes_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 保存: {output_file}")
        
        return results
        
    finally:
        scraper.close()
        print("✅ 終了")

if __name__ == "__main__":
    test_quick_3routes()