#!/usr/bin/env python3
"""
Google Maps Transit スクレイピング - 最終版
正確な乗り換え時間と待ち時間の計算を実装
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
import os

def parse_time(time_str):
    """時刻文字列をタプル(hour, minute)に変換"""
    match = re.match(r'(\d+):(\d+)', time_str)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None

def time_diff_minutes(start_time, end_time):
    """2つの時刻タプル間の差分を分で返す"""
    if not start_time or not end_time:
        return 0
    
    start_minutes = start_time[0] * 60 + start_time[1]
    end_minutes = end_time[0] * 60 + end_time[1]
    
    # 日をまたぐ場合の処理
    if end_minutes < start_minutes:
        end_minutes += 24 * 60
    
    return end_minutes - start_minutes

def extract_route_from_panel_text(panel_text):
    """directions_panelのテキストから完全なルート情報を抽出"""
    
    # 総所要時間の抽出: "9:35 (火曜日) - 9:58 （23 分）"
    total_pattern = r'(\d+):(\d+)[^-]+-\s*(\d+):(\d+)\s*[（\(](\d+)\s*分'
    total_match = re.search(total_pattern, panel_text)
    
    if not total_match:
        return None
    
    start_time = (int(total_match.group(1)), int(total_match.group(2)))
    end_time = (int(total_match.group(3)), int(total_match.group(4)))
    total_minutes = int(total_match.group(5))
    
    # 時刻付きステップの抽出
    steps = []
    lines = panel_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 時刻行を探す
        time_match = re.match(r'^(\d+):(\d+)$', line)
        if time_match:
            step_time = parse_time(time_match.group(0))
            step_info = {
                'time': step_time,
                'time_str': time_match.group(0),
                'content': []
            }
            
            # 次の時刻行まで内容を収集
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if re.match(r'^\d+:\d+$', next_line):
                    break
                if next_line:
                    step_info['content'].append(next_line)
                i += 1
            
            steps.append(step_info)
        else:
            i += 1
    
    # ルート詳細の構築
    route_details = {
        'walk_to_station': 0,
        'station_used': '',
        'trains': [],
        'walk_from_station': 0
    }
    
    # 各ステップを解析
    i = 0
    while i < len(steps):
        step = steps[i]
        content_text = ' '.join(step['content'])
        
        # 次のステップの時刻を取得
        next_time = steps[i + 1]['time'] if i + 1 < len(steps) else end_time
        duration = time_diff_minutes(step['time'], next_time)
        
        # ステップの種類を判定
        if '徒歩' in content_text:
            # 徒歩ステップ
            if not route_details['trains']:  
                # 最初の徒歩（駅まで）
                route_details['walk_to_station'] = duration
            else:  
                # 電車の後の徒歩
                # 最後の徒歩かチェック（次が目的地または最後のステップ）
                is_last_walk = (i == len(steps) - 2 or 
                               (i + 1 < len(steps) and '〒' in ' '.join(steps[i + 1]['content'])))
                
                if is_last_walk:
                    route_details['walk_from_station'] = duration
                else:
                    # 乗り換え徒歩
                    if route_details['trains']:
                        # 乗り換え徒歩の実際の時間を計算
                        # 現在のステップ（徒歩）の終了時刻と次の電車の出発時刻の差が待ち時間
                        if i + 2 < len(steps):
                            next_train_time = steps[i + 2]['time']
                            wait_time = time_diff_minutes(next_time, next_train_time)
                            
                            route_details['trains'][-1]['transfer_after'] = {
                                'time': duration,
                                'to_line': '',
                                'wait_time': wait_time  # 待ち時間を保存
                            }
                        else:
                            route_details['trains'][-1]['transfer_after'] = {
                                'time': duration,
                                'to_line': ''
                            }
        
        elif '駅' in content_text and '線' in content_text:
            # 電車ステップ
            # 路線名の抽出
            line_match = re.search(r'([^\s]+線)', content_text)
            line_name = line_match.group(1) if line_match else '不明'
            
            # 駅名の抽出（現在の駅）
            station_match = re.search(r'(\S+駅)', ' '.join(step['content']))
            from_station = station_match.group(1) if station_match else step['content'][0]
            
            # 到着駅の取得（次の駅名を含むステップから）
            to_station = ''
            if i + 1 < len(steps):
                next_content = ' '.join(steps[i + 1]['content'])
                to_match = re.search(r'(\S+駅)', next_content)
                if to_match:
                    to_station = to_match.group(1)
            
            # 使用駅の設定（最初の電車の場合）
            if not route_details['station_used']:
                route_details['station_used'] = from_station
            
            # 前の電車の乗り換え先路線名を設定
            if route_details['trains'] and 'transfer_after' in route_details['trains'][-1]:
                route_details['trains'][-1]['transfer_after']['to_line'] = line_name
            
            train_info = {
                'line': line_name,
                'time': duration,
                'from': from_station.replace('駅', ''),
                'to': to_station.replace('駅', '')
            }
            
            # 待ち時間を前の乗り換え情報から取得
            if (route_details['trains'] and 
                'transfer_after' in route_details['trains'][-1] and 
                'wait_time' in route_details['trains'][-1]['transfer_after']):
                train_info['wait_time'] = route_details['trains'][-1]['transfer_after']['wait_time']
                # 待ち時間を転送後、元の場所から削除
                del route_details['trains'][-1]['transfer_after']['wait_time']
            
            route_details['trains'].append(train_info)
        
        i += 1
    
    return {
        'total_time': total_minutes,
        'details': route_details
    }

def scrape_google_maps_route(origin, destination, arrival_time=None):
    """Google Mapsから経路情報をスクレイピング"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja')
    
    # Selenium Grid URLを使用
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    try:
        # URLの構築
        base_url = f"https://www.google.com/maps/dir/{origin}/{destination}"
        params = "/@35.6762,139.6503,12z/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{}!3e3"
        
        if arrival_time:
            dt = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M:%S")
            timestamp = int(dt.timestamp())
            url = base_url + params.format(timestamp)
        else:
            url = base_url + "/@35.6762,139.6503,12z/data=!3m1!4b1!4m2!4m1!3e3"
        
        driver.get(url)
        
        # ルートパネルの読み込み待機
        wait = WebDriverWait(driver, 20)
        
        # 最初のルートを展開
        try:
            # 詳細リンクをクリック
            details_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '詳細')]"))
            )
            details_link.click()
            time.sleep(2)  # 展開を待つ
        except:
            # 既に展開されている可能性もある
            pass
        
        # 展開されたパネルを取得
        panel = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.WNBkOb"))
        )
        
        # パネルテキストの取得
        panel_text = panel.text
        
        # デバッグ用に保存
        debug_dir = "/app/output/japandatascience.com/timeline-mapping/data"
        os.makedirs(debug_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"{debug_dir}/debug_panel_text_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(panel_text)
        
        # ルート情報の抽出
        route_info = extract_route_from_panel_text(panel_text)
        
        if route_info:
            return {
                'status': 'success',
                'search_info': {
                    'type': 'arrival' if arrival_time else 'departure',
                    'time': arrival_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                'route': route_info
            }
        else:
            return {
                'status': 'error',
                'message': 'ルート情報の抽出に失敗しました'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: script.py <origin> <destination> [arrival_time]'
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = scrape_google_maps_route(origin, destination, arrival_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))