#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5スクレイパーで3ルートを高速テスト
クリック操作をスキップしてURLパラメータのみ使用
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5 import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz
import json

class FastGoogleMapsScraperV5(GoogleMapsScraperV5):
    """高速版スクレイパー（クリック操作スキップ）"""
    
    def scrape_route(self, origin_address, dest_address, dest_name=None, arrival_time=None):
        """ルート情報をスクレイピング（クリック操作スキップ版）"""
        # 住所を正規化
        origin_normalized = self.normalize_address(origin_address)
        dest_normalized = self.normalize_address(dest_address)
        
        # キャッシュキーを作成
        cache_key = f"{origin_normalized}→{dest_normalized}"
        
        # キャッシュチェック
        if cache_key in self.route_cache:
            print(f"  ⚡ キャッシュからルート取得")
            cached_result = self.route_cache[cache_key].copy()
            cached_result['from_cache'] = True
            return cached_result
        
        try:
            # Place IDを事前取得
            origin_info = self.get_place_id(origin_address, "出発地")
            dest_info = self.get_place_id(dest_address, dest_name)
            
            # タイムスタンプ付きURLを構築
            url = self.build_url_with_timestamp(origin_info, dest_info, arrival_time)
            
            print(f"  📍 ルート検索中...")
            self.driver.get(url)
            import time
            time.sleep(5)  # ページロード待機
            
            # クリック操作をスキップ
            print(f"  ⏩ クリック操作をスキップ（高速モード）")
            
            # ルート詳細を抽出
            routes = self.extract_route_details()
            
            if routes:
                # 公共交通機関のルートを優先
                transit_routes = [r for r in routes if r['route_type'] == '公共交通機関']
                if transit_routes:
                    shortest = min(transit_routes, key=lambda r: r['travel_time'])
                else:
                    shortest = min(routes, key=lambda r: r['travel_time'])
                
                result = {
                    'success': True,
                    'origin': origin_address,
                    'destination': dest_address,
                    'destination_name': dest_name,
                    'travel_time': shortest['travel_time'],
                    'departure_time': shortest.get('departure_time'),
                    'arrival_time': shortest.get('arrival_time'),
                    'fare': shortest.get('fare'),
                    'route_type': shortest['route_type'],
                    'train_lines': shortest.get('train_lines', []),
                    'all_routes': routes,
                    'place_ids': {
                        'origin': origin_info.get('place_id'),
                        'destination': dest_info.get('place_id')
                    },
                    'url': url
                }
                
                # キャッシュに保存
                self.route_cache[cache_key] = result
                
                return result
            else:
                return {
                    'success': False,
                    'error': 'ルート情報を取得できませんでした',
                    'url': url
                }
                
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # ルート処理後のクリーンアップ
            self.cleanup_after_route()

def test_3_routes_fast():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🚇 v5スクレイパー 3ルート高速テスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("⚡ 高速モード: クリック操作をスキップ")
    print("="*80)
    
    # テストルート
    test_routes = [
        {
            'name': 'Shizenkan University（近距離）',
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都中央区日本橋2-5-1'
        },
        {
            'name': '早稲田大学（中距離）',
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都新宿区西早稲田1-6-11'
        },
        {
            'name': '府中オフィス（長距離）',
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都府中市住吉町5-22-5'
        }
    ]
    
    scraper = FastGoogleMapsScraperV5()
    
    try:
        print("\n📌 初期化中...")
        scraper.setup_driver()
        print("✅ 初期化完了\n")
        
        results = []
        
        for i, route in enumerate(test_routes, 1):
            print(f"[{i}/3] {route['name']}")
            
            import time
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
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/test_3_routes_fast.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 保存: {output_file}")
        
        return results
        
    finally:
        scraper.close()
        print("✅ 終了")

if __name__ == "__main__":
    test_3_routes_fast()