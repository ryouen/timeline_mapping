#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ユーザーフローエミュレーション
json-generator.html のユーザー操作を再現して
目的地登録 → 物件登録 → ルート検索 → JSON生成の完全フローをテスト
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
import pytz

sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from json_data_loader import JsonDataLoader
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserFlowEmulator:
    """ユーザーフローをエミュレート"""
    
    def __init__(self):
        self.data_loader = JsonDataLoader()
        self.scraper = None
        self.destinations = []
        self.properties = []
        self.routes = []
        self.intermediate_file = '/app/output/japandatascience.com/timeline-mapping/data/emulation_progress.json'
        self.final_properties_file = '/app/output/japandatascience.com/timeline-mapping/data/properties_emulated.json'
        
    def step1_load_destinations(self):
        """Step 1: 目的地を登録（既存のdestinations.jsonから読み込み）"""
        logger.info("=" * 60)
        logger.info("📍 Step 1: 目的地登録")
        logger.info("=" * 60)
        
        self.destinations = self.data_loader.get_all_destinations()
        logger.info(f"✅ {len(self.destinations)}件の目的地を登録しました")
        
        for i, dest in enumerate(self.destinations, 1):
            logger.info(f"  {i}. {dest['name']} - {dest['address'][:30]}...")
            
        return len(self.destinations) > 0
    
    def step2_load_properties(self):
        """Step 2: 物件を登録（properties_base.jsonから読み込み）"""
        logger.info("\n" + "=" * 60)
        logger.info("🏢 Step 2: 物件登録")
        logger.info("=" * 60)
        
        self.properties = self.data_loader.get_all_properties()
        logger.info(f"✅ {len(self.properties)}件の物件を登録しました")
        
        for i, prop in enumerate(self.properties[:5], 1):  # 最初の5件のみ表示
            logger.info(f"  {i}. {prop['name']} - {prop['address'][:30]}...")
        if len(self.properties) > 5:
            logger.info(f"  ... 他{len(self.properties) - 5}件")
            
        return len(self.properties) > 0
    
    def step3_route_search(self, limit_properties=2):
        """Step 3: ルート検索（制限付き）"""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 Step 3: ルート検索")
        logger.info("=" * 60)
        
        # 到着時刻設定（明日の10:00）
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.now(jst) + timedelta(days=1)
        arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # 検索対象を制限
        test_properties = self.properties[:limit_properties]
        total_routes = len(test_properties) * len(self.destinations)
        
        logger.info(f"📊 検索概要:")
        logger.info(f"  - 物件数: {len(test_properties)}件（全{len(self.properties)}件中）")
        logger.info(f"  - 目的地数: {len(self.destinations)}件")
        logger.info(f"  - 総ルート数: {total_routes}件")
        logger.info(f"  - 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')}")
        
        # スクレイパー初期化
        self.scraper = GoogleMapsScraper()
        self.scraper.setup_driver()
        logger.info("✅ スクレイパー初期化完了")
        
        # 進捗状況の初期化
        progress = {
            'total_routes': total_routes,
            'completed': 0,
            'success': 0,
            'failed': 0,
            'routes': []
        }
        
        # 各物件ごとに処理
        for prop_idx, prop in enumerate(test_properties, 1):
            logger.info(f"\n🏢 物件 {prop_idx}/{len(test_properties)}: {prop['name']}")
            
            prop_routes = []
            
            for dest_idx, dest in enumerate(self.destinations, 1):
                route_num = (prop_idx - 1) * len(self.destinations) + dest_idx
                print(f"  [{route_num}/{total_routes}] {dest['name']}...", end="", flush=True)
                
                start_time = time.time()
                
                # ルート検索実行
                result = self.scraper.scrape_route(
                    prop['address'],
                    dest['address'], 
                    dest['name'],
                    arrival_time
                )
                
                elapsed = time.time() - start_time
                
                # 結果を記録
                route_data = {
                    'property_id': prop.get('id', prop['name']),
                    'property_name': prop['name'],
                    'destination_id': dest.get('id', dest['name']),
                    'destination_name': dest['name'],
                    'success': result.get('success', False),
                    'travel_time': result.get('travel_time'),
                    'route_type': result.get('route_type'),
                    'train_lines': result.get('train_lines', []),
                    'fare': result.get('fare'),
                    'processing_time': elapsed,
                    'error': result.get('error') if not result.get('success') else None
                }
                
                prop_routes.append(route_data)
                progress['routes'].append(route_data)
                progress['completed'] += 1
                
                if result.get('success'):
                    progress['success'] += 1
                    print(f" ✅ {result['travel_time']}分 ({elapsed:.1f}秒)")
                else:
                    progress['failed'] += 1
                    print(f" ❌ {result.get('error', '不明')} ({elapsed:.1f}秒)")
                
                # 中間結果を保存
                self._save_intermediate_progress(progress)
            
            # 物件ごとのサマリー
            success_count = sum(1 for r in prop_routes if r['success'])
            logger.info(f"  物件サマリー: 成功 {success_count}/{len(self.destinations)}")
            
            # エラーチェック
            if success_count < len(self.destinations) * 0.5:  # 50%以上失敗
                logger.warning(f"  ⚠️ 警告: 成功率が低いです ({success_count}/{len(self.destinations)})")
                if prop_idx == 1:
                    logger.error("最初の物件で問題が発生しました。処理を中断します。")
                    return False
        
        # 最終サマリー
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ ルート検索完了")
        logger.info(f"  成功: {progress['success']}/{total_routes}")
        logger.info(f"  失敗: {progress['failed']}/{total_routes}")
        
        self.routes = progress['routes']
        return progress['success'] > 0
    
    def step4_generate_json(self):
        """Step 4: properties.jsonを生成"""
        logger.info("\n" + "=" * 60)
        logger.info("📄 Step 4: JSON生成")
        logger.info("=" * 60)
        
        # properties.jsonのフォーマットに変換
        properties_data = []
        
        # ルートを物件ごとにグループ化
        from collections import defaultdict
        routes_by_property = defaultdict(list)
        
        for route in self.routes:
            routes_by_property[route['property_name']].append(route)
        
        # 各物件のデータを生成
        for prop in self.properties[:len(routes_by_property)]:
            prop_data = {
                'name': prop['name'],
                'address': prop['address'],
                'rent': prop.get('rent'),
                'area': prop.get('area'),
                'routes': []
            }
            
            # この物件のルートを追加
            prop_routes = routes_by_property.get(prop['name'], [])
            for route in prop_routes:
                if route['success']:
                    route_entry = {
                        'destination': route['destination_name'],
                        'total_time': route['travel_time'],
                        'route_type': route['route_type'],
                        'train_lines': route.get('train_lines', []),
                        'fare': route.get('fare')
                    }
                    prop_data['routes'].append(route_entry)
            
            properties_data.append(prop_data)
        
        # JSONファイルに保存
        output = {'properties': properties_data}
        
        with open(self.final_properties_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ properties_emulated.json を生成しました")
        logger.info(f"   保存先: {self.final_properties_file}")
        logger.info(f"   物件数: {len(properties_data)}")
        
        # サンプル表示
        if properties_data:
            sample = properties_data[0]
            logger.info(f"\n📊 サンプル（{sample['name']}）:")
            for route in sample['routes'][:3]:
                logger.info(f"  → {route['destination']}: {route['total_time']}分")
        
        return True
    
    def _save_intermediate_progress(self, progress):
        """中間進捗を保存"""
        with open(self.intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def cleanup(self):
        """クリーンアップ処理"""
        if self.scraper:
            self.scraper.close()
            logger.info("✅ スクレイパーを終了しました")
    
    def run_full_flow(self, limit_properties=2):
        """完全なユーザーフローを実行"""
        logger.info("🚀 ユーザーフローエミュレーション開始")
        logger.info("=" * 60)
        
        try:
            # Step 1: 目的地登録
            if not self.step1_load_destinations():
                logger.error("目的地登録に失敗しました")
                return False
            
            # Step 2: 物件登録
            if not self.step2_load_properties():
                logger.error("物件登録に失敗しました")
                return False
            
            # Step 3: ルート検索
            if not self.step3_route_search(limit_properties):
                logger.error("ルート検索に失敗しました")
                return False
            
            # Step 4: JSON生成
            if not self.step4_generate_json():
                logger.error("JSON生成に失敗しました")
                return False
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 ユーザーフローエミュレーション完了！")
            logger.info("=" * 60)
            
            logger.info("\n次のステップ:")
            logger.info("1. 生成されたJSONファイルを確認")
            logger.info("2. エラーがあれば修正")
            logger.info("3. 全物件で再実行")
            
            return True
            
        except Exception as e:
            logger.error(f"エラーが発生しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        finally:
            self.cleanup()


if __name__ == "__main__":
    emulator = UserFlowEmulator()
    
    # 2物件でテスト実行（エラーチェック用）
    success = emulator.run_full_flow(limit_properties=2)
    
    if success:
        logger.info("\n✅ エミュレーション成功")
        sys.exit(0)
    else:
        logger.error("\n❌ エミュレーション失敗")
        sys.exit(1)