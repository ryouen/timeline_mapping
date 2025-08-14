#!/usr/bin/env python3
"""
Google Maps時刻選択UIとの対話テスト
"""

import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote

def setup_driver(headless=True):
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja-JP')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    return driver

def interact_with_time_options(driver, departure_time):
    """時刻選択UIと対話を試みる"""
    
    result = {
        "success": False,
        "steps": [],
        "final_url": None,
        "time_selected": None
    }
    
    try:
        # Step 1: 「すぐに出発」ボタンまたは時刻表示を探してクリック
        time_button_selectors = [
            "span.uEubGf.NlVald",  # "すぐに出発"のテキスト要素
            "button[aria-label*='すぐに出発']",
            "button[aria-label*='出発時刻']",
            "button[aria-label*='Departure time']",
            "div.MlqQ3d.Hk4XGb",  # 時刻選択の親要素
            "span:contains('すぐ')",
            "button:contains('すぐ')"
        ]
        
        time_button_found = False
        for selector in time_button_selectors:
            try:
                if selector.startswith("span:contains") or selector.startswith("button:contains"):
                    # XPath for text content
                    xpath = f"//{selector.split(':')[0]}[contains(text(), '{selector.split('(')[1].split(')')[0][1:-1]}')]"
                    elements = driver.find_elements(By.XPATH, xpath)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    for elem in elements:
                        try:
                            # 親要素がクリック可能か確認
                            parent = elem.find_element(By.XPATH, "..")
                            if parent.tag_name in ['button', 'div']:
                                parent.click()
                            else:
                                elem.click()
                            
                            time.sleep(2)
                            result["steps"].append(f"時刻ボタンをクリック: {selector}")
                            time_button_found = True
                            break
                        except:
                            continue
                    
                    if time_button_found:
                        break
            except:
                continue
        
        if not time_button_found:
            # Step 2: オプションボタンを探す
            option_selectors = [
                "span:contains('オプション')",
                "button[aria-label*='オプション']",
                "button[aria-label*='Options']",
                "button.J45yZc",  # オプションボタンのクラス
                "span.google-symbols[aria-hidden='true']"  # アイコンボタン
            ]
            
            for selector in option_selectors:
                try:
                    if selector.startswith("span:contains"):
                        xpath = f"//span[contains(text(), 'オプション')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        elements[0].click()
                        time.sleep(2)
                        result["steps"].append(f"オプションボタンをクリック: {selector}")
                        break
                except:
                    continue
        
        # Step 3: 時刻選択のドロップダウンやモーダルを探す
        time.sleep(2)
        
        # スクリーンショットを撮る
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/interaction_after_click_{timestamp_str}.png"
        driver.save_screenshot(screenshot_path)
        result["screenshot_after_click"] = screenshot_path
        
        # 時刻選択UI要素を探す
        time_input_selectors = [
            "input[type='time']",
            "input[aria-label*='時刻']",
            "input[aria-label*='time']",
            "select[aria-label*='時']",
            "div[role='listbox']",
            "div[role='menu']",
            "button[aria-label*='出発']",
            "button[aria-label*='到着']"
        ]
        
        time_ui_found = False
        for selector in time_input_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                result["steps"].append(f"時刻選択UI発見: {selector} ({len(elements)}個)")
                time_ui_found = True
                
                # 時刻を設定してみる
                if elements[0].tag_name == 'input':
                    try:
                        elements[0].clear()
                        elements[0].send_keys(departure_time.strftime("%H:%M"))
                        result["steps"].append(f"時刻入力: {departure_time.strftime('%H:%M')}")
                    except:
                        pass
        
        # Step 4: 現在のURLを記録
        result["final_url"] = driver.current_url
        
        # Step 5: ページから時刻情報を読み取る
        time_displays = driver.find_elements(By.XPATH, "//*[contains(text(), '出発') or contains(text(), '到着')]")
        for display in time_displays[:5]:
            text = display.text
            if any(char in text for char in ['時', ':', 'AM', 'PM']):
                result["time_selected"] = text
                break
        
        result["success"] = time_ui_found
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    """メイン処理"""
    origin = "東京駅"
    destination = "渋谷駅"
    
    # 明日の朝8時を指定
    departure_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    print(f"時刻選択UIとの対話テスト開始")
    print(f"ルート: {origin} → {destination}")
    print(f"指定時刻: {departure_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    driver = setup_driver()
    
    try:
        # まず通常のURLでアクセス
        url = f"https://www.google.com/maps/dir/?api=1&origin={quote(origin)}&destination={quote(destination)}&travelmode=transit"
        
        print(f"\nURL: {url}")
        driver.get(url)
        
        # ページが完全に読み込まれるまで待つ
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-trip-index]")))
        time.sleep(5)
        
        # 初期スクリーンショット
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        initial_screenshot = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/interaction_initial_{timestamp_str}.png"
        driver.save_screenshot(initial_screenshot)
        
        # 時刻選択UIとの対話を試みる
        result = interact_with_time_options(driver, departure_time)
        
        # 結果を表示
        print("\n=== 対話結果 ===")
        print(f"成功: {result['success']}")
        print(f"実行したステップ:")
        for step in result['steps']:
            print(f"  - {step}")
        
        if result.get('time_selected'):
            print(f"選択された時刻: {result['time_selected']}")
        
        if result.get('final_url'):
            print(f"最終URL: {result['final_url']}")
        
        # 最終的なページソースを保存
        html_path = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/interaction_final_page.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        # 結果をJSONに保存
        output_path = "/app/output/japandatascience.com/timeline-mapping/api/test_interaction_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n結果を保存: {output_path}")
        
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        driver.quit()

if __name__ == '__main__':
    main()