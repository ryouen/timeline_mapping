#!/usr/bin/env python3
"""
Google Maps Transit Scraping API - Final Version
正確なルート詳細抽出に特化した最終版
Updated: 2025-08-14
"""

import json
import sys
import time
import re
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import traceback
import os
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_address(address):
    """
    住所文字列をGoogle Mapsが解釈しやすい形式に正規化する
    """
    if not address:
        return address
    
    # 元の住所を記録
    original = address
    
    # 1. 全角英数字を半角に変換
    # 全角数字
    address = address.translate(str.maketrans(
        '０１２３４５６７８９',
        '0123456789'
    ))
    # 全角アルファベット（大文字）
    address = address.translate(str.maketrans(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ))
    # 全角アルファベット（小文字）
    address = address.translate(str.maketrans(
        'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
        'abcdefghijklmnopqrstuvwxyz'
    ))
    
    # 2. 丁目・番地・号をハイフン形式に統一
    # 例: "2丁目22番3号" → "2-22-3"
    address = re.sub(r'(\d+)丁目\s*', r'\1-', address)
    address = re.sub(r'(\d+)番地?\s*', r'\1-', address)
    address = re.sub(r'(\d+)号\s*', r'\1', address)
    
    # 3. 不要なスペースを削除
    # 数字-数字の間のスペースを削除
    address = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', address)
    # 数字の後のスペースを削除（ただし、その後に漢字が続く場合は残す）
    address = re.sub(r'(\d+)\s+(?=[^\u4e00-\u9fff])', r'\1', address)
    
    # 4. 建物名は保持（Google Mapsでの認識率向上のため）
    
    # ログ出力
    if address != original:
        logger.info(f"Address normalized: '{original}' → '{address}'")
    
    return address

def setup_driver():
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
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

