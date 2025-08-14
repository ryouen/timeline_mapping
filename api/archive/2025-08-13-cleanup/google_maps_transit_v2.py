#!/usr/bin/env python3
"""
Google Maps Transit スクレイピング V2
時刻情報から待ち時間を自動計算し、正確なルート情報を抽出
"""

import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import quote

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=ja')
    
    # Connect to Selenium Grid
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    return driver

def parse_time(time_str):
    """時刻文字列から時・分を抽出 '9:53' -> (9, 53)"""
    match = re.search(r'(\d+):(\d+)', time_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

def time_diff_minutes(time1, time2):
    """2つの時刻の差を分で返す"""
    if not time1 or not time2:
        return 0
    h1, m1 = time1
    h2, m2 = time2
    return (h2 * 60 + m2) - (h1 * 60 + m1)

def extract_time_based_route(panel_text):
    """パネルテキストから時刻ベースでルート情報を抽出"""
    
    # 全体の時間を抽出 "9:35 - 9:58 （23 分）"
    total_match = re.search(r'(\d+):(\d+).*?-.*?(\d+):(\d+).*?（(\d+)\s*分）', panel_text)
    if not total_match:
        return None
    
    start_time = (int(total_match.group(1)), int(total_match.group(2)))
    end_time = (int(total_match.group(3)), int(total_match.group(4)))
    total_minutes = int(total_match.group(5))
    
    # ステップを時刻で分割 - 改善版パターン
    # 時刻の後に続くコンテンツをより正確に取得
    time_pattern = r'(\d+):(\d+)\s*\n([^\d][^\n]*(?:\n(?!\d+:)[^\n]*)*)'
    steps = list(re.finditer(time_pattern, panel_text))
    
    route_details = {
        'walk_to_station': 0,
        'station_used': None,
        'trains': [],
        'walk_from_station': 0,
        'wait_time_minutes': 0
    }
    
    current_time = start_time
    station_arrival_time = None
    
    # 最初のステップがアドレスの場合はスキップ
    start_index = 0
    if steps and '〒' in steps[0].group(3):
        start_index = 1
    
    for i in range(start_index, len(steps)):
        step = steps[i]
        step_time = parse_time(step.group(0))
        step_text = step.group(3).strip()
        
        # 次のステップの時刻を取得
        next_time = None
        if i + 1 < len(steps):
            next_time = parse_time(steps[i + 1].group(0))
        
        # 徒歩ステップの処理
        if '徒歩' in step_text:
            duration = time_diff_minutes(step_time, next_time) if next_time else 0
            
            # 最初の徒歩は駅まで
            if not route_details['walk_to_station'] and not route_details['trains']:
                route_details['walk_to_station'] = duration
                station_arrival_time = next_time
            # 最後の徒歩は駅から（最後のステップか、次が目的地アドレスの場合）
            elif (i == len(steps) - 2 or 
                  (i + 1 < len(steps) and '〒' in steps[i + 1].group(3))):
                route_details['walk_from_station'] = duration
            # 中間の徒歩は乗り換え
            else:
                # 前のtrainに乗り換え情報を追加
                if route_details['trains']:
                    route_details['trains'][-1]['transfer_after'] = {
                        'time': duration,
                        'to_line': '次の路線'  # 後で更新
                    }
        
        # 駅名の抽出
        elif '駅' in step_text:
            station_match = re.search(r'([^駅\s]+)駅', step_text)
            if station_match:
                station_name = station_match.group(1)
                
                # 最初の駅を記録
                if not route_details['station_used']:
                    route_details['station_used'] = station_name
                
                # 電車ステップの処理
                if '線' in step_text or any(x in step_text for x in ['JR', '東京メトロ', '都営']):
                    # 路線名の抽出
                    line_patterns = [
                        r'(東京メトロ[^線]*線)',
                        r'(都営[^線]*線)',
                        r'(JR[^線\s]*(?:線)?)',
                        r'([^線\s]*線)'
                    ]
                    
                    line_name = None
                    for pattern in line_patterns:
                        match = re.search(pattern, step_text)
                        if match:
                            line_name = match.group(1)
                            # "各停渋谷行" などの部分を削除
                            line_name = re.sub(r'各停.*?行$', '', line_name).strip()
                            break
                    
                    # 待ち時間の計算（駅到着から電車出発まで）
                    if station_arrival_time and not route_details['wait_time_minutes']:
                        wait_time = time_diff_minutes(station_arrival_time, step_time)
                        route_details['wait_time_minutes'] = max(0, wait_time)
                    
                    # 乗車時間の計算
                    train_duration = time_diff_minutes(step_time, next_time) if next_time else 0
                    
                    # 行き先駅の推定
                    to_station = None
                    if i + 1 < len(steps):
                        next_text = steps[i + 1].group(3)
                        to_match = re.search(r'([^駅\s]+)駅', next_text)
                        if to_match:
                            to_station = to_match.group(1)
                    
                    train_info = {
                        'line': line_name or '電車',
                        'time': train_duration,
                        'from': station_name,
                        'to': to_station or '不明'
                    }
                    
                    # 前の乗り換え情報に路線名を更新
                    if route_details['trains'] and 'transfer_after' in route_details['trains'][-1]:
                        route_details['trains'][-1]['transfer_after']['to_line'] = line_name or '電車'
                    
                    route_details['trains'].append(train_info)
                    
                    # 次の待ち時間計算のため、到着時刻を更新
                    station_arrival_time = next_time
    
    # 最後のtrainから不要なtransfer_afterを削除
    if route_details['trains'] and 'transfer_after' in route_details['trains'][-1]:
        # 最後の乗り換えが実際には降車後の徒歩の場合
        if route_details['trains'][-1]['transfer_after']['to_line'] == '次の路線':
            route_details['walk_from_station'] = route_details['trains'][-1]['transfer_after']['time']
            del route_details['trains'][-1]['transfer_after']
    
    return {
        'total_time': total_minutes,
        'details': route_details
    }

def get_transit_route(origin, destination, arrival_time=None):
    """メイン関数：Google Mapsから経路情報を取得"""
    driver = None
    
    try:
        driver = setup_driver()
        
        # Build URL
        encoded_origin = quote(origin)
        encoded_dest = quote(destination)
        
        if arrival_time and arrival_time != 'now':
            try:
                datetime_obj = datetime.strptime(arrival_time, '%Y-%m-%d %H:%M:%S')
                timestamp = int(datetime_obj.timestamp())
                url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/@35.6762,139.6503,12z/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{timestamp}!3e3'
            except:
                url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/data=!3m1!4b1!4m2!4m1!3e3'
        else:
            url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/data=!3m1!4b1!4m2!4m1!3e3'
        
        driver.get(url)
        
        # Wait for route to load
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-trip-index]')))
        time.sleep(3)
        
        # Click to expand details
        try:
            route_element = driver.find_element(By.CSS_SELECTOR, '[data-trip-index="0"]')
            route_element.click()
            time.sleep(2)
        except:
            pass
        
        # Get full panel text
        panel_element = driver.find_element(By.CSS_SELECTOR, '.m6QErb[role="main"]')
        panel_text = panel_element.text
        
        # デバッグ用：パネルテキストを保存
        debug_path = f'/app/output/japandatascience.com/timeline-mapping/data/debug_panel_text_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(panel_text)
        
        # Extract route using time-based parsing
        route_data = extract_time_based_route(panel_text)
        
        if not route_data:
            raise Exception("Could not parse route data from panel text")
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'arrival' if arrival_time and arrival_time != 'now' else 'departure',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A')
            },
            'route': route_data,
            'debug': {
                'panel_text_saved': debug_path
            }
        }
        
    except Exception as e:
        import traceback
        
        # Save error screenshot
        if driver:
            try:
                error_path = f'/app/output/japandatascience.com/timeline-mapping/data/debug_screenshots/error_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                driver.save_screenshot(error_path)
            except:
                pass
        
        return {
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }
    finally:
        if driver:
            driver.quit()

# For testing
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python google_maps_transit_v2.py <origin> <destination> [arrival_time]")
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = get_transit_route(origin, destination, arrival_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))