#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最適化版v5で最初の物件×9目的地をテスト
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5_optimized import GoogleMapsScraperV5Optimized
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
    print("⚡ 最適化版: 最初の物件×9目的地テスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # 最初の物件
    property_name = 'ルフォンプログレ神田プレミア'
    origin = '東京都千代田区神田須田町1-20-1'
    
    # 9つの目的地
    destinations = [
        {'name': 'Shizenkan University', 'address': '東京都中央区日本橋2-5-1', 'type': '近距離'},
        {'name': 'パラレルマーケターズ', 'address': '東京都中野区中野3-49-1', 'type': '中距離'},
        {'name': 'ネクセンス', 'address': '東京都千代田区麹町3-5-2', 'type': '近距離'},
        {'name': 'メディファーマ', 'address': '東京都千代田区紀尾井町3-12', 'type': '近距離'},
        {'name': 'アクスル', 'address': '東京都千代田区麹町1-12-12', 'type': '近距離'},
        {'name': '早稲田大学', 'address': '東京都新宿区西早稲田1-6-11', 'type': '中距離'},
        {'name': '羽田空港国際線', 'address': '東京都大田区羽田空港2-6-5', 'type': '長距離'},
        {'name': '駒澤大学', 'address': '東京都世田谷区駒沢1-23-1', 'type': '中距離'},
        {'name': '府中オフィス', 'address': '東京都府中市住吉町5-22-5', 'type': '長距離'}
    ]
    
    scraper = GoogleMapsScraperV5Optimized()
    
    try:
        print("\n📌 WebDriver初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了（最適化版）\n")
        
        results = []
        start_total = time.time()
        
        for i, dest in enumerate(destinations, 1):
            print(f"[{i}/9] {dest['name']} ({dest['type']})")
            
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
                
                if result.get('train_lines'):
                    print(f"    路線: {', '.join(result['train_lines'])}")
                
                if result.get('fare'):
                    print(f"    料金: ¥{result['fare']}")
                
                if result.get('from_cache'):
                    print(f"    ⚡ キャッシュから取得")
                
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
        
        # 通常版との比較（推定）
        estimated_normal_time = total_elapsed * 4.3  # 4.3倍の高速化を基に推定
        print(f"\n推定通常版処理時間: {estimated_normal_time:.0f}秒")
        print(f"削減時間: {estimated_normal_time - total_elapsed:.0f}秒")
        
        print("\n【取得結果】")
        for r in results:
            if r['success']:
                cache_mark = "⚡" if r.get('from_cache') else "  "
                print(f"{cache_mark} {r['destination']:20}: {r['travel_time']:3}分 ({r['route_type']})")
                if r['train_lines']:
                    print(f"    路線: {', '.join(r['train_lines'])}")
        
        # 要確認ルートを確認
        print("\n【データ品質チェック】")
        problem_count = 0
        for r in results:
            if r['success']:
                # 徒歩時間が長すぎる場合
                if r['route_type'] == '徒歩のみ' and r['travel_time'] > 30:
                    print(f"  ⚠️ {r['destination']}: 徒歩{r['travel_time']}分 (要確認)")
                    problem_count += 1
                # 公共交通機関でない近距離ルート
                elif r['destination'] in ['Shizenkan University', 'ネクセンス', 'メディファーマ', 'アクスル'] and r['route_type'] != '公共交通機関':
                    print(f"  ⚠️ {r['destination']}: {r['route_type']} (電車ルートが期待される)")
                    problem_count += 1
        
        if problem_count == 0:
            print("  ✅ 全ルート正常")
        
        # 結果をJSON保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/test_first_property_9_optimized.json'
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
                    'average_time_seconds': total_elapsed / 9,
                    'estimated_speedup': estimated_normal_time / total_elapsed if 'estimated_normal_time' in locals() else None
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