#!/usr/bin/env python3
"""
Google Maps Transit スクレイピング V3
より確実なパターンマッチングで正確なデータ抽出
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
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    return driver

def parse_minutes(text):
    """テキストから分数を抽出"""
    match = re.search(r'(\d+)\s*分', text)
    if match:
        return int(match.group(1))
    return 0

def parse_panel_text_v3(panel_text):
    """パネルテキストをより確実に解析"""
    
    # 全体の時間を抽出
    total_match = re.search(r'(\d+):(\d+).*?-.*?(\d+):(\d+).*?（(\d+)\s*分）', panel_text)
    if not total_match:
        return None
    
    total_minutes = int(total_match.group(5))
    start_time = f"{total_match.group(1)}:{total_match.group(2)}"
    
    # ルートの詳細部分を抽出（時刻とアドレスを含む部分）
    route_section_match = re.search(rf'{start_time}.*?料金', panel_text, re.DOTALL)
    if not route_section_match:
        return None
    
    route_text = route_section_match.group(0)
    
    # ステップを抽出
    route_details = {
        'walk_to_station': 0,
        'station_used': None,
        'trains': [],
        'walk_from_station': 0,
        'wait_time_minutes': 0
    }
    
    # 各ステップを時刻で分割
    steps = []
    lines = route_text.split('\n')
    current_step = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 時刻パターンのチェック
        time_match = re.match(r'^(\d+):(\d+)$', line)
        if time_match:
            # 新しいステップの開始
            if current_step:
                steps.append(current_step)
            
            current_step = {
                'time': line,
                'content': []
            }
            i += 1
            
            # 次の時刻まで内容を収集
            while i < len(lines) and not re.match(r'^(\d+):(\d+)$', lines[i].strip()):
                if lines[i].strip():
                    current_step['content'].append(lines[i].strip())
                i += 1
            i -= 1  # 次のループで時刻をチェックするため
        i += 1
    
    # 最後のステップを追加
    if current_step:
        steps.append(current_step)
    
    # ステップの解析
    first_walk_done = False
    trains_started = False
    
    for i, step in enumerate(steps):
        step_content = ' '.join(step['content'])
        
        # 出発地点（アドレス）のスキップ
        if '〒' in step_content and i == 0:
            continue
        
        # 徒歩の処理
        if '徒歩' in step_content:
            minutes = parse_minutes(step_content)
            
            if not first_walk_done and not trains_started:
                # 最初の徒歩（駅まで）
                route_details['walk_to_station'] = minutes
                first_walk_done = True
                
                # 次のステップで待ち時間を計算
                if i + 1 < len(steps):
                    next_time = steps[i + 1]['time']
                    time_match = re.match(r'(\d+):(\d+)', step['time'])
                    next_match = re.match(r'(\d+):(\d+)', next_time)
                    if time_match and next_match:
                        current_min = int(time_match.group(1)) * 60 + int(time_match.group(2))
                        next_min = int(next_match.group(1)) * 60 + int(next_match.group(2))
                        wait_time = next_min - current_min - minutes
                        route_details['wait_time_minutes'] = max(0, wait_time)
            
            elif trains_started and i < len(steps) - 1:
                # 乗り換えの徒歩
                if route_details['trains']:
                    route_details['trains'][-1]['transfer_after'] = {
                        'time': minutes,
                        'to_line': '次の路線'
                    }
            else:
                # 最後の徒歩（駅から目的地）
                route_details['walk_from_station'] = minutes
        
        # 駅と電車の処理
        elif '駅' in step_content:
            trains_started = True
            
            # 駅名の抽出
            station_match = re.search(r'([^駅\s]+)駅', step_content)
            if station_match:
                station_name = station_match.group(1)
                
                if not route_details['station_used']:
                    route_details['station_used'] = station_name
                
                # 路線情報の確認
                if '線' in step_content or any(x in step_content for x in ['JR', '東京メトロ', '都営']):
                    # 路線名の抽出
                    line_patterns = [
                        r'(東京メトロ[^線]*線)',
                        r'(都営[^線]*線)',
                        r'(JR[^線\s]*(?:線)?)',
                        r'([^線\s]*線)'
                    ]
                    
                    line_name = None
                    for pattern in line_patterns:
                        match = re.search(pattern, step_content)
                        if match:
                            line_name = match.group(1)
                            line_name = re.sub(r'各停.*?行$', '', line_name).strip()
                            break
                    
                    # 乗車時間の抽出
                    time_match = re.search(r'(\d+)\s*分', step_content)
                    train_time = int(time_match.group(1)) if time_match else 0
                    
                    # 到着駅の推定
                    to_station = None
                    if i + 1 < len(steps):
                        next_content = ' '.join(steps[i + 1]['content'])
                        to_match = re.search(r'([^駅\s]+)駅', next_content)
                        if to_match:
                            to_station = to_match.group(1)
                    
                    train_info = {
                        'line': line_name or '電車',
                        'time': train_time,
                        'from': station_name,
                        'to': to_station or '不明'
                    }
                    
                    # 前の乗り換え情報を更新
                    if route_details['trains'] and 'transfer_after' in route_details['trains'][-1]:
                        route_details['trains'][-1]['transfer_after']['to_line'] = line_name or '電車'
                    
                    route_details['trains'].append(train_info)
    
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
        
        # Extract route using improved parsing
        route_data = parse_panel_text_v3(panel_text)
        
        if not route_data:
            raise Exception("Could not parse route data from panel text")
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'arrival' if arrival_time and arrival_time != 'now' else 'departure',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A')
            },
            'route': route_data
        }
        
    except Exception as e:
        import traceback
        
        # Save error screenshot
        if driver:
            try:
                error_path = f'/app/output/japandatascience.com/timeline-mapping/data/debug_screenshots/error_v3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
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
        print("Usage: python google_maps_transit_v3.py <origin> <destination> [arrival_time]")
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = get_transit_route(origin, destination, arrival_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))