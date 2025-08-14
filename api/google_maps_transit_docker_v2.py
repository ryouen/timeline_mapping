#!/usr/bin/env python3
"""
Google Maps Transit Scraping API - Docker version v2
時刻指定に対応した改良版
"""

import json
import sys
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback

def setup_driver():
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja-JP')
    
    # Connect to Selenium Grid container
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    return driver

def parse_duration_text(text):
    """Parse duration text like '15分' or '15 min' to integer minutes"""
    match = re.search(r'(\d+)\s*(?:分|min)', text)
    if match:
        return int(match.group(1))
    return 0

def set_departure_time(driver, departure_time):
    """出発時刻を設定する"""
    try:
        # Step 1: 「すぐに出発」ボタンを探してクリック
        time_button_selectors = [
            "//span[contains(text(), 'すぐ')]/..",  # 「すぐに出発」テキストの親要素
            "//span[@class='uEubGf NlVald']/..",    # クラス名で特定
            "//div[@class='MlqQ3d Hk4XGb ']",       # 時刻選択の親要素
        ]
        
        time_button_clicked = False
        for selector in time_button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # クリック可能な要素を探す
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            elem.click()
                            time.sleep(2)
                            time_button_clicked = True
                            break
                    
                    if time_button_clicked:
                        break
            except:
                continue
        
        if not time_button_clicked:
            return False
        
        # Step 2: 時刻選択メニューから「出発時刻」を選択
        departure_option_selectors = [
            "//button[contains(@aria-label, '出発')]",
            "//div[contains(text(), '出発時刻')]",
            "//span[contains(text(), '出発時刻')]",
        ]
        
        for selector in departure_option_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    time.sleep(2)
                    break
            except:
                continue
        
        # Step 3: 時刻入力フィールドまたは選択肢を探す
        time_input_selectors = [
            "//input[@type='time']",
            "//input[contains(@aria-label, '時刻')]",
            "//select[contains(@aria-label, '時')]",
        ]
        
        for selector in time_input_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # 時刻を設定
                    time_str = departure_time.strftime("%H:%M")
                    elements[0].clear()
                    elements[0].send_keys(time_str)
                    time.sleep(1)
                    
                    # 設定を確定（Enterキーなど）
                    elements[0].send_keys("\n")
                    time.sleep(2)
                    return True
            except:
                continue
        
        # 時刻入力フィールドが見つからない場合は、プリセットの時刻を探す
        # （例：8:00, 9:00などのボタン）
        hour = departure_time.hour
        preset_xpath = f"//button[contains(text(), '{hour}:00')]"
        try:
            preset_buttons = driver.find_elements(By.XPATH, preset_xpath)
            if preset_buttons:
                preset_buttons[0].click()
                time.sleep(2)
                return True
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"時刻設定エラー: {str(e)}", file=sys.stderr)
        return False

