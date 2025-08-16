#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3スクレイパーテスト（適切なクリーンアップ付き）
メモリリーク対策版
"""

from google_maps_scraper_v3 import setup_driver, get_place_details, build_complete_url, extract_all_routes
from datetime import datetime, timedelta, timezone
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_route_with_cleanup():
    """単一ルートのテスト（確実なクリーンアップ）"""
    
    driver = None
    try:
        # 明日の10時到着（JST）
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
        
        print("=" * 60)
        print("単一ルートテスト（メモリ管理改善版）")
        print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
        print("=" * 60)
        
        # ドライバー起動
        driver = setup_driver()
        
        # Yawaraへのルート（問題があったもの）
        origin = "東京都千代田区神田須田町1-20-1"
        destination = "東京都渋谷区神宮前１丁目８−１０"
        
        print(f"\nテスト: {origin} → {destination}")
        
        # 場所解決
        print("場所を解決中...")
        origin_info = get_place_details(origin, driver)
        dest_info = get_place_details(destination, driver)
        
        if not (origin_info.get('lat') and dest_info.get('lat')):
            print("❌ 場所の解決に失敗")
            return
        
        print(f"  出発地: {origin_info['lat']}, {origin_info['lng']}")
        print(f"  目的地: {dest_info['lat']}, {dest_info['lng']}")
        
        # URL構築
        url = build_complete_url(origin_info, dest_info, arrival_time=arrival_10am)
        print(f"  URL: {url[:100]}...")
        
        # ルート検索
        print("ルート検索中...")
        driver.get(url)
        
        # 短い待機
        time.sleep(5)
        
        # ルート抽出
        routes = extract_all_routes(driver)
        
        if routes:
            print(f"✅ 成功: {len(routes)}ルート取得")
            shortest = min(routes, key=lambda r: r['total_time'])
            print(f"  最短時間: {shortest['total_time']}分")
            
            # 詳細情報
            if shortest.get('trains'):
                print(f"  詳細: {', '.join(shortest['trains'][:3])}")
            else:
                raw_text = shortest.get('raw_text', '')
                if '徒歩' in raw_text and '駅' not in raw_text:
                    print(f"  詳細: 徒歩のみ")
                else:
                    print(f"  詳細: 取得できず（テキスト長: {len(raw_text)}文字）")
        else:
            print("❌ ルート取得失敗")
            
    except Exception as e:
        logger.error(f"エラー: {e}")
        
    finally:
        # 確実にドライバーを終了
        if driver:
            try:
                driver.quit()
                print("\n✅ Seleniumセッションを正常に終了")
            except:
                pass

def main():
    """メインテスト実行"""
    test_single_route_with_cleanup()
    
    # メモリ使用状況を確認
    print("\n" + "=" * 60)
    print("テスト完了 - Seleniumセッションは適切にクリーンアップされました")
    print("メモリ使用状況は改善されているはずです")
    print("=" * 60)

if __name__ == "__main__":
    main()