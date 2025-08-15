#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v2
改良版：複数路線・長距離ルートに対応

主な改善点：
1. より長い待機時間で完全な読み込みを確認
2. 複数のルートオプションを正しく取得
3. 1時間以上の時間表記に対応
4. エラー時の詳細なデバッグ情報出力
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import json
import logging
from datetime import datetime
import os
from urllib.parse import urlencode

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# デバッグディレクトリの設定
DEBUG_DIR = os.path.join(os.path.dirname(__file__), 'debug')
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

def create_google_maps_url(origin, destination, mode='transit', departure_time=None, arrival_time=None):
    """Google MapsのURLを生成"""
    from urllib.parse import quote
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    
    # 時刻指定がある場合はdata=ブロブ形式を使用
    if departure_time or arrival_time:
        base_url = f"https://www.google.com/maps/dir/{encoded_origin}/{encoded_destination}"
        
        time_type_param = ""
        timestamp_param = ""
        
        if departure_time and isinstance(departure_time, datetime):
            time_type_param = "!6e0"  # 出発時刻
            timestamp = int(departure_time.timestamp())
            timestamp_param = f"!8j{timestamp}"
            logger.info(f"Using departure time: {departure_time} (timestamp: {timestamp})")
        
        elif arrival_time and isinstance(arrival_time, datetime):
            time_type_param = "!6e1"  # 到着時刻
            timestamp = int(arrival_time.timestamp())
            timestamp_param = f"!8j{timestamp}"
            logger.info(f"Using arrival time: {arrival_time} (timestamp: {timestamp})")
        
        # dataブロブの構造
        # 実際のURLから正確な構造をコピー
        # !3e3 は公共交通機関モード
        data_blob = f"/data=!3m6!1m0!1m2!1s{encoded_origin}!2s{encoded_destination}!3e3{time_type_param}{timestamp_param}!4e0"
        
        return base_url + data_blob
    else:
        # 時刻指定なしの場合はシンプルな形式
        url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_destination}&travelmode={mode}"
        return url