def extract_route_details(driver, origin, destination, departure_time=None, arrival_time=None):
    """Extract transit route details from Google Maps"""
    
    # Build URL for transit directions
    base_url = "https://www.google.com/maps/dir/"
    
    # URL encode the locations
    from urllib.parse import quote
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    
    # 基本URL（公共交通機関モード）
    url = f"{base_url}?api=1&origin={encoded_origin}&destination={encoded_destination}&travelmode=transit"
    
    # 時刻指定がある場合（URLパラメータとして追加、後でUIで設定）
    if departure_time and departure_time != 'now':
        timestamp = int(departure_time.timestamp())
        url += f"&departure_time={timestamp}"
    elif arrival_time and arrival_time != 'now':
        timestamp = int(arrival_time.timestamp())
        url += f"&arrival_time={timestamp}"
    
    driver.get(url)
    
    # Wait for directions panel to load
    wait = WebDriverWait(driver, 30)
    
    try:
        # Wait for transit routes to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-trip-index]')))
        time.sleep(5)  # Allow dynamic content to fully load
        
        # 時刻指定がある場合は設定を試みる
        if departure_time and departure_time != 'now':
            time_set = set_departure_time(driver, departure_time)
            if time_set:
                # 時刻設定後、ルートが更新されるのを待つ
                time.sleep(5)
        
        # Get the first route
        route_selectors = [
            '[data-trip-index="0"]',
            'div[role="button"][data-trip-index="0"]',
            'div.Ylt4Kd',  # Alternative route container
        ]
        
        route_element = None
        for selector in route_selectors:
            try:
                route_element = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
                
        if not route_element:
            raise Exception("Could not find route element")
        
        # Extract departure/arrival times
        departure_time_str = None
        arrival_time_str = None
        
        # 時刻情報を含むテキストを探す
        time_info_selectors = [
            'h1.yIkJof span',  # 時刻範囲を含むヘッダー
            'h1.VuCHmb span',  # 別の時刻表示形式
            'div.tUEI8e span',  # 詳細な時刻情報
        ]
        
        for selector in time_info_selectors:
            try:
                time_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in time_elements:
                    text = elem.text
                    # 時刻パターン（例：13:38 - 14:04）
                    time_range_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', text)
                    if time_range_match:
                        departure_time_str = time_range_match.group(1)
                        arrival_time_str = time_range_match.group(2)
                        break
                if departure_time_str:
                    break
            except:
                continue
        
        # Extract total time
        total_time_selectors = [
            'span[jsan*="分"]',
            'span[jstcache*="duration"]',
            'div.Fk3sm span',
            'span.xB1mrd',
        ]
        
        total_minutes = None
        for selector in total_time_selectors:
            try:
                time_elements = route_element.find_elements(By.CSS_SELECTOR, selector)
                for elem in time_elements:
                    text = elem.text
                    if '分' in text or 'min' in text:
                        total_minutes = parse_duration_text(text)
                        if total_minutes > 0:
                            break
                if total_minutes:
                    break
            except:
                continue
        
        if not total_minutes:
            # Fallback: look for any text containing minutes
            route_text = route_element.text
            total_minutes = parse_duration_text(route_text) or 30  # Default 30 min
        
        # Click on the route to expand details
        try:
            route_element.click()
            time.sleep(3)
        except:
            pass
        
        # Initialize route details
        walk_to_station = 0
        walk_from_station = 0
        station_used = None
        trains = []
        wait_time_minutes = 3  # Default wait time
        
        # Try to find detailed steps
        step_selectors = [
            'div.cYhGGe',  # Step container
            'div[role="listitem"]',
            'div.VLwlLc',
            'div.T4gWAd',
        ]
        
        steps = []
        for selector in step_selectors:
            steps = driver.find_elements(By.CSS_SELECTOR, selector)
            if steps:
                break
        
        # Parse each step (既存のロジックを維持)
        for i, step in enumerate(steps):
            try:
                step_text = step.text
                
                # Skip empty steps
                if not step_text.strip():
                    continue
                
                # Check if it's a walking step
                if any(word in step_text.lower() for word in ['徒歩', 'walk', '歩', 'à pied']):
                    duration = parse_duration_text(step_text)
                    if duration > 0:
                        if i == 0:
                            walk_to_station = duration
                        elif i == len(steps) - 1:
                            walk_from_station = duration
                
                # Check if it's a transit step
                elif any(word in step_text for word in ['線', 'Line', 'Metro', '地下鉄', 'JR', '東急', '京王', '小田急', '西武', '東武', '京成', '都営']):
                    # Extract line name
                    line_patterns = [
                        r'([^、\n]*線)',
                        r'(JR[^\n]*線)',
                        r'([^\n]*Line)',
                        r'(東京メトロ[^\n]*)',
                        r'(都営[^\n]*)',
                    ]
                    
                    line_name = None
                    for pattern in line_patterns:
                        match = re.search(pattern, step_text)
                        if match:
                            line_name = match.group(1)
                            break
                    
                    if not line_name:
                        line_name = '不明'
                    
                    # Extract duration
                    duration = parse_duration_text(step_text) or 10
                    
                    # Extract station names
                    station_patterns = [
                        r'([^\n]+駅)',
                        r'([^\n]+[Ss]tation)',
                        r'→\s*([^\n]+)',
                    ]
                    
                    stations = []
                    for pattern in station_patterns:
                        matches = re.findall(pattern, step_text)
                        stations.extend(matches)
                    
                    # Clean station names
                    stations = [s.replace('駅', '').replace('Station', '').strip() for s in stations]
                    stations = [s for s in stations if s]  # Remove empty
                    
                    from_station = stations[0] if len(stations) > 0 else '不明'
                    to_station = stations[1] if len(stations) > 1 else '不明'
                    
                    if not station_used and from_station != '不明':
                        station_used = from_station
                    
                    train_info = {
                        'line': line_name,
                        'time': duration,
                        'from': from_station,
                        'to': to_station
                    }
                    
                    # Check for transfer information
                    if i + 1 < len(steps):
                        next_step = steps[i + 1]
                        next_text = next_step.text
                        if any(word in next_text.lower() for word in ['徒歩', 'walk', '乗り換え', 'transfer']):
                            transfer_time = parse_duration_text(next_text)
                            if transfer_time > 0 and i + 2 < len(steps):
                                # Look for the next train line
                                for j in range(i + 2, min(i + 4, len(steps))):
                                    future_step = steps[j].text
                                    for pattern in line_patterns:
                                        match = re.search(pattern, future_step)
                                        if match:
                                            train_info['transfer_after'] = {
                                                'time': transfer_time,
                                                'to_line': match.group(1)
                                            }
                                            break
                                    if 'transfer_after' in train_info:
                                        break
                    
                    trains.append(train_info)
                    
            except Exception as e:
                continue
        
        # If we couldn't parse detailed steps, create a simple route
        if not trains and total_minutes:
            # Estimate walk times
            walk_to_station = 5
            walk_from_station = 5
            train_time = total_minutes - walk_to_station - walk_from_station - wait_time_minutes
            
            trains = [{
                'line': '電車',
                'time': max(train_time, 10),
                'from': origin.split('、')[0] if '、' in origin else origin[:10],
                'to': destination.split('、')[0] if '、' in destination else destination[:10]
            }]
            
            if not station_used:
                station_used = trains[0]['from']
        
        # Build response
        route_details = {
            'wait_time_minutes': wait_time_minutes,
            'walk_to_station': walk_to_station,
            'station_used': station_used or '不明',
            'trains': trains,
            'walk_from_station': walk_from_station
        }
        
        # 時刻情報を追加
        if departure_time_str:
            route_details['departure_time'] = departure_time_str
        if arrival_time_str:
            route_details['arrival_time'] = arrival_time_str
        
        # Recalculate total time
        recalculated_total = (
            wait_time_minutes + 
            walk_to_station + 
            walk_from_station +
            sum(train['time'] for train in trains) +
            sum(train.get('transfer_after', {}).get('time', 0) for train in trains)
        )
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'departure' if departure_time else 'arrival' if arrival_time else 'now',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A'),
                'requested_time': departure_time.strftime('%Y-%m-%d %H:%M:%S') if departure_time and departure_time != 'now' else None
            },
            'route': {
                'total_time': recalculated_total or total_minutes,
                'original_total_time': total_minutes,
                'details': route_details
            }
        }
        
    except TimeoutException:
        return {
            'status': 'error',
            'message': 'Timeout waiting for route information'
        }
    except Exception as e:
        # Save screenshot for debugging
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Use container's mounted path
            screenshot_path = f'/app/output/japandatascience.com/timeline-mapping/api/error_screenshots/google_maps_error_{timestamp}.png'
            driver.save_screenshot(screenshot_path)
        except:
            pass
            
        # Log detailed error for debugging
        import os
        if os.environ.get('DEBUG', '').lower() == 'true':
            error_details = {
                'status': 'error',
                'message': f'Error extracting route: {str(e)}',
                'traceback': traceback.format_exc()
            }
        else:
            error_details = {
                'status': 'error',
                'message': 'Failed to extract route information'
            }
        
        return error_details

