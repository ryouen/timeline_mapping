#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v5 統合版
Place ID事前取得機能とクリック操作による時刻指定を統合

主な改善点：
1. Place ID事前取得で効率化
2. 住所正規化機能
3. クリック操作による確実な時刻指定
4. メモリリーク対策
5. 重複処理の排除
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

class GoogleMapsScraperV5:
    """Google Maps スクレイパー v5 統合版"""
    
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
            "//img[@aria-label='公共交通機関']/.."
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
            logger.warning("公共交通機関ボタンが見つからない")
        
        # 2. 時刻オプションボタンを探してクリック
        time_option_clicked = False
        time_selectors = [
            "//button[contains(@aria-label, '出発時刻')]",
            "//button[contains(@aria-label, 'Depart at')]",
            "//button[contains(text(), 'すぐに出発')]",
            "//span[contains(text(), 'すぐに出発')]/.."
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
            logger.warning("時刻オプションボタンが見つからない - URLパラメータでの指定を使用")
            return False
        
        # 3. 「到着時刻」を選択
        try:
            arrival_option_selectors = [
                "//div[contains(text(), '到着時刻')]",
                "//div[contains(text(), '到着')]",
                "//div[@role='option'][contains(text(), '到着')]"
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
            # 日付入力
            jst = pytz.timezone('Asia/Tokyo')
            arrival_jst = arrival_time.astimezone(jst)
            date_str = arrival_jst.strftime('%Y/%m/%d')
            time_str = arrival_jst.strftime('%H:%M')
            
            # 日付フィールド
            date_selectors = [
                "//input[@aria-label='日付を選択']",
                "//input[@type='date']",
                "//input[contains(@aria-label, '日付')]"
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
            
            # 時刻フィールド
            time_selectors = [
                "//input[@aria-label='時刻を選択']",
                "//input[@type='time']",
                "//input[contains(@aria-label, '時刻')]"
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
                    time_range_match = re.search(r'(\d{1,2}:\d{2})\s*\([^)]+\)\s*-\s*(\d{1,2}:\d{2})', text)
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
        ルート情報をスクレイピング（v5統合版）
        
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
            
            # 基本的なルート検索URL
            base_url = f"https://www.google.com/maps/dir/{quote(origin_normalized)}/{quote(dest_normalized)}"
            
            # Place IDがある場合は追加
            if origin_info.get('place_id') and dest_info.get('place_id'):
                base_url += f"/data=!4m2!4m1!1s{dest_info['place_id']}"
            
            logger.info(f"📍 ルート検索: {dest_name or dest_address[:30]}...")
            self.driver.get(base_url)
            time.sleep(3)
            
            # 時刻指定が必要な場合
            if arrival_time:
                success = self.click_transit_and_set_time(arrival_time)
                if not success:
                    logger.warning("クリック操作での時刻設定に失敗")
            
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
                    'url': base_url
                }
                
                # キャッシュに保存
                self.route_cache[cache_key] = result
                
                return result
            else:
                return {
                    'success': False,
                    'error': 'ルート情報を取得できませんでした',
                    'url': base_url
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

def test_v5_unified():
    """v5統合版のテスト"""
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("Google Maps スクレイパー v5 統合版テスト")
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
    test_v5_unified()