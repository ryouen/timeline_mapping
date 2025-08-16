#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メインルートスクレイピングスクリプト
ユーザーフローをエミュレート：
1. properties_base.jsonとdestinations.jsonを読み込み
2. 全ルートを段階的にスクレイピング
3. 中間結果を保存（プロセス中断時の復旧用）
4. 最終的にproperties.json（ルート情報付き）を生成
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from json_data_loader import JsonDataLoader
from datetime import datetime, timedelta
import pytz
import json
import time
import os
import traceback

class RouteScraperManager:
    """
    ルートスクレイピングを管理するクラス
    中断・再開、進捗管理、エラーハンドリングを含む
    """
    
    def __init__(self):
        self.loader = JsonDataLoader()
        self.scraper = None
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # 中間結果ファイルのパス
        self.progress_file = '/app/output/japandatascience.com/timeline-mapping/data/scraping_progress.json'
        self.intermediate_file = '/app/output/japandatascience.com/timeline-mapping/data/routes_intermediate.json'
        self.final_file = '/app/output/japandatascience.com/timeline-mapping/data/properties.json'
        
        # 到着時刻の設定（明日の10時）
        tomorrow = datetime.now(self.jst) + timedelta(days=1)
        self.arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # 進捗状況
        self.progress = self.load_progress()
        
    def load_progress(self):
        """保存された進捗を読み込む"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                print(f"📂 既存の進捗を読み込みました: {progress['completed_count']}/{progress['total_count']} 完了")
                return progress
        else:
            # 新規開始
            properties = self.loader.get_all_properties()
            destinations = self.loader.get_all_destinations()
            unique_addresses = self.loader.get_unique_property_addresses()
            
            return {
                'start_time': datetime.now(self.jst).isoformat(),
                'total_properties': len(properties),
                'total_destinations': len(destinations),
                'unique_addresses': len(unique_addresses),
                'total_count': len(unique_addresses) * len(destinations),
                'completed_count': 0,
                'completed_routes': [],
                'failed_routes': [],
                'current_property_index': 0
            }
    
    def save_progress(self):
        """進捗を保存"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2, default=str)
    
    def save_intermediate_results(self, results):
        """中間結果を保存"""
        # 既存の結果を読み込み
        if os.path.exists(self.intermediate_file):
            with open(self.intermediate_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
        else:
            all_results = {}
        
        # 新しい結果を追加
        all_results.update(results)
        
        # 保存
        with open(self.intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 中間結果を保存: {self.intermediate_file}")
    
    def scrape_property_routes(self, property_data, property_index):
        """
        一つの物件に対して全目的地へのルートをスクレイピング
        """
        destinations = self.loader.get_all_destinations()
        property_results = {
            'property_name': property_data['properties'][0] if 'properties' in property_data else property_data['name'],
            'address': property_data['address'],
            'routes': []
        }
        
        print(f"\n🏢 物件 {property_index + 1}: {property_results['property_name']}")
        print(f"   住所: {property_data['address']}")
        
        for dest_index, destination in enumerate(destinations):
            route_key = f"{property_data['address']}→{destination['address']}"
            
            # 既に処理済みかチェック
            if route_key in self.progress['completed_routes']:
                print(f"   ⏭️ スキップ: {destination['name']} (処理済み)")
                continue
            
            print(f"   [{dest_index + 1}/{len(destinations)}] {destination['name']}")
            
            try:
                start_time = time.time()
                
                result = self.scraper.scrape_route(
                    property_data['address'],
                    destination['address'],
                    destination['name'],
                    self.arrival_time
                )
                
                elapsed = time.time() - start_time
                
                if result.get('success'):
                    route_info = {
                        'destination_id': destination['id'],
                        'destination_name': destination['name'],
                        'destination_category': destination['category'],
                        'travel_time': result['travel_time'],
                        'route_type': result['route_type'],
                        'train_lines': result.get('train_lines', []),
                        'fare': result.get('fare'),
                        'departure_time': result.get('departure_time'),
                        'arrival_time': result.get('arrival_time'),
                        'scraped_at': datetime.now(self.jst).isoformat()
                    }
                    
                    property_results['routes'].append(route_info)
                    self.progress['completed_routes'].append(route_key)
                    self.progress['completed_count'] += 1
                    
                    print(f"      ✅ {result['travel_time']}分 ({result['route_type']}) - {elapsed:.1f}秒")
                    
                else:
                    self.progress['failed_routes'].append({
                        'route': route_key,
                        'error': result.get('error'),
                        'timestamp': datetime.now(self.jst).isoformat()
                    })
                    print(f"      ❌ 失敗: {result.get('error')}")
            
            except Exception as e:
                print(f"      ❌ エラー: {str(e)}")
                self.progress['failed_routes'].append({
                    'route': route_key,
                    'error': str(e),
                    'timestamp': datetime.now(self.jst).isoformat()
                })
            
            # 進捗を保存（各ルート処理後）
            self.save_progress()
        
        return property_results
    
    def run(self, max_properties=None):
        """
        メイン処理実行
        
        Args:
            max_properties: 処理する物件数の上限（テスト用）
        """
        print("="*80)
        print("🚀 ルートスクレイピング開始")
        print(f"📅 到着時刻: {self.arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
        print("="*80)
        
        # ユニーク住所を取得
        unique_addresses = self.loader.get_unique_property_addresses()
        
        if max_properties:
            unique_addresses = unique_addresses[:max_properties]
            print(f"\n⚠️ テストモード: 最初の{max_properties}物件のみ処理")
        
        print(f"\n📊 処理対象:")
        print(f"   ユニーク物件数: {len(unique_addresses)}")
        print(f"   目的地数: {len(self.loader.get_all_destinations())}")
        print(f"   総ルート数: {len(unique_addresses) * len(self.loader.get_all_destinations())}")
        
        # スクレイパー初期化
        self.scraper = GoogleMapsScraper()
        
        try:
            print("\n🔧 WebDriver初期化中...")
            self.scraper.setup_driver()
            print("✅ 初期化完了\n")
            
            all_results = {}
            
            # 各物件を処理
            for prop_index in range(self.progress['current_property_index'], len(unique_addresses)):
                property_data = unique_addresses[prop_index]
                
                # 物件のルートをスクレイピング
                property_results = self.scrape_property_routes(property_data, prop_index)
                
                # 結果を保存
                all_results[property_data['address']] = property_results
                
                # 中間結果を保存
                self.save_intermediate_results(all_results)
                
                # 進捗を更新
                self.progress['current_property_index'] = prop_index + 1
                self.save_progress()
                
                # 進捗表示
                total_progress = self.progress['completed_count'] / self.progress['total_count'] * 100
                print(f"\n📈 全体進捗: {self.progress['completed_count']}/{self.progress['total_count']} ({total_progress:.1f}%)")
                
                # エラーチェック（2物件ごと）
                if (prop_index + 1) % 2 == 0:
                    self.check_errors_and_quality()
            
            # 最終結果を生成
            self.generate_final_json(all_results)
            
            print("\n" + "="*80)
            print("✅ スクレイピング完了！")
            print(f"   成功: {self.progress['completed_count']}ルート")
            print(f"   失敗: {len(self.progress['failed_routes'])}ルート")
            
        except Exception as e:
            print(f"\n❌ 致命的エラー: {str(e)}")
            traceback.print_exc()
        
        finally:
            if self.scraper:
                self.scraper.close()
                print("🔧 クリーンアップ完了")
    
    def check_errors_and_quality(self):
        """エラーと品質をチェック"""
        print("\n" + "-"*40)
        print("🔍 品質チェック")
        print("-"*40)
        
        if self.progress['failed_routes']:
            print(f"⚠️ 失敗したルート: {len(self.progress['failed_routes'])}件")
            for failed in self.progress['failed_routes'][-3:]:  # 最新3件を表示
                print(f"   - {failed['route']}: {failed['error']}")
        else:
            print("✅ エラーなし")
        
        # 成功率
        if self.progress['completed_count'] > 0:
            success_rate = self.progress['completed_count'] / (self.progress['completed_count'] + len(self.progress['failed_routes'])) * 100
            print(f"📊 成功率: {success_rate:.1f}%")
        
        print("-"*40)
    
    def generate_final_json(self, all_results):
        """最終的なproperties.jsonを生成"""
        print("\n📝 最終JSONファイル生成中...")
        
        # properties_base.jsonを読み込み
        properties = self.loader.get_all_properties()
        
        # ルート情報を追加
        for prop in properties:
            if prop['address'] in all_results:
                prop['routes'] = all_results[prop['address']]['routes']
            else:
                prop['routes'] = []
        
        # 保存
        output = {
            'generated_at': datetime.now(self.jst).isoformat(),
            'arrival_time': self.arrival_time.isoformat(),
            'total_properties': len(properties),
            'total_routes_scraped': self.progress['completed_count'],
            'properties': properties
        }
        
        with open(self.final_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 最終結果を保存: {self.final_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ルートスクレイピング')
    parser.add_argument('--test', type=int, help='テストモード（処理する物件数）')
    parser.add_argument('--reset', action='store_true', help='進捗をリセットして最初から開始')
    args = parser.parse_args()
    
    if args.reset and os.path.exists('/app/output/japandatascience.com/timeline-mapping/data/scraping_progress.json'):
        os.remove('/app/output/japandatascience.com/timeline-mapping/data/scraping_progress.json')
        print("進捗をリセットしました")
    
    manager = RouteScraperManager()
    manager.run(max_properties=args.test)