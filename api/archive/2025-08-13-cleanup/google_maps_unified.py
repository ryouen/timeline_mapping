#!/usr/bin/env python3
"""
Google Maps 統合版スクレイピング
電車ルートと徒歩ルートの両方に対応
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

def get_route(origin, destination, arrival_time=None):
    """ルート取得（電車優先、徒歩フォールバック）"""
    
    # まず電車ルートを試す
    transit_result = get_transit_route(origin, destination, arrival_time)
    
    if transit_result["status"] == "success":
        return transit_result
    
    # 電車ルートが取得できない場合は徒歩ルートを試す
    print("電車ルートが見つからないため、徒歩ルートを検索します...")
    return get_walking_route(origin, destination)

def get_transit_route(origin, destination, arrival_time=None):
    """電車ルートの取得"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    try:
        # URL構築（電車優先）
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origin}/{destination}/"
        
        if arrival_time:
            # 到着時刻指定の場合
            url += f"@35.6762,139.6503,12z/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{int(arrival_time.timestamp())}!3e0"
        else:
            url += "data=!3m1!4b1!4m2!4m1!3e0"  # 3e0は電車優先
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        # directions panelを探す
        panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
        text = panel.text
        
        # 時刻と駅名を抽出
        lines = text.split('\n')
        
        # 電車が含まれているか確認
        if not any('電車' in line or '地下鉄' in line or 'JR' in line for line in lines):
            return {"status": "error", "message": "電車ルートが見つかりません"}
        
        # 時刻ベースで解析
        route_data = parse_transit_route(lines)
        
        if route_data:
            # 待ち時間の調整（最初の駅での待ち時間は0にする）
            if route_data.get("trains") and len(route_data["trains"]) > 0:
                # 最初の電車の待ち時間を0に
                if "wait_time" in route_data["trains"][0]:
                    route_data["trains"][0]["wait_time"] = 0
            
            return {
                "status": "success",
                "search_info": {
                    "type": "transit",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "route": {
                    "total_time": route_data["total_time"],
                    "details": route_data
                }
            }
        else:
            return {"status": "error", "message": "ルート解析に失敗しました"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

def get_walking_route(origin, destination):
    """徒歩ルートの取得"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    try:
        # URL構築（徒歩モード）
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origin}/{destination}/data=!4m2!4m1!3e2"  # 3e2は徒歩
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
        text = panel.text
        lines = text.split('\n')
        
        # 時間と距離を抽出
        time_pattern = r'(\d+)\s*分'
        distance_pattern = r'(\d+\.?\d*)\s*km|(\d+)\s*m'
        
        total_time = None
        distance = None
        
        for line in lines[:10]:
            time_match = re.search(time_pattern, line)
            if time_match and not total_time:
                total_time = int(time_match.group(1))
                
            dist_match = re.search(distance_pattern, line)
            if dist_match and not distance:
                if dist_match.group(1):  # km
                    distance = float(dist_match.group(1)) * 1000
                else:  # m
                    distance = int(dist_match.group(2))
        
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
                        "walk_to_station": 0,
                        "station_used": "",
                        "trains": [],
                        "walk_from_station": total_time,
                        "distance_meters": distance,
                        "route_type": "walking_only"
                    }
                }
            }
        else:
            return {"status": "error", "message": "徒歩時間を取得できませんでした"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

def parse_transit_route(lines):
    """電車ルートの解析（簡略版）"""
    # ここは既存のgoogle_maps_transit_final.pyのロジックを使用
    # 簡略化のため基本的な解析のみ
    
    total_time = None
    walk_to_station = 3  # デフォルト値
    walk_from_station = 3  # デフォルト値
    
    # 総時間を探す
    for line in lines[:10]:
        time_match = re.search(r'(\d+)\s*分', line)
        if time_match:
            total_time = int(time_match.group(1))
            break
    
    if not total_time:
        return None
    
    # 簡略化した電車情報
    trains = [{
        "line": "路線",
        "time": total_time - walk_to_station - walk_from_station,
        "from": "出発駅",
        "to": "到着駅",
        "wait_time": 0  # 最初の駅での待ち時間は0
    }]
    
    return {
        "walk_to_station": walk_to_station,
        "station_used": "最寄駅",
        "trains": trains,
        "walk_from_station": walk_from_station,
        "total_time": total_time
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python google_maps_unified.py <出発地> <目的地> [到着時刻]")
        sys.exit(1)
        
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = None
    
    if len(sys.argv) > 3:
        # 到着時刻の処理（必要に応じて実装）
        pass
    
    result = get_route(origin, destination, arrival_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))