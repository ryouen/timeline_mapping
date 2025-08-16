#!/usr/bin/env python3
"""
Google Maps スクレイピングの詳細デバッグスクリプト
実際のHTML構造とAPIパラメータを確認する
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys
import json

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    return driver

def debug_scraping():
    driver = setup_driver()
    
    try:
        # テストケース
        origin = "東京都千代田区神田須田町1-20-1 ルフォンプログレ神田プレミア"
        destination = "東京都中央区日本橋2-5-1 髙島屋三井ビルディング"
        
        print("=== Google Maps デバッグ詳細分析 ===")
        print(f"出発: {origin}")
        print(f"到着: {destination}")
        print("")
        
        # 1. 古い形式のURL（動作確認）
        print("1. 古い形式のURLテスト:")
        old_url = f"https://www.google.com/maps/dir/{origin}/{destination}/?travelmode=transit"
        driver.get(old_url)
        time.sleep(5)
        print(f"  URL: {old_url}")
        print(f"  最終URL: {driver.current_url}")
        print(f"  transitモード: {'travelmode=transit' in driver.current_url}")
        driver.save_screenshot('/app/output/japandatascience.com/timeline-mapping/api/debug_screenshots/old_format.png')
        
        # 2. 新しいAPI形式のURL
        print("\n2. 新しいAPI v1形式のURLテスト:")
        from urllib.parse import quote
        encoded_origin = quote(origin)
        encoded_destination = quote(destination)
        new_url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_destination}&travelmode=transit"
        driver.get(new_url)
        time.sleep(5)
        print(f"  URL: {new_url}")
        print(f"  最終URL: {driver.current_url}")
        print(f"  transitモード: {'travelmode=transit' in driver.current_url}")
        driver.save_screenshot('/app/output/japandatascience.com/timeline-mapping/api/debug_screenshots/new_format.png')
        
        # 3. モードボタンの検索
        print("\n3. 交通手段ボタンの検索:")
        mode_selectors = [
            ("data-value", "//button[@data-value='transit']"),
            ("aria-label Transit", "//button[contains(@aria-label, 'Transit')]"),
            ("aria-label 公共交通機関", "//button[contains(@aria-label, '公共交通機関')]"),
            ("aria-label 電車", "//button[contains(@aria-label, '電車')]"),
            ("travel-mode class", "//div[contains(@class, 'travel-mode')]"),
            ("img transit", "//img[contains(@src, 'transit')]"),
            ("role=radio transit", "//div[@role='radio' and contains(., 'Transit')]"),
            ("data-travel-mode", "//button[@data-travel-mode='transit']")
        ]
        
        for name, selector in mode_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"  ✓ {name}: {len(elements)}個見つかりました")
                    for i, elem in enumerate(elements[:2]):
                        print(f"    [{i}] visible={elem.is_displayed()}, enabled={elem.is_enabled()}")
                        if elem.get_attribute('aria-label'):
                            print(f"        aria-label: {elem.get_attribute('aria-label')}")
                else:
                    print(f"  ✗ {name}: 見つかりません")
            except Exception as e:
                print(f"  ✗ {name}: エラー - {str(e)[:50]}")
        
        # 4. ルート情報の検索
        print("\n4. ルート情報の検索:")
        route_selectors = [
            ("trip-index=0", "//div[@data-trip-index='0']"),
            ("section-directions", "//div[contains(@class, 'section-directions')]"),
            ("directions-mode-group", "//div[contains(@class, 'directions-mode-group')]"),
            ("transit-container", "//div[contains(@class, 'transit-container')]"),
            ("route-preview", "//div[contains(@class, 'route-preview')]")
        ]
        
        for name, selector in route_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                print(f"  ✓ {name}: {len(elements)}個")
                text = elements[0].text[:100].replace('\n', ' ')
                print(f"    テキスト: {text}...")
        
        # 5. 時間情報の検索
        print("\n5. 時間情報の検索:")
        time_patterns = [
            "//span[contains(text(), '分')]",
            "//div[contains(text(), '分')]",
            "//span[contains(@aria-label, '分')]",
            "//div[contains(@class, 'duration')]"
        ]
        
        for pattern in time_patterns:
            elements = driver.find_elements(By.XPATH, pattern)
            if elements:
                print(f"  ✓ {pattern}: {len(elements)}個")
                for i, elem in enumerate(elements[:3]):
                    print(f"    [{i}] {elem.text}")
        
        # 6. HTML構造の出力
        print("\n6. ページのHTML構造（最初の2000文字）:")
        body = driver.find_element(By.TAG_NAME, 'body')
        html = body.get_attribute('innerHTML')[:2000]
        print(html)
        
        # 7. JavaScript実行でのデータ取得
        print("\n7. JavaScript実行でのデータ取得:")
        try:
            # Google Maps内部データの取得を試みる
            result = driver.execute_script("""
                // 交通手段モードの取得
                var mode = document.querySelector('[data-travel-mode="transit"]');
                var modeInfo = mode ? {
                    'found': true,
                    'class': mode.className,
                    'aria-label': mode.getAttribute('aria-label')
                } : {'found': false};
                
                // ルート情報の取得
                var routes = document.querySelectorAll('[data-trip-index]');
                var routeInfo = [];
                for (var i = 0; i < Math.min(routes.length, 3); i++) {
                    routeInfo.push({
                        'index': routes[i].getAttribute('data-trip-index'),
                        'text': routes[i].innerText.substring(0, 100)
                    });
                }
                
                return {
                    'url': window.location.href,
                    'mode': modeInfo,
                    'routes': routeInfo
                };
            """)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"JavaScriptエラー: {e}")
        
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_scraping()