#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクレイピングのデバッグ - スクリーンショットとHTML保存
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import os

def setup_driver():
    """Selenium WebDriverのセットアップ"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    driver.implicitly_wait(10)
    return driver

def debug_route_page():
    """ルートページをデバッグ"""
    
    driver = None
    try:
        driver = setup_driver()
        
        # テスト用のシンプルなルート
        origin = "東京都千代田区神田須田町1-20-1"
        destination = "東京都中央区日本橋２丁目５−１"
        
        # 明日の10時到着のタイムスタンプ
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
        timestamp = int(arrival_10am.timestamp())
        
        # 試すURL形式
        urls = [
            # 1. シンプルなルート
            f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}",
            
            # 2. 公共交通機関モード付き
            f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!3e3",
            
            # 3. 時刻指定付き（v3形式）
            f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!4m2!4m1!3e3!5m2!6e1!8j{timestamp}",
            
            # 4. より完全な形式
            f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!3m1!4b1!4m14!4m13!1m5!1m1!1s0x0:0x0!2m2!1d139.768563!2d35.6949994!1m5!1m1!1s0x0:0x0!2m2!1d139.7712416!2d35.6811282!3e3"
        ]
        
        debug_dir = "/app/output/japandatascience.com/timeline-mapping/api/debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        for i, url in enumerate(urls, 1):
            print(f"\n=== テスト {i}/4 ===")
            print(f"URL: {url[:100]}...")
            
            driver.get(url)
            time.sleep(5)  # ページ読み込み待機
            
            # 現在のURLを取得
            current_url = driver.current_url
            print(f"現在のURL: {current_url[:100]}...")
            
            # スクリーンショット保存
            screenshot_path = f"{debug_dir}/screenshot_{i}.png"
            driver.save_screenshot(screenshot_path)
            print(f"スクリーンショット保存: screenshot_{i}.png")
            
            # HTML保存
            html_path = f"{debug_dir}/page_{i}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"HTML保存: page_{i}.html")
            
            # ページ上の要素を確認
            try:
                # 公共交通機関ボタンを探す
                transit_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='公共交通機関' or @aria-label='Transit']")
                print(f"公共交通機関ボタン数: {len(transit_buttons)}")
                
                # 時刻設定要素を探す
                time_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '出発') or contains(text(), 'すぐに')]")
                print(f"時刻関連要素数: {len(time_elements)}")
                for elem in time_elements[:3]:  # 最初の3つだけ表示
                    print(f"  - {elem.text[:50]}")
                
                # ルート要素を探す
                route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
                print(f"ルート要素数: {len(route_elements)}")
                
                if route_elements:
                    # 最初のルートの情報を表示
                    first_route = route_elements[0].text
                    lines = first_route.split('\n')[:5]  # 最初の5行
                    print("最初のルートの内容:")
                    for line in lines:
                        print(f"  {line}")
                        
            except Exception as e:
                print(f"要素確認エラー: {e}")
        
        # 結果ファイルのパスを表示
        print("\n=== デバッグファイル保存完了 ===")
        print(f"保存先: {debug_dir}")
        print("ファイル:")
        for i in range(1, 5):
            print(f"  - screenshot_{i}.png")
            print(f"  - page_{i}.html")
            
    except Exception as e:
        print(f"エラー: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("\nSeleniumセッション終了")

if __name__ == "__main__":
    debug_route_page()