#!/usr/bin/env python3
"""
Google Maps 徒歩ルート最終版
徒歩のみのルートを適切な形式で取得
"""
import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

def get_walking_route(origin, destination):
    """徒歩ルートの取得"""
    
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
        
        driver.get(url)
        
        # ページ読み込み待機
        wait = WebDriverWait(driver, 20)
        time.sleep(3)  # 初期読み込み待機
        
        # メインパネルを取得
        panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
        text = panel.text
        
        # デバッグ用にテキストを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = f'/app/output/japandatascience.com/timeline-mapping/data/debug_walking_{timestamp}.txt'
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 時間と距離を抽出
        lines = text.split('\n')
        time_pattern = r'(\d+)\s*分'
        distance_pattern = r'(\d+\.?\d*)\s*km|(\d+)\s*m'
        
        total_time = None
        distance = None
        
        for line in lines[:10]:  # 最初の10行をチェック
            time_match = re.search(time_pattern, line)
            if time_match and not total_time:
                total_time = int(time_match.group(1))
                
            dist_match = re.search(distance_pattern, line)
            if dist_match and not distance:
                if dist_match.group(1):  # km
                    distance = float(dist_match.group(1)) * 1000
                else:  # m
                    distance = int(dist_match.group(2))
        
        # 結果を返す
        if total_time:
            return {
                "status": "success",
                "search_info": {
                    "type": "walking",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "route": {
                    "total_time": total_time,
                    "details": {
                        "walk_to_station": 0,  # 徒歩のみなので0
                        "station_used": "",
                        "trains": [],  # 電車は使用しない
                        "walk_from_station": total_time,  # 全て徒歩時間
                        "distance_meters": distance,
                        "route_type": "walking_only"
                    }
                }
            }
        else:
            return {
                "status": "error",
                "message": "徒歩時間を取得できませんでした"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: python google_maps_walking_final.py <出発地> <目的地>")
        sys.exit(1)
        
    origin = sys.argv[1]
    destination = sys.argv[2]
    
    result = get_walking_route(origin, destination)
    print(json.dumps(result, ensure_ascii=False, indent=2))