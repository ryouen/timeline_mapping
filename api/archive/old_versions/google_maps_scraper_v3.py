#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v3
2ステップ戦略による時刻指定対応版

主な改善点：
1. 場所解決機能：住所からプレイスIDと緯度経度を取得
2. 完全なdata=ブロブ形式のURL構築
3. 時刻指定の確実な動作
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
    住所での検索により曖昧さを排除し、確実に場所を特定する
    """
    place_info = {
        'name': address,  # 住所をそのまま名前として保持
        'address': address,
        'place_id': None,
        'lat': None,
        'lng': None,
        'formatted_address': None,
        'search_url': None,  # 検索に使用したURL
        'final_url': None    # リダイレクト後のURL
    }
    
    created_driver = False
    if driver is None:
        driver = setup_driver()
        created_driver = True
    
    try:
        # Google Mapsで住所を検索（曖昧さを排除するため住所を使用）
        search_url = f"https://www.google.com/maps?q={quote(address)}"
        logger.info(f"Searching for address: {address}")
        logger.info(f"Search URL: {search_url}")
        place_info['search_url'] = search_url
        
        driver.get(search_url)
        
        # 検索結果が読み込まれるまで待機
        wait = WebDriverWait(driver, 15)
        
        # URLが変更されるまで待つ（検索結果が表示される）
        time.sleep(3)
        
        # 複数の検索結果がある場合、最初の結果をクリック
        try:
            # 検索結果のリストを探す
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
        # パターン1: @35.6812362,139.7671248
        coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
        if coord_match:
            place_info['lat'] = float(coord_match.group(1))
            place_info['lng'] = float(coord_match.group(2))
            logger.info(f"Found coordinates: {place_info['lat']}, {place_info['lng']}")
        else:
            # パターン2: !3d35.6812362!4d139.7671248
            coord_match2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', current_url)
            if coord_match2:
                place_info['lat'] = float(coord_match2.group(1))
                place_info['lng'] = float(coord_match2.group(2))
                logger.info(f"Found coordinates (alternative pattern): {place_info['lat']}, {place_info['lng']}")
        
        # ページソースから正しい形式のプレイスIDを抽出
        page_source = driver.page_source
        
        # ChIJ形式のplace_idを検索（これが正しい完全な形式）
        # より包括的なパターンで検索
        place_id_patterns = [
            r'"(ChIJ[A-Za-z0-9_-]+)"',  # 標準的なChIJ形式
            r'place_id[":\s]+["\']?(ChIJ[A-Za-z0-9_-]+)["\']?',  # place_idフィールド
            r'data-place-id=["\']?(ChIJ[A-Za-z0-9_-]+)["\']?',  # data属性
            r'placeid[":\s]+["\']?(ChIJ[A-Za-z0-9_-]+)["\']?',  # 別の形式
            r'/place/[^/]+/(ChIJ[A-Za-z0-9_-]+)',  # URLパス内
        ]
        
        place_id_found = False
        for pattern in place_id_patterns:
            place_id_match = re.search(pattern, page_source, re.IGNORECASE)
            if place_id_match:
                place_info['place_id'] = place_id_match.group(1)
                logger.info(f"Found place ID: {place_info['place_id']}")
                place_id_found = True
                break
        
        if not place_id_found:
            # フォールバック: 0x形式も保持
            place_id_match = re.search(r'!1s(0x[0-9a-fA-F:]+)', current_url)
            if place_id_match:
                place_info['place_id'] = place_id_match.group(1)
                logger.info(f"Found place ID (0x format - incomplete): {place_info['place_id']}")
        
        # ページソースからも情報を抽出
        page_source = driver.page_source
        
        # 住所を抽出
        address_pattern = r'<span[^>]*>([^<]+(?:都|道|府|県)[^<]+)</span>'
        address_matches = re.findall(address_pattern, page_source)
        if address_matches:
            # 最も長い住所を選択（通常、より詳細）
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
    if origin_info.get('place_id') and origin_info['place_id'].startswith('ChIJ'):
        data_parts.append(f"!1m1!1s{origin_info['place_id']}")
    if origin_info.get('lat') and origin_info.get('lng'):
        data_parts.append(f"!2m2!1d{origin_info['lng']}!2d{origin_info['lat']}")
    
    # 目的地のブロック
    data_parts.append("!1m5")
    if dest_info.get('place_id') and dest_info['place_id'].startswith('ChIJ'):
        data_parts.append(f"!1m1!1s{dest_info['place_id']}")
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
        
        data_parts.append("!7e2")  # フラグ（詳細不明だが必要）
        data_parts.append(f"!8j{timestamp}")
    
    # 公共交通機関モード
    data_parts.append("!3e3")  # transit mode
    
    # 完全なURLを構築
    full_url = base_url + path + "/data=" + "".join(data_parts)
    
    # URL構造をシンプルに（travelmode=transitは不要、!3e3があれば十分）
    
    return full_url

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
    時間テキストをパース（すべての時間に対応）
    例: "1時間7分" -> 67, "69分" -> 69, "7分" -> 7
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
        
        # まず公共交通機関モードが選択されているか確認
        try:
            # 公共交通機関ボタンがアクティブか確認（複数のセレクタを試す）
            transit_selectors = [
                "//button[@aria-label='公共交通機関']",
                "//button[@data-travel-mode='3']",
                "//div[@data-value='3']//button",
                "//button[contains(@class, 'transit')][@aria-pressed='true']"
            ]
            
            transit_active = False
            for selector in transit_selectors:
                try:
                    transit_btn = driver.find_element(By.XPATH, selector)
                    if transit_btn and (transit_btn.get_attribute('aria-pressed') == 'true' or 
                                      'selected' in transit_btn.get_attribute('class') or 
                                      'active' in transit_btn.get_attribute('class')):
                        transit_active = True
                        logger.info("Transit mode is active")
                        break
                except:
                    continue
                    
            if not transit_active:
                logger.warning("Transit mode may not be active, trying to click transit button")
                # 公共交通機関ボタンをクリックしてみる
                for selector in transit_selectors:
                    try:
                        transit_btn = driver.find_element(By.XPATH, selector)
                        transit_btn.click()
                        logger.info("Clicked transit button")
                        time.sleep(2)
                        break
                    except:
                        continue
        except Exception as e:
            logger.debug(f"Could not verify transit mode: {e}")
        
        # ルート候補が表示されるまで待つ
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
        return False

def extract_route_info_from_option(option_element):
    """個別のルートオプションから情報を抽出"""
    route_info = {
        'total_time': None,
        'trains': [],
        'raw_text': '',
        'is_transit': True  # デフォルトで公共交通機関と仮定
    }
    
    try:
        # オプション要素のテキストを取得
        text = option_element.text
        route_info['raw_text'] = text
        
        # 車ルートの兆候をチェック
        # 首都高速や中央自動車道などの明確な道路名
        highway_names = ['首都高速', '中央自動車道', '東名高速']
        car_indicators = ['車で', '自動車']
        transit_indicators = ['駅', '線', '電車', 'バス', '徒歩', '乗換', '発', '着', 'ホーム']
        
        has_highway_name = any(highway in text for highway in highway_names)
        has_car_indicator = any(indicator in text for indicator in car_indicators)
        has_transit_indicator = any(indicator in text for indicator in transit_indicators)
        
        # 車ルートの判定（明確な場合のみ）
        if has_highway_name:
            # 高速道路名が含まれている場合は確実に車ルート
            route_info['is_transit'] = False
            logger.debug(f"Detected car route (highway name): {text[:50]}...")
        elif has_car_indicator and not has_transit_indicator:
            # 「車で」「自動車」があり、公共交通機関の指標がない場合
            route_info['is_transit'] = False
            logger.debug(f"Detected car route: {text[:50]}...")
        
        # 総所要時間を探す
        lines = text.split('\n')
        for line in lines:
            duration = parse_duration_text(line)
            if duration:  # すべての時間を受け入れる
                route_info['total_time'] = duration
                break
        
        # 路線情報を抽出（徒歩、駅名、路線名を含む）
        transport_pattern = r'(徒歩|.*駅|.*線|JR.*|地下鉄.*|メトロ.*|.*バス|乗換)'
        for line in lines:
            if re.search(transport_pattern, line) and not re.search(r'^\d+分$', line):
                route_info['trains'].append(line.strip())
        
    except Exception as e:
        logger.debug(f"Error extracting route info: {e}")
    
    return route_info

def extract_all_routes(driver):
    """すべてのルートオプションを抽出"""
    routes = []
    
    try:
        # ルートオプションを取得
        route_options = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        
        logger.info(f"Found {len(route_options)} route options")
        
        transit_routes_count = 0
        car_routes_count = 0
        
        for i, option in enumerate(route_options):
            try:
                route_info = extract_route_info_from_option(option)
                if route_info and route_info.get('total_time'):
                    # 公共交通機関のルートのみを含める
                    if route_info.get('is_transit', True):
                        routes.append(route_info)
                        transit_routes_count += 1
                        logger.info(f"Route {i+1}: {route_info['total_time']} minutes (transit)")
                    else:
                        car_routes_count += 1
                        logger.info(f"Route {i+1}: {route_info['total_time']} minutes (car - skipped)")
            except Exception as e:
                logger.error(f"Error extracting route {i+1}: {e}")
        
        logger.info(f"Extracted {transit_routes_count} transit routes, skipped {car_routes_count} car routes")
        
    except Exception as e:
        logger.error(f"Error extracting routes: {e}")
    
    return routes

def scrape_route(origin, destination, departure_time=None, arrival_time=None, save_debug=True):
    """
    指定された出発地と目的地の経路情報をスクレイピング
    2ステップ戦略を使用
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
        
        # 少し待機してページが完全に読み込まれるのを確認
        time.sleep(2)
        
        # 公共交通機関ボタンを明示的にクリック（念のため）
        try:
            transit_button_selectors = [
                "//button[@aria-label='公共交通機関']",
                "//button[@aria-label='Transit']",
                "//button[@data-travel-mode='3']",
                "//div[@data-value='3']//button",
                "//button[contains(@class, 'transit-mode')]",
                "//img[@aria-label='公共交通機関']/..",
                "//div[@aria-label='公共交通機関']//button"
            ]
            
            for selector in transit_button_selectors:
                try:
                    transit_btn = driver.find_element(By.XPATH, selector)
                    if transit_btn and transit_btn.is_displayed():
                        # ボタンが押されていない場合のみクリック
                        if transit_btn.get_attribute('aria-pressed') != 'true':
                            transit_btn.click()
                            logger.info("Clicked transit button to ensure transit mode")
                            time.sleep(2)
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"Could not click transit button: {e}")
        
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
            'origin_details': origin_info,
            'destination_details': dest_info,
            'travel_time': shortest_route['total_time'],
            'all_routes': routes,
            'scraped_at': datetime.now().isoformat(),
            'url': url
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
    logger.info("府中ルートのテスト - v3（2ステップ戦略）")
    logger.info("=" * 50)
    
    # 9時出発での検索（ゴールデンデータ: 67分）
    print("\n9時出発での検索（ゴールデンデータ: 67分）:")
    tomorrow = datetime.now() + timedelta(days=1)
    departure_9am = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    
    result = scrape_route(origin, destination, departure_time=departure_9am, save_debug=True)
    
    if result:
        print(f"\n結果:")
        print(f"出発地: {result['origin']}")
        print(f"  座標: {result['origin_details']['lat']}, {result['origin_details']['lng']}")
        print(f"目的地: {result['destination']}")
        print(f"  座標: {result['destination_details']['lat']}, {result['destination_details']['lng']}")
        print(f"最短所要時間: {result['travel_time']}分")
        print(f"\nすべてのルートオプション:")
        for i, route in enumerate(result['all_routes']):
            print(f"  ルート{i+1}: {route['total_time']}分")
            if route['trains']:
                print(f"    路線: {', '.join(route['trains'])}")
    else:
        print("スクレイピングに失敗しました")

if __name__ == "__main__":
    from datetime import timedelta
    test_fuchu_route()