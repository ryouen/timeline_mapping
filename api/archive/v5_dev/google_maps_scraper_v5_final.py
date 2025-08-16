#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v5 最終版
URLパラメータ方式とPlace ID事前取得を統合

主な特徴：
1. Place ID事前取得で効率化
2. 住所正規化機能
3. URLパラメータによる確実な時刻指定
4. メモリリーク対策
5. 重複処理の排除（住所ベースのキャッシュ）
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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

class GoogleMapsScraperV5:
    """Google Maps スクレイパー v5 最終版"""
    
    def __init__(self):
        self.driver = None
        self.place_id_cache = {}  # Place IDキャッシュ
        self.route_cache = {}     # ルート結果キャッシュ（住所ベース）
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
        住所からPlace IDを取得（v5改良版）
        住所のみで検索し、施設名は使わない
        """
        # 正規化した住所でキャッシュチェック
        normalized = self.normalize_address(address)
        
        if normalized in self.place_id_cache:
            logger.info(f"⚡ キャッシュからPlace ID取得: {name or address[:30]}...")
            return self.place_id_cache[normalized]
        
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
            
            # キャッシュに保存
            self.place_id_cache[normalized] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Place ID取得エラー: {e}")
            return {'place_id': None, 'lat': None, 'lon': None, 'normalized_address': normalized}
    
    def build_complete_url(self, origin_info, dest_info, arrival_time):
        """
        Place IDを含む完全なGoogle Maps URLを構築
        """
        # 住所を正規化
        origin_str = quote(origin_info['normalized_address'])
        dest_str = quote(dest_info['normalized_address'])
        
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
            # JSTをUTC基準でタイムスタンプ生成
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
                    time_range_match = re.search(r'(\d{1,2}:\d{2})[^\d]*-[^\d]*(\d{1,2}:\d{2})', text)
                    if time_range_match:
                        departure_time = time_range_match.group(1)
                        arrival_time = time_range_match.group(2)
                    else:
                        departure_match = re.search(r'(\d{1,2}:\d{2})', text)
                        departure_time = departure_match.group(1) if departure_match else None
                        arrival_time = None
                    
                    # 料金を抽出
                    fare_match = re.search(r'([\d,]+)\s*円', text)
                    fare = int(fare_match.group(1).replace(',', '')) if fare_match else None
                    
                    # ルートタイプを判定
                    if '徒歩' in text and not any(word in text for word in ['駅', '線', '電車']):
                        route_type = '徒歩のみ'
                    elif any(word in text for word in ['線', '駅', '電車', 'バス']):
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
                        'summary': text[:100]
                    }
                    
                    routes.append(route_info)
                    logger.info(f"ルート{i+1}: {travel_time}分 ({route_type}) 料金:{fare}円")
                    
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
        """
        各ルート処理後のメモリクリーンアップ
        """
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
    
    def scrape_route(self, origin_address, dest_address, dest_name=None, arrival_time=None):
        """
        ルート情報をスクレイピング（v5最終版）
        
        Args:
            origin_address: 出発地の住所
            dest_address: 目的地の住所
            dest_name: 目的地の名前（オプション）
            arrival_time: 到着時刻（datetime）
        """
        # 住所を正規化
        origin_normalized = self.normalize_address(origin_address)
        dest_normalized = self.normalize_address(dest_address)
        
        # キャッシュキーを作成
        cache_key = f"{origin_normalized}→{dest_normalized}"
        
        # キャッシュチェック（同じ住所ペアは再検索しない）
        if cache_key in self.route_cache:
            logger.info(f"⚡ キャッシュからルート取得: {dest_name or dest_address[:30]}...")
            cached_result = self.route_cache[cache_key].copy()
            cached_result['from_cache'] = True
            return cached_result
        
        try:
            # Place IDを事前取得
            origin_info = self.get_place_id(origin_address, "出発地")
            dest_info = self.get_place_id(dest_address, dest_name)
            
            # 完全なURLを構築
            url = self.build_complete_url(origin_info, dest_info, arrival_time)
            
            logger.info(f"📍 ルート検索: {dest_name or dest_address[:30]}...")
            logger.debug(f"URL: {url[:150]}...")
            
            self.driver.get(url)
            time.sleep(5)  # ページロード待機
            
            # ルート詳細を抽出
            routes = self.extract_route_details()
            
            if routes:
                # 最短ルートを選択
                shortest = min(routes, key=lambda r: r['travel_time'])
                
                result = {
                    'success': True,
                    'origin': origin_address,
                    'destination': dest_address,
                    'destination_name': dest_name,
                    'travel_time': shortest['travel_time'],
                    'departure_time': shortest.get('departure_time'),
                    'arrival_time': shortest.get('arrival_time'),
                    'fare': shortest.get('fare'),
                    'route_type': shortest['route_type'],
                    'all_routes': routes,
                    'place_ids': {
                        'origin': origin_info.get('place_id'),
                        'destination': dest_info.get('place_id')
                    },
                    'url': url
                }
                
                # キャッシュに保存
                self.route_cache[cache_key] = result
                
                return result
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

def test_v5_final():
    """v5最終版のテスト"""
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("Google Maps スクレイパー v5 最終版テスト")
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
            'name': '同じ建物の別部屋（キャッシュテスト）',
            'origin': '東京都千代田区 神田須田町１丁目２０−１',  # 同じ住所
            'destination': '東京都中央区日本橋２丁目５−１'  # 同じ建物
        }
    ]
    
    scraper = GoogleMapsScraperV5()
    
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
                if result.get('from_cache'):
                    print(f"  ⚡ キャッシュから取得")
            else:
                print(f"❌ 失敗: {result.get('error')}")
                
    finally:
        scraper.close()

if __name__ == "__main__":
    test_v5_final()