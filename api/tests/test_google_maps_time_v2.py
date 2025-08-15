#!/usr/bin/env python3
"""
Google Maps時刻指定のテストスクリプト v2
より詳細な調査とページ要素の分析
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

def analyze_page_structure(driver, name):
    """ページ構造を詳細に分析"""
    analysis = {
        "name": name,
        "elements_found": {},
        "time_related_texts": [],
        "buttons_found": [],
        "inputs_found": []
    }
    
    # 時刻関連のテキストを探す
    time_keywords = ['時', '分', 'AM', 'PM', '出発', '到着', 'depart', 'arrive', '時刻', 'time']
    all_text_elements = driver.find_elements(By.XPATH, "//*[text()]")
    
    for elem in all_text_elements[:100]:  # 最初の100要素のみ
        try:
            text = elem.text.strip()
            if text and any(keyword in text for keyword in time_keywords):
                analysis["time_related_texts"].append({
                    "text": text[:100],
                    "tag": elem.tag_name,
                    "class": elem.get_attribute("class") or ""
                })
        except:
            pass
    
    # すべてのボタンを探す
    buttons = driver.find_elements(By.XPATH, "//button | //div[@role='button'] | //span[@role='button']")
    for btn in buttons[:20]:  # 最初の20個
        try:
            text = btn.text.strip()
            aria_label = btn.get_attribute("aria-label") or ""
            if text or aria_label:
                analysis["buttons_found"].append({
                    "text": text[:50],
                    "aria-label": aria_label[:50],
                    "class": btn.get_attribute("class") or ""
                })
        except:
            pass
    
    # すべての入力フィールドを探す
    inputs = driver.find_elements(By.XPATH, "//input | //select")
    for inp in inputs[:10]:  # 最初の10個
        try:
            analysis["inputs_found"].append({
                "type": inp.get_attribute("type") or "text",
                "placeholder": inp.get_attribute("placeholder") or "",
                "aria-label": inp.get_attribute("aria-label") or "",
                "value": inp.get_attribute("value") or "",
                "class": inp.get_attribute("class") or ""
            })
        except:
            pass
    
    # 特定の重要な要素を探す
    important_selectors = {
        "transit_options": "div[aria-label*='transit'] button",
        "time_options": "button[aria-label*='time'], button[aria-label*='時刻']",
        "departure_time": "span[class*='depart'], span[class*='出発']",
        "route_panel": "div[role='main'] div[data-trip-index]",
        "options_button": "button[aria-label*='オプション'], button[aria-label*='Options']"
    }
    
    for key, selector in important_selectors.items():
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                analysis["elements_found"][key] = f"{len(elements)} found"
        except:
            pass
    
    return analysis

def test_url_with_interaction(url, name, departure_time):
    """URLをテストし、ページとの対話を試みる"""
    driver = setup_driver()
    result = {
        "name": name,
        "url": url,
        "timestamp": int(departure_time.timestamp()),
        "stages": {}
    }
    
    try:
        # ステージ1: 初期ロード
        print(f"\n  ステージ1: ページロード中...")
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        
        # 初期ロードを待つ
        time.sleep(5)
        
        # ページ分析
        result["stages"]["initial_load"] = analyze_page_structure(driver, f"{name}_initial")
        
        # スクリーンショット
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_name = name.replace('（', '_').replace('）', '_').replace(' ', '_')
        screenshot_path = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/v2_{screenshot_name}_1_initial_{timestamp_str}.png"
        driver.save_screenshot(screenshot_path)
        result["stages"]["initial_load"]["screenshot"] = screenshot_path
        
        # ステージ2: ルートパネルをクリック
        print(f"  ステージ2: ルートパネルを探す...")
        try:
            # ルートパネルを探してクリック
            route_elements = driver.find_elements(By.CSS_SELECTOR, "[data-trip-index='0']")
            if route_elements:
                route_elements[0].click()
                time.sleep(3)
                
                result["stages"]["after_route_click"] = analyze_page_structure(driver, f"{name}_after_click")
                
                screenshot_path2 = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/v2_{screenshot_name}_2_clicked_{timestamp_str}.png"
                driver.save_screenshot(screenshot_path2)
                result["stages"]["after_route_click"]["screenshot"] = screenshot_path2
        except Exception as e:
            result["stages"]["after_route_click"] = {"error": str(e)}
        
        # ステージ3: オプションボタンを探す
        print(f"  ステージ3: オプションボタンを探す...")
        try:
            # 様々なオプションボタンを試す
            option_selectors = [
                "button[aria-label*='その他のオプション']",
                "button[aria-label*='More options']",
                "button[aria-label*='オプション']",
                "button[jsaction*='options']",
                "span.material-icons-extended:contains('more_vert')",
                "button svg"  # SVGアイコンを含むボタン
            ]
            
            for selector in option_selectors:
                try:
                    option_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    if option_buttons:
                        option_buttons[0].click()
                        time.sleep(2)
                        
                        result["stages"]["after_options_click"] = analyze_page_structure(driver, f"{name}_options")
                        
                        screenshot_path3 = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/v2_{screenshot_name}_3_options_{timestamp_str}.png"
                        driver.save_screenshot(screenshot_path3)
                        result["stages"]["after_options_click"]["screenshot"] = screenshot_path3
                        break
                except:
                    continue
        except Exception as e:
            result["stages"]["after_options_click"] = {"error": str(e)}
        
        # ページ全体のHTMLを保存（デバッグ用）
        html_path = f"/app/output/japandatascience.com/timeline-mapping/api/test_screenshots/v2_{screenshot_name}_full.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        result["html_saved"] = html_path
        
    except Exception as e:
        result["error"] = str(e)
    finally:
        driver.quit()
    
    return result

def main():
    """メイン処理"""
    # テスト用のルート
    origin = "東京駅"
    destination = "渋谷駅"
    
    # 明日の朝8時を指定
    departure_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    print(f"詳細テスト開始: {origin} → {destination}")
    print(f"指定時刻: {departure_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"タイムスタンプ: {int(departure_time.timestamp())}")
    
    # スクリーンショット保存用ディレクトリを作成
    import os
    os.makedirs("/app/output/japandatascience.com/timeline-mapping/api/test_screenshots", exist_ok=True)
    
    # テストするURL（最も有望なもののみ）
    test_cases = [
        {
            "name": "API版_departure_time",
            "url": f"https://www.google.com/maps/dir/?api=1&origin={quote(origin)}&destination={quote(destination)}&travelmode=transit&departure_time={int(departure_time.timestamp())}"
        },
        {
            "name": "arrival_time版",
            "url": f"https://www.google.com/maps/dir/?api=1&origin={quote(origin)}&destination={quote(destination)}&travelmode=transit&arrival_time={int(departure_time.timestamp())}"
        }
    ]
    
    results = []
    for test_case in test_cases:
        print(f"\n=== {test_case['name']} のテスト ===")
        result = test_url_with_interaction(test_case["url"], test_case["name"], departure_time)
        results.append(result)
    
    # 結果を保存
    output_path = "/app/output/japandatascience.com/timeline-mapping/api/test_results_time_format_v2.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細な結果を保存: {output_path}")
    
    # サマリーを表示
    print("\n=== 分析サマリー ===")
    for result in results:
        print(f"\n{result['name']}:")
        for stage_name, stage_data in result.get("stages", {}).items():
            if isinstance(stage_data, dict) and "time_related_texts" in stage_data:
                print(f"  {stage_name}:")
                print(f"    時刻関連テキスト: {len(stage_data['time_related_texts'])}個")
                for text_info in stage_data['time_related_texts'][:3]:  # 最初の3個
                    print(f"      - {text_info['text']}")

if __name__ == '__main__':
    main()