def main():
    """Main function to handle command line arguments and execute scraping"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: python google_maps_transit.py <origin> <destination> [departure_time|arrival_time]'
        }))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    departure_time = None
    arrival_time = None
    
    if len(sys.argv) > 3:
        time_arg = sys.argv[3]
        if time_arg == 'now':
            departure_time = 'now'
        else:
            try:
                # 時刻指定のフォーマット: "departure:2024-12-25 08:00:00" または "arrival:2024-12-25 09:00:00"
                if time_arg.startswith('departure:'):
                    departure_time = datetime.strptime(time_arg[10:], '%Y-%m-%d %H:%M:%S')
                elif time_arg.startswith('arrival:'):
                    arrival_time = datetime.strptime(time_arg[8:], '%Y-%m-%d %H:%M:%S')
                else:
                    # 後方互換性のため、単純な時刻文字列は出発時刻として扱う
                    departure_time = datetime.strptime(time_arg, '%Y-%m-%d %H:%M:%S')
            except:
                departure_time = 'now'
    
    driver = None
    try:
        driver = setup_driver()
        result = extract_route_details(driver, origin, destination, departure_time, arrival_time)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        import os
        if os.environ.get('DEBUG', '').lower() == 'true':
            error_output = {
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            }
        else:
            error_output = {
                'status': 'error',
                'message': 'Service temporarily unavailable'
            }
        print(json.dumps(error_output))
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    main()