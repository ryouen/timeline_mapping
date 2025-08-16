#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
残りのルート処理を完了させる
1. La Belle三越前の失敗した7ルート再試行
2. 未処理6物件の処理
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_failed_routes():
    """La Belle三越前の失敗ルートを再試行"""
    logger.info("=" * 60)
    logger.info("📍 失敗ルートの再試行")
    logger.info("=" * 60)
    
    # 失敗ルートの情報
    failed_routes = [
        ("東京都中央区日本橋本町1丁目", "東京都千代田区神田小川町３丁目２８−５", "axle御茶ノ水"),
        ("東京都中央区日本橋本町1丁目", "東京都渋谷区神宮前１丁目８−１０ Ｔｈｅ Ｉｃｅ Ｃｕｂｅｓ 9階", "Yawara"),
        ("東京都中央区日本橋本町1丁目", "東京都港区虎ノ門４丁目２−６ 第二扇屋ビル 1F", "神谷町(EE)"),
        ("東京都中央区日本橋本町1丁目", "東京都新宿区西早稲田１丁目６ 11号館", "早稲田大学"),
        ("東京都中央区日本橋本町1丁目", "東京都千代田区丸の内１丁目", "東京駅"),
        ("東京都中央区日本橋本町1丁目", "東京都大田区羽田空港3-3-2", "羽田空港"),
        ("東京都中央区日本橋本町1丁目", "東京都府中市住吉町５丁目２２−５", "府中オフィス")
    ]
    
    # 到着時刻設定
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    scraper = GoogleMapsScraper()
    scraper.setup_driver()
    
    results = []
    for origin, dest, dest_name in failed_routes:
        logger.info(f"再試行: La Belle → {dest_name}")
        start_time = time.time()
        
        result = scraper.scrape_route(origin, dest, dest_name, arrival_time)
        elapsed = time.time() - start_time
        
        if result.get('success'):
            logger.info(f"  ✅ 成功: {result['travel_time']}分 ({elapsed:.1f}秒)")
        else:
            logger.error(f"  ❌ 失敗: {result.get('error', '不明')} ({elapsed:.1f}秒)")
        
        results.append({
            'property_name': 'La Belle 三越前 0702',
            'property_address': origin,
            'destination_name': dest_name,
            'destination_address': dest,
            'success': result.get('success', False),
            'travel_time': result.get('travel_time'),
            'route_type': result.get('route_type'),
            'train_lines': result.get('train_lines', []),
            'fare': result.get('fare'),
            'processing_time': elapsed,
            'timestamp': datetime.now().isoformat(),
            'is_retry': True
        })
    
    scraper.close()
    return results

def process_remaining_properties():
    """未処理6物件を処理"""
    logger.info("=" * 60)
    logger.info("🏢 未処理物件の処理")
    logger.info("=" * 60)
    
    data_loader = JsonDataLoader()
    all_properties = data_loader.get_all_properties()
    destinations = data_loader.get_all_destinations()
    
    # 未処理物件リスト
    unprocessed = [
        "ルフォンプログレ神田プレミア",
        "テラス月島 801",
        "J-FIRST CHIYODA 702",
        "アイル秋葉原EAST 307",
        "リベルテ月島 604",
        "シティハウス東京八重洲通り 1502"
    ]
    
    # 到着時刻設定
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    all_results = []
    
    for prop_name in unprocessed:
        # 物件情報を取得
        prop = next((p for p in all_properties if p['name'] == prop_name), None)
        if not prop:
            logger.warning(f"物件が見つかりません: {prop_name}")
            continue
        
        logger.info(f"\n処理中: {prop_name}")
        logger.info(f"  住所: {prop['address']}")
        
        # 新しいスクレイパーインスタンス（物件ごとに再起動）
        scraper = GoogleMapsScraper()
        scraper.setup_driver()
        
        prop_results = []
        for dest in destinations:
            print(f"  → {dest['name']}...", end="", flush=True)
            start_time = time.time()
            
            result = scraper.scrape_route(
                prop['address'],
                dest['address'],
                dest['name'],
                arrival_time
            )
            elapsed = time.time() - start_time
            
            if result.get('success'):
                print(f" ✅ {result['travel_time']}分 ({elapsed:.1f}秒)")
            else:
                print(f" ❌ {result.get('error', '不明')} ({elapsed:.1f}秒)")
            
            prop_results.append({
                'property_name': prop_name,
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
            })
        
        all_results.extend(prop_results)
        scraper.close()
        
        # サマリー
        success_count = sum(1 for r in prop_results if r['success'])
        logger.info(f"  完了: 成功 {success_count}/9")
        
        # メモリ解放のため少し待機
        time.sleep(2)
    
    return all_results

def save_final_results(retry_results, new_results):
    """最終結果を保存"""
    logger.info("=" * 60)
    logger.info("📄 最終結果の保存")
    logger.info("=" * 60)
    
    # 既存の進捗を読み込み
    progress_file = '/app/output/japandatascience.com/timeline-mapping/data/batch_progress.json'
    with open(progress_file, 'r', encoding='utf-8') as f:
        progress = json.load(f)
    
    # 再試行結果を追加
    for r in retry_results:
        if r['success']:
            progress['total_success'] += 1
            # 失敗を成功に置き換え
            progress['total_failed'] -= 1
    
    # 新規結果を追加
    for r in new_results:
        if r['success']:
            progress['total_success'] += 1
        else:
            progress['total_failed'] += 1
    
    # ルートリストに追加
    progress['routes'].extend(retry_results)
    progress['routes'].extend(new_results)
    
    # 完了物件リストを更新
    for prop_name in set(r['property_name'] for r in new_results):
        if prop_name not in progress['completed_properties']:
            progress['completed_properties'].append(prop_name)
    
    progress['last_property_index'] = 23  # 全物件完了
    
    # 最終ファイルとして保存
    final_file = '/app/output/japandatascience.com/timeline-mapping/data/batch_progress_final.json'
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 最終結果を保存: {final_file}")
    logger.info(f"  総成功: {progress['total_success']}")
    logger.info(f"  総失敗: {progress['total_failed']}")
    logger.info(f"  成功率: {progress['total_success']*100/207:.1f}%")
    
    return progress

if __name__ == "__main__":
    # 1. 失敗ルートの再試行
    retry_results = retry_failed_routes()
    
    # 2. 未処理物件の処理
    new_results = process_remaining_properties()
    
    # 3. 最終結果の保存
    final_progress = save_final_results(retry_results, new_results)
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 全処理完了！")
    logger.info("=" * 60)