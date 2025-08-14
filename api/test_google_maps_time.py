#!/usr/bin/env python3
"""
Google Maps時刻指定のテストスクリプト
異なるURL形式での動作を検証
"""

import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote

def setup_driver():
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    return driver

def test_url_formats(origin, destination, departure_time):
    """異なるURL形式をテスト"""
    
    # タイムスタンプを秒単位で計算
    timestamp = int(departure_time.timestamp())
    
    # テストするURL形式
    test_urls = {
        "現在の形式（data=）": f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!3m1!4b1!4m2!4m1!3e3",
        
        "アプローチA（departure_time）": f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/?travelmode=transit&departure_time={timestamp}",
        
        "アプローチA（API版）": f"https://www.google.com/maps/dir/?api=1&origin={quote(origin)}&destination={quote(destination)}&travelmode=transit&departure_time={timestamp}",
        
        "アプローチB（data=時刻付き）": f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!3e3!6e1!8j{timestamp}",
    }
    
    results = {}
    driver = setup_driver()
    
    try:
        for name, url in test_urls.items():
            print(f"\n=== {name} のテスト ===")
            print(f"URL: {url}")
            
            driver.get(url)
            wait = WebDriverWait(driver, 30)
            
            # ページが読み込まれるまで待機
            time.sleep(5)
            
            result = {
                "url": url,
                "時刻選択UI": "未検出",
                "出発時刻表示": "未検出",
                "エラー": None
            }
            
            try:
                # 時刻選択のUIを探す
                time_selectors = [
                    'input[aria-label*="出発時刻"]',
                    'input[aria-label*="Departure time"]',
                    'button[aria-label*="出発時刻"]',
                    'button[aria-label*="Departure time"]',
                    'div[data-value*="departure"]',
                    'div.LfUqke',  # 時刻選択ドロップダウン
                    'span.HlZEkd',  # 時刻表示
                ]
                
                for selector in time_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        result["時刻選択UI"] = f"検出: {selector}"
                        break
                
                # 現在選択されている時刻を探す
                time_display_selectors = [
                    'span.HlZEkd',
                    'div[jstcache*="departureTime"]',
                    'span[jsan*="時"]',
                ]
                
                for selector in time_display_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text
                        if any(char in text for char in ['時', ':', 'AM', 'PM']):
                            result["出発時刻表示"] = text
                            break
                
                # ルート情報があるか確認
                route_found = False
                route_selectors = [
                    '[data-trip-index]',
                    'div[role="button"][data-trip-index="0"]',
                    'div.Ylt4Kd',
                ]
                
                for selector in route_selectors:
                    if driver.find_elements(By.CSS_SELECTOR, selector):
                        route_found = True
                        break
                
                result["ルート表示"] = "あり" if route_found else "なし"
                
                # スクリーンショットを保存
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_name = name.replace('（', '_').replace('）', '_').replace(' ', '_')
                screenshot_path = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/test_{screenshot_name}_{timestamp_str}.png"
                driver.save_screenshot(screenshot_path)
                result["スクリーンショット"] = screenshot_path
                
            except Exception as e:
                result["エラー"] = str(e)
            
            results[name] = result
            
            # ページのHTMLも一部保存（デバッグ用）
            try:
                page_source = driver.page_source[:1000]
                result["HTML冒頭"] = page_source
            except:
                pass
    
    finally:
        driver.quit()
    
    return results

def main():
    """メイン処理"""
    # テスト用のルート
    origin = "東京駅"
    destination = "渋谷駅"
    
    # 明日の朝8時を指定
    departure_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    print(f"テスト開始: {origin} → {destination}")
    print(f"指定時刻: {departure_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"タイムスタンプ: {int(departure_time.timestamp())}")
    
    # スクリーンショット保存用ディレクトリを作成
    import os
    os.makedirs("/app/output/japandatascience.com/timeline-mapping/api/test_screenshots", exist_ok=True)
    
    results = test_url_formats(origin, destination, departure_time)
    
    # 結果を表示
    print("\n\n=== テスト結果まとめ ===")
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  時刻選択UI: {result['時刻選択UI']}")
        print(f"  出発時刻表示: {result['出発時刻表示']}")
        print(f"  ルート表示: {result.get('ルート表示', '不明')}")
        if result['エラー']:
            print(f"  エラー: {result['エラー']}")
    
    # 結果をJSONファイルに保存
    output_path = "/app/output/japandatascience.com/timeline-mapping/api/test_results_time_format.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細な結果を保存: {output_path}")

if __name__ == '__main__':
    main()