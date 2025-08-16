#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全207ルート（23物件×9目的地）のバッチ処理
セッションエラーを回避するため、物件ごとに新しいスクレイパーインスタンスを作成
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
import pytz
import logging

sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from json_data_loader import JsonDataLoader

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RouteBatchProcessor:
    """全ルートをバッチ処理"""
    
    def __init__(self):
        self.data_loader = JsonDataLoader()
        self.progress_file = '/app/output/japandatascience.com/timeline-mapping/data/batch_progress.json'
        self.results_file = '/app/output/japandatascience.com/timeline-mapping/data/routes_batch.json'
        self.final_file = '/app/output/japandatascience.com/timeline-mapping/data/properties.json'
        
    def load_progress(self):
        """進捗状況を読み込み"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'completed_properties': [],
            'last_property_index': 0,
            'total_success': 0,
            'total_failed': 0,
            'routes': []
        }
    
    def save_progress(self, progress):
        """進捗状況を保存"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def process_all_routes(self):
        """全ルートを処理"""
        # データ読み込み
        properties = self.data_loader.get_all_properties()
        destinations = self.data_loader.get_all_destinations()
        
        if not properties or not destinations:
            logger.error("データの読み込みに失敗しました")
            return False
        
        # 進捗読み込み
        progress = self.load_progress()
        start_index = progress['last_property_index']
        
        # 到着時刻設定（明日の10:00）
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.now(jst) + timedelta(days=1)
        arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        logger.info("=" * 60)
        logger.info("📊 バッチ処理開始")
        logger.info(f"  物件数: {len(properties)}件")
        logger.info(f"  目的地数: {len(destinations)}件")
        logger.info(f"  総ルート数: {len(properties) * len(destinations)}件")
        logger.info(f"  開始位置: 物件 {start_index + 1}/{len(properties)}")
        logger.info(f"  到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')}")
        logger.info("=" * 60)
        
        # 各物件を処理
        for prop_idx, prop in enumerate(properties[start_index:], start_index + 1):
            if prop['name'] in progress['completed_properties']:
                logger.info(f"物件 {prop_idx}/{len(properties)}: {prop['name']} - スキップ（処理済み）")
                continue
            
            logger.info(f"\n🏢 物件 {prop_idx}/{len(properties)}: {prop['name']}")
            logger.info(f"   住所: {prop['address']}")
            
            # この物件用の新しいスクレイパーを作成
            scraper = GoogleMapsScraper()
            prop_routes = []
            
            try:
                scraper.setup_driver()
                logger.info("   ✅ WebDriver初期化完了")
                
                # 各目的地へのルートを検索
                for dest_idx, dest in enumerate(destinations, 1):
                    route_num = (prop_idx - 1) * len(destinations) + dest_idx
                    total_routes = len(properties) * len(destinations)
                    
                    print(f"   [{route_num}/{total_routes}] {dest['name']}...", end="", flush=True)
                    start_time = time.time()
                    
                    try:
                        # ルート検索実行
                        result = scraper.scrape_route(
                            prop['address'],
                            dest['address'],
                            dest['name'],
                            arrival_time
                        )
                        
                        elapsed = time.time() - start_time
                        
                        # 結果を記録
                        route_data = {
                            'property_name': prop['name'],
                            'property_address': prop['address'],
                            'destination_name': dest['name'],
                            'destination_address': dest['address'],
                            'success': result.get('success', False),
                            'travel_time': result.get('travel_time'),
                            'route_type': result.get('route_type'),
                            'train_lines': result.get('train_lines', []),
                            'fare': result.get('fare'),
                            'processing_time': elapsed,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        if result.get('success'):
                            progress['total_success'] += 1
                            print(f" ✅ {result['travel_time']}分 ({elapsed:.1f}秒)")
                        else:
                            progress['total_failed'] += 1
                            route_data['error'] = result.get('error', '不明なエラー')
                            print(f" ❌ {result.get('error', '不明')} ({elapsed:.1f}秒)")
                        
                        prop_routes.append(route_data)
                        progress['routes'].append(route_data)
                        
                    except Exception as e:
                        logger.error(f" ❌ エラー: {e}")
                        progress['total_failed'] += 1
                        route_data = {
                            'property_name': prop['name'],
                            'destination_name': dest['name'],
                            'success': False,
                            'error': str(e),
                            'processing_time': time.time() - start_time,
                            'timestamp': datetime.now().isoformat()
                        }
                        prop_routes.append(route_data)
                        progress['routes'].append(route_data)
                
                # 物件完了
                progress['completed_properties'].append(prop['name'])
                progress['last_property_index'] = prop_idx
                
                # 進捗保存
                self.save_progress(progress)
                
                # サマリー表示
                success_count = sum(1 for r in prop_routes if r['success'])
                logger.info(f"   物件完了: 成功 {success_count}/{len(destinations)}, 失敗 {len(destinations) - success_count}")
                
            except Exception as e:
                logger.error(f"   物件処理エラー: {e}")
                
            finally:
                # スクレイパーをクリーンアップ
                if scraper:
                    scraper.close()
                    logger.info("   WebDriver終了")
                
                # 少し待機（メモリ解放のため）
                time.sleep(2)
        
        # 全体のサマリー
        logger.info("\n" + "=" * 60)
        logger.info("🎉 バッチ処理完了")
        logger.info(f"  総処理数: {progress['total_success'] + progress['total_failed']}")
        logger.info(f"  成功: {progress['total_success']}")
        logger.info(f"  失敗: {progress['total_failed']}")
        logger.info(f"  成功率: {progress['total_success'] / max(1, progress['total_success'] + progress['total_failed']) * 100:.1f}%")
        logger.info("=" * 60)
        
        # 最終JSONを生成
        self.generate_final_json(progress)
        
        return True
    
    def generate_final_json(self, progress):
        """最終的なproperties.jsonを生成"""
        logger.info("\n📄 最終JSON生成中...")
        
        # 物件ごとにルートをグループ化
        from collections import defaultdict
        routes_by_property = defaultdict(list)
        
        for route in progress['routes']:
            if route['success']:
                routes_by_property[route['property_name']].append(route)
        
        # properties.json形式に変換
        properties_data = []
        
        for prop_name, routes in routes_by_property.items():
            # 元の物件データを取得
            orig_props = self.data_loader.get_all_properties()
            prop_data = next((p for p in orig_props if p['name'] == prop_name), {})
            
            property_json = {
                'name': prop_name,
                'address': routes[0]['property_address'] if routes else prop_data.get('address', ''),
                'rent': prop_data.get('rent'),
                'area': prop_data.get('area'),
                'routes': []
            }
            
            # ルート情報を追加
            for route in routes:
                route_entry = {
                    'destination': route['destination_name'],
                    'total_time': route['travel_time'],
                    'route_type': route['route_type'],
                    'train_lines': route.get('train_lines', []),
                    'fare': route.get('fare')
                }
                property_json['routes'].append(route_entry)
            
            properties_data.append(property_json)
        
        # JSONファイルに保存
        output = {'properties': properties_data}
        
        with open(self.final_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ properties.json 生成完了")
        logger.info(f"   保存先: {self.final_file}")
        logger.info(f"   物件数: {len(properties_data)}")
        
        # バッチ結果も保存
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        
        logger.info(f"   詳細結果: {self.results_file}")


if __name__ == "__main__":
    processor = RouteBatchProcessor()
    success = processor.process_all_routes()
    sys.exit(0 if success else 1)