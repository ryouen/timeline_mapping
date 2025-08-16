#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール
URLパラメータとクリック操作の両方を活用し、Place ID事前取得も統合
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import logging
import json
import gc
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoogleMapsScraper:
    """Google Maps スクレイパー"""
    
    def __init__(self):
        self.driver = None
        # self.place_id_cache = {}  # Place IDキャッシュ - 無効化
        # self.route_cache = {}     # ルート結果キャッシュ - 無効化
        self.route_count = 0      # 処理済みルート数
        
    def setup_driver(self):
        """Selenium WebDriverのセットアップ"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
        # メモリ最適化
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        logger.info("WebDriver初期化完了")
    
    def normalize_address(self, address):
        """
        住所を正規化（Google Maps検索用）
        例: "東京都千代田区 神田須田町１丁目２０−１" → "東京都千代田区神田須田町1-20-1"
        """
        # 全角スペースを削除
        normalized = address.replace('　', '').replace(' ', '')
        
        # 「丁目」を「-」に変換
        normalized = re.sub(r'(\d+)丁目(\d+)−(\d+)', r'\1-\2-\3', normalized)
        normalized = re.sub(r'(\d+)丁目(\d+)番(\d+)', r'\1-\2-\3', normalized)
        normalized = re.sub(r'(\d+)丁目(\d+)', r'\1-\2', normalized)
        
        # 「番」「号」を削除
        normalized = re.sub(r'(\d+)番(\d+)号', r'\1-\2', normalized)
        normalized = re.sub(r'(\d+)番', r'\1', normalized)
        normalized = re.sub(r'(\d+)号', r'\1', normalized)
        
        # 全角数字を半角に
        normalized = normalized.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        # 全角ハイフンを半角に
        normalized = normalized.replace('−', '-').replace('ー', '-')
        
        return normalized
    
    def generate_google_maps_timestamp(self, year, month, day, hour, minute):
        """
        Google Maps用のタイムスタンプを生成
        重要: JSTの時刻をUTC基準で計算（タイムゾーン無視）
        """
        # UTC時刻として作成（タイムゾーンを無視）
        utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
        return int(utc_time.timestamp())
    
    def get_place_id(self, address, name=None):
        """
        住所からPlace IDを取得
        住所のみで検索し、施設名は使わない
        """
        # 正規化した住所でキャッシュチェック
        normalized = self.normalize_address(address)
        
        # キャッシュ無効化
        # if normalized in self.place_id_cache:
        #     logger.debug(f"⚡ キャッシュからPlace ID取得: {name or address[:30]}...")
        #     return self.place_id_cache[normalized]
        
        try:
            # Google Mapsで住所を直接検索
            url = f"https://www.google.com/maps/search/{quote(normalized)}"
            
            logger.info(f"🔍 Place ID取得中: {name or address[:30]}...")
            self.driver.get(url)
            time.sleep(3)
            
            # URLからPlace IDを抽出
            current_url = self.driver.current_url
            place_id = None
            
            # 複数のパターンで検索
            patterns = [
                r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)',
                r'/place/[^/]+/@[^/]+/data=.*!1s(0x[0-9a-f]+:0x[0-9a-f]+)',
                r'ftid=(0x[0-9a-f]+:0x[0-9a-f]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, current_url)
                if match:
                    place_id = match.group(1)
                    logger.info(f"   ✅ Place ID: {place_id}")
                    break
            
            # 座標を抽出
            lat, lon = None, None
            coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
            if coord_match:
                lat = coord_match.group(1)
                lon = coord_match.group(2)
            
            result = {
                'place_id': place_id,
                'lat': lat,
                'lon': lon,
                'normalized_address': normalized
            }
            
            # キャッシュ無効化
            # self.place_id_cache[normalized] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Place ID取得エラー: {e}")
            return {'place_id': None, 'lat': None, 'lon': None, 'normalized_address': normalized}
    
    def check_needs_setup(self):
        """
        URLパラメータを確認して手動設定が必要かどうか判定
        v5の重要な発見：URLに!3e3と!8jが含まれていれば設定済み
        
        Returns:
            bool: 手動設定が必要な場合True、不要な場合False
        """
        try:
            current_url = self.driver.current_url
            
            # URLパラメータの確認
            has_transit = '!3e3' in current_url or 'travelmode=transit' in current_url
            has_time = '!8j' in current_url or 'arrival_time=' in current_url
            
            # ルート要素の存在確認
            route_elements = self.driver.find_elements(By.XPATH, "//div[@data-trip-index]")
            has_routes = len(route_elements) > 0
            
            if has_transit and has_time and has_routes:
                logger.info(f"✅ URLパラメータ適用済み (transit:{has_transit}, time:{has_time}, routes:{len(route_elements)})")
                return False  # 手動設定不要
            else:
                logger.info(f"⚠️ 手動設定必要 (transit:{has_transit}, time:{has_time}, routes:{len(route_elements)})")
                return True  # 手動設定必要
                
        except Exception as e:
            logger.warning(f"URL確認エラー: {e}")
            return True  # エラーの場合は安全のため手動設定を試みる
    
    def build_url_with_timestamp(self, origin_info, dest_info, arrival_time):
        """
        タイムスタンプ付きURLを構築
        """
        # 住所を正規化
        origin_str = quote(origin_info['normalized_address'])
        dest_str = quote(dest_info['normalized_address'])
        
        # 基本URL
        url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
        
        # dataパラメータの構築
        data_parts = []
        
        # Place IDがある場合
        if origin_info.get('place_id') and dest_info.get('place_id'):
            data_parts.append("!4m18!4m17")
            data_parts.append("!1m5!1m1")
            data_parts.append(f"!1s{origin_info['place_id']}")
            if origin_info.get('lon') and origin_info.get('lat'):
                data_parts.append(f"!2m2!1d{origin_info['lon']}!2d{origin_info['lat']}")
            data_parts.append("!1m5!1m1")
            data_parts.append(f"!1s{dest_info['place_id']}")
            if dest_info.get('lon') and dest_info.get('lat'):
                data_parts.append(f"!2m2!1d{dest_info['lon']}!2d{dest_info['lat']}")
        
        # 時刻指定
        if arrival_time:
            jst = pytz.timezone('Asia/Tokyo')
            arrival_jst = arrival_time.astimezone(jst)
            timestamp = self.generate_google_maps_timestamp(
                arrival_jst.year,
                arrival_jst.month,
                arrival_jst.day,
                arrival_jst.hour,
                arrival_jst.minute
            )
            data_parts.append(f"!2m3!6e1!7e2!8j{timestamp}")
        
        # 公共交通機関モード
        data_parts.append("!3e3")
        
        if data_parts:
            url += "data=" + "".join(data_parts)
        
        return url
    
    def click_transit_and_set_time(self, arrival_time):
        """
        公共交通機関ボタンをクリックし、時刻を設定
        """
        logger.info("公共交通機関モードと時刻設定を開始")
        
        # 1. 公共交通機関ボタンをクリック
        transit_clicked = False
        transit_selectors = [
            "//button[@aria-label='公共交通機関']",
            "//button[@aria-label='Transit']",
            "//button[@data-travel-mode='3']",
            "//div[@data-value='3']//button",
            "//img[@aria-label='公共交通機関']/..",
            "//span[contains(text(), '電車')]/..",
            "//button[contains(@class, 'transit')]"
        ]
        
        for selector in transit_selectors:
            try:
                transit_btn = self.driver.find_element(By.XPATH, selector)
                if transit_btn.is_displayed():
                    transit_btn.click()
                    logger.info(f"公共交通機関ボタンをクリック")
                    transit_clicked = True
                    time.sleep(2)
                    break
            except:
                continue
        
        if not transit_clicked:
            logger.warning("公共交通機関ボタンが見つからない - URLパラメータで設定済み")
            return True  # URLパラメータで設定済みなので続行
        
        # 2. 時刻オプションボタンを探してクリック
        time_option_clicked = False
        time_selectors = [
            "//button[contains(@aria-label, '出発時刻')]",
            "//button[contains(@aria-label, 'Depart at')]",
            "//button[contains(text(), '出発')]",
            "//button[contains(text(), 'すぐに出発')]",
            "//span[contains(text(), 'すぐに出発')]/..",
            "//div[contains(@class, 'time-selection')]//button",
            "//button[@data-value='0']"
        ]
        
        for selector in time_selectors:
            try:
                time_btn = self.driver.find_element(By.XPATH, selector)
                if time_btn.is_displayed():
                    time_btn.click()
                    logger.info(f"時刻オプションボタンをクリック")
                    time_option_clicked = True
                    time.sleep(1)
                    break
            except:
                continue
        
        if not time_option_clicked:
            logger.warning("時刻オプションボタンが見つからない - URLパラメータで設定済み")
            return True  # URLパラメータで設定済みなので続行
        
        # 3. 「到着時刻」を選択
        try:
            arrival_option_selectors = [
                "//div[contains(text(), '到着時刻')]",
                "//div[contains(text(), '到着')]",
                "//span[contains(text(), '到着')]",
                "//div[@role='option'][contains(text(), '到着')]",
                "//div[contains(text(), 'Arrive by')]"
            ]
            
            for selector in arrival_option_selectors:
                try:
                    arrival_option = self.driver.find_element(By.XPATH, selector)
                    if arrival_option.is_displayed():
                        arrival_option.click()
                        logger.info("「到着時刻」を選択")
                        time.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"到着時刻オプションの選択に失敗: {e}")
        
        # 4. 日付・時刻を入力
        try:
            # JSTに変換
            jst = pytz.timezone('Asia/Tokyo')
            arrival_jst = arrival_time.astimezone(jst)
            date_str = arrival_jst.strftime('%Y/%m/%d')
            time_str = arrival_jst.strftime('%H:%M')
            
            # 日付入力
            date_selectors = [
                "//input[@aria-label='日付を選択']",
                "//input[@type='date']",
                "//input[contains(@aria-label, '日付')]",
                "//input[contains(@placeholder, '日付')]"
            ]
            
            for selector in date_selectors:
                try:
                    date_input = self.driver.find_element(By.XPATH, selector)
                    if date_input.is_displayed():
                        date_input.clear()
                        date_input.send_keys(date_str)
                        logger.info(f"日付を入力: {date_str}")
                        break
                except:
                    continue
            
            # 時刻入力
            time_selectors = [
                "//input[@aria-label='時刻を選択']",
                "//input[@type='time']",
                "//input[contains(@aria-label, '時刻')]",
                "//input[contains(@placeholder, '時刻')]"
            ]
            
            for selector in time_selectors:
                try:
                    time_input = self.driver.find_element(By.XPATH, selector)
                    if time_input.is_displayed():
                        time_input.clear()
                        time_input.send_keys(time_str)
                        time_input.send_keys(Keys.RETURN)
                        logger.info(f"時刻を入力: {time_str}")
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"日付・時刻の入力に失敗: {e}")
            return False
        
        time.sleep(3)
        logger.info("時刻設定完了")
        return True
    
    def click_route_details(self):
        """
        ルート詳細を展開する（improvedから移植、複数の方法を試す）
        """
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
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        element = elements[0]
                        # スクロールして要素を表示
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        
                        # クリック
                        try:
                            element.click()
                        except:
                            # JavaScriptでクリック
                            self.driver.execute_script("arguments[0].click();", element)
                        
                        logger.info(f"ルートをクリック: {selector}")
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
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        elements[0].click()
                        logger.info(f"詳細ボタンをクリック: {selector}")
                        time.sleep(3)
                        return True
                except:
                    continue
                    
            logger.warning("ルート詳細の展開に失敗")
            return False
            
        except Exception as e:
            logger.error(f"ルート詳細クリックエラー: {e}")
            return False
    
    def extract_route_steps(self):
        """
        詳細なルートステップを抽出する（improvedから移植、ハードコード削除）
        """
        steps_info = []
        
        # 複数のセレクタで詳細ステップを探す
        step_selectors = [
            "//div[@class='cYhGGe']",
            "//div[contains(@class, 'directions-mode-step')]",
            "//div[contains(@class, 'section-directions-trip-line')]",
            "//div[contains(@class, 'transit-stop')]",
            "//div[@role='listitem' and contains(@class, 'trip')]"
        ]
        
        for selector in step_selectors:
            try:
                steps = self.driver.find_elements(By.XPATH, selector)
                if steps:
                    logger.info(f"{len(steps)}個のステップを検出: {selector}")
                    
                    for i, step in enumerate(steps):
                        try:
                            step_text = step.text.strip()
                            if step_text:
                                step_info = {
                                    'text': step_text,
                                    'index': i,
                                    'type': None  # 徒歩/電車/バスなど
                                }
                                
                                # 駅名を探す
                                station_match = re.search(r'([^\s]+駅)', step_text)
                                if station_match:
                                    step_info['station'] = station_match.group(1).replace('駅', '')
                                
                                # 路線名を探す
                                line_match = re.search(r'((?:JR|東京メトロ|都営|東急|京王|小田急|西武|東武|京成|京浜東北|山手|中央|総武|[^\s]+)線)', step_text)
                                if line_match:
                                    step_info['line'] = line_match.group(1)
                                
                                # 時間を探す（分単位）
                                time_match = re.search(r'(\d+)\s*分', step_text)
                                if time_match:
                                    step_info['duration'] = int(time_match.group(1))
                                
                                # ステップタイプを判定
                                if '徒歩' in step_text or '歩' in step_text:
                                    step_info['type'] = 'walk'
                                elif 'line' in step_info or 'station' in step_info:
                                    step_info['type'] = 'train'
                                elif 'バス' in step_text:
                                    step_info['type'] = 'bus'
                                
                                steps_info.append(step_info)
                                
                        except Exception as e:
                            logger.debug(f"ステップ{i}の解析エラー: {e}")
                            continue
                            
                    if steps_info:
                        return steps_info
                        
            except Exception as e:
                continue
        
        return steps_info
    
    def build_detailed_json(self, steps, routes, origin_address, dest_address, dest_name):
        """
        ステップ情報とルート情報から詳細JSONを構築
        重要：ハードコード値は一切使わず、取得できたデータのみを使用
        """
        try:
            # 基本構造
            result = {
                'success': True,
                'origin': origin_address,
                'destination': dest_address,
                'destination_name': dest_name
            }
            
            # 詳細情報の構築
            details = {}
            trains = []
            walk_to_station = None
            walk_from_station = None
            wait_time_minutes = None
            station_used = None
            
            # ステップ情報から詳細を抽出
            if steps:
                logger.info(f"ステップ情報から詳細を抽出: {len(steps)}ステップ")
                
                for i, step in enumerate(steps):
                    step_type = step.get('type')
                    
                    # 最初の徒歩（駅まで）
                    if step_type == 'walk' and i == 0:
                        walk_to_station = step.get('duration')
                        logger.info(f"駅までの徒歩: {walk_to_station}分")
                    
                    # 電車情報
                    elif step_type == 'train':
                        train_info = {
                            'line': step.get('line'),
                            'time': step.get('duration'),
                            'from': step.get('station')
                        }
                        
                        # 次のステップから到着駅を探す
                        for j in range(i+1, len(steps)):
                            if 'station' in steps[j]:
                                train_info['to'] = steps[j]['station']
                                break
                        
                        # 有効な電車情報のみ追加
                        if train_info.get('line') and train_info.get('time'):
                            trains.append(train_info)
                            
                            # 最初の駅を記録
                            if not station_used and train_info.get('from'):
                                station_used = train_info['from']
                    
                    # 最後の徒歩（駅から目的地）
                    elif step_type == 'walk' and i == len(steps) - 1:
                        walk_from_station = step.get('duration')
                        logger.info(f"駅からの徒歩: {walk_from_station}分")
            
            # ルート情報からの補完（ステップ情報が不十分な場合）
            if routes and len(routes) > 0:
                route = routes[0]  # 最初のルートを使用
                
                # 基本情報
                result['travel_time'] = route.get('travel_time')
                result['departure_time'] = route.get('departure_time')
                result['arrival_time'] = route.get('arrival_time')
                result['fare'] = route.get('fare')
                result['route_type'] = route.get('route_type')
                
                # 路線情報が取得できていない場合
                if not trains and route.get('train_lines'):
                    for line in route['train_lines']:
                        trains.append({
                            'line': line,
                            # 時間と駅名は不明（ハードコードしない）
                        })
            
            # 詳細情報の構築（取得できたデータのみ）
            if walk_to_station is not None:
                details['walk_to_station'] = walk_to_station
            
            if walk_from_station is not None:
                details['walk_from_station'] = walk_from_station
            
            if wait_time_minutes is not None:
                details['wait_time_minutes'] = wait_time_minutes
            
            if station_used:
                details['station_used'] = station_used
            
            if trains:
                # 不完全な電車情報を除外
                valid_trains = []
                for train in trains:
                    if train.get('line') and train.get('time'):
                        valid_trains.append(train)
                
                if valid_trains:
                    details['trains'] = valid_trains
            
            # 詳細が何か取得できた場合のみ詳細を含める
            if details:
                result['details'] = details
                logger.info(f"詳細情報構築完了: {details}")
            else:
                logger.warning("詳細情報を構築できませんでした")
            
            return result
            
        except Exception as e:
            logger.error(f"詳細JSON構築エラー: {e}")
            return None
    
    def extract_route_details(self):
        """ルート詳細を抽出（改良版）"""
        try:
            # まず既存の要素を確認
            route_elements = self.driver.find_elements(By.XPATH, "//div[@data-trip-index]")
            
            if not route_elements:
                # 要素がない場合のみ待機
                wait = WebDriverWait(self.driver, 20)
                route_elements = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
                )
            
            logger.info(f"{len(route_elements)}個のルートを検出")
            
            routes = []
            for i, element in enumerate(route_elements[:3]):  # 最初の3つのルートのみ
                try:
                    text = element.text
                    
                    # 所要時間を抽出
                    hour_match = re.search(r'(\d+)\s*時間', text)
                    minute_match = re.search(r'(\d+)\s*分', text)
                    
                    if not minute_match and not hour_match:
                        continue
                    
                    hours = int(hour_match.group(1)) if hour_match else 0
                    minutes = int(minute_match.group(1)) if minute_match else 0
                    travel_time = hours * 60 + minutes
                    
                    # 出発・到着時刻を抽出
                    time_pattern = r'(\d{1,2}:\d{2})[^\d]*(?:\([^)]+\)[^\d]*)?\s*-\s*(\d{1,2}:\d{2})'
                    time_match = re.search(time_pattern, text)
                    if time_match:
                        departure_time = time_match.group(1)
                        arrival_time = time_match.group(2)
                    else:
                        departure_time = None
                        arrival_time = None
                    
                    # 料金を抽出
                    fare_match = re.search(r'([\d,]+)\s*円', text)
                    fare = int(fare_match.group(1).replace(',', '')) if fare_match else None
                    
                    # 路線情報を抽出
                    train_lines = []
                    # 路線名パターン（「線」「ライン」などを含む）
                    line_pattern = r'([^\s]+(?:線|ライン|Line))'
                    line_matches = re.findall(line_pattern, text)
                    if line_matches:
                        train_lines = list(set(line_matches))  # 重複を除去
                    
                    # ルートタイプを判定
                    if '徒歩' in text and not any(word in text for word in ['駅', '線', '電車', 'バス']):
                        route_type = '徒歩のみ'
                    elif any(word in text for word in ['線', '駅', '電車', 'バス']) or train_lines:
                        route_type = '公共交通機関'
                    else:
                        route_type = '不明'
                    
                    route_info = {
                        'index': i + 1,
                        'travel_time': travel_time,
                        'departure_time': departure_time,
                        'arrival_time': arrival_time,
                        'fare': fare,
                        'route_type': route_type,
                        'train_lines': train_lines,
                        'summary': text[:200]
                    }
                    
                    routes.append(route_info)
                    logger.info(f"ルート{i+1}: {travel_time}分 ({route_type}) 料金:{fare}円 路線:{','.join(train_lines)}")
                    
                except Exception as e:
                    logger.error(f"ルート{i+1}の抽出エラー: {e}")
            
            return routes
            
        except TimeoutException:
            logger.error("ルート情報の読み込みタイムアウト")
            return []
        except Exception as e:
            logger.error(f"ルート抽出エラー: {e}")
            return []
    
    def cleanup_after_route(self):
        """各ルート処理後のメモリクリーンアップ"""
        try:
            # ページをabout:blankにしてメモリ解放
            self.driver.execute_script("window.location.href='about:blank'")
            time.sleep(0.5)
            
            # ガベージコレクション実行
            gc.collect()
            
            # 30ルートごとにWebDriverを再起動
            self.route_count += 1
            if self.route_count >= 30:
                logger.info("30ルート処理完了。WebDriverを再起動します...")
                self.restart_driver()
                self.route_count = 0
                
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")
    
    def restart_driver(self):
        """WebDriverを再起動する"""
        try:
            if self.driver:
                self.driver.quit()
            self.setup_driver()
            logger.info("WebDriver再起動完了")
        except Exception as e:
            logger.error(f"WebDriver再起動エラー: {e}")
    
    def scrape_route(self, origin_address, dest_address, dest_name=None, arrival_time=None,
                     origin_place_id=None, dest_place_id=None, 
                     origin_lat=None, origin_lon=None, dest_lat=None, dest_lon=None):
        """
        ルート情報をスクレイピング
        Place IDを外部から受け取る（オプション）
        Place IDが渡されない場合は従来通り取得
        """
        
        try:
            # Place ID情報の準備
            if origin_place_id:
                # Place IDが渡された場合はそれを使用
                origin_info = {
                    'place_id': origin_place_id,
                    'lat': origin_lat,
                    'lon': origin_lon,
                    'normalized_address': self.normalize_address(origin_address)
                }
                logger.info(f"📍 外部Place ID使用（出発地）: {origin_place_id}")
            else:
                # Place IDが渡されない場合は従来通り取得
                origin_info = self.get_place_id(origin_address, "出発地")
            
            if dest_place_id:
                # Place IDが渡された場合はそれを使用
                dest_info = {
                    'place_id': dest_place_id,
                    'lat': dest_lat,
                    'lon': dest_lon,
                    'normalized_address': self.normalize_address(dest_address)
                }
                logger.info(f"📍 外部Place ID使用（目的地）: {dest_place_id}")
            else:
                # Place IDが渡されない場合は従来通り取得
                dest_info = self.get_place_id(dest_address, dest_name)
            
            # タイムスタンプ付きURLを構築
            url = self.build_url_with_timestamp(origin_info, dest_info, arrival_time)
            
            logger.info(f"📍 ルート検索: {dest_name or dest_address[:30]}...")
            logger.debug(f"URL: {url[:150]}...")
            
            self.driver.get(url)
            time.sleep(5)  # 初期ロード待機
            
            # URLパラメータ確認と手動設定判定
            if self.check_needs_setup():
                # 手動設定が必要な場合
                if arrival_time:
                    try:
                        self.click_transit_and_set_time(arrival_time)
                    except Exception as e:
                        logger.warning(f"クリック操作エラー（続行）: {e}")
            else:
                # URLパラメータが適用済みの場合は詳細を展開
                logger.info("URLパラメータ適用済み - 詳細展開を試みる")
                self.click_route_details()
            
            # 詳細ステップ情報を取得（improved方式）
            steps = self.extract_route_steps()
            
            # サマリー情報も取得（フォールバック用）
            routes = self.extract_route_details()
            
            # 詳細JSONを構築
            if steps or routes:
                detailed_result = self.build_detailed_json(steps, routes, origin_address, dest_address, dest_name)
                
                if detailed_result:
                    detailed_result['place_ids'] = {
                        'origin': origin_info.get('place_id'),
                        'destination': dest_info.get('place_id')
                    }
                    detailed_result['url'] = url
                    return detailed_result
                    
            # データが取得できなかった場合
            return {
                'success': False,
                'error': 'ルート詳細情報を取得できませんでした',
                'url': url,
                'debug_info': {
                    'steps_found': len(steps) if steps else 0,
                    'routes_found': len(routes) if routes else 0
                }
            }
                
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # ルート処理後のクリーンアップ
            self.cleanup_after_route()
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Seleniumセッション終了")
            except:
                pass

def test_v5_ultimate():
    """動作テスト"""
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("Google Maps スクレイパー テスト")
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    print("="*60)
    
    # テストケース
    test_cases = [
        {
            'name': 'Shizenkan University',
            'origin': '東京都千代田区 神田須田町１丁目２０−１',
            'destination': '東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階'
        },
        {
            'name': '早稲田大学（公共交通機関が必須）',
            'origin': '東京都千代田区 神田須田町１丁目２０−１',
            'destination': '東京都新宿区西早稲田１丁目６ 11号館'
        }
    ]
    
    scraper = GoogleMapsScraper()
    
    try:
        scraper.setup_driver()
        
        for test in test_cases:
            print(f"\n[{test['name']}]")
            result = scraper.scrape_route(
                test['origin'],
                test['destination'],
                test['name'],
                arrival_time
            )
            
            if result['success']:
                print(f"✅ 成功")
                print(f"  所要時間: {result['travel_time']}分")
                print(f"  ルートタイプ: {result['route_type']}")
                print(f"  料金: {result.get('fare', 'N/A')}円")
                print(f"  路線: {', '.join(result.get('train_lines', []))}")
                print(f"  時刻: {result.get('departure_time', 'N/A')} → {result.get('arrival_time', 'N/A')}")
                if result.get('from_cache'):
                    print(f"  ⚡ キャッシュから取得")
            else:
                print(f"❌ 失敗: {result.get('error')}")
                
    finally:
        scraper.close()

if __name__ == "__main__":
    test_v5_ultimate()