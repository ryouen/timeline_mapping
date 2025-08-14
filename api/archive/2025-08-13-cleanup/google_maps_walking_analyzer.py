#!/usr/bin/env python3
"""
Google Maps 徒歩ルート解析ツール
徒歩のみのルートでHTMLを取得し、詳細情報を抽出
"""
import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import sys

def analyze_walking_route(origin, destination):
    """徒歩ルートのHTML解析"""
    
    # Selenium設定
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    
    # リモートWebDriver接続
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    try:
        # Google Maps URLを構築（徒歩モード）
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origin}/{destination}/data=!4m2!4m1!3e2"  # 3e2は徒歩モード
        
        print(f"URL: {url}")
        driver.get(url)
        
        # ページ読み込み待機
        wait = WebDriverWait(driver, 20)
        
        # 複数のルートオプションを探す
        time.sleep(3)  # 初期読み込み待機
        
        # すべてのルートオプションをクリックしてHTMLを保存
        route_data = []
        
        # ルートオプションを探す
        route_options = driver.find_elements(By.CSS_SELECTOR, '[data-trip-index]')
        print(f"見つかったルートオプション数: {len(route_options)}")
        
        for i, option in enumerate(route_options[:3]):  # 最大3つのルートを取得
            try:
                # オプションをクリック
                ActionChains(driver).move_to_element(option).click().perform()
                time.sleep(2)  # クリック後の読み込み待機
                
                # directions panelを取得
                panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
                
                # HTMLを保存
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                html_path = f'/app/output/japandatascience.com/timeline-mapping/data/walking_route_{i}_{timestamp}.html'
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"HTMLを保存: {html_path}")
                
                # ルート情報を抽出
                route_info = extract_walking_info(panel)
                route_info['route_index'] = i
                route_info['html_path'] = html_path
                route_data.append(route_info)
                
            except Exception as e:
                print(f"ルート{i}の処理エラー: {str(e)}")
                
        # スクリーンショット保存
        screenshot_path = f'/app/output/japandatascience.com/timeline-mapping/data/walking_routes_{timestamp}.png'
        driver.save_screenshot(screenshot_path)
        print(f"スクリーンショット保存: {screenshot_path}")
        
        return {
            "status": "success",
            "routes": route_data,
            "screenshot": screenshot_path
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        driver.quit()

def extract_walking_info(panel):
    """徒歩ルート情報の抽出"""
    try:
        text = panel.text
        lines = text.split('\n')
        
        # デバッグ用にテキストを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = f'/app/output/japandatascience.com/timeline-mapping/data/debug_walking_text_{timestamp}.txt'
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 時間と距離を抽出
        time_pattern = r'(\d+)\s*分'
        distance_pattern = r'(\d+\.?\d*)\s*km'
        
        total_time = None
        distance = None
        
        for line in lines[:10]:  # 最初の10行をチェック
            time_match = re.search(time_pattern, line)
            if time_match and not total_time:
                total_time = int(time_match.group(1))
                
            dist_match = re.search(distance_pattern, line)
            if dist_match and not distance:
                distance = float(dist_match.group(1))
        
        # 詳細な徒歩指示を抽出
        instructions = []
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['向かう', '進む', '曲がる', '歩く', '渡る']):
                instructions.append({
                    'step': len(instructions) + 1,
                    'instruction': line,
                    'line_number': i
                })
        
        return {
            'total_time': total_time,
            'distance': distance,
            'instructions': instructions[:10],  # 最初の10個の指示
            'debug_file': debug_path
        }
        
    except Exception as e:
        return {
            'error': str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: python google_maps_walking_analyzer.py <出発地> <目的地>")
        sys.exit(1)
        
    origin = sys.argv[1]
    destination = sys.argv[2]
    
    result = analyze_walking_route(origin, destination)
    print(json.dumps(result, ensure_ascii=False, indent=2))