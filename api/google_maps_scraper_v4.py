#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v4
改善版：公共交通機関ボタンクリック、詳細情報取得強化

主な改善点：
1. 公共交通機関ボタンを確実にクリック
2. 徒歩のみルートの表示改善
3. 複数ルート候補からの選択改善
4. 時刻・経路詳細の取得強化
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
from datetime import datetime, timedelta, timezone
import os
from urllib.parse import quote, unquote

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

def setup_driver():
    """Selenium WebDriverのセットアップ"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    # Selenium Gridを使用
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    driver.implicitly_wait(10)
    return driver

def get_place_details(address, driver=None):
    """
    ステップA: 住所からプレイスIDと緯度経度を取得
    """
    place_info = {
        'name': address,
        'address': address,
        'place_id': None,
        'lat': None,
        'lng': None,
        'formatted_address': None,
        'search_url': None,
        'final_url': None
    }
    
    created_driver = False
    if driver is None:
        driver = setup_driver()
        created_driver = True
    
    try:
        # Google Mapsで住所を検索
        search_url = f"https://www.google.com/maps?q={quote(address)}"
        logger.info(f"Searching for address: {address}")
        logger.info(f"Search URL: {search_url}")
        place_info['search_url'] = search_url
        
        driver.get(search_url)
        
        # 検索結果が読み込まれるまで待機
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        # 複数の検索結果がある場合、最初の結果をクリック
        try:
            search_results = driver.find_elements(By.CSS_SELECTOR, "a[data-index='0']")
            if search_results:
                logger.info("Multiple search results found, clicking first result")
                search_results[0].click()
                time.sleep(2)
        except Exception as e:
            logger.debug(f"No multiple search results or error clicking: {e}")
        
        # 現在のURLを取得
        current_url = driver.current_url
        logger.info(f"Current URL after search: {current_url}")
        place_info['final_url'] = current_url
        
        # URLから緯度経度を抽出
        coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
        if coord_match:
            place_info['lat'] = float(coord_match.group(1))
            place_info['lng'] = float(coord_match.group(2))
            logger.info(f"Found coordinates: {place_info['lat']}, {place_info['lng']}")
        else:
            coord_match2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', current_url)
            if coord_match2:
                place_info['lat'] = float(coord_match2.group(1))
                place_info['lng'] = float(coord_match2.group(2))
                logger.info(f"Found coordinates (alternative pattern): {place_info['lat']}, {place_info['lng']}")
        
        # Place IDを抽出
        place_id_match = re.search(r'!1s(0x[0-9a-fA-F:]+)', current_url)
        if place_id_match:
            place_info['place_id'] = place_id_match.group(1)
            logger.info(f"Found place ID: {place_info['place_id']}")
        
        # 住所を抽出
        page_source = driver.page_source
        address_pattern = r'<span[^>]*>([^<]+(?:都|道|府|県)[^<]+)</span>'
        address_matches = re.findall(address_pattern, page_source)
        if address_matches:
            place_info['formatted_address'] = max(address_matches, key=len)
            logger.info(f"Found address: {place_info['formatted_address']}")
        
    except Exception as e:
        logger.error(f"Error getting place details: {e}")
    
    finally:
        if created_driver:
            driver.quit()
    
    return place_info

def build_complete_url(origin_info, dest_info, departure_time=None, arrival_time=None):
    """
    ステップB: 完全なdata=ブロブ形式のURLを構築
    """
    base_url = "https://www.google.com/maps/dir/"
    
    # URLパスに場所名を含める
    path = f"{quote(origin_info['name'])}/{quote(dest_info['name'])}"
    
    # data=ブロブの構築
    data_parts = []
    
    # データ構造のコンテナ
    data_parts.append("!4m18!4m17")
    
    # 出発地のブロック
    data_parts.append("!1m5")
    if origin_info.get('lat') and origin_info.get('lng'):
        data_parts.append(f"!2m2!1d{origin_info['lng']}!2d{origin_info['lat']}")
    
    # 目的地のブロック
    data_parts.append("!1m5")
    if dest_info.get('lat') and dest_info.get('lng'):
        data_parts.append(f"!2m2!1d{dest_info['lng']}!2d{dest_info['lat']}")
    
    # 時刻指定のブロック
    if departure_time or arrival_time:
        data_parts.append("!2m3")
        
        if departure_time and isinstance(departure_time, datetime):
            data_parts.append("!6e0")  # 出発時刻
            timestamp = int(departure_time.timestamp())
            logger.info(f"Using departure time: {departure_time} (timestamp: {timestamp})")
        elif arrival_time and isinstance(arrival_time, datetime):
            data_parts.append("!6e1")  # 到着時刻
            timestamp = int(arrival_time.timestamp())
            logger.info(f"Using arrival time: {arrival_time} (timestamp: {timestamp})")
        
        data_parts.append("!7e2")  # 時刻指定有効化
        data_parts.append(f"!8j{timestamp}")
    
    # 公共交通機関モード
    data_parts.append("!3e3")  # transit mode
    
    # 完全なURLを構築
    full_url = base_url + path + "/data=" + "".join(data_parts)
    
    return full_url

def click_transit_button(driver):
    """公共交通機関ボタンをクリック"""
    transit_clicked = False
    
    # 複数のセレクタパターンを試す
    transit_selectors = [
        "//button[@aria-label='公共交通機関']",
        "//button[@aria-label='Transit']",
        "//button[@data-travel-mode='3']",
        "//div[@data-value='3']//button",
        "//button[contains(@class, 'transit')]",
        "//img[@aria-label='公共交通機関']/..",
        "//div[contains(@aria-label, '公共交通機関')]//button",
        "//button[contains(@aria-label, '電車')]"
    ]
    
    for selector in transit_selectors:
        try:
            transit_btn = driver.find_element(By.XPATH, selector)
            if transit_btn and transit_btn.is_displayed():
                # ボタンが押されていない場合のみクリック
                aria_pressed = transit_btn.get_attribute('aria-pressed')
                if aria_pressed != 'true':
                    transit_btn.click()
                    logger.info(f"Clicked transit button using selector: {selector}")
                    time.sleep(2)
                    transit_clicked = True
                else:
                    logger.info("Transit button already pressed")
                    transit_clicked = True
                break
        except:
            continue
    
    return transit_clicked

def extract_route_details_v4(driver):
    """v4: 改善された経路詳細抽出"""
    routes = []
    
    try:
        # すべてのルートオプションを取得
        route_options = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        logger.info(f"Found {len(route_options)} route options")
        
        for i, option in enumerate(route_options):
            try:
                route_info = {
                    'total_time': None,
                    'departure_time': None,
                    'arrival_time': None,
                    'trains': [],
                    'raw_text': '',
                    'is_transit': True,
                    'is_walking_only': False
                }
                
                # オプションのテキストを取得
                text = option.text
                route_info['raw_text'] = text
                
                # 時間を抽出（より柔軟なパターン）
                time_patterns = [
                    r'(\d+)\s*時間\s*(\d+)\s*分',  # X時間Y分
                    r'(\d+)\s*分',                   # Y分のみ
                    r'(\d+)\s*hr\s*(\d+)\s*min',     # 英語版
                    r'(\d+)\s*min'                    # 英語版（分のみ）
                ]
                
                for pattern in time_patterns:
                    match = re.search(pattern, text)
                    if match:
                        if '時間' in pattern or 'hr' in pattern:
                            if len(match.groups()) == 2:
                                hours = int(match.group(1))
                                minutes = int(match.group(2)) if match.group(2) else 0
                                route_info['total_time'] = hours * 60 + minutes
                            else:
                                route_info['total_time'] = int(match.group(1)) * 60
                        else:
                            route_info['total_time'] = int(match.group(1))
                        break
                
                # 出発・到着時刻を抽出
                time_match = re.search(r'(\d{1,2}:\d{2})\s*[発出]\s*.*?\s*(\d{1,2}:\d{2})\s*[着到]', text)
                if time_match:
                    route_info['departure_time'] = time_match.group(1)
                    route_info['arrival_time'] = time_match.group(2)
                
                # 徒歩のみチェック
                walking_indicators = ['徒歩', '歩い', 'walk', 'Walking']
                transit_indicators = ['駅', '線', '電車', 'バス', '乗換', 'Station', 'Line', 'Bus', 'Train']
                car_indicators = ['車で', '自動車', '高速', '国道', '都道', '県道']
                
                has_walking = any(ind in text for ind in walking_indicators)
                has_transit = any(ind in text for ind in transit_indicators)
                has_car = any(ind in text for ind in car_indicators)
                
                # 判定ロジック
                if has_car and not has_transit:
                    route_info['is_transit'] = False
                elif has_walking and not has_transit and not has_car:
                    route_info['is_walking_only'] = True
                    route_info['trains'] = ['徒歩のみ']
                else:
                    # 路線情報を抽出
                    lines = text.split('\n')
                    for line in lines:
                        if any(ind in line for ind in ['線', 'Line', 'バス', 'Bus']):
                            route_info['trains'].append(line.strip())
                
                if route_info['total_time']:
                    routes.append(route_info)
                    logger.info(f"Route {i+1}: {route_info['total_time']}分 "
                              f"({'徒歩のみ' if route_info['is_walking_only'] else '公共交通機関' if route_info['is_transit'] else '車'})")
                
            except Exception as e:
                logger.error(f"Error extracting route {i+1}: {e}")
        
    except Exception as e:
        logger.error(f"Error in extract_route_details_v4: {e}")
    
    return routes

def scrape_route_v4(origin, destination, departure_time=None, arrival_time=None, save_debug=True):
    """
    v4: 改善版スクレイピング
    """
    driver = None
    try:
        # ドライバー起動
        driver = setup_driver()
        
        # ステップA: 場所の解決
        logger.info("Step A: Resolving place details...")
        origin_info = get_place_details(origin, driver)
        dest_info = get_place_details(destination, driver)
        
        if not (origin_info.get('lat') and dest_info.get('lat')):
            logger.error("Failed to resolve place coordinates")
            return None
        
        # ステップB: 完全なURLの構築
        logger.info("Step B: Building complete URL...")
        url = build_complete_url(origin_info, dest_info, departure_time, arrival_time)
        logger.info(f"Complete URL: {url}")
        
        # ルート検索ページにアクセス
        driver.get(url)
        time.sleep(3)
        
        # 公共交通機関ボタンを確実にクリック
        transit_clicked = click_transit_button(driver)
        if not transit_clicked:
            logger.warning("Could not click transit button, continuing anyway")
        
        # ルート情報が読み込まれるまで待機
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-trip-index]")))
            logger.info("Route options loaded")
        except TimeoutException:
            logger.error("Timeout waiting for routes")
            return None
        
        # 追加の待機
        time.sleep(2)
        
        # v4の改善された抽出メソッドを使用
        routes = extract_route_details_v4(driver)
        
        if not routes:
            logger.error("No route information could be extracted")
            return None
        
        # 公共交通機関のルートを優先、なければ徒歩のみ
        transit_routes = [r for r in routes if r['is_transit'] and not r['is_walking_only']]
        walking_routes = [r for r in routes if r['is_walking_only']]
        
        if transit_routes:
            shortest_route = min(transit_routes, key=lambda r: r['total_time'])
        elif walking_routes:
            shortest_route = walking_routes[0]
            logger.info("Only walking routes available")
        else:
            # 車ルートしかない場合
            shortest_route = min(routes, key=lambda r: r['total_time'])
            logger.warning("Only car routes available")
        
        result = {
            'origin': origin,
            'destination': destination,
            'origin_details': origin_info,
            'destination_details': dest_info,
            'travel_time': shortest_route['total_time'],
            'departure_time': shortest_route.get('departure_time'),
            'arrival_time': shortest_route.get('arrival_time'),
            'route_type': '徒歩のみ' if shortest_route['is_walking_only'] else '公共交通機関' if shortest_route['is_transit'] else '車',
            'route_details': shortest_route.get('trains', []),
            'all_routes': routes,
            'scraped_at': datetime.now().isoformat(),
            'url': url
        }
        
        logger.info(f"Successfully scraped route: {origin} -> {destination}")
        logger.info(f"Travel time: {result['travel_time']} minutes ({result['route_type']})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error scraping route: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def test_v4_improvements():
    """v4改善版のテスト（明日の日付で）"""
    
    # 明日の10時到着（JST）
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00
    
    print("=" * 60)
    print("v4スクレイパーテスト - 改善版")
    print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
    print("=" * 60)
    
    # テストルート（問題があったもの）
    test_routes = [
        {
            "name": "Yawara（詳細なし問題）",
            "origin": "東京都千代田区神田須田町1-20-1",
            "destination": "東京都渋谷区神宮前１丁目８−１０"
        },
        {
            "name": "東京駅（車ルート問題）",
            "origin": "東京都千代田区神田須田町1-20-1",
            "destination": "JR東京駅"  # より具体的な指定
        }
    ]
    
    results = []
    for route in test_routes:
        print(f"\nテスト: {route['name']}")
        result = scrape_route_v4(
            route['origin'],
            route['destination'],
            arrival_time=arrival_10am,
            save_debug=False
        )
        
        if result:
            print(f"✅ 成功")
            print(f"  所要時間: {result['travel_time']}分")
            print(f"  ルートタイプ: {result['route_type']}")
            if result['route_details']:
                print(f"  詳細: {', '.join(result['route_details'][:3])}")
            results.append(result)
        else:
            print(f"❌ 失敗")
    
    return results

if __name__ == "__main__":
    test_v4_improvements()