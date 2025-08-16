#!/usr/bin/env python3
"""
Google Maps Transit Scraping API - Docker version (Improved)
住所正規化、セレクタ管理、待機処理の改善版
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    4. 建物名を除去（オプション）
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
    
    # 4. 建物名の除去（コメントアウト - Google Mapsでは建物名も重要）
    # # 最後のハイフン以降で、数字で始まらない部分を削除
    # # 例: "港区芝1-2-3 ABCビル" → "港区芝1-2-3"
    # address = re.sub(r'\s+[^\d\s]+$', '', address)
    
    # ログ出力
    if address != original:
        logger.info(f"Address normalized: '{original}' → '{address}'")
    
    return address

def load_selectors_config():
    """
    セレクタ設定を読み込む
    外部ファイルが存在しない場合は、デフォルト設定を返す
    """
    config_path = Path(__file__).parent / 'selectors.json'
    
    # デフォルト設定
    default_config = {
        "route_container": [
            "[data-trip-index=\"0\"]",
            "div[role=\"button\"][data-trip-index=\"0\"]",
            "div.Ylt4Kd"
        ],
        "total_time": [
            "span[jsan*=\"分\"]",
            "span[jstcache*=\"duration\"]",
            "div.Fk3sm span",
            "span.xB1mrd"
        ],
        "steps": [
            "div.cYhGGe",
            "div[role=\"listitem\"]",
            "div.VLwlLc",
            "div.T4gWAd"
        ],
        "line_patterns": [
            "([^、\\n]*線)",
            "(JR[^\\n]*線)",
            "([^\\n]*Line)",
            "(東京メトロ[^\\n]*)",
            "(都営[^\\n]*)"
        ],
        "station_patterns": [
            "([^\\n]+駅)",
            "([^\\n]+[Ss]tation)",
            "→\\s*([^\\n]+)"
        ],
        "walking_keywords": ["徒歩", "walk", "歩", "à pied", "walking"],
        "transit_keywords": ["線", "Line", "Metro", "地下鉄", "JR", "東急", "京王", "小田急", "西武", "東武", "京成", "都営"]
    }
    
    # 外部ファイルがあれば読み込む
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # デフォルト設定とマージ（外部ファイルの設定を優先）
                default_config.update(loaded_config)
                logger.info(f"Loaded selectors config from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load selectors config: {e}, using defaults")
    
    return default_config

def setup_driver():
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
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

def build_url(origin, destination, arrival_time=None):
    """
    URL構築（安全な形式のみ使用）
    
    Args:
        origin: 出発地
        destination: 目的地  
        arrival_time: 到着時刻（datetime object）
    
    Returns:
        構築されたURL
    """
    from urllib.parse import quote
    
    base_url = "https://www.google.com/maps/dir/"
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    
    # 安全な形式のみを使用
    url = f"{base_url}{encoded_origin}/{encoded_destination}/?travelmode=transit"
    
    if arrival_time and isinstance(arrival_time, datetime):
        # 到着時刻の指定
        # 注意: この形式は変更される可能性があるため、定期的な確認が必要
        timestamp = int(arrival_time.timestamp())
        # arrival_timeパラメータを試す（より新しい形式）
        url += f"&arrival_time={timestamp}"
        logger.info(f"Using arrival time: {arrival_time} (timestamp: {timestamp})")
    
    return url

def wait_for_element(driver, selectors, timeout=10, context=None):
    """
    複数のセレクタから最初に見つかった要素を待機して返す
    
    Args:
        driver: WebDriver instance
        selectors: セレクタのリスト
        timeout: タイムアウト秒数
        context: 検索コンテキスト（要素内で検索する場合）
    
    Returns:
        見つかった要素、見つからない場合はNone
    """
    wait = WebDriverWait(driver, timeout)
    
    for selector in selectors:
        try:
            if context:
                element = wait.until(
                    lambda d: context.find_element(By.CSS_SELECTOR, selector)
                )
            else:
                element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            logger.debug(f"Found element with selector: {selector}")
            return element
        except TimeoutException:
            continue
    
    return None

def extract_route_details(driver, origin, destination, arrival_time=None):
    """Extract transit route details from Google Maps"""
    
    # セレクタ設定を読み込む
    selectors = load_selectors_config()
    
    start_time = datetime.now()
    request_id = f"{origin[:10]}-{destination[:10]}-{start_time.timestamp()}"
    logger.info(f"[{request_id}] Starting route search: {origin} -> {destination}")
    
    # 住所の正規化
    origin = normalize_address(origin)
    destination = normalize_address(destination)
    logger.info(f"[{request_id}] Normalized addresses - Origin: {origin}, Destination: {destination}")
    
    # URL構築とページ読み込み
    url = build_url(origin, destination, arrival_time)
    logger.info(f"[{request_id}] Loading URL: {url}")
    
    try:
        driver.get(url)
        
        # ルート情報が読み込まれるまで待機
        route_element = wait_for_element(driver, selectors['route_container'], timeout=30)
        
        if not route_element:
            logger.error(f"[{request_id}] Could not find route element")
            return {
                "status": "error",
                "message": "Failed to load route information",
                "origin": origin,
                "destination": destination
            }
        
        logger.info(f"[{request_id}] Route information loaded")
        
        # 電車ルートが確実に選択されるように待機
        time.sleep(5)
    
        # 総所要時間の抽出
        total_minutes = None
        time_element = wait_for_element(driver, selectors['total_time'], timeout=5, context=route_element)
        
        if time_element:
            total_minutes = parse_duration_text(time_element.text)
        
        if not total_minutes:
            # フォールバック: route_element全体から時間を探す
            route_text = route_element.text
            total_minutes = parse_duration_text(route_text) or 30
            logger.warning(f"[{request_id}] Using fallback total time: {total_minutes} minutes")
        else:
            logger.info(f"[{request_id}] Found total time: {total_minutes} minutes")
        
        # ルートをクリックして詳細を展開
        try:
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", route_element)
            time.sleep(3)
            
            # 詳細が表示されたか確認
            details_visible = False
            for selector in selectors['steps']:
                if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0:
                    details_visible = True
                    break
            
            if details_visible:
                logger.info(f"[{request_id}] Expanded route details")
            else:
                logger.warning(f"[{request_id}] Route details not visible, trying alternative method")
                # 別の方法を試す
                try:
                    details_button = driver.find_element(By.XPATH, "//button[contains(text(), '詳細')] | //button[contains(text(), 'Details')]")
                    details_button.click()
                    time.sleep(2)
                except:
                    pass
        except Exception as e:
            logger.warning(f"[{request_id}] Could not expand route details: {str(e)}")
        
        # ルート詳細の初期化
        walk_to_station = 0
        walk_from_station = 0
        station_used = None
        trains = []
        wait_time_minutes = 3  # デフォルト待ち時間
        
        # ステップの検索（複数の方法を試す）
        steps = []
        
        # 方法1: CSSセレクタ
        for selector in selectors['steps']:
            steps = driver.find_elements(By.CSS_SELECTOR, selector)
            if steps:
                logger.info(f"[{request_id}] Found {len(steps)} steps with CSS: {selector}")
                break
        
        # 方法2: XPathで探す
        if not steps:
            xpath_patterns = [
                "//div[contains(@class, 'transit-step')]",
                "//div[contains(@class, 'directions-step')]",
                "//div[@role='listitem']",
                "//div[contains(@class, 'section-directions-trip-step')]"
            ]
            for xpath in xpath_patterns:
                steps = driver.find_elements(By.XPATH, xpath)
                if steps:
                    logger.info(f"[{request_id}] Found {len(steps)} steps with XPath: {xpath}")
                    break
        
        # 各ステップを解析
        for i, step in enumerate(steps):
            try:
                step_text = step.text.strip()
                
                if not step_text:
                    continue
                
                logger.debug(f"[{request_id}] Step {i}: {step_text[:50]}...")
                
                # 徒歩ステップの判定
                if any(keyword in step_text.lower() for keyword in selectors['walking_keywords']):
                    duration = parse_duration_text(step_text)
                    if duration > 0:
                        if i == 0:
                            walk_to_station = duration
                            logger.info(f"[{request_id}] Walk to station: {duration} minutes")
                        elif i == len(steps) - 1:
                            walk_from_station = duration
                            logger.info(f"[{request_id}] Walk from station: {duration} minutes")
                        else:
                            # 乗り換え時の徒歩
                            logger.info(f"[{request_id}] Transfer walk: {duration} minutes")
                
                # 電車ステップの判定
                elif any(keyword in step_text for keyword in selectors['transit_keywords']):
                    # 路線名の抽出
                    line_name = None
                    for pattern in selectors['line_patterns']:
                        match = re.search(pattern, step_text)
                        if match:
                            line_name = match.group(1)
                            break
                    
                    if not line_name:
                        line_name = '不明'
                    
                    # 所要時間の抽出
                    duration = parse_duration_text(step_text) or 10
                    
                    # 駅名の抽出
                    stations = []
                    for pattern in selectors['station_patterns']:
                        matches = re.findall(pattern, step_text)
                        stations.extend(matches)
                    
                    # 駅名のクリーンアップ
                    stations = [s.replace('駅', '').replace('Station', '').strip() for s in stations]
                    stations = [s for s in stations if s]
                    
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
                    
                    trains.append(train_info)
                    logger.info(f"[{request_id}] Train: {line_name} ({duration}min) {from_station} -> {to_station}")
                    
            except Exception as e:
                logger.debug(f"[{request_id}] Error parsing step {i}: {str(e)}")
                continue
        
        # 簡易ルートの作成（詳細が取得できない場合）
        if not trains and total_minutes:
            logger.warning(f"[{request_id}] No detailed steps found, creating simple route")
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
            sum(train['time'] for train in trains)
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Success in {duration:.2f}s, total time: {recalculated_total or total_minutes} minutes")
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'arrival' if arrival_time else 'departure',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A'),
                'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M:%S') if arrival_time and isinstance(arrival_time, datetime) else None
            },
            'route': {
                'total_time': recalculated_total or total_minutes,
                'original_total_time': total_minutes,
                'details': route_details
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
            'message': 'Usage: python google_maps_transit_docker.py <origin> <destination> [arrival_time]'
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