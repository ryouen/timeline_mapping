#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全207ルート（23物件×9目的地）のバッチ処理 - 改良版
・運賃の正確な抽出（1000円以上対応）
・実際にアクセスしたGoogle Maps URLの記録
・全ルート記録の保持
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
import pytz
import logging
import re

sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from json_data_loader import JsonDataLoader

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedGoogleMapsScraper(GoogleMapsScraper):
    """改良版スクレイパー - URLトラッキング付き"""
    
    def __init__(self):
        super().__init__()
        self.last_accessed_url = None
    
    def scrape_route(self, origin, destination, dest_name, arrival_time):
        """オーバーライド: 実際のアクセスURLを記録"""
        try:
            # Place IDを事前取得
            origin_place_id = self.get_place_id(origin, "出発地")
            dest_place_id = self.get_place_id(destination, dest_name)
            
            # タイムスタンプ付きURLを構築
            timestamp = int(arrival_time.timestamp())
            
            # URLパス部分（表示用の名前）
            from urllib.parse import quote
            url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/"
            
            # Place IDを使ったdataブロブを構築
            if origin_place_id and dest_place_id:
                if origin_place_id.startswith('ChIJ') and dest_place_id.startswith('ChIJ'):
                    # Place IDをdataブロブに埋め込む
                    origin_blob = f"!1m5!1m1!1s{origin_place_id}"
                    dest_blob = f"!1m5!1m1!1s{dest_place_id}"
                    time_blob = f"!2m3!6e1!7e2!8j{timestamp}"  # !6e1=到着時刻
                    transit_mode = "!3e3"  # 公共交通機関
                    
                    # dataブロブを結合
                    url += f"data=!4m14!4m13{origin_blob}{dest_blob}{time_blob}{transit_mode}"
                else:
                    # Place IDがない場合は従来のパラメータ
                    url += f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
            else:
                # Place IDがない場合は従来のパラメータ
                url += f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
            
            # 実際にアクセスするURLを記録
            self.last_accessed_url = url
            logger.info(f"📍 アクセスURL: {url[:100]}...")
            
            # 基底クラスのメソッドを呼び出し
            result = super().scrape_route(origin, destination, dest_name, arrival_time)
            
            # アクセスしたURLを結果に追加
            result['accessed_url'] = self.last_accessed_url
            
            return result
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'destination': dest_name,
                'accessed_url': self.last_accessed_url
            }
    
    def _extract_fare(self, text):
        """改良版: 4桁以上の運賃も正確に抽出"""
        # 料金パターン（カンマ区切りも対応）
        fare_patterns = [
            r'¥\s*(\d{1,3}(?:,\d{3})*)',  # ¥1,234形式
            r'(\d{1,3}(?:,\d{3})*)\s*円',  # 1,234円形式
            r'¥\s*(\d+)',                  # ¥1234形式
            r'(\d+)\s*円',                  # 1234円形式
            r'￥\s*(\d+)',                  # 全角￥
            r'(\d+)\s*yen'                 # yen表記
        ]
        
        for pattern in fare_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # カンマを除去して数値に変換
                fare_str = match.group(1).replace(',', '')
                try:
                    fare = int(fare_str)
                    # 妥当性チェック（50円〜10000円の範囲）
                    if 50 <= fare <= 10000:
                        return fare
                except ValueError:
                    continue
        
        return None

class RouteBatchProcessorImproved:
    """改良版バッチプロセッサー"""
    
    def __init__(self, start_from_property=15):  # 15番目の物件から開始
        self.data_loader = JsonDataLoader()
        self.progress_file = '/app/output/japandatascience.com/timeline-mapping/data/batch_progress_improved.json'
        self.results_file = '/app/output/japandatascience.com/timeline-mapping/data/routes_batch_improved.json'
        self.final_file = '/app/output/japandatascience.com/timeline-mapping/data/properties.json'
        self.start_from_property = start_from_property
        
    def load_existing_progress(self):
        """既存の進捗を読み込み（14物件分）"""
        existing_file = '/app/output/japandatascience.com/timeline-mapping/data/batch_progress.json'
        if os.path.exists(existing_file):
            with open(existing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_progress(self, progress):
        """進捗状況を保存"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def process_remaining_routes(self):
        """残りのルートを処理（15物件目から）"""
        # データ読み込み
        properties = self.data_loader.get_all_properties()
        destinations = self.data_loader.get_all_destinations()
        
        if not properties or not destinations:
            logger.error("データの読み込みに失敗しました")
            return False
        
        # 既存の進捗を読み込み
        existing_progress = self.load_existing_progress()
        if existing_progress:
            progress = existing_progress
            logger.info(f"既存の進捗を読み込みました: {len(progress['completed_properties'])}物件完了")
        else:
            progress = {
                'completed_properties': [],
                'last_property_index': 0,
                'total_success': 0,
                'total_failed': 0,
                'routes': []
            }
        
        # 到着時刻設定（明日の10:00）
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.now(jst) + timedelta(days=1)
        arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        logger.info("=" * 60)
        logger.info("📊 改良版バッチ処理開始")
        logger.info(f"  物件数: {len(properties)}件")
        logger.info(f"  目的地数: {len(destinations)}件")
        logger.info(f"  総ルート数: {len(properties) * len(destinations)}件")
        logger.info(f"  開始位置: 物件 {self.start_from_property}/{len(properties)}")
        logger.info(f"  到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')}")
        logger.info("=" * 60)
        
        # 15物件目から処理
        for prop_idx, prop in enumerate(properties[self.start_from_property - 1:], self.start_from_property):
            if prop['name'] in progress['completed_properties']:
                logger.info(f"物件 {prop_idx}/{len(properties)}: {prop['name']} - スキップ（処理済み）")
                continue
            
            logger.info(f"\n🏢 物件 {prop_idx}/{len(properties)}: {prop['name']}")
            logger.info(f"   住所: {prop['address']}")
            
            # この物件用の改良版スクレイパーを作成
            scraper = ImprovedGoogleMapsScraper()
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
                        
                        # 結果を記録（アクセスURLを含む）
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
                            'accessed_url': result.get('accessed_url'),  # 実際のアクセスURL
                            'processing_time': elapsed,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        if result.get('success'):
                            progress['total_success'] += 1
                            fare_str = f"¥{result['fare']}" if result.get('fare') else "-"
                            print(f" ✅ {result['travel_time']}分 {fare_str} ({elapsed:.1f}秒)")
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
                    'fare': route.get('fare'),
                    'accessed_url': route.get('accessed_url')  # 実際のアクセスURL
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


if __name__ == "__main__":
    processor = RouteBatchProcessorImproved(start_from_property=15)
    success = processor.process_remaining_routes()
    sys.exit(0 if success else 1)