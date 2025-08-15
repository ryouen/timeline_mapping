#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v4 改良版
柔軟な日時指定対応

主な改良点：
1. 今日・明日・特定日時の到着時刻指定
2. 過去の時刻には対応しない（Google Mapsの仕様）
3. デフォルトは「明日の10時」
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
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote
import os

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoogleMapsScraperV4Improved:
    """Google Maps スクレイパー v4 改良版"""
    
    def __init__(self):
        self.driver = None
        self.place_id_cache = {}  # Place IDのキャッシュ
        
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
        
        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
    
    def get_arrival_time(self, target_time=None, days_ahead=None):
        """
        到着時刻を決定する
        
        Args:
            target_time: 指定時刻 (datetime) または文字列 "10:00"
            days_ahead: 何日後か (0=今日, 1=明日, など)
        
        Returns:
            datetime: 到着時刻
        """
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)
        
        # target_timeがdatetimeオブジェクトの場合
        if isinstance(target_time, datetime):
            # 過去の時刻チェック
            if target_time < now:
                logger.warning(f"過去の時刻が指定されました: {target_time}. 明日の同時刻に変更します。")
                target_time = target_time + timedelta(days=1)
            return target_time
        
        # days_aheadが指定されている場合
        if days_ahead is not None:
            target_date = now + timedelta(days=days_ahead)
        else:
            # デフォルトは明日
            target_date = now + timedelta(days=1)
        
        # 時刻の解析
        if isinstance(target_time, str):
            # "10:00" 形式
            hour, minute = map(int, target_time.split(':'))
        else:
            # デフォルトは10:00
            hour, minute = 10, 0
        
        arrival_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 今日の指定時刻が過去の場合は明日に変更
        if arrival_time < now:
            logger.info(f"指定時刻 {arrival_time.strftime('%H:%M')} は既に過ぎているため、明日に設定します")
            arrival_time = arrival_time + timedelta(days=1)
        
        return arrival_time
        
    def generate_google_maps_timestamp(self, arrival_time):
        """
        Google Maps用のタイムスタンプを生成
        重要: JSTの時刻をUTC基準で計算（タイムゾーン無視）
        """
        # datetimeオブジェクトから年月日時分を取得
        year = arrival_time.year
        month = arrival_time.month
        day = arrival_time.day
        hour = arrival_time.hour
        minute = arrival_time.minute
        
        # UTC時刻として作成（タイムゾーンを無視）
        utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
        return int(utc_time.timestamp())
    
    def get_place_info(self, address, name=None):
        """
        住所からPlace IDと座標を取得
        
        Args:
            address: 住所
            name: 施設名（オプション）
        
        Returns:
            dict: place_id, lat, lon
        """
        # キャッシュチェック
        cache_key = address
        if cache_key in self.place_id_cache:
            logger.info(f"キャッシュからPlace ID取得: {name or address}")
            return self.place_id_cache[cache_key]
        
        try:
            # 出発地（ルフォンプログレ）
            origin = "東京都千代田区神田須田町1-20-1"
            
            # Google Maps URLを構築（住所を使用）
            url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(address)}/data=!3e3"
            
            logger.info(f"Place ID取得中: {name or address}")
            self.driver.get(url)
            time.sleep(5)
            
            # URLからPlace IDを抽出（2番目が目的地）
            current_url = self.driver.current_url
            place_id_matches = re.findall(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
            
            if len(place_id_matches) >= 2:
                place_id = place_id_matches[1]
            else:
                place_id = None
                logger.warning(f"Place ID取得失敗: {name or address}")
            
            # 座標を抽出
            coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
            if coord_match:
                lat = coord_match.group(1)
                lon = coord_match.group(2)
            else:
                # 別のパターンを試す
                coord_matches = re.findall(r'!2d([\d.]+)', current_url)
                if len(coord_matches) >= 4:
                    lon = coord_matches[2]
                    lat = coord_matches[3]
                else:
                    lat, lon = None, None
            
            result = {
                'place_id': place_id,
                'lat': lat,
                'lon': lon
            }
            
            # キャッシュに保存
            self.place_id_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Place ID取得エラー ({name or address}): {e}")
            return {'place_id': None, 'lat': None, 'lon': None}
    
    def build_complete_url(self, origin_info, dest_info, arrival_time):
        """
        Place IDを含む完全なGoogle Maps URLを構築
        
        Args:
            origin_info: 出発地情報（address, place_id, lat, lon, postal_code）
            dest_info: 目的地情報（address, place_id, lat, lon, postal_code, name）
            arrival_time: 到着時刻（datetime）
        """
        # 郵便番号付き住所を構築
        if origin_info.get('postal_code'):
            origin_str = f"〒{origin_info['postal_code']}+{quote(origin_info['address'])}"
        else:
            origin_str = quote(origin_info['address'])
        
        if dest_info.get('postal_code'):
            dest_str = f"〒{dest_info['postal_code']}+{quote(dest_info['address'])}"
        else:
            dest_str = quote(dest_info['address'])
        
        # Place IDがない場合は取得を試みる
        if not dest_info.get('place_id'):
            place_info = self.get_place_info(dest_info['address'], dest_info.get('name'))
            dest_info.update(place_info)
        
        # 中心座標の計算
        if origin_info.get('lat') and dest_info.get('lat'):
            center_lat = (float(origin_info['lat']) + float(dest_info['lat'])) / 2
            center_lon = (float(origin_info['lon']) + float(dest_info['lon'])) / 2
            coord_str = f"@{center_lat},{center_lon},15z/"
        else:
            coord_str = ""
        
        # URLの構築
        url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
        
        if coord_str:
            url += coord_str
        
        # dataパラメータの構築
        data_parts = []
        
        # Place IDがある場合のみ完全な構造を使用
        if origin_info.get('place_id') and dest_info.get('place_id'):
            data_parts.append("!3m1!4b1")  # モード指定
            data_parts.append("!4m18!4m17")
            
            # 出発地情報
            data_parts.append("!1m5!1m1")
            data_parts.append(f"!1s{origin_info['place_id']}")
            if origin_info.get('lon') and origin_info.get('lat'):
                data_parts.append(f"!2m2!1d{origin_info['lon']}!2d{origin_info['lat']}")
            
            # 目的地情報
            data_parts.append("!1m5!1m1")
            data_parts.append(f"!1s{dest_info['place_id']}")
            if dest_info.get('lon') and dest_info.get('lat'):
                data_parts.append(f"!2m2!1d{dest_info['lon']}!2d{dest_info['lat']}")
        
        # 時刻指定
        if arrival_time:
            timestamp = self.generate_google_maps_timestamp(arrival_time)
            data_parts.append(f"!2m3!6e1!7e2!8j{timestamp}")
            logger.info(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST (timestamp: {timestamp})")
        
        # 公共交通機関モード
        data_parts.append("!3e3")
        
        if data_parts:
            url += "data=" + "".join(data_parts)
        
        return url
    
    def extract_route_details(self):
        """ルート詳細を抽出"""
        try:
            # ルート要素を待機
            wait = WebDriverWait(self.driver, 20)
            route_elements = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
            )
            
            logger.info(f"{len(route_elements)}個のルートを検出")
            
            routes = []
            for i, element in enumerate(route_elements[:3]):  # 最初の3つのルートのみ
                try:
                    text = element.text
                    
                    # 所要時間を抽出（時間と分の両方を考慮）
                    hour_match = re.search(r'(\d+)\s*時間', text)
                    minute_match = re.search(r'(\d+)\s*分', text)
                    
                    if not minute_match and not hour_match:
                        continue
                    
                    hours = int(hour_match.group(1)) if hour_match else 0
                    minutes = int(minute_match.group(1)) if minute_match else 0
                    travel_time = hours * 60 + minutes
                    
                    # 出発・到着時刻を抽出
                    # 「出発時刻 (曜日) - 到着時刻」形式を探す
                    time_range_match = re.search(r'(\d{1,2}:\d{2})\s*\([^)]+\)\s*-\s*(\d{1,2}:\d{2})', text)
                    if time_range_match:
                        departure_time = time_range_match.group(1)
                        arrival_time = time_range_match.group(2)
                    else:
                        # フォールバック：最初の時刻を出発時刻とする
                        departure_match = re.search(r'(\d{1,2}:\d{2})', text)
                        departure_time = departure_match.group(1) if departure_match else None
                        arrival_time = None
                    
                    # 料金を抽出
                    fare_match = re.search(r'(\d+)\s*円', text)
                    fare = int(fare_match.group(1)) if fare_match else None
                    
                    # ルートタイプを判定
                    if '徒歩' in text and not any(word in text for word in ['駅', '線', '電車']):
                        route_type = '徒歩のみ'
                    elif any(word in text for word in ['線', '駅', '電車', 'バス']):
                        route_type = '公共交通機関'
                        # 路線名を抽出
                        lines = re.findall(r'([^\s]+線)', text)
                    else:
                        route_type = '不明'
                    
                    route_info = {
                        'index': i + 1,
                        'travel_time': travel_time,
                        'departure_time': departure_time,
                        'arrival_time': arrival_time,
                        'fare': fare,
                        'route_type': route_type,
                        'summary': text[:100]  # 最初の100文字
                    }
                    
                    routes.append(route_info)
                    logger.info(f"ルート{i+1}: {travel_time}分 ({route_type})")
                    
                except Exception as e:
                    logger.error(f"ルート{i+1}の抽出エラー: {e}")
            
            return routes
            
        except TimeoutException:
            logger.error("ルート情報の読み込みタイムアウト")
            return []
        except Exception as e:
            logger.error(f"ルート抽出エラー: {e}")
            return []
    
    def scrape_route(self, origin_address, dest_address, dest_name=None, arrival_time=None, 
                     target_time=None, days_ahead=None):
        """
        ルート情報をスクレイピング
        
        Args:
            origin_address: 出発地の住所
            dest_address: 目的地の住所
            dest_name: 目的地の名前
            arrival_time: 到着時刻（datetime）- 優先
            target_time: 到着時刻文字列 "10:00" 形式
            days_ahead: 何日後か (0=今日, 1=明日)
        """
        try:
            # 到着時刻の決定
            if arrival_time is None:
                arrival_time = self.get_arrival_time(target_time, days_ahead)
            
            # 出発地情報（ルフォンプログレ）
            origin_info = {
                'address': origin_address,
                'postal_code': '101-0041',
                'place_id': '0x60188c02f64e1cd9:0x987c1c7aa7e7f84a',
                'lat': '35.6949994',
                'lon': '139.7711379'
            }
            
            # 目的地情報
            dest_info = {
                'address': dest_address,
                'name': dest_name
            }
            
            # 完全なURLを構築
            url = self.build_complete_url(origin_info, dest_info, arrival_time)
            logger.info(f"アクセスURL: {url[:150]}...")
            
            # ページにアクセス
            self.driver.get(url)
            time.sleep(5)
            
            # ルート詳細を抽出
            routes = self.extract_route_details()
            
            if routes:
                # 最短ルートを選択
                shortest = min(routes, key=lambda r: r['travel_time'])
                
                return {
                    'success': True,
                    'origin': origin_address,
                    'destination': dest_address,
                    'destination_name': dest_name,
                    'arrival_datetime': arrival_time.strftime('%Y-%m-%d %H:%M'),
                    'travel_time': shortest['travel_time'],
                    'departure_time': shortest.get('departure_time'),
                    'arrival_time': shortest.get('arrival_time'),
                    'fare': shortest.get('fare'),
                    'route_type': shortest['route_type'],
                    'all_routes': routes,
                    'url': url,
                    'place_id': dest_info.get('place_id')
                }
            else:
                return {
                    'success': False,
                    'error': 'ルート情報を取得できませんでした',
                    'url': url
                }
                
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("Seleniumセッション終了")

def test_improved_scraper():
    """改良版スクレイパーのテスト"""
    from datetime import datetime, timedelta
    import pytz
    
    # テスト用の目的地
    test_destination = {
        'name': 'Shizenkan University',
        'address': '東京都中央区日本橋２丁目５−１'
    }
    
    jst = pytz.timezone('Asia/Tokyo')
    
    print("="*60)
    print("Google Maps スクレイパー v4 改良版テスト")
    print("="*60)
    
    # スクレイパー初期化
    scraper = GoogleMapsScraperV4Improved()
    
    try:
        scraper.setup_driver()
        
        # ケース1: デフォルト（明日の10時）
        print("\n[ケース1] デフォルト設定")
        result = scraper.scrape_route(
            origin_address="東京都千代田区神田須田町1-20-1",
            dest_address=test_destination['address'],
            dest_name=test_destination['name']
        )
        
        if result['success']:
            print(f"✅ 成功")
            print(f"  到着日時: {result['arrival_datetime']}")
            print(f"  所要時間: {result['travel_time']}分")
            print(f"  出発時刻: {result.get('departure_time')}")
            print(f"  到着時刻: {result.get('arrival_time')}")
        
        # ケース2: 今日の22時
        print("\n[ケース2] 今日の22時到着")
        result = scraper.scrape_route(
            origin_address="東京都千代田区神田須田町1-20-1",
            dest_address=test_destination['address'],
            dest_name=test_destination['name'],
            target_time="22:00",
            days_ahead=0
        )
        
        if result['success']:
            print(f"✅ 成功")
            print(f"  到着日時: {result['arrival_datetime']}")
            print(f"  所要時間: {result['travel_time']}分")
        
        # ケース3: 3日後の15時
        print("\n[ケース3] 3日後の15時到着")
        result = scraper.scrape_route(
            origin_address="東京都千代田区神田須田町1-20-1",
            dest_address=test_destination['address'],
            dest_name=test_destination['name'],
            target_time="15:00",
            days_ahead=3
        )
        
        if result['success']:
            print(f"✅ 成功")
            print(f"  到着日時: {result['arrival_datetime']}")
            print(f"  所要時間: {result['travel_time']}分")
                
    finally:
        scraper.close()

if __name__ == "__main__":
    test_improved_scraper()