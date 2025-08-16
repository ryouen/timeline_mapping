#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONローダーを使用した正確なテスト
絶対に偽住所を使用しない安全な実装
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5_optimized import GoogleMapsScraperV5Optimized
from json_data_loader import JsonDataLoader
from datetime import datetime, timedelta
import pytz
import json
import time

def test_first_property_with_loader():
    """
    JSONローダーを使用して最初の物件×9目的地をテスト
    """
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🔒 JSONローダー使用: 偽住所ゼロの安全なテスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # JSONローダーを初期化
    print("\n📋 JSONデータを読み込み中...")
    loader = JsonDataLoader()
    
    # 最初の物件を取得（インデックス0）
    first_property = loader.get_property_by_index(0)
    if not first_property:
        print("❌ 物件が見つかりません")
        return
    
    print(f"\n🏢 テスト物件:")
    print(f"  名前: {first_property['name']}")
    print(f"  住所: {first_property['address']}")
    print(f"  家賃: {first_property['rent']}")  # すでに円が含まれている
    print(f"  広さ: {first_property['area']}㎡")  # areaが正しいキー
    
    # すべての目的地を取得
    destinations = loader.get_all_destinations()
    
    print(f"\n📍 {len(destinations)}個の目的地:")
    for i, dest in enumerate(destinations, 1):
        print(f"  {i}. {dest['name']:20} ({dest['category']:8}) - {dest['address'][:40]}...")
    
    # アドレス検証
    print("\n🔍 アドレス検証中...")
    origin_valid = loader.validate_address(first_property['address'], 'properties')
    if not origin_valid:
        print(f"❌ 物件住所が無効: {first_property['address']}")
        return
    print("  ✅ 物件住所: 検証済み")
    
    invalid_destinations = []
    for dest in destinations:
        if not loader.validate_address(dest['address'], 'destinations'):
            invalid_destinations.append(dest['name'])
    
    if invalid_destinations:
        print(f"❌ 無効な目的地: {', '.join(invalid_destinations)}")
        return
    print("  ✅ 全目的地住所: 検証済み")
    
    # スクレイパー初期化
    scraper = GoogleMapsScraperV5Optimized()
    
    try:
        print("\n📌 WebDriver初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了\n")
        
        results = []
        start_total = time.time()
        
        # 各目的地へのルートをスクレイピング
        for i, dest in enumerate(destinations, 1):
            print(f"[{i}/{len(destinations)}] {dest['name']} ({dest['category']})")
            print(f"  📍 {dest['address']}")
            
            start_route = time.time()
            
            # スクレイピング実行（住所は一文字も変更しない）
            result = scraper.scrape_route(
                first_property['address'],  # JSONから読み込んだまま使用
                dest['address'],            # JSONから読み込んだまま使用
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
                
                if result.get('departure_time') and result.get('arrival_time'):
                    print(f"    時刻: {result['departure_time']} → {result['arrival_time']}")
                
                results.append({
                    'destination_id': dest['id'],
                    'destination_name': dest['name'],
                    'destination_address': dest['address'],
                    'category': dest['category'],
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
                    'destination_id': dest['id'],
                    'destination_name': dest['name'],
                    'destination_address': dest['address'],
                    'category': dest['category'],
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
        
        print(f"\n成功率: {success_count}/{len(destinations)} ({success_count*100/len(destinations):.0f}%)")
        print(f"キャッシュヒット: {cache_count}/{len(destinations)}")
        print(f"総処理時間: {total_elapsed:.1f}秒")
        print(f"平均処理時間: {total_elapsed/len(destinations):.1f}秒/ルート")
        
        # カテゴリ別分析
        print("\n【カテゴリ別分析】")
        categories = {}
        for r in results:
            if r['success']:
                cat = r['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append({
                    'name': r['destination_name'],
                    'time': r['travel_time'],
                    'type': r['route_type']
                })
        
        for cat, items in sorted(categories.items()):
            if items:
                avg_time = sum(item['time'] for item in items) / len(items)
                print(f"\n  {cat}:")
                print(f"    平均所要時間: {avg_time:.0f}分")
                for item in items:
                    print(f"    - {item['name']:20}: {item['time']:3}分 ({item['type']})")
        
        # 詳細なルート情報
        print("\n【詳細ルート情報（10:00到着想定）】")
        for r in results:
            if r['success']:
                # 出発時刻を計算（到着時刻から逆算）
                departure_time = arrival_time - timedelta(minutes=r['travel_time'])
                print(f"\n{r['destination_name']}:")
                print(f"  出発: {departure_time.strftime('%H:%M')} → 到着: {arrival_time.strftime('%H:%M')}")
                print(f"  所要時間: {r['travel_time']}分")
                if r['train_lines']:
                    print(f"  経路: 徒歩 → {' → '.join(r['train_lines'])} → 徒歩")
                else:
                    print(f"  経路: {r['route_type']}")
                if r['fare']:
                    print(f"  料金: ¥{r['fare']}")
        
        # 結果をJSON保存
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/test_with_loader_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_type': 'first_property_all_destinations',
                'property': {
                    'name': first_property['name'],
                    'address': first_property['address'],
                    'rent': first_property['rent'],
                    'size': first_property['size']
                },
                'arrival_time': arrival_time.isoformat(),
                'results': results,
                'summary': {
                    'success_count': success_count,
                    'total_destinations': len(destinations),
                    'cache_count': cache_count,
                    'total_time_seconds': total_elapsed,
                    'average_time_seconds': total_elapsed / len(destinations)
                },
                'validation': {
                    'all_addresses_verified': True,
                    'no_fake_addresses': True,
                    'data_source': 'properties.json and destinations.json'
                }
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 結果を保存: {output_file}")
        print("✅ すべての住所はJSONファイルから直接読み込まれ、検証済みです")
        
        return results
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔧 クリーンアップ中...")
        scraper.close()
        print("✅ 完了")


def test_all_routes_with_loader():
    """
    全207ルート（23住所×9目的地）をテスト
    """
    print("="*80)
    print("🔒 全ルートテスト: JSONローダー使用")
    print("="*80)
    
    loader = JsonDataLoader()
    loader.print_summary()
    
    # テストマトリックスを生成
    matrix = loader.get_test_matrix()
    print(f"\n合計{len(matrix)}ルートをテスト予定")
    
    # ここで実際のテストを実行
    # （時間がかかるため、必要に応じて実装）


if __name__ == "__main__":
    # 最初の物件のテストを実行
    test_first_property_with_loader()