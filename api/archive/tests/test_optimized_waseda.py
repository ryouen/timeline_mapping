#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最適化版v5で早稲田大学ルートをテスト
処理時間の短縮効果を測定
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper_v5_optimized import GoogleMapsScraperV5Optimized
from google_maps_scraper_v5 import GoogleMapsScraperV5
from datetime import datetime, timedelta
import pytz
import time

def test_waseda_comparison():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("⚡ 最適化版 vs 通常版 比較テスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    origin = '東京都千代田区神田須田町1-20-1'
    destination = '東京都新宿区西早稲田1-6-11'
    dest_name = '早稲田大学'
    
    # 1. 最適化版でテスト
    print("\n【最適化版v5】")
    print("-"*40)
    
    scraper_opt = GoogleMapsScraperV5Optimized()
    
    try:
        scraper_opt.setup_driver()
        
        start_time = time.time()
        result_opt = scraper_opt.scrape_route(
            origin,
            destination,
            dest_name,
            arrival_time
        )
        elapsed_opt = time.time() - start_time
        
        if result_opt['success']:
            print(f"✅ 成功")
            print(f"  所要時間: {result_opt['travel_time']}分")
            print(f"  ルートタイプ: {result_opt['route_type']}")
            if result_opt.get('train_lines'):
                print(f"  路線: {', '.join(result_opt['train_lines'])}")
            print(f"  料金: ¥{result_opt.get('fare', 'N/A')}")
            print(f"  処理時間: {elapsed_opt:.1f}秒")
        else:
            print(f"❌ 失敗: {result_opt['error']}")
            
    finally:
        scraper_opt.close()
    
    print("\n少し待機...")
    time.sleep(5)
    
    # 2. 通常版でテスト（比較用）
    print("\n【通常版v5】")
    print("-"*40)
    
    scraper_normal = GoogleMapsScraperV5()
    
    try:
        scraper_normal.setup_driver()
        
        start_time = time.time()
        result_normal = scraper_normal.scrape_route(
            origin,
            destination,
            dest_name,
            arrival_time
        )
        elapsed_normal = time.time() - start_time
        
        if result_normal['success']:
            print(f"✅ 成功")
            print(f"  所要時間: {result_normal['travel_time']}分")
            print(f"  ルートタイプ: {result_normal['route_type']}")
            if result_normal.get('train_lines'):
                print(f"  路線: {', '.join(result_normal['train_lines'])}")
            print(f"  料金: ¥{result_normal.get('fare', 'N/A')}")
            print(f"  処理時間: {elapsed_normal:.1f}秒")
        else:
            print(f"❌ 失敗: {result_normal['error']}")
            
    finally:
        scraper_normal.close()
    
    # 3. 結果比較
    print("\n" + "="*80)
    print("📊 比較結果")
    print("="*80)
    
    if 'elapsed_opt' in locals() and 'elapsed_normal' in locals():
        speedup = elapsed_normal / elapsed_opt
        reduction = elapsed_normal - elapsed_opt
        reduction_pct = (reduction / elapsed_normal) * 100
        
        print(f"\n処理時間:")
        print(f"  通常版: {elapsed_normal:.1f}秒")
        print(f"  最適化版: {elapsed_opt:.1f}秒")
        print(f"  短縮: {reduction:.1f}秒 ({reduction_pct:.0f}%削減)")
        print(f"  高速化: {speedup:.1f}倍")
        
        # データの一致確認
        if 'result_opt' in locals() and 'result_normal' in locals():
            if result_opt['success'] and result_normal['success']:
                print(f"\nデータ精度:")
                print(f"  所要時間一致: {result_opt['travel_time'] == result_normal['travel_time']}")
                print(f"  ルートタイプ一致: {result_opt['route_type'] == result_normal['route_type']}")
                
                if result_opt['travel_time'] == result_normal['travel_time']:
                    print("  ✅ 精度維持：データが完全一致")
                else:
                    print(f"  ⚠️ 差異あり：最適化版{result_opt['travel_time']}分 vs 通常版{result_normal['travel_time']}分")

if __name__ == "__main__":
    test_waseda_comparison()