def save_debug_info(driver, filename_prefix):
    """デバッグ情報を保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # HTMLソースを保存
    html_path = os.path.join(DEBUG_DIR, f"{filename_prefix}_{timestamp}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    logger.info(f"Saved HTML source to {html_path}")
    
    # スクリーンショットを保存
    screenshot_path = os.path.join(DEBUG_DIR, f"{filename_prefix}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    logger.info(f"Saved screenshot to {screenshot_path}")
    
    return html_path, screenshot_path

def parse_duration_text(text):
    """
    時間テキストをパース（1時間以上にも対応）
    例: "1時間7分" -> 67, "69分" -> 69
    """
    if not text:
        return None
    
    total_minutes = 0
    
    # 時間を抽出
    hour_match = re.search(r'(\d+)\s*時間', text)
    if hour_match:
        total_minutes += int(hour_match.group(1)) * 60
    
    # 分を抽出
    min_match = re.search(r'(\d+)\s*分', text)
    if min_match:
        total_minutes += int(min_match.group(1))
    
    return total_minutes if total_minutes > 0 else None

def wait_for_routes_to_load(driver, timeout=30):
    """ルート情報が完全に読み込まれるまで待機"""
    wait = WebDriverWait(driver, timeout)
    
    try:
        logger.info("Waiting for route information to load...")
        
        # 現在のスクレイパーと同じセレクタを使用
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
        
        # 追加の待機時間を設定（動的コンテンツの完全な読み込みのため）
        time.sleep(3)
        
        return True
        
    except TimeoutException:
        logger.error("Timeout waiting for route details")
        # デバッグのために現在のページソースの一部を出力
        try:
            page_source_snippet = driver.page_source[:1000]
            logger.error(f"Page source snippet: {page_source_snippet}")
        except:
            pass
        return False

def extract_all_routes(driver):
    """すべてのルートオプションを抽出"""
    routes = []
    
    try:
        # 現在のスクレイパーと同じセレクタを使用
        route_options = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        
        logger.info(f"Found {len(route_options)} route options")
        
        for i, option in enumerate(route_options):
            try:
                route_info = extract_route_info_from_option(option)
                if route_info and route_info.get('total_time'):
                    routes.append(route_info)
                    logger.info(f"Route {i+1}: {route_info['total_time']} minutes")
            except Exception as e:
                logger.error(f"Error extracting route {i+1}: {e}")
        
        # ルートが見つからない場合、ページソースから直接抽出を試みる
        if not routes:
            logger.warning("No routes found with data-trip-index, trying page source extraction...")
            routes = extract_routes_from_page_source(driver)
        
    except Exception as e:
        logger.error(f"Error extracting routes: {e}")
    
    return routes

def extract_route_info_from_option(option_element):
    """個別のルートオプションから情報を抽出"""
    route_info = {
        'total_time': None,
        'trains': [],
        'raw_text': ''
    }
    
    try:
        # オプション要素のテキストを取得
        text = option_element.text
        route_info['raw_text'] = text
        
        # 総所要時間を探す
        lines = text.split('\n')
        for line in lines:
            duration = parse_duration_text(line)
            if duration and duration > 30:  # 30分以上を総所要時間と判断
                route_info['total_time'] = duration
                break
        
        # 路線情報を抽出
        train_pattern = r'(.*線|JR.*)'
        for line in lines:
            if re.search(train_pattern, line):
                route_info['trains'].append(line.strip())
        
    except Exception as e:
        logger.debug(f"Error extracting route info: {e}")
    
    return route_info

def extract_routes_from_page_source(driver):
    """ページソースから直接ルート情報を抽出（フォールバック）"""
    routes = []
    page_source = driver.page_source
    
    try:
        # 時間のパターンマッチング
        # 例: "67 分", "1 時間 7 分"
        time_pattern = r'(?:(\d+)\s*時間\s*)?(\d+)\s*分'
        time_matches = re.findall(time_pattern, page_source)
        
        seen_times = set()
        for match in time_matches:
            hours = int(match[0]) if match[0] else 0
            minutes = int(match[1])
            total_minutes = hours * 60 + minutes
            
            # 妥当な範囲の時間のみを採用（10分〜180分）
            if 10 <= total_minutes <= 180 and total_minutes not in seen_times:
                seen_times.add(total_minutes)
                route_info = {
                    'total_time': total_minutes,
                    'trains': [],
                    'raw_text': f"{hours}時間{minutes}分" if hours > 0 else f"{minutes}分"
                }
                routes.append(route_info)
                logger.info(f"Found route time from page source: {total_minutes} minutes")
        
        # 路線情報も抽出を試みる
        line_pattern = r'((?:JR|東京メトロ|都営|京王|小田急|東急|西武|東武)[^\s]+線)'
        line_matches = re.findall(line_pattern, page_source)
        
        if line_matches and routes:
            # 最初のルートに路線情報を追加
            routes[0]['trains'] = list(set(line_matches))[:3]  # 最大3路線まで
            
    except Exception as e:
        logger.error(f"Error extracting from page source: {e}")
    
    return routes

def extract_routes_alternative(driver):
    """代替方法でルート情報を抽出"""
    routes = []
    
    try:
        # より広範な要素を探す
        main_content = driver.find_element(By.XPATH, "//div[@role='main']")
        
        # 時間情報を含むテキストブロックを探す
        time_blocks = main_content.find_elements(By.XPATH, ".//*[contains(text(), '分') or contains(text(), '時間')]")
        
        for block in time_blocks:
            try:
                parent = block.find_element(By.XPATH, "./ancestor::div[@role='option' or @data-trip-index]")
                text = parent.text
                
                duration = parse_duration_text(text)
                if duration and duration > 30:
                    route_info = {
                        'total_time': duration,
                        'trains': [],
                        'raw_text': text
                    }
                    
                    # 路線情報を抽出
                    lines = text.split('\n')
                    for line in lines:
                        if re.search(r'(.*線|JR.*)', line):
                            route_info['trains'].append(line.strip())
                    
                    # 重複を避ける
                    if not any(r['total_time'] == duration for r in routes):
                        routes.append(route_info)
                        
            except Exception as e:
                logger.debug(f"Error in alternative extraction: {e}")
    
    except Exception as e:
        logger.error(f"Alternative extraction failed: {e}")
    
    return routes

def scrape_route(origin, destination, departure_time=None, arrival_time=None, save_debug=True):
    """
    指定された出発地と目的地の経路情報をスクレイピング
    """
    driver = None
    try:
        # Chrome設定
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
        
        # ドライバー起動（Selenium Gridを使用）
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        driver.implicitly_wait(10)
        
        # Google Mapsにアクセス
        url = create_google_maps_url(origin, destination, departure_time=departure_time, arrival_time=arrival_time)
        logger.info(f"Accessing: {url}")
        driver.get(url)
        
        # ルート情報の読み込みを待機
        if not wait_for_routes_to_load(driver):
            logger.error("Failed to load routes")
            if save_debug:
                save_debug_info(driver, f"error_{origin[:10]}-{destination[:10]}")
            return None
        
        # デバッグ情報を保存
        if save_debug:
            save_debug_info(driver, f"success_{origin[:10]}-{destination[:10]}")
        
        # すべてのルート情報を抽出
        routes = extract_all_routes(driver)
        
        if not routes:
            logger.error("No route information could be extracted")
            return None
        
        # 最短時間のルートを選択
        shortest_route = min(routes, key=lambda r: r['total_time'])
        
        result = {
            'origin': origin,
            'destination': destination,
            'travel_time': shortest_route['total_time'],
            'all_routes': routes,
            'scraped_at': datetime.now().isoformat()
        }
        
        logger.info(f"Successfully scraped route: {origin} -> {destination}")
        logger.info(f"Travel time: {result['travel_time']} minutes")
        logger.info(f"Found {len(routes)} route options")
        
        return result
        
    except Exception as e:
        logger.error(f"Error scraping route: {e}")
        if driver and save_debug:
            save_debug_info(driver, f"exception_{origin[:10]}-{destination[:10]}")
        return None
        
    finally:
        if driver:
            driver.quit()

def test_fuchu_route():
    """府中ルートのテスト"""
    origin = "東京都千代田区神田須田町1-20-1"
    destination = "東京都府中市住吉町5-22-5"
    
    logger.info("=" * 50)
    logger.info("府中ルートのテスト - 3つのパターン")
    logger.info("=" * 50)
    
    # 1. 現在時刻での検索
    print("\n1. 現在時刻での検索:")
    result1 = scrape_route(origin, destination, save_debug=True)
    if result1:
        print(f"  最短所要時間: {result1['travel_time']}分")
    
    # 2. 9時出発での検索（ゴールデンデータ: 67分）
    print("\n2. 9時出発での検索（ゴールデンデータ: 67分）:")
    tomorrow = datetime.now() + timedelta(days=1)
    departure_9am = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    result2 = scrape_route(origin, destination, departure_time=departure_9am, save_debug=True)
    if result2:
        print(f"  最短所要時間: {result2['travel_time']}分")
        if result2['all_routes']:
            print("  すべてのルート:")
            for i, route in enumerate(result2['all_routes']):
                print(f"    ルート{i+1}: {route['total_time']}分")
    
    # 3. 10時到着での検索（ゴールデンデータ: 69分）
    print("\n3. 10時到着での検索（ゴールデンデータ: 69分）:")
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    result3 = scrape_route(origin, destination, arrival_time=arrival_10am, save_debug=True)
    if result3:
        print(f"  最短所要時間: {result3['travel_time']}分")
        if result3['all_routes']:
            print("  すべてのルート:")
            for i, route in enumerate(result3['all_routes']):
                print(f"    ルート{i+1}: {route['total_time']}分")

if __name__ == "__main__":
    from datetime import timedelta
    test_fuchu_route()