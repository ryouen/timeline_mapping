#!/usr/bin/env python3
"""
Google Maps 統合版スクレイピング（修正版）
電車ルートと徒歩ルートの両方に対応
タイムアウト問題を解決
"""
import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys

def extract_route_from_panel_text(panel_text):
    """directions_panelのテキストから詳細なルート情報を抽出"""
    routes = []
    lines = panel_text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 時刻情報を検索（例: "22:45"）
        time_match = re.match(r'^(\d{1,2}:\d{2})$', line)
        if time_match:
            departure_time = time_match.group(1)
            
            # 次の行を確認
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # 徒歩の場合（例: "徒歩約2分"）
                walk_match = re.match(r'^徒歩約(\d+)分', next_line)
                if walk_match:
                    duration = int(walk_match.group(1))
                    
                    # 目的地を探す
                    dest_line = ""
                    if i + 2 < len(lines):
                        dest_line = lines[i + 2].strip()
                    
                    routes.append({
                        "type": "walk",
                        "departure_time": departure_time,
                        "duration": duration,
                        "destination": dest_line if dest_line else "目的地"
                    })
                    i += 3
                    continue
                
                # 電車の場合（路線名が含まれる）
                elif any(keyword in next_line for keyword in ['線', 'ライン', 'Line', 'JR']):
                    train_line = next_line
                    
                    # 到着時刻を探す
                    arrival_time = None
                    arrival_station = None
                    
                    j = i + 2
                    while j < len(lines):
                        # 到着時刻のパターン
                        arr_match = re.match(r'^(\d{1,2}:\d{2})$', lines[j].strip())
                        if arr_match:
                            arrival_time = arr_match.group(1)
                            # 次の行が駅名
                            if j + 1 < len(lines):
                                arrival_station = lines[j + 1].strip()
                            break
                        j += 1
                    
                    if arrival_time:
                        # 所要時間を計算
                        dep_h, dep_m = map(int, departure_time.split(':'))
                        arr_h, arr_m = map(int, arrival_time.split(':'))
                        duration = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
                        if duration < 0:  # 日をまたぐ場合
                            duration += 24 * 60
                        
                        routes.append({
                            "type": "train",
                            "departure_time": departure_time,
                            "arrival_time": arrival_time,
                            "duration": duration,
                            "line": train_line,
                            "destination": arrival_station if arrival_station else "到着駅"
                        })
                        i = j + 2
                        continue
        
        i += 1
    
    return routes

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
            url += f"@35.6762,139.6503,12z/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{int(arrival_time.timestamp())}!3e3"
        else:
            # 現在時刻で出発の場合（3e3 = 公共交通機関）
            url += "data=!4m2!4m1!3e3"
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        
        # ルートが読み込まれるまで待機
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="list"]')))
        time.sleep(3)
        
        # 詳細を展開
        try:
            details_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="詳細"], button[aria-label*="Details"]')
            driver.execute_script("arguments[0].click();", details_button)
            time.sleep(2)
        except NoSuchElementException:
            print("詳細ボタンが見つかりませんでした")
        
        # directions_panelを取得
        try:
            panel = driver.find_element(By.CSS_SELECTOR, 'div[role="list"]')
            panel_text = panel.text
            
            # デバッグ用に保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = f"/app/output/japandatascience.com/timeline-mapping/data/debug_panel_text_{timestamp}.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(panel_text)
            
            # ルート情報を抽出
            route_segments = extract_route_from_panel_text(panel_text)
            
            if not route_segments:
                return {
                    "status": "no_route",
                    "message": "電車ルートが見つかりませんでした"
                }
            
            # 結果を整形
            total_duration = sum(seg["duration"] for seg in route_segments)
            walking_duration = sum(seg["duration"] for seg in route_segments if seg["type"] == "walk")
            
            # 最初の出発時刻と最後の到着時刻を取得
            first_departure = route_segments[0]["departure_time"]
            last_arrival = None
            for seg in reversed(route_segments):
                if seg["type"] == "train" and "arrival_time" in seg:
                    last_arrival = seg["arrival_time"]
                    break
            
            # 待ち時間の処理
            processed_routes = []
            for i, segment in enumerate(route_segments):
                seg_copy = segment.copy()
                
                if seg_copy["type"] == "train":
                    # 最初の電車の待ち時間は0に設定
                    if i == 0 or (i > 0 and route_segments[i-1]["type"] == "walk" and i == 1):
                        seg_copy["waiting_time"] = 0
                    else:
                        # 乗り換え時の待ち時間を計算
                        prev_arrival = None
                        for j in range(i-1, -1, -1):
                            if route_segments[j]["type"] == "train" and "arrival_time" in route_segments[j]:
                                prev_arrival = route_segments[j]["arrival_time"]
                                break
                        
                        if prev_arrival and "departure_time" in seg_copy:
                            prev_h, prev_m = map(int, prev_arrival.split(':'))
                            curr_h, curr_m = map(int, seg_copy["departure_time"].split(':'))
                            wait_time = (curr_h * 60 + curr_m) - (prev_h * 60 + prev_m)
                            
                            # 徒歩時間を差し引く
                            for k in range(j+1, i):
                                if route_segments[k]["type"] == "walk":
                                    wait_time -= route_segments[k]["duration"]
                            
                            seg_copy["waiting_time"] = max(0, wait_time)
                        else:
                            seg_copy["waiting_time"] = 0
                
                processed_routes.append(seg_copy)
            
            return {
                "status": "success",
                "search_info": {
                    "type": "arrival" if arrival_time else "departure",
                    "time": arrival_time.strftime("%Y-%m-%d %H:%M") if arrival_time else datetime.now().strftime("%Y-%m-%d %H:%M")
                },
                "route": {
                    "departure_time": first_departure,
                    "arrival_time": last_arrival,
                    "duration": total_duration,
                    "walking_duration": walking_duration,
                    "route_found": True
                },
                "route_segments": processed_routes
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"ルート解析エラー: {str(e)}"
            }
            
    except TimeoutException:
        return {
            "status": "timeout",
            "message": "ページの読み込みがタイムアウトしました"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"エラーが発生しました: {str(e)}"
        }
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
        # URL構築（徒歩）
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origin}/{destination}/data=!4m2!4m1!3e2"  # 3e2 = 徒歩
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        
        # ルートが読み込まれるまで待機
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="section-directions-trip-duration"]')))
        time.sleep(3)
        
        # 所要時間を取得
        duration_element = driver.find_element(By.CSS_SELECTOR, '[class*="section-directions-trip-duration"] span')
        duration_text = duration_element.text
        
        # 距離を取得
        distance_element = driver.find_element(By.CSS_SELECTOR, '[class*="section-directions-trip-distance"]')
        distance_text = distance_element.text
        
        # 分に変換
        duration_minutes = 0
        if '時間' in duration_text:
            hours = int(re.search(r'(\d+)\s*時間', duration_text).group(1))
            duration_minutes += hours * 60
        if '分' in duration_text:
            minutes = int(re.search(r'(\d+)\s*分', duration_text).group(1))
            duration_minutes += minutes
        
        return {
            "status": "success",
            "search_info": {
                "type": "walking",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            "route": {
                "departure_time": datetime.now().strftime("%H:%M"),
                "arrival_time": (datetime.now().timestamp() + duration_minutes * 60),
                "duration": duration_minutes,
                "walking_duration": duration_minutes,
                "distance": distance_text,
                "route_found": True
            },
            "route_segments": [{
                "type": "walk",
                "departure_time": datetime.now().strftime("%H:%M"),
                "duration": duration_minutes,
                "distance": distance_text,
                "destination": destination
            }]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"徒歩ルート取得エラー: {str(e)}"
        }
    finally:
        driver.quit()

def main():
    if len(sys.argv) < 3:
        print("Usage: python google_maps_unified_fixed.py <origin> <destination> [arrival_time]")
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = None
    
    if len(sys.argv) > 3:
        # 到着時刻の処理
        arrival_time = datetime.strptime(sys.argv[3], "%Y-%m-%d %H:%M")
    
    result = get_route(origin, destination, arrival_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()