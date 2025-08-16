#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ページロードのデバッグ - URLアクセス後のHTML確認
"""

import sys
import time
from datetime import datetime, timedelta
import pytz

sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

print("WebDriver起動中...")
scraper = GoogleMapsScraper()
scraper.setup_driver()

# テストURL（先ほど確認したもの）
url = "https://www.google.com/maps/dir/%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA%E7%A5%9E%E7%94%B0%E9%A0%88%E7%94%B0%E7%94%BA1-20-1/%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA%E4%B8%B8%E3%81%AE%E5%86%851%E4%B8%81%E7%9B%AE/data=!4m18!4m17!1m5!1m1!1sChIJ2RxO9gKMGGARSvjnp3ocfJg!2m2!1d139.7711!2d35.6950!1m5!1m1!1sChIJLdASefmLGGARF3Ez6A4i4Q4!2m2!1d139.7676!2d35.6812!2m3!6e1!7e2!8j1755511200!3e3"

print(f"\nURL長さ: {len(url)}文字")
print("\nページアクセス開始...")
print(f"開始時刻: {datetime.now().strftime('%H:%M:%S')}")

try:
    # ページを開く
    scraper.driver.get(url)
    print(f"get()完了: {datetime.now().strftime('%H:%M:%S')}")
    
    # 5秒待つ
    print("5秒待機中...")
    time.sleep(5)
    print(f"待機完了: {datetime.now().strftime('%H:%M:%S')}")
    
    # 現在のURL確認
    current_url = scraper.driver.current_url
    print(f"\n現在のURL（最初の100文字）:")
    print(current_url[:100] + "...")
    
    # ページタイトル
    print(f"\nページタイトル: {scraper.driver.title}")
    
    # ルート要素の存在確認
    print("\n要素の存在確認:")
    
    # 1. data-trip-index要素（ルート）
    try:
        route_elements = scraper.driver.find_elements_by_xpath("//div[@data-trip-index]")
        print(f"  ✓ ルート要素: {len(route_elements)}個見つかりました")
    except:
        print(f"  ✗ ルート要素が見つかりません")
    
    # 2. 公共交通機関ボタン
    try:
        transit_btn = scraper.driver.find_element_by_xpath("//button[@aria-label='公共交通機関']")
        print(f"  ✓ 公共交通機関ボタン: 存在")
    except:
        try:
            transit_btn = scraper.driver.find_element_by_xpath("//button[@data-travel-mode='3']")
            print(f"  ✓ 公共交通機関ボタン（別形式）: 存在")
        except:
            print(f"  ✗ 公共交通機関ボタンが見つかりません")
    
    # 3. HTMLの一部を確認
    print("\nページソースの最初の500文字:")
    page_source = scraper.driver.page_source
    print(page_source[:500])
    
    # 4. エラーメッセージの確認
    if "エラー" in page_source or "error" in page_source.lower():
        print("\n⚠️ エラーメッセージが含まれている可能性があります")
    
    # 5. Place IDが認識されているか
    if "ChIJ2RxO9gKMGGARSvjnp3ocfJg" in page_source:
        print("\n✓ ルフォンプログレのPlace IDが認識されています")
    if "ChIJLdASefmLGGARF3Ez6A4i4Q4" in page_source:
        print("✓ 東京駅のPlace IDが認識されています")
    
except Exception as e:
    print(f"\n❌ エラー発生: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print(f"\n終了時刻: {datetime.now().strftime('%H:%M:%S')}")
    scraper.close()