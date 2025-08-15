#!/usr/bin/env python3
"""
Google Maps Transit Scraping API - Ultimate Version
コンポーネントベース抽出による堅牢なルート情報取得
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
    level=logging.DEBUG if os.environ.get('DEBUG', '').lower() == 'true' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_id(text_id):
    """
    ID正規化関数：ハイフンをアンダースコアに変換
    destinations.jsonとproperties.jsonのID形式を統一
    """
    return text_id.lower().replace('-', '_')

def normalize_address(address):
    """
    住所文字列をGoogle Mapsが解釈しやすい形式に正規化する
    """
    if not address:
        return address
    
    original = address
    
    # 1. 全角英数字を半角に変換
    address = address.translate(str.maketrans(
        '０１２３４５６７８９',
        '0123456789'
    ))
    address = address.translate(str.maketrans(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ))
    address = address.translate(str.maketrans(
        'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
        'abcdefghijklmnopqrstuvwxyz'
    ))
    
    # 2. 丁目・番地・号をハイフン形式に統一
    address = re.sub(r'(\d+)丁目\s*', r'\1-', address)
    address = re.sub(r'(\d+)番地?\s*', r'\1-', address)
    address = re.sub(r'(\d+)号\s*', r'\1', address)
    
    # 3. 不要なスペースを削除
    address = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', address)
    address = re.sub(r'(\d+)\s+(?=[^\u4e00-\u9fff])', r'\1', address)
    
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

def ensure_transit_mode(driver):
    """
    公共交通機関モードが選択されていることを確認し、必要に応じて選択する
    """
    try:
        wait = WebDriverWait(driver, 5)
        
        # 公共交通機関ボタンを探す（複数のセレクタを試す）
        transit_selectors = [
            "button[aria-label*='公共交通機関']",
            "button[aria-label*='Transit']",
            "button[data-value='transit']",
            "img[src*='transit']",
            "div[data-travel-mode='transit']"
        ]
        
        for selector in transit_selectors:
            try:
                transit_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                # aria-pressedまたは選択状態を確認
                is_selected = transit_button.get_attribute('aria-pressed') == 'true'
                if not is_selected:
                    # 親要素がボタンの場合もあるので確認
                    parent = transit_button.find_element(By.XPATH, '..')
                    if parent.tag_name.lower() == 'button':
                        is_selected = parent.get_attribute('aria-pressed') == 'true'
                        if not is_selected:
                            parent.click()
                            logger.info("Clicked parent transit button")
                    else:
                        transit_button.click()
                        logger.info("Clicked transit button")
                    
                    # モード切り替えの完了を待つ
                    time.sleep(3)
                    return True
                else:
                    logger.info("Transit mode already selected")
                    return True
                    
            except (TimeoutException, NoSuchElementException):
                continue
                
        # URLにtravelmode=transitが含まれていれば、モードは正しいと判断
        if 'travelmode=transit' in driver.current_url or 'data=!3e3' in driver.current_url:
            logger.info("Transit mode confirmed via URL")
            return True
            
        logger.warning("Could not confirm transit mode selection")
        return False
        
    except Exception as e:
        logger.error(f"Error ensuring transit mode: {e}")
        return False

def wait_for_route_details(driver, timeout=30):
    """
    ルート候補が完全に読み込まれるまで待機
    """
    wait = WebDriverWait(driver, timeout)
    
    try:
        # 少なくとも1つのルート候補が表示されるまで待つ
        route_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-trip-index]"))
        )
        logger.info("Route options are present on the page")
        
        # ルート内に時間情報が含まれているか確認
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-trip-index]//*[contains(text(), '分')]"))
        )
        logger.info("Route timing information is loaded")
        
        return True
        
    except TimeoutException:
        logger.error("Timeout waiting for route details")
        return False

def expand_route_details(driver, trip_element):
    """
    ルート詳細を展開し、完全に読み込まれるまで待機
    """
    try:
        # 現在の要素数を記録
        initial_elements = len(driver.find_elements(By.XPATH, "//*"))
        
        # クリックして展開
        try:
            trip_element.click()
        except:
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", trip_element)
        
        logger.info("Clicked trip element to expand details")
        
        # 展開アニメーションの完了を待つ
        time.sleep(2)
        
        # 要素数が増えたか確認（詳細が展開されたか）
        wait = WebDriverWait(driver, 10)
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//*")) > initial_elements)
        
        logger.info("Route details expanded successfully")
        return True
        
    except Exception as e:
        logger.warning(f"Could not expand route details: {e}")
        return False

def extract_step_component(step_element):
    """
    個別のステップ要素からコンポーネント情報を抽出
    """
    step_info = {
        'type': 'unknown',
        'raw_text': step_element.text.strip()
    }
    
    try:
        # 1. アイコンから交通手段を判定
        try:
            icon_imgs = step_element.find_elements(By.TAG_NAME, 'img')
            for img in icon_imgs:
                src = img.get_attribute('src') or ''
                alt = img.get_attribute('alt') or ''
                
                if any(word in src.lower() for word in ['walk', 'walking']):
                    step_info['type'] = 'walk'
                    break
                elif any(word in src.lower() for word in ['transit', 'train', 'subway']):
                    step_info['type'] = 'transit'
                    break
        except:
            pass
        
        # 2. aria-labelから情報を取得
        try:
            aria_labels = step_element.find_elements(By.XPATH, ".//*[@aria-label]")
            for elem in aria_labels:
                label = elem.get_attribute('aria-label')
                if label:
                    # 時間情報
                    duration = parse_duration_text(label)
                    if duration:
                        step_info['duration'] = duration
                    
                    # 駅名
                    station_match = re.search(r'([^\s]+駅)', label)
                    if station_match:
                        step_info['station'] = station_match.group(1).replace('駅', '')
                    
                    # 路線名
                    line_match = re.search(r'([^\s]+線)', label)
                    if line_match:
                        step_info['line'] = line_match.group(1)
        except:
            pass
        
        # 3. テキストベースの判定（フォールバック）
        text = step_info['raw_text']
        
        if step_info['type'] == 'unknown':
            if any(word in text.lower() for word in ['徒歩', 'walk', '歩']):
                step_info['type'] = 'walk'
            elif any(word in text for word in ['線', 'Line', 'JR', '東急', '東京メトロ', '都営']):
                step_info['type'] = 'transit'
        
        # 4. 詳細情報の抽出
        if step_info['type'] == 'walk':
            duration = parse_duration_text(text)
            if duration:
                step_info['duration'] = duration
                
        elif step_info['type'] == 'transit':
            # 路線名
            if 'line' not in step_info:
                line_patterns = [
                    r'([^\s]+線)',
                    r'(JR[^\s]+)',
                    r'(東京メトロ[^\s]+)',
                    r'(都営[^\s]+)',
                ]
                for pattern in line_patterns:
                    match = re.search(pattern, text)
                    if match:
                        step_info['line'] = match.group(1)
                        break
            
            # 駅名（出発・到着）
            station_patterns = [
                r'([^\s]+駅)(?:から|発)',  # 出発駅
                r'([^\s]+駅)(?:まで|着)',  # 到着駅
                r'([^\s]+)駅',  # 一般的な駅名
            ]
            
            stations = []
            for pattern in station_patterns:
                matches = re.findall(pattern, text)
                stations.extend([m.replace('駅', '') for m in matches])
            
            if stations:
                step_info['from_station'] = stations[0]
                if len(stations) > 1:
                    step_info['to_station'] = stations[-1]
            
            # 時刻情報
            time_pattern = r'(\d+:\d+)(?:発|着)'
            time_matches = re.findall(time_pattern, text)
            if time_matches:
                if len(time_matches) >= 1:
                    step_info['departure_time'] = time_matches[0]
                if len(time_matches) >= 2:
                    step_info['arrival_time'] = time_matches[1]
            
            # 所要時間
            if 'duration' not in step_info:
                duration = parse_duration_text(text)
                if duration:
                    step_info['duration'] = duration
    
    except Exception as e:
        logger.debug(f"Error extracting step component: {e}")
    
    return step_info

def extract_route_components(driver, trip_element):
    """
    展開されたルート詳細からコンポーネントベースで情報を抽出
    """
    route_info = {
        'total_time': None,
        'trains': [],
        'walk_to_station': None,
        'walk_from_station': None,
        'station_used': None,
        'steps': []
    }
    
    try:
        # 1. 総所要時間を取得
        try:
            time_elem = trip_element.find_element(By.XPATH, ".//*[contains(text(), '分')]")
            route_info['total_time'] = parse_duration_text(time_elem.text)
        except:
            logger.warning("Could not find total time in trip element")
        
        # 2. ステップ要素を探す（複数のパターンを試す）
        step_selectors = [
            ".//div[contains(@class, 'transit-step')]",
            ".//div[contains(@class, 'directions-mode-step')]",
            ".//li[contains(@class, 'step')]",
            ".//div[@role='listitem']",
            ".//div[contains(@class, 'section-directions-trip-line')]"
        ]
        
        step_elements = []
        for selector in step_selectors:
            step_elements = trip_element.find_elements(By.XPATH, selector)
            if step_elements:
                logger.info(f"Found {len(step_elements)} steps with selector: {selector}")
                break
        
        if not step_elements:
            # より広範囲で探す
            step_elements = trip_element.find_elements(By.XPATH, ".//div[@jsaction]")
            step_elements = [e for e in step_elements if e.text.strip()]
            logger.info(f"Found {len(step_elements)} potential steps with broad selector")
        
        # 3. 各ステップを解析
        for i, step_elem in enumerate(step_elements):
            step_info = extract_step_component(step_elem)
            route_info['steps'].append(step_info)
            
            # 情報を整理
            if step_info['type'] == 'walk':
                if i == 0:
                    route_info['walk_to_station'] = step_info.get('duration')
                elif i == len(step_elements) - 1:
                    route_info['walk_from_station'] = step_info.get('duration')
                    
            elif step_info['type'] == 'transit':
                # 必須情報が揃っている場合のみ追加
                if step_info.get('line') and step_info.get('from_station') and step_info.get('to_station'):
                    train_info = {
                        'line': step_info.get('line'),
                        'time': step_info.get('duration') or 0,
                        'from': step_info.get('from_station'),
                        'to': step_info.get('to_station')
                    }
                
                    if 'departure_time' in step_info:
                        train_info['departure'] = step_info['departure_time']
                    if 'arrival_time' in step_info:
                        train_info['arrival'] = step_info['arrival_time']
                    
                    route_info['trains'].append(train_info)
                    
                    # 最初の駅を記録
                    if not route_info['station_used']:
                        route_info['station_used'] = train_info['from']
        
        # 4. データの検証と補完
        if not route_info['trains']:
            logger.warning("No train information extracted from components")
        else:
            logger.info(f"Extracted {len(route_info['trains'])} train segments")
            for train in route_info['trains']:
                logger.info(f"Train: {train['line']} ({train['time']}min) {train['from']} -> {train['to']}")
        
        return route_info
        
    except Exception as e:
        logger.error(f"Error in component extraction: {e}")
        logger.debug(traceback.format_exc())
        return route_info

def extract_route_fallback(driver):
    """
    フォールバック：ページ全体から情報を抽出（詳細版）
    """
    logger.info("Using fallback page-wide extraction")
    
    # ページ全体のHTMLを取得
    page_source = driver.page_source
    
    route_info = {
        'total_time': None,  # デフォルト値を使わない
        'trains': [],
        'walk_to_station': None,
        'walk_from_station': None,
        'station_used': None
    }
    
    # HTMLソースから情報を抽出
    # 1. 全体の所要時間を探す - 新しいパターン
    # 例: 12:59 <span class="hPzYFf">（8 分
    total_time_pattern = r'(\d+:\d+)\s*<span[^>]*>\s*（\s*(\d+)\s*分'
    total_time_match = re.search(total_time_pattern, page_source)
    if total_time_match:
        route_info['total_time'] = int(total_time_match.group(2))
        logger.info(f"Found total time: {route_info['total_time']} minutes")
    else:
        # 旧パターンも試す
        total_time_pattern = r'\[(\d+),"(\d+)\s*分",\d+\](?:,null,\[)'
        total_time_matches = re.findall(total_time_pattern, page_source)
        if total_time_matches:
            total_seconds = int(total_time_matches[0][0])
            route_info['total_time'] = (total_seconds + 30) // 60
            logger.info(f"Found total time (old pattern): {route_info['total_time']} minutes")
    
    # 2. 駅名と路線情報を抽出
    # 新パターン: 神田駅から <span class="">12:55</span>
    departure_info_pattern = r'>([^<]+駅)から\s*<span[^>]*>(\d+:\d+)</span>'
    departure_match = re.search(departure_info_pattern, page_source)
    
    # 路線名の抽出: <span class="cukLmd">銀座線</span>
    line_pattern = r'<span[^>]*class="cukLmd"[^>]*>([^<]+線)</span>'
    line_match = re.search(line_pattern, page_source)
    
    # 徒歩時間の抽出: </span> 5 分 (徒歩アイコンの後)
    walk_pattern = r'aria-label="徒歩"[^>]*>[^<]*</span>\s*(\d+)\s*分'
    walk_matches = list(re.finditer(walk_pattern, page_source))
    
    if walk_matches:
        # 最初の徒歩時間
        route_info['walk_to_station'] = int(walk_matches[0].group(1))
        # 最後の徒歩時間（複数ある場合）
        if len(walk_matches) > 1:
            route_info['walk_from_station'] = int(walk_matches[-1].group(1))
    
    # 駅情報の組み立て
    if departure_match:
        from_station = departure_match.group(1).replace('駅', '')
        departure_time = departure_match.group(2)
        route_info['station_used'] = from_station
        
        # 到着駅を特定できない場合は不明とする
        to_station = None
        
        # 路線情報と組み合わせ
        if line_match and to_station:
            # 徒歩時間が取得できている場合のみ、電車時間を計算
            if route_info['total_time'] and route_info['walk_to_station'] is not None and route_info['walk_from_station'] is not None:
                train_time = route_info['total_time'] - route_info['walk_to_station'] - route_info['walk_from_station']
                if train_time > 0:
                    train_info = {
                        'line': line_match.group(1),
                        'time': train_time,
                        'from': from_station,
                        'to': to_station,
                        'departure': departure_time
                    }
                    route_info['trains'].append(train_info)
                    logger.info(f"Found train: {train_info['line']} from {from_station} at {departure_time}")
    
    # 旧パターンのフォールバック
    if not route_info['trains']:
        # より詳細なパターン: ["神田駅","G13",null,[時刻情報]...]
        station_pattern = r'\["([^"]+駅)","([^"]*)"(?:,null)?,\[([^\]]+)\][^\[]*\[null,null,([\d.]+),([\d.]+)\]'
        station_matches = list(re.finditer(station_pattern, page_source))
        
        if len(station_matches) >= 2:
            # 出発駅と到着駅
            from_match = station_matches[0]
            to_match = station_matches[1]
            
            from_station = from_match.group(1).replace('駅', '')
            to_station = to_match.group(1).replace('駅', '')
            route_info['station_used'] = from_station
            
            # 時刻情報を解析
            departure_time = None
            arrival_time = None
            
            # 時刻パターン: [1755142980,"Asia/Tokyo","12:43",32400,...]
            time_info_pattern = r'\[(\d+),"[^"]*","(\d+:\d+)",'
            
            from_time_search = re.search(time_info_pattern, from_match.group(3))
            if from_time_search:
                departure_time = from_time_search.group(2)
            
            # 到着駅の時刻は前方検索
            to_time_pattern = to_match.group(1) + r'[^[]*\[(\d+),"[^"]*","(\d+:\d+)",'
            to_time_search = re.search(to_time_pattern, page_source)
            if to_time_search:
                arrival_time = to_time_search.group(2)
            
            # 3. 路線情報を探す
            line_pattern = r'\["([^"]+線)",\d+,"([^"]*)"(?:,"[^"]*")?\]'
            line_match = re.search(line_pattern, page_source)
            
            if line_match:
                line_name = line_match.group(1)
                
                # 電車の乗車時間を計算
                train_time_pattern = r'\[(\d+),"(\d+)\s*分",\d+\][^[]*' + re.escape(line_name)
                train_time_match = re.search(train_time_pattern, page_source)
                train_duration = 3  # デフォルト
                
                if train_time_match:
                    train_duration = int(train_time_match.group(1)) // 60
                
                train_info = {
                    'line': line_name,
                    'time': train_duration,
                    'from': from_station,
                    'to': to_station
                }
                
                # 時刻情報を追加
                if departure_time:
                    train_info['departure'] = departure_time
                if arrival_time:
                    train_info['arrival'] = arrival_time
                
                route_info['trains'].append(train_info)
                
                logger.info(f"Found train: {line_name} from {from_station} to {to_station} ({train_duration}min)")
    
    # 旧パターンでの徒歩時間抽出（新パターンで取得できなかった場合）
    if route_info['walk_to_station'] is None or route_info['walk_from_station'] is None:
        # 徒歩のパターン: [[2,null,[距離,距離表示,0],[時間,時間表示,秒],
        walk_detailed_pattern = r'\[\[2,null,\[\d+,"[^"]+",0\],\[(\d+),"([^"]+)",(\d+)\][^\]]*"徒歩"'
        walk_matches_old = list(re.finditer(walk_detailed_pattern, page_source))
        
        if walk_matches_old:
            # 最初の徒歩 = 駅まで
            first_walk = walk_matches_old[0]
            walk_seconds = int(first_walk.group(1))
            route_info['walk_to_station'] = (walk_seconds + 30) // 60
            
            # 最後の徒歩 = 駅から
            if len(walk_matches_old) > 1:
                last_walk = walk_matches_old[-1]
                walk_seconds = int(last_walk.group(1))
                route_info['walk_from_station'] = (walk_seconds + 30) // 60
    
    # ルート情報が取得できなかった場合はNoneを返す
    if not route_info['trains']:
        logger.warning("No train information could be extracted from page source")
        return None
    
    return route_info

def save_debug_info(driver, request_id, trip_element=None):
    """
    デバッグ情報を保存（スクリーンショットとHTML）
    """
    if not os.environ.get('DEBUG', '').lower() == 'true':
        return
        
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/debug')
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # スクリーンショット
        screenshot_path = debug_dir / f'{request_id}_{timestamp}.png'
        driver.save_screenshot(str(screenshot_path))
        logger.info(f"Saved screenshot: {screenshot_path}")
        
        # HTML保存
        if trip_element:
            html_path = debug_dir / f'{request_id}_{timestamp}.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(trip_element.get_attribute('innerHTML'))
            logger.info(f"Saved HTML: {html_path}")
            
    except Exception as e:
        logger.error(f"Error saving debug info: {e}")

def extract_route_details(driver, origin, destination, arrival_time=None, departure_time=None):
    """
    Extract transit route details from Google Maps
    コンポーネントベース抽出を採用した最終版
    """
    start_time = datetime.now()
    request_id = f"{origin[:10]}-{destination[:10]}-{start_time.timestamp()}"
    logger.info(f"[{request_id}] Starting route search: {origin} -> {destination}")
    
    # 住所の正規化
    origin = normalize_address(origin)
    destination = normalize_address(destination)
    logger.info(f"[{request_id}] Normalized addresses - Origin: {origin}, Destination: {destination}")
    
    # URL構築
    from urllib.parse import quote
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    
    # Google Maps Direction API v1形式
    url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_destination}&travelmode=transit"
    
    if arrival_time and isinstance(arrival_time, datetime):
        timestamp = int(arrival_time.timestamp())
        url += f"&arrival_time={timestamp}"
        logger.info(f"Using arrival time: {arrival_time} (timestamp: {timestamp})")
    elif departure_time and isinstance(departure_time, datetime):
        timestamp = int(departure_time.timestamp())
        url += f"&departure_time={timestamp}"
        logger.info(f"Using departure time: {departure_time} (timestamp: {timestamp})")
    
    logger.info(f"[{request_id}] Loading URL: {url}")
    
    try:
        # ページ読み込み
        driver.get(url)
        
        # Step 1: 基盤の安定化
        if not wait_for_route_details(driver):
            return {
                'status': 'error',
                'message': 'Failed to load route information'
            }
        
        # 公共交通機関モードの確認
        ensure_transit_mode(driver)
        
        # Wait for trip elements to load
        time.sleep(3)
        
        # Save screenshot for debugging
        debug_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/debug')
        debug_dir.mkdir(exist_ok=True)
        session_id = f"{origin[:10]}-{destination[:10]}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        screenshot_path = debug_dir / f"screenshot_{session_id}.png"
        driver.save_screenshot(str(screenshot_path))
        logger.info(f"Saved screenshot to: {screenshot_path}")
        
        # Save page source for debugging
        page_source_path = debug_dir / f"page_source_{session_id}.html"
        with open(page_source_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"Saved page source to: {page_source_path}")
        
        # ルート要素を取得（複数のセレクタを試す）
        trip_elements = []
        trip_selectors = [
            '[data-trip-index="0"]',
            '[data-trip-index]',
            'div[role="option"]',
            'div.Hk4XGb',
            'div.TbDNX'
        ]
        
        for selector in trip_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    # 最初の要素をクリックしてみる
                    trip_elements = elements
                    break
            except Exception as e:
                logger.debug(f"Failed to find elements with {selector}: {e}")
        
        if not trip_elements:
            logger.error(f"[{request_id}] No trip elements found with any selector")
            return {
                'status': 'error',
                'message': 'No route information found'
            }
        
        trip_element = trip_elements[0]
        
        # Step 2: ルート詳細の展開
        details_expanded = expand_route_details(driver, trip_element)
        
        # デバッグ情報を保存
        save_debug_info(driver, request_id, trip_element)
        
        # Step 3: コンポーネントベース抽出
        route_info = None
        
        if details_expanded:
            route_info = extract_route_components(driver, trip_element)
            
        # Step 4: フォールバック処理
        if not route_info or not route_info.get('trains'):
            logger.warning(f"[{request_id}] Component extraction failed, using fallback")
            fallback_info = extract_route_fallback(driver)
            if fallback_info:
                route_info = fallback_info
            else:
                # ルート情報が全く取得できない場合
                logger.error(f"[{request_id}] Failed to extract any route information")
                return {
                    'status': 'error',
                    'message': 'No route information could be extracted',
                    'extraction_info': {
                        'method': 'failed',
                        'details_expanded': details_expanded,
                        'request_id': request_id
                    }
                }
        
        # データ検証
        if not route_info.get('total_time'):
            logger.error(f"[{request_id}] Total time not found in route info")
            return {
                'status': 'error',
                'message': 'Total travel time could not be determined',
                'extraction_info': {
                    'method': 'partial',
                    'details_expanded': details_expanded,
                    'request_id': request_id
                }
            }
        
        # レスポンスの構築
        route_details = {
            'wait_time_minutes': 3,
            'walk_to_station': route_info.get('walk_to_station'),
            'station_used': route_info.get('station_used'),
            'trains': route_info.get('trains', []),
            'walk_from_station': route_info.get('walk_from_station')
        }
        
        # 妥当性チェック
        total_minutes = route_info.get('total_time')
        if origin.lower().find('府中') >= 0 or destination.lower().find('府中') >= 0:
            # 府中へのルートは最低でも30分はかかるはず
            if total_minutes < 30:
                logger.error(f"[{request_id}] Suspicious route time to/from Fuchu: {total_minutes} minutes")
                return {
                    'status': 'error',
                    'message': f'Route time seems incorrect: {total_minutes} minutes to/from Fuchu',
                    'extraction_info': {
                        'method': 'validation_failed',
                        'details_expanded': details_expanded,
                        'request_id': request_id,
                        'extracted_time': total_minutes
                    }
                }
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Success in {duration:.2f}s, total time: {total_minutes} minutes")
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'arrival' if arrival_time else 'departure',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A'),
                'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M:%S') if arrival_time and isinstance(arrival_time, datetime) else None,
                'departure_time': departure_time.strftime('%Y-%m-%d %H:%M:%S') if departure_time and isinstance(departure_time, datetime) else None
            },
            'route': {
                'total_time': total_minutes,
                'details': route_details
            },
            'extraction_info': {
                'method': 'component' if route_info.get('steps') else 'fallback',
                'details_expanded': details_expanded,
                'steps_found': len(route_info.get('steps', [])),
                'trains_extracted': len(route_details['trains'])
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
        logger.debug(traceback.format_exc())
        
        save_debug_info(driver, request_id)
        
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
            'message': 'Usage: python google_maps_transit_ultimate.py <origin> <destination> [departure|arrival] [time]'
        }))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = None
    departure_time = None
    
    if len(sys.argv) > 3:
        mode = sys.argv[3]
        if len(sys.argv) > 4:
            time_str = sys.argv[4]
            try:
                if time_str == '9AM':
                    # 今日の9AMを設定
                    today = datetime.now()
                    departure_time = today.replace(hour=9, minute=0, second=0, microsecond=0)
                elif time_str == '10AM':
                    # 今日の10AMを設定
                    today = datetime.now()
                    arrival_time = today.replace(hour=10, minute=0, second=0, microsecond=0)
                else:
                    # 時刻文字列をパース
                    time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    if mode == 'arrival':
                        arrival_time = time_obj
                    else:
                        departure_time = time_obj
            except:
                pass
    
    driver = None
    try:
        driver = setup_driver()
        result = extract_route_details(driver, origin, destination, arrival_time, departure_time)
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