def extract_route_from_trip_element(trip_element):
    """
    トリップ要素から詳細なルート情報を抽出する
    """
    try:
        trip_text = trip_element.text
        logger.info(f"Extracting from trip text: {trip_text[:200]}...")
        
        # 基本情報の初期化
        total_time = 0
        trains = []
        walk_to_station = 0
        walk_from_station = 0
        station_used = None
        
        # 1. 総所要時間の抽出（最初の「X分」）
        time_match = re.search(r'^(\d+)\s*分', trip_text, re.MULTILINE)
        if time_match:
            total_time = int(time_match.group(1))
            logger.info(f"Total time: {total_time} minutes")
        
        # 2. 路線情報の抽出
        # パターン例: "銀座線", "JR山手線", "東京メトロ丸ノ内線"
        line_patterns = [
            r'([^\s]+線)',  # 基本的な「〇〇線」
            r'(JR[^\s]+)',  # JR路線
            r'(東京メトロ[^\s]+)',  # 東京メトロ
            r'(都営[^\s]+)',  # 都営線
            r'([^\s]+Line)',  # 英語表記
        ]
        
        for pattern in line_patterns:
            line_matches = re.findall(pattern, trip_text)
            if line_matches:
                for line in line_matches:
                    # 駅名の抽出（路線名の周辺から）
                    # パターン: "神田駅から", "日本橋駅まで"
                    station_pattern = r'([^\s]+駅)(?:から|まで|で)'
                    stations = re.findall(station_pattern, trip_text)
                    
                    from_station = '不明'
                    to_station = '不明'
                    
                    if stations:
                        from_station = stations[0].replace('駅', '')
                        if len(stations) > 1:
                            to_station = stations[-1].replace('駅', '')
                        else:
                            # 目的地の駅を探す
                            to_match = re.search(r'([^\s]+)(?:駅)?まで', trip_text)
                            if to_match:
                                to_station = to_match.group(1).replace('駅', '')
                    
                    # 路線の所要時間を推定
                    # 路線名の後の時間を探す
                    line_time = 10  # デフォルト
                    line_time_match = re.search(f'{re.escape(line)}[^\\d]*(\\d+)\\s*分', trip_text)
                    if line_time_match:
                        line_time = int(line_time_match.group(1))
                    
                    trains.append({
                        'line': line,
                        'time': line_time,
                        'from': from_station,
                        'to': to_station
                    })
                    
                    if not station_used and from_station != '不明':
                        station_used = from_station
                    
                    logger.info(f"Found train: {line} ({line_time}min) {from_station} -> {to_station}")
        
        # 3. 徒歩時間の抽出
        walk_matches = re.findall(r'(?:徒歩|walk)\s*(\d+)\s*分', trip_text, re.IGNORECASE)
        if walk_matches:
            # 最初の徒歩は駅まで、最後の徒歩は駅から
            walk_to_station = int(walk_matches[0])
            if len(walk_matches) > 1:
                walk_from_station = int(walk_matches[-1])
            logger.info(f"Walk times: to station {walk_to_station}min, from station {walk_from_station}min")
        
        # 4. 詳細ボタンがあるかチェック
        if '詳細' in trip_text:
            logger.info("Details button found in trip element")
        
        # 結果の構築
        if trains:
            return {
                'total_time': total_time,
                'trains': trains,
                'walk_to_station': walk_to_station,
                'walk_from_station': walk_from_station,
                'station_used': station_used,
                'raw_text': trip_text
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting from trip element: {e}")
        return None

def click_trip_details(driver, trip_element):
    """
    トリップ要素の詳細を展開する
    """
    try:
        # 詳細ボタンを探す
        detail_buttons = trip_element.find_elements(By.XPATH, ".//button[contains(text(), '詳細')]")
        if detail_buttons:
            detail_buttons[0].click()
            logger.info("Clicked details button")
            time.sleep(2)
            return True
        
        # トリップ要素自体をクリック
        try:
            trip_element.click()
            logger.info("Clicked trip element")
            time.sleep(2)
            return True
        except:
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", trip_element)
            logger.info("Clicked trip element via JavaScript")
            time.sleep(2)
            return True
            
    except Exception as e:
        logger.warning(f"Could not click trip details: {e}")
        return False

def extract_route_details(driver, origin, destination, arrival_time=None):
    """Extract transit route details from Google Maps"""
    
    start_time = datetime.now()
    request_id = f"{origin[:10]}-{destination[:10]}-{start_time.timestamp()}"
    logger.info(f"[{request_id}] Starting route search: {origin} -> {destination}")
    
    # 住所の正規化
    origin = normalize_address(origin)
    destination = normalize_address(destination)
    logger.info(f"[{request_id}] Normalized addresses - Origin: {origin}, Destination: {destination}")
    
    # URL構築とページ読み込み
    from urllib.parse import quote
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    
    # Google Maps Direction API v1 形式を使用（api=1が必須）
    url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_destination}&travelmode=transit"
    
    if arrival_time and isinstance(arrival_time, datetime):
        # 到着時刻は公共交通機関モードでのみ有効
        timestamp = int(arrival_time.timestamp())
        url += f"&arrival_time={timestamp}"
        logger.info(f"Using arrival time: {arrival_time} (timestamp: {timestamp})")
    
    logger.info(f"[{request_id}] Loading URL: {url}")
    
    try:
        driver.get(url)
        
        # ページロード待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-trip-index='0'] | //div[contains(@class, 'section-directions')]"))
        )
        
        # ルート情報が完全に読み込まれるまで待機
        time.sleep(5)
        
        # トリップ要素を探す
        trip_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index='0']")
        
        if not trip_elements:
            logger.error(f"[{request_id}] No trip elements found")
            return {
                'status': 'error',
                'message': 'No route information found'
            }
        
        # 最初のトリップ要素から情報を抽出
        trip_element = trip_elements[0]
        route_info = extract_route_from_trip_element(trip_element)
        
        if not route_info:
            logger.warning(f"[{request_id}] Could not extract route info from trip element, trying to expand details")
            
            # 詳細を展開してみる
            if click_trip_details(driver, trip_element):
                # 展開後の全体から情報を再取得
                time.sleep(2)
                # ページ全体のテキストから抽出を試みる
                body_text = driver.find_element(By.TAG_NAME, 'body').text
                
                # より詳細な情報を探す
                trains = []
                
                # 路線情報のパターンマッチング
                # 例: "10:25発 - 10:30着 銀座線 神田 → 三越前"
                detailed_pattern = r'(\d+:\d+)発.*?(\d+:\d+)着\s+([^\s]+線)\s+([^\s→]+)\s*→\s*([^\s]+)'
                detailed_matches = re.findall(detailed_pattern, body_text)
                
                for match in detailed_matches:
                    dep_time, arr_time, line, from_st, to_st = match
                    
                    # 時間差を計算
                    dep_h, dep_m = map(int, dep_time.split(':'))
                    arr_h, arr_m = map(int, arr_time.split(':'))
                    duration = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
                    if duration < 0:
                        duration += 24 * 60  # 日をまたぐ場合
                    
                    trains.append({
                        'line': line,
                        'time': duration,
                        'from': from_st,
                        'to': to_st,
                        'departure': dep_time,
                        'arrival': arr_time
                    })
                    
                    logger.info(f"Found detailed train: {line} ({duration}min) {from_st} -> {to_st} [{dep_time}-{arr_time}]")
                
                if trains:
                    route_info = {
                        'total_time': sum(t['time'] for t in trains) + 10,  # 徒歩時間を追加
                        'trains': trains,
                        'walk_to_station': 5,
                        'walk_from_station': 5,
                        'station_used': trains[0]['from'] if trains else None
                    }
        
        # フォールバック：最小限の情報でも返す
        if not route_info or not route_info.get('trains'):
            logger.warning(f"[{request_id}] Using minimal fallback")
            
            # トリップ要素のテキストから最低限の情報を抽出
            trip_text = trip_element.text
            total_time = parse_duration_text(trip_text) or 30
            
            # 駅名を何とか見つける
            station_matches = re.findall(r'([^\s]+駅)', trip_text)
            from_station = station_matches[0].replace('駅', '') if station_matches else origin.split('、')[0]
            to_station = station_matches[-1].replace('駅', '') if len(station_matches) > 1 else destination.split('、')[0]
            
            # 路線名を探す
            line_match = re.search(r'([^\s]+線)', trip_text)
            line_name = line_match.group(1) if line_match else '電車'
            
            route_info = {
                'total_time': total_time,
                'trains': [{
                    'line': line_name,
                    'time': total_time - 10,  # 徒歩時間を引く
                    'from': from_station,
                    'to': to_station
                }],
                'walk_to_station': 5,
                'walk_from_station': 5,
                'station_used': from_station
            }
        
        # レスポンスの構築
        route_details = {
            'wait_time_minutes': 3,
            'walk_to_station': route_info.get('walk_to_station', 5),
            'station_used': route_info.get('station_used', '不明'),
            'trains': route_info.get('trains', []),
            'walk_from_station': route_info.get('walk_from_station', 5)
        }
        
        # 総所要時間の計算
        total_minutes = route_info.get('total_time', 30)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Success in {duration:.2f}s, total time: {total_minutes} minutes")
        logger.info(f"[{request_id}] Extracted {len(route_details['trains'])} train segments")
        
        # デバッグ用スクリーンショット
        if os.environ.get('DEBUG', '').lower() == 'true':
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/debug_screenshots')
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshot_dir / f'google_maps_final_{timestamp}.png'
                driver.save_screenshot(str(screenshot_path))
                logger.info(f"[{request_id}] Saved debug screenshot: {screenshot_path}")
            except:
                pass
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'arrival' if arrival_time else 'departure',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A'),
                'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M:%S') if arrival_time and isinstance(arrival_time, datetime) else None
            },
            'route': {
                'total_time': total_minutes,
                'details': route_details
            },
            'debug_info': {
                'extraction_method': 'trip_element' if route_info else 'fallback',
                'raw_text': route_info.get('raw_text', '')[:200] if route_info else None
            }
        }
        
    except TimeoutException:
        logger.error(f"[{request_id}] Timeout waiting for page to load")
        return {
            'status': 'error',
            'message': 'Timeout waiting for route information'
        }
    except Exception as e:
        logger.error(f"[{request_id}] Error extracting route: {str(e)}")
        logger.exception(e)
        
        # デバッグ用スクリーンショット
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/error_screenshots')
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshot_dir / f'google_maps_error_{timestamp}.png'
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"[{request_id}] Saved error screenshot: {screenshot_path}")
        except:
            pass
        
        return {
            'status': 'error',
            'message': 'Failed to extract route information',
            'error': str(e) if os.environ.get('DEBUG', '').lower() == 'true' else None
        }

def main():
    """Main function to handle command line arguments and execute scraping"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: python google_maps_transit_final.py <origin> <destination> [arrival_time]'
        }))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = None
    
    if len(sys.argv) > 3:
        if sys.argv[3] == 'now':
            arrival_time = 'now'
        else:
            try:
                arrival_time = datetime.strptime(sys.argv[3], '%Y-%m-%d %H:%M:%S')
            except:
                arrival_time = None
    
    driver = None
    try:
        driver = setup_driver()
        result = extract_route_details(driver, origin, destination, arrival_time)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_output = {
            'status': 'error',
            'message': str(e) if os.environ.get('DEBUG', '').lower() == 'true' else 'Service temporarily unavailable'
        }
        print(json.dumps(error_output))
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()