#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最初の物件（ルフォンプログレ神田プレミア）× 9目的地のテスト
v5スクレイパーでURLパラメータとクリック操作の両方を使用
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5 import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz
import json
import time

def test_first_property_9_routes():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🏢 最初の物件テスト: ルフォンプログレ神田プレミア × 9目的地")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # 最初の物件
    property_name = 'ルフォンプログレ神田プレミア'
    origin = '東京都千代田区神田須田町１丁目２０−１'
    
    # 9つの目的地
    destinations = [
        {
            'name': 'Shizenkan University',
            'address': '東京都中央区日本橋２丁目５−１',
            'type': '近距離'
        },
        {
            'name': 'パラレルマーケターズ',
            'address': '東京都中野区中野３丁目４９−１',
            'type': '中距離'
        },
        {
            'name': 'ネクセンス',
            'address': '東京都千代田区麹町３丁目５−２',
            'type': '近距離'
        },
        {
            'name': 'メディファーマ',
            'address': '東京都千代田区紀尾井町３−１２',
            'type': '近距離'
        },
        {
            'name': 'アクスル',
            'address': '東京都千代田区麹町１丁目１２番１２号',
            'type': '近距離'
        },
        {
            'name': '早稲田大学',
            'address': '東京都新宿区西早稲田１丁目６ 11号館',
            'type': '中距離・要クリック'
        },
        {
            'name': '羽田空港国際線',
            'address': '東京都大田区羽田空港２丁目６−５',
            'type': '長距離'
        },
        {
            'name': '駒澤大学',
            'address': '東京都世田谷区駒沢１丁目２３−１',
            'type': '中距離'
        },
        {
            'name': '府中オフィス',
            'address': '東京都府中市住吉町５丁目２２−５',
            'type': '長距離'
        }
    ]
    
    scraper = GoogleMapsScraperV5()
    
    try:
        print("\n📌 WebDriver初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了\n")
        
        results = []
        start_total = time.time()
        
        for i, dest in enumerate(destinations, 1):
            print(f"[{i}/9] {dest['name']} ({dest['type']})")
            print(f"  出発: {origin}")
            print(f"  到着: {dest['address'][:50]}...")
            
            start_route = time.time()
            
            result = scraper.scrape_route(
                origin,
                dest['address'],
                dest['name'],
                arrival_time
            )
            
            elapsed = time.time() - start_route
            
            if result.get('success'):
                print(f"  ✅ 成功 ({elapsed:.1f}秒)")
                print(f"    {result['travel_time']}分 ({result['route_type']})")
                
                # 路線情報
                if result.get('train_lines'):
                    print(f"    路線: {', '.join(result['train_lines'])}")
                
                # 料金
                if result.get('fare'):
                    print(f"    料金: ¥{result['fare']}")
                
                # 時刻
                if result.get('departure_time') and result.get('arrival_time'):
                    print(f"    時刻: {result['departure_time']} → {result['arrival_time']}")
                
                # キャッシュ状態
                if result.get('from_cache'):
                    print(f"    ⚡ キャッシュから取得")
                
                # 早稲田の場合は詳細確認
                if dest['name'] == '早稲田大学':
                    print(f"\n    【早稲田大学ルート詳細】")
                    for j, route in enumerate(result.get('all_routes', [])[:3], 1):
                        print(f"    候補{j}: {route['travel_time']}分 ({route['route_type']})")
                        if route.get('train_lines'):
                            print(f"       路線: {', '.join(route['train_lines'])}")
                        if '高速' in route.get('summary', ''):
                            print(f"       ⚠️ 高速道路を含む")
                
                results.append({
                    'destination': dest['name'],
                    'success': True,
                    'travel_time': result['travel_time'],
                    'route_type': result['route_type'],
                    'fare': result.get('fare'),
                    'train_lines': result.get('train_lines', []),
                    'departure_time': result.get('departure_time'),
                    'arrival_time': result.get('arrival_time'),
                    'elapsed_seconds': elapsed,
                    'from_cache': result.get('from_cache', False)
                })
            else:
                print(f"  ❌ 失敗: {result.get('error')} ({elapsed:.1f}秒)")
                results.append({
                    'destination': dest['name'],
                    'success': False,
                    'error': result.get('error'),
                    'elapsed_seconds': elapsed
                })
            
            print()  # 空行
        
        total_elapsed = time.time() - start_total
        
        # サマリー
        print("="*80)
        print("📊 テスト結果サマリー")
        print("="*80)
        
        success_count = sum(1 for r in results if r['success'])
        cache_count = sum(1 for r in results if r.get('from_cache', False))
        
        print(f"\n成功率: {success_count}/9 ({success_count*100/9:.0f}%)")
        print(f"キャッシュヒット: {cache_count}/9")
        print(f"総処理時間: {total_elapsed:.1f}秒 (平均: {total_elapsed/9:.1f}秒/ルート)")
        
        print("\n【取得結果】")
        for r in results:
            if r['success']:
                cache_mark = "⚡" if r.get('from_cache') else "  "
                print(f"{cache_mark} {r['destination']:20}: {r['travel_time']:3}分 ({r['route_type']})")
                if r['train_lines']:
                    print(f"    路線: {', '.join(r['train_lines'])}")
        
        # 問題のあるルートを確認
        print("\n【要確認ルート】")
        problem_routes = []
        for r in results:
            if r['success']:
                # 早稲田が公共交通機関でない場合
                if r['destination'] == '早稲田大学' and r['route_type'] != '公共交通機関':
                    problem_routes.append(f"  ⚠️ 早稲田大学: {r['route_type']} (電車ルートが必要)")
                # 徒歩時間が長すぎる場合
                elif r['route_type'] == '徒歩のみ' and r['travel_time'] > 30:
                    problem_routes.append(f"  ⚠️ {r['destination']}: 徒歩{r['travel_time']}分 (長すぎる)")
        
        if problem_routes:
            for p in problem_routes:
                print(p)
        else:
            print("  ✅ 全ルート正常")
        
        # 結果をJSON保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/test_first_property_9_routes.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'property': property_name,
                'origin': origin,
                'arrival_time': arrival_time.isoformat(),
                'results': results,
                'summary': {
                    'success_count': success_count,
                    'cache_count': cache_count,
                    'total_time_seconds': total_elapsed,
                    'average_time_seconds': total_elapsed / 9
                }
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 結果を保存: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔧 クリーンアップ中...")
        scraper.close()
        print("✅ 完了")

if __name__ == "__main__":
    test_first_property_9_routes()