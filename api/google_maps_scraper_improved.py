#!/usr/bin/env python3
"""
Google Maps Transit Scraping API - Improved Version
複数路線・長距離ルートに対応した改良版
Updated: 2025-08-15
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
    """Parse duration text like '15分' or '15 min' or '1時間7分' to integer minutes"""
    # 時間と分のパターン
    hour_min_match = re.search(r'(\d+)\s*時間\s*(\d+)\s*分', text)
    if hour_min_match:
        hours = int(hour_min_match.group(1))
        minutes = int(hour_min_match.group(2))
        return hours * 60 + minutes
    
    # 分のみのパターン
    min_match = re.search(r'(\d+)\s*(?:分|min)', text)
    if min_match:
        return int(min_match.group(1))
    
    return 0

def extract_route_from_expanded_trip(driver, trip_element):
    """
    展開された旅程から詳細なルート情報を抽出（複数路線対応版）
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
        # 1. 全体の所要時間を取得
        duration_selectors = [
            ".//span[contains(@class, 'duration')]",
            ".//div[contains(@class, 'duration')]",
            ".//span[contains(text(), '分')]",
            ".//div[contains(text(), '分')]"
        ]
        
        for selector in duration_selectors:
            duration_elems = trip_element.find_elements(By.XPATH, selector)
            for elem in duration_elems:
                text = elem.text.strip()
                if text:
                    duration = parse_duration_text(text)
                    if duration > 0:
                        route_info['total_time'] = duration
                        logger.info(f"Found total duration: {duration} minutes")
                        break
            if route_info['total_time']:
                break
        
        # 2. ステップ要素を探す（複数のパターンを試す）
        step_selectors = [
            ".//div[contains(@class, 'section-directions-trip-line')]",
            ".//div[contains(@class, 'transit-step')]",
            ".//div[contains(@class, 'directions-mode-step')]",
            ".//li[contains(@class, 'step')]",
            ".//div[@role='listitem']"
        ]
        
        step_elements = []
        for selector in step_selectors:
            step_elements = trip_element.find_elements(By.XPATH, selector)
            if step_elements:
                logger.info(f"Found {len(step_elements)} steps with selector: {selector}")
                break
        
        # 3. 各ステップを解析
        walk_times = []
        for i, step_elem in enumerate(step_elements):
            step_text = step_elem.text.strip()
            logger.debug(f"Step {i}: {step_text[:100]}...")
            
            # 徒歩の場合
            if '徒歩' in step_text or 'walk' in step_text.lower():
                duration = parse_duration_text(step_text)
                if duration > 0:
                    walk_times.append(duration)
                    logger.info(f"Found walk step: {duration} minutes")
            
            # 電車の場合
            elif '線' in step_text:
                # 路線名を抽出
                line_patterns = [
                    r'([\u4e00-\u9fff]+線)',  # 日本語の線名
                    r'(JR[\u4e00-\u9fff]+線)',  # JR線
                    r'(京王[\u4e00-\u9fff]+)',  # 京王線など
                    r'(地下鉄[\u4e00-\u9fff]+線)'  # 地下鉄線
                ]
                
                line_name = None
                for pattern in line_patterns:
                    match = re.search(pattern, step_text)
                    if match:
                        line_name = match.group(1)
                        break
                
                # 駅名を抽出
                station_pattern = r'([\u4e00-\u9fff]+駅)'
                stations = re.findall(station_pattern, step_text)
                
                # 時間を抽出
                duration = parse_duration_text(step_text)
                
                if line_name and len(stations) >= 2:
                    train_info = {
                        'line': line_name,
                        'time': duration if duration > 0 else 10,  # デフォルト10分
                        'from': stations[0].replace('駅', ''),
                        'to': stations[-1].replace('駅', '')
                    }
                    
                    # 時刻情報があれば追加
                    time_pattern = r'(\d{1,2}:\d{2})'
                    times = re.findall(time_pattern, step_text)
                    if times:
                        train_info['departure'] = times[0]
                        if len(times) > 1:
                            train_info['arrival'] = times[1]
                    
                    route_info['trains'].append(train_info)
                    logger.info(f"Found train: {line_name} from {train_info['from']} to {train_info['to']}")
                    
                    # 最初の駅を記録
                    if not route_info['station_used']:
                        route_info['station_used'] = train_info['from']
        
        # 4. 徒歩時間を設定
        if walk_times:
            route_info['walk_to_station'] = walk_times[0]
            if len(walk_times) > 1:
                route_info['walk_from_station'] = walk_times[-1]
            else:
                route_info['walk_from_station'] = 5  # デフォルト
        
        # 5. データの検証
        if not route_info['trains']:
            logger.warning("No train information extracted")
            return None
        
        return route_info
        
    except Exception as e:
        logger.error(f"Error in route extraction: {e}")
        logger.debug(traceback.format_exc())
        return None

