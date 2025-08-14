#!/usr/bin/env python3
"""
Google Maps スクレイピングのデバッグスクリプト
実際のHTML構造を確認する
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    return driver

def debug_scraping():
    driver = setup_driver()
    
    try:
        # テストURL
        origin = "東京都千代田区神田須田町1-20-1"
        destination = "東京都中央区日本橋2-5-1"
        url = f"https://www.google.com/maps/dir/{origin}/{destination}/?travelmode=transit"
        
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # ページが読み込まれるまで待機
        time.sleep(10)
        
        print("\n=== デバッグ情報 ===")
        
        # 1. ルートコンテナを探す
        print("\n1. ルートコンテナの検索:")
        selectors = [
            '[data-trip-index="0"]',
            'div[role="button"][data-trip-index="0"]',
            'div.Ylt4Kd',
            'div[jsaction*="directionsSearchbox"]',
            'div[class*="directions-mode-group"]',
            'div[class*="section-directions"]'
        ]
        
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  ✓ Found {len(elements)} elements with selector: {selector}")
                print(f"    Text preview: {elements[0].text[:100]}...")
            else:
                print(f"  ✗ Not found: {selector}")
        
        # 2. 時間情報を探す
        print("\n2. 時間情報の検索:")
        time_selectors = [
            'span[jsan*="分"]',
            'span[jstcache*="duration"]',
            'span[aria-label*="分"]',
            'div[class*="duration"]',
            'span:contains("分")'
        ]
        
        for selector in time_selectors:
            try:
                if ':contains' in selector:
                    # XPathを使用
                    elements = driver.find_elements(By.XPATH, "//span[contains(text(), '分')]")
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                if elements:
                    print(f"  ✓ Found {len(elements)} time elements with: {selector}")
                    for i, elem in enumerate(elements[:3]):
                        print(f"    [{i}] {elem.text}")
            except:
                pass
        
        # 3. ステップ情報を探す
        print("\n3. ルートステップの検索:")
        step_selectors = [
            'div.cYhGGe',
            'div[role="listitem"]',
            'div[class*="transit-step"]',
            'div[class*="directions-step"]',
            'div[class*="section-directions-trip"]'
        ]
        
        for selector in step_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  ✓ Found {len(elements)} steps with selector: {selector}")
                print(f"    First step: {elements[0].text[:100]}...")
        
        # 4. 駅名・路線名を探す
        print("\n4. 交通機関情報の検索:")
        # 実際のHTMLを出力
        print("\n実際のHTML構造（最初の1000文字）:")
        body = driver.find_element(By.TAG_NAME, 'body')
        print(body.get_attribute('innerHTML')[:1000])
        
        # スクリーンショットを保存
        driver.save_screenshot('/app/output/japandatascience.com/timeline-mapping/api/debug_screenshot.png')
        print("\nスクリーンショットを保存: debug_screenshot.png")
        
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_scraping()