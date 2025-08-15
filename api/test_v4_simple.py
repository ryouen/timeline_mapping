#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4スクレイパーの簡単なテスト
Seleniumの問題を回避してv3で明日の日付でテスト
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta, timezone
import json

def main():
    # 明日の10時到着（JST）- 2025年8月16日
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00
    
    print("=" * 60)
    print("明日の日付でテスト（v3使用）")
    print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
    print(f"タイムスタンプ: {int(arrival_10am.timestamp())}")
    print("=" * 60)
    
    # 問題があったルートをテスト
    test_cases = [
        {
            "name": "Yawara（詳細取得改善テスト）",
            "origin": "東京都千代田区神田須田町1-20-1",
            "destination": "東京都渋谷区神宮前１丁目８−１０"
        },
        {
            "name": "府中（長距離ルート）",
            "origin": "東京都千代田区神田須田町1-20-1",
            "destination": "東京都府中市住吉町5-22-5"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n[{test['name']}]")
        print(f"出発: {test['origin']}")
        print(f"到着: {test['destination']}")
        
        result = scrape_route(
            test['origin'],
            test['destination'],
            arrival_time=arrival_10am,
            save_debug=False
        )
        
        if result:
            print(f"✅ 成功")
            print(f"  所要時間: {result['travel_time']}分")
            print(f"  ルート数: {len(result.get('all_routes', []))}件")
            
            # 最短ルートの詳細
            if result.get('all_routes'):
                shortest = min(result['all_routes'], key=lambda r: r['total_time'])
                print(f"  最短ルート: {shortest['total_time']}分")
                
                # 路線情報があるか確認
                if shortest.get('trains'):
                    print(f"  路線情報: {', '.join(shortest['trains'][:3])}")
                else:
                    # raw_textから詳細を抽出
                    raw_text = shortest.get('raw_text', '')
                    if '徒歩' in raw_text and '駅' not in raw_text:
                        print(f"  詳細: 徒歩のみ")
                    elif raw_text:
                        # テキストから路線名や駅名を抽出
                        lines = raw_text.split('\n')
                        route_lines = []
                        for line in lines:
                            if any(keyword in line for keyword in ['線', '駅', 'バス', '電車']):
                                route_lines.append(line.strip())
                        if route_lines:
                            print(f"  抽出した詳細: {', '.join(route_lines[:3])}")
                        else:
                            print(f"  詳細: 詳細なし（raw_text長: {len(raw_text)}文字）")
                    else:
                        print(f"  詳細: 情報なし")
            
            results.append({
                'name': test['name'],
                'success': True,
                'travel_time': result['travel_time'],
                'url': result.get('url')
            })
        else:
            print(f"❌ 失敗")
            results.append({
                'name': test['name'],
                'success': False
            })
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("結果サマリー")
    print("=" * 60)
    success_count = sum(1 for r in results if r['success'])
    print(f"成功: {success_count}/{len(results)}")
    
    for r in results:
        if r['success']:
            print(f"  ✅ {r['name']}: {r['travel_time']}分")
        else:
            print(f"  ❌ {r['name']}: 失敗")

if __name__ == "__main__":
    main()