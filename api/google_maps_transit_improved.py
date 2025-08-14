#!/usr/bin/env python3
"""
Google Maps Transit Scraping API - Improved Version
Better route detail extraction with multiple fallback strategies
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
    
    主な処理:
    1. 全角英数字を半角に変換
    2. 丁目・番地表記をハイフン形式に統一
    3. 不要なスペースを削除
    4. 建物名は保持（Google Mapsでの認識率向上のため）
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

def wait_and_click_transit_mode(driver):
    """電車モードを確実に選択する"""
    try:
        # まず現在のモードを確認
        current_url = driver.current_url
        if 'travelmode=transit' in current_url:
            logger.info("Already in transit mode")
            return True
            
        # 電車アイコンを探す（優先順位順）
        transit_selectors = [
            # Google Maps APIドキュメントに基づく最新のセレクタ
            "//button[@data-value='transit']",
            "//button[contains(@aria-label, 'Transit') or contains(@aria-label, '公共交通機関')]",
            "//button[@data-travel-mode='transit']",
            "//div[contains(@class, 'travel-mode') and contains(., 'Transit')]",
            "//img[@alt='Transit']/..",
            # 日本語版のセレクタ
            "//button[contains(@aria-label, '電車')]",
            "//button[contains(text(), '電車')]",
            # レガシーセレクタ
            "//img[contains(@src, 'transit_')]/ancestor::button",
            "//div[@role='button' and contains(@data-tooltip, 'transit')]"
        ]
        
        for selector in transit_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    # 要素が表示されているか確認
                    if element.is_displayed():
                        # スクロールして表示
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        
                        # クリック可能になるまで待つ
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(element))
                        
                        # 通常クリックを試す
                        try:
                            element.click()
                        except:
                            # JavaScriptクリックにフォールバック
                            driver.execute_script("arguments[0].click();", element)
                        
                        logger.info(f"Clicked transit mode with selector: {selector}")
                        time.sleep(3)  # モード切り替えの待機
                        
                        # モードが切り替わったか確認
                        new_url = driver.current_url
                        if 'travelmode=transit' in new_url or 'data=!3e3' in new_url:
                            logger.info("Successfully switched to transit mode")
                            return True
                            
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {e}")
                continue
                
        logger.warning("Could not find transit mode button, URL should handle it")
        return False
        
    except Exception as e:
        logger.error(f"Error selecting transit mode: {e}")
        return False

def extract_route_steps_detailed(driver):
    """詳細なルートステップを抽出する（複数の方法を試す）"""
    steps_info = []
    
    # 方法1: 展開されたルート詳細を探す
    step_selectors = [
        "//div[@class='cYhGGe']",
        "//div[contains(@class, 'directions-mode-step')]",
        "//div[contains(@class, 'section-directions-trip-line')]",
        "//div[contains(@class, 'transit-stop')]",
        "//div[@role='listitem' and contains(@class, 'trip')]"
    ]
    
    for selector in step_selectors:
        try:
            steps = driver.find_elements(By.XPATH, selector)
            if steps:
                logger.info(f"Found {len(steps)} steps with selector: {selector}")
                
                for i, step in enumerate(steps):
                    try:
                        step_text = step.text.strip()
                        if step_text:
                            # 詳細な情報を抽出
                            step_info = {
                                'text': step_text,
                                'index': i
                            }
                            
                            # 駅名を探す
                            station_match = re.search(r'([^\s]+駅)', step_text)
                            if station_match:
                                step_info['station'] = station_match.group(1).replace('駅', '')
                            
                            # 路線名を探す
                            line_match = re.search(r'((?:JR|東京メトロ|都営|東急|京王|小田急|西武|東武|京成|京浜東北|山手|中央|総武|[^\s]+)線)', step_text)
                            if line_match:
                                step_info['line'] = line_match.group(1)
                            
                            # 時間を探す
                            time_match = re.search(r'(\d+)\s*分', step_text)
                            if time_match:
                                step_info['duration'] = int(time_match.group(1))
                            
                            steps_info.append(step_info)
                            
                    except Exception as e:
                        logger.debug(f"Error parsing step {i}: {e}")
                        continue
                        
                if steps_info:
                    return steps_info
                    
        except Exception as e:
            continue
    
    return steps_info

def click_route_details(driver):
    """ルート詳細を展開する（複数の方法を試す）"""
    try:
        # 方法1: ルートコンテナをクリック
        route_selectors = [
            "//div[@data-trip-index='0']",
            "//button[@data-trip-index='0']",
            "//div[contains(@class, 'section-directions-trip-0')]",
            "//div[contains(@class, 'directions-mode-group')]//div[contains(@class, 'trip')]"
        ]
        
        for selector in route_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    element = elements[0]
                    # スクロールして要素を表示
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    # クリック
                    try:
                        element.click()
                    except:
                        # JavaScriptでクリック
                        driver.execute_script("arguments[0].click();", element)
                    
                    logger.info(f"Clicked route with selector: {selector}")
                    time.sleep(3)
                    return True
                    
            except Exception as e:
                continue
        
        # 方法2: 詳細ボタンを探す
        detail_buttons = [
            "//button[contains(text(), '詳細')]",
            "//button[contains(text(), 'Details')]",
            "//span[contains(text(), '詳細')]/..",
            "//button[contains(@aria-label, '詳細')]"
        ]
        
        for selector in detail_buttons:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    logger.info(f"Clicked details button: {selector}")
                    time.sleep(3)
                    return True
            except:
                continue
                
        return False
        
    except Exception as e:
        logger.error(f"Error clicking route details: {e}")
        return False

def extract_route_from_summary(driver):
    """ルートサマリーから情報を抽出する（フォールバック用）"""
    try:
        # ルートサマリーのテキストを取得
        summary_selectors = [
            "//div[@data-trip-index='0']",
            "//div[contains(@class, 'section-directions-trip-0')]",
            "//div[contains(@class, 'directions-mode-group')]"
        ]
        
        for selector in summary_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                summary_text = elements[0].text
                logger.info(f"Route summary text: {summary_text[:200]}...")
                
                # 路線名を抽出
                lines = []
                line_patterns = [
                    r'((?:JR|東京メトロ|都営|東急|京王|小田急|西武|東武|京成|[^\s]+)線)',
                    r'([^\s]+Line)',
                    r'(山手線|京浜東北線|中央線|総武線|東西線|有楽町線|半蔵門線|銀座線|丸ノ内線)'
                ]
                
                for pattern in line_patterns:
                    matches = re.findall(pattern, summary_text)
                    lines.extend(matches)
                
                # 駅名を抽出
                stations = []
                station_patterns = [
                    r'([^\s→]+駅)',
                    r'→\s*([^\s→]+)',
                    r'([^\s]+Station)'
                ]
                
                for pattern in station_patterns:
                    matches = re.findall(pattern, summary_text)
                    stations.extend([s.replace('駅', '').replace('Station', '') for s in matches])
                
                # 時間を抽出
                total_time = parse_duration_text(summary_text) or 30
                
                return {
                    'lines': lines,
                    'stations': stations,
                    'total_time': total_time,
                    'summary_text': summary_text
                }
                
        return None
        
    except Exception as e:
        logger.error(f"Error extracting from summary: {e}")
        return None

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
            EC.presence_of_element_located((By.XPATH, "//div[@id='directions-searchbox-0'] | //div[@class='section-directions-trip-0']"))
        )
        
        # 電車モードを確実に選択
        time.sleep(3)
        wait_and_click_transit_mode(driver)
        
        # ルート情報が読み込まれるまで待機
        time.sleep(5)
        
        # ルート詳細を展開
        click_route_details(driver)
        
        # 詳細なステップ情報を抽出
        steps_info = extract_route_steps_detailed(driver)
        
        # サマリーからも情報を抽出（バックアップ）
        summary_info = extract_route_from_summary(driver)
        
        # 結果を構築
        walk_to_station = 5
        walk_from_station = 5
        wait_time_minutes = 3
        trains = []
        station_used = None
        total_minutes = 30
        
        # ステップ情報から詳細を構築
        if steps_info:
            logger.info(f"[{request_id}] Processing {len(steps_info)} detailed steps")
            
            for i, step in enumerate(steps_info):
                if 'line' in step and step.get('line'):
                    train_info = {
                        'line': step['line'],
                        'time': step.get('duration', 10),
                        'from': step.get('station', '不明'),
                        'to': '不明'
                    }
                    
                    # 次のステップから到着駅を探す
                    for j in range(i+1, len(steps_info)):
                        if 'station' in steps_info[j]:
                            train_info['to'] = steps_info[j]['station']
                            break
                    
                    trains.append(train_info)
                    
                    if not station_used and train_info['from'] != '不明':
                        station_used = train_info['from']
                
                # 徒歩時間の抽出
                if '徒歩' in step.get('text', '') and 'duration' in step:
                    if i == 0:
                        walk_to_station = step['duration']
                    elif i == len(steps_info) - 1:
                        walk_from_station = step['duration']
        
        # サマリー情報を使用（ステップ情報が不十分な場合）
        if not trains and summary_info:
            logger.info(f"[{request_id}] Using summary information as fallback")
            
            # 総時間
            total_minutes = summary_info.get('total_time', 30)
            
            # 路線と駅の情報から電車情報を構築
            if summary_info.get('lines'):
                for i, line in enumerate(summary_info['lines'][:3]):  # 最大3路線まで
                    train_time = max((total_minutes - walk_to_station - walk_from_station - wait_time_minutes) // len(summary_info['lines']), 5)
                    
                    from_station = '不明'
                    to_station = '不明'
                    
                    if summary_info.get('stations'):
                        if i * 2 < len(summary_info['stations']):
                            from_station = summary_info['stations'][i * 2]
                        if i * 2 + 1 < len(summary_info['stations']):
                            to_station = summary_info['stations'][i * 2 + 1]
                    
                    trains.append({
                        'line': line,
                        'time': train_time,
                        'from': from_station,
                        'to': to_station
                    })
                    
                    if not station_used and from_station != '不明':
                        station_used = from_station
        
        # 最終フォールバック（何も取得できなかった場合）
        if not trains:
            logger.warning(f"[{request_id}] Creating minimal fallback route")
            
            # ページ全体から時間を探す
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            total_minutes = parse_duration_text(page_text) or 30
            
            train_time = total_minutes - walk_to_station - walk_from_station - wait_time_minutes
            trains = [{
                'line': '電車',
                'time': max(train_time, 10),
                'from': origin.split('、')[0] if '、' in origin else origin.split(' ')[0],
                'to': destination.split('、')[0] if '、' in destination else destination.split(' ')[0]
            }]
            
            station_used = trains[0]['from']
        
        # レスポンスの構築
        route_details = {
            'wait_time_minutes': wait_time_minutes,
            'walk_to_station': walk_to_station,
            'station_used': station_used or '不明',
            'trains': trains,
            'walk_from_station': walk_from_station
        }
        
        # 総所要時間の再計算
        recalculated_total = (
            wait_time_minutes + 
            walk_to_station + 
            walk_from_station +
            sum(train.get('time', 10) for train in trains)
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Success in {duration:.2f}s, total time: {recalculated_total} minutes")
        logger.info(f"[{request_id}] Extracted {len(trains)} train segments")
        for train in trains:
            logger.info(f"[{request_id}] Train: {train['line']} ({train['time']}min) {train['from']} -> {train['to']}")
        
        # デバッグ用スクリーンショット（成功時も保存）
        if os.environ.get('DEBUG', '').lower() == 'true':
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/debug_screenshots')
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshot_dir / f'google_maps_success_{timestamp}.png'
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
                'total_time': recalculated_total,
                'original_total_time': total_minutes,
                'details': route_details
            },
            'debug_info': {
                'steps_found': len(steps_info),
                'trains_extracted': len(trains),
                'extraction_method': 'detailed' if steps_info else 'summary' if summary_info else 'fallback'
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
            'message': 'Usage: python google_maps_transit_improved.py <origin> <destination> [arrival_time]'
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