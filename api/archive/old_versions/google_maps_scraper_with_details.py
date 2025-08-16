#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール（詳細情報対応版）
v5ベースに詳細抽出機能を追加
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
    """Google Maps スクレイパー（詳細情報対応）"""
    
    def __init__(self):
        self.driver = None
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
            
            return result
            
        except Exception as e:
            logger.error(f"Place ID取得エラー: {e}")
            return {'place_id': None, 'lat': None, 'lon': None, 'normalized_address': normalized}
    
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
    
    def extract_detailed_info(self, expanded_text):
        """
        展開されたルートテキストから詳細情報を抽出
        """
        detailed_info = {
            'walk_to_station': None,
            'walk_from_station': None,
            'wait_time_minutes': None,
            'trains': []
        }
        
        try:
            # 駅名と時刻を探す（例: "神田駅から 0:44"）
            station_time_pattern = r'([^\s]+駅)から\s*(\d+:\d+)'
            station_matches = re.findall(station_time_pattern, expanded_text)
            
            # 分単位の時間を探す（例: "7 分"、"19 分"）
            time_pattern = r'(\d+)\s*分'
            time_matches = re.findall(time_pattern, expanded_text)
            
            # 路線名を探す（例: "山手線"）
            line_pattern = r'([^\s]+線)'
            line_matches = re.findall(line_pattern, expanded_text)
            
            # 徒歩時間の推定（最初と最後の時間を徒歩と仮定）
            if time_matches:
                # 時間リストから徒歩時間を推定
                times = [int(t) for t in time_matches]
                
                # 合計時間が最初の要素の場合、その後の要素を見る
                if len(times) >= 2:
                    # 最初の要素が合計時間の可能性が高い（例: 21分）
                    # 2番目以降を徒歩時間として扱う
                    detailed_info['walk_to_station'] = times[1] if len(times) > 1 else None
                    # 最後の要素を駅から目的地への徒歩時間とする
                    if len(times) > 2:
                        detailed_info['walk_from_station'] = times[-1]
            
            # 電車情報の構築
            if station_matches and line_matches:
                for i, line in enumerate(line_matches[:1]):  # 最初の路線のみ
                    train_info = {
                        'line': line,
                        'departure': station_matches[0][1] if station_matches else None,
                        'arrival': None,
                        'duration': None
                    }
                    
                    # 到着時刻を推定（出発時刻から次の時刻）
                    all_times = re.findall(r'\d+:\d+', expanded_text)
                    if len(all_times) >= 2:
                        train_info['arrival'] = all_times[1]
                    
                    detailed_info['trains'].append(train_info)
            
            logger.info(f"詳細情報抽出: 徒歩{detailed_info['walk_to_station']}/{detailed_info['walk_from_station']}分, 電車{len(detailed_info['trains'])}本")
            
        except Exception as e:
            logger.warning(f"詳細情報抽出エラー: {e}")
        
        return detailed_info
    
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
            
            # 最初のルートをクリックして詳細を展開
            detailed_info = None
            if route_elements:
                try:
                    logger.info(f"最初のルートをクリック - セレクタ: //div[@data-trip-index='0']")
                    logger.info(f"要素のテキスト（最初の100文字）: {route_elements[0].text[:100]}...")
                    route_elements[0].click()
                    time.sleep(2)
                    
                    # クリック後はDOMが変わるので、要素を再取得
                    expanded_route = self.driver.find_element(By.XPATH, "//div[@data-trip-index='0']")
                    expanded_text = expanded_route.text
                    logger.info(f"展開後のテキスト長: {len(expanded_text)}文字")
                    
                    # 詳細情報を抽出
                    detailed_info = self.extract_detailed_info(expanded_text)
                    
                except Exception as e:
                    logger.warning(f"ルートクリックエラー: {e}")
                    # クリックに失敗した場合、要素を再取得して続行
                    try:
                        route_elements = self.driver.find_elements(By.XPATH, "//div[@data-trip-index]")
                    except:
                        pass
            
            # ルート要素を再取得（クリック後はDOMが変わるため）
            route_elements = self.driver.find_elements(By.XPATH, "//div[@data-trip-index]")
            
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
                    
                    # 最初のルートに詳細情報を追加
                    if i == 0 and detailed_info:
                        route_info.update(detailed_info)
                    
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
            
            # 現在のURLをログ出力
            current_url = self.driver.current_url
            logger.info(f"📍 現在のURL: {current_url[:200]}...")
            
            # ルート詳細を抽出（自動的に詳細展開も含む）
            routes = self.extract_route_details()
            
            if routes:
                # 公共交通機関のルートを優先
                transit_routes = [r for r in routes if r['route_type'] == '公共交通機関']
                if transit_routes:
                    shortest = min(transit_routes, key=lambda r: r['travel_time'])
                else:
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
                    'train_lines': shortest.get('train_lines', []),
                    'walk_to_station': shortest.get('walk_to_station'),
                    'walk_from_station': shortest.get('walk_from_station'),
                    'wait_time_minutes': shortest.get('wait_time_minutes'),
                    'trains': shortest.get('trains', []),
                    'all_routes': routes,
                    'place_ids': {
                        'origin': origin_info.get('place_id'),
                        'destination': dest_info.get('place_id')
                    },
                    'url': url
                }
                
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

def test_with_details():
    """詳細情報取得のテスト"""
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*60)
    print("Google Maps スクレイパー 詳細情報テスト")
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    print("="*60)
    
    # テストケース
    test_cases = [
        {
            'name': '東京駅',
            'origin': '東京都千代田区 神田須田町１丁目２０−１',
            'destination': '東京都千代田区丸の内1-9-1'
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
                
                # 詳細情報を表示
                print(f"\n  【詳細情報】")
                print(f"  駅まで徒歩: {result.get('walk_to_station', 'N/A')}分")
                print(f"  駅から徒歩: {result.get('walk_from_station', 'N/A')}分")
                print(f"  待機時間: {result.get('wait_time_minutes', 'N/A')}分")
                
                if result.get('trains'):
                    print(f"  電車情報:")
                    for train in result['trains']:
                        print(f"    - {train.get('line', 'N/A')}: {train.get('departure', 'N/A')} → {train.get('arrival', 'N/A')}")
            else:
                print(f"❌ 失敗: {result.get('error')}")
                
    finally:
        scraper.close()

if __name__ == "__main__":
    test_with_details()