def save_debug_info(driver, request_id):
    """
    デバッグ情報を保存（スクリーンショットとHTML）
    """
    if not os.environ.get('DEBUG', '').lower() == 'true':
        return
        
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/debug')
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # スクリーンショット保存
        screenshot_path = debug_dir / f'screenshot_{request_id}_{timestamp}.png'
        driver.save_screenshot(str(screenshot_path))
        logger.info(f"Screenshot saved: {screenshot_path}")
        
        # HTML保存
        html_path = debug_dir / f'page_source_{request_id}_{timestamp}.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"HTML saved: {html_path}")
        
    except Exception as e:
        logger.error(f"Failed to save debug info: {e}")

def scrape_route(origin, destination):
    """
    Google Mapsから経路情報をスクレイピング（改良版）
    """
    driver = None
    origin = normalize_address(origin)
    destination = normalize_address(destination)
    
    # リクエストIDを生成（デバッグ用）
    request_id = f"{origin[:10]}-{destination[:10]}".replace(' ', '').replace(',', '')
    
    try:
        driver = setup_driver()
        logger.info(f"Scraping route from '{origin}' to '{destination}'")
        
        # URLを構築（日本時間の朝9時出発を指定）
        base_url = "https://www.google.com/maps/dir/"
        params = {
            'api': '1',
            'origin': origin,
            'destination': destination,
            'travelmode': 'transit',
            'departure_time': '9am'  # 朝9時出発
        }
        
        # パラメータをURLエンコード
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        
        # ページの読み込みを待つ
        wait = WebDriverWait(driver, 30)
        
        # 経路が表示されるまで待つ
        route_container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[role='main']"))
        )
        
        # 追加の待機
        time.sleep(3)
        
        # デバッグ情報を保存
        save_debug_info(driver, request_id)
        
        # 経路オプションを探す
        trip_selectors = [
            "div[data-trip-index]",
            "div.section-directions-trip",
            "div[jsaction*='directions']",
            "div[role='listitem']"
        ]
        
        trip_elements = []
        for selector in trip_selectors:
            trip_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if trip_elements:
                logger.info(f"Found {len(trip_elements)} trip options with selector: {selector}")
                break
        
        if not trip_elements:
            logger.error("No trip elements found")
            return None
        
        # 最初の経路を選択してクリック
        first_trip = trip_elements[0]
        try:
            # クリック可能になるまで待つ
            wait.until(EC.element_to_be_clickable(first_trip))
            first_trip.click()
            time.sleep(2)
        except:
            logger.warning("Could not click trip element")
        
        # 展開された経路情報を取得
        route_info = extract_route_from_expanded_trip(driver, driver.find_element(By.CSS_SELECTOR, "[role='main']"))
        
        if route_info and route_info['trains']:
            logger.info(f"Successfully extracted route with {len(route_info['trains'])} trains")
            return route_info
        else:
            logger.error("Failed to extract route information")
            return None
        
    except TimeoutException:
        logger.error(f"Timeout waiting for route: {origin} -> {destination}")
        return None
    except Exception as e:
        logger.error(f"Error scraping route: {e}")
        logger.debug(traceback.format_exc())
        return None
    finally:
        if driver:
            driver.quit()

def main():
    if len(sys.argv) != 4:
        print("Usage: python google_maps_scraper_improved.py <origin> <destination> <property_id>")
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    property_id = normalize_id(sys.argv[3])
    
    # スクレイピング実行
    route_info = scrape_route(origin, destination)
    
    if route_info:
        # 結果を整形
        result = {
            "property_id": property_id,
            "origin": origin,
            "destination": destination,
            "route_info": route_info,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # JSON形式で出力
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        error_result = {
            "property_id": property_id,
            "origin": origin,
            "destination": destination,
            "error": "Failed to scrape route information",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()