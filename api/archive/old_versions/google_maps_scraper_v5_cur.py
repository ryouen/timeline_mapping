#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール
統合版：高速化 + メモリ管理 + タイムアウト最適化
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

class GoogleMapsScraper:  # プロらしい命名
    def __init__(self):
        self.driver = None
        self.place_id_cache = {}
        self.route_cache = {}
        
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
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # メモリ使用量を制限
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=1024')  # 512→1024MB
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        
        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.driver.set_page_load_timeout(60)  # 30→60秒（Chrome Rendererタイムアウト対策）
        self.driver.implicitly_wait(0)  # Explicit Waitのみ使用（ベストプラクティス）
        self.route_count = 0  # メモリ管理用カウンター
        logger.info("WebDriver初期化完了（統合版）")
        
    def normalize_address(self, address):
        """住所を正規化（Place ID検索用）"""
        # 全角スペースを削除
        normalized = address.replace('　', '').replace(' ', '')
        
        # 「丁目」を「-」に変換（例：１丁目２０−１ → 1-20-1）
        normalized = re.sub(r'(\d+)丁目(\d+)−(\d+)', r'\1-\2-\3', normalized)
        normalized = re.sub(r'(\d+)丁目(\d+)番(\d+)', r'\1-\2-\3', normalized)
        
        # 全角数字を半角に変換
        trans_table = str.maketrans('０１２３４５６７８９', '0123456789')
        normalized = normalized.translate(trans_table)
        
        # 全角ハイフンを半角に
        normalized = normalized.replace('−', '-').replace('ー', '-')
        
        return normalized
    
    def get_place_id(self, address, name=None):
        """Place IDを取得（改善版）"""
        normalized = self.normalize_address(address)
        
        # 長いビル名を削除して基本住所のみに
        # 番地の後のビル名・階数情報を削除（例：2-5-1髙島屋三井ビルディング17階 → 2-5-1）
        simplified = normalized
        
        # 階数情報を削除（17階、9階、1F、B1F など）
        simplified = re.sub(r'\s*\d+階.*$', '', simplified)
        simplified = re.sub(r'\s*[B]?\d+[F].*$', '', simplified)
        
        # ビル名を削除（髙島屋、三井ビルディング、Axle、The Ice Cubes など）
        simplified = re.sub(r'髙島屋.*$', '', simplified)
        simplified = re.sub(r'三井ビルディング.*$', '', simplified)
        simplified = re.sub(r'第二扇屋ビル.*$', '', simplified)
        simplified = re.sub(r'Axle.*$', '', simplified)
        simplified = re.sub(r'The\s+Ice\s+Cubes.*$', '', simplified, flags=re.IGNORECASE)
        
        # 余分なスペースを削除
        simplified = simplified.strip()
        
        # メモリ内キャッシュは検証用（再利用しない）
        cache_key = normalized
        
        logger.info(f"🔍 Place ID取得中: {name or address[:20]}...")
        if normalized != simplified:
            logger.info(f"   簡略化: {simplified}")
        
        try:
            # Google MapsでPlace IDを検索（簡略化した住所を使用）
            search_url = f"https://www.google.com/maps/search/{quote(simplified)}"
            self.driver.get(search_url)
            time.sleep(3)  # ページロード待機
            
            # Place IDを複数の方法で抽出を試みる
            current_url = self.driver.current_url
            place_id = None
            
            # 方法1: ChIJ形式のPlace ID（新形式）をページソースから検索
            chij_match = re.search(r'(ChIJ[a-zA-Z0-9\-\_\.]{23})', self.driver.page_source)
            if chij_match:
                place_id = chij_match.group(1)
                logger.info(f"   ✅ Place ID取得（ChIJ形式）: {place_id}")
            
            # 方法2: URLから/place/の後を取得
            if not place_id:
                place_match = re.search(r'/place/([^/]+)', current_url)
                if place_match:
                    extracted = place_match.group(1)
                    # URLエンコードされた住所でないことを確認
                    if not extracted.startswith('%') and not '+' in extracted[:10]:
                        place_id = extracted
                        logger.info(f"   ✅ Place ID取得（URL）: {place_id}")
            
            # 方法3: 0x形式の古いPlace ID
            if not place_id:
                hex_match = re.search(r'(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
                if hex_match:
                    place_id = hex_match.group(1)
                    logger.info(f"   ✅ Place ID取得（0x形式）: {place_id}")
            
            # 方法4: data-placeid属性から取得
            if not place_id:
                try:
                    element = self.driver.find_element(By.XPATH, "//*[@data-placeid]")
                    attr_id = element.get_attribute("data-placeid")
                    if attr_id and attr_id.startswith('ChIJ'):
                        place_id = attr_id
                        logger.info(f"   ✅ Place ID取得（data属性）: {place_id}")
                except:
                    pass
            
            if place_id:
                # メモリキャッシュと比較（検証用）
                if cache_key in self.place_id_cache:
                    old_value = self.place_id_cache[cache_key]
                    if old_value != place_id:
                        logger.warning(f"   ⚠️ Place ID変更検出: {old_value} → {place_id}")
                    else:
                        logger.info(f"   ✓ Place ID一致確認: {place_id[:20]}...")
                
                # 新しい値を保存
                self.place_id_cache[cache_key] = place_id
                return place_id
            
            # Place IDが見つからない場合は、簡略化した住所を返す（URLエンコードなし）
            logger.warning(f"   ⚠️ Place ID取得失敗、住所で代用: {simplified}")
            self.place_id_cache[cache_key] = simplified  # 住所をキャッシュ
            return simplified  # 住所を返す
            
        except Exception as e:
            logger.error(f"   ❌ Place IDエラー: {e}")
            return None
    
    def click_transit_and_set_time_optimized(self, arrival_time):
        """
        最適化されたクリック操作：動的待機時間制御
        """
        logger.info("公共交通機関モードと時刻設定を開始（最適化版）")
        
        # 一時的にimplicit waitを短縮
        original_implicit_wait = 5
        self.driver.implicitly_wait(2)  # さらに短縮
        
        try:
            # 1. 公共交通機関ボタンをクリック（実績のあるセレクタのみ）
            transit_clicked = self._click_element_fast(
                selectors=[
                    "//div[@aria-label='公共交通機関']",  # 最も確実（動作確認済み）
                    "//div[@role='radio'][@aria-label='公共交通機関']",  # バックアップ
                ],
                action_name="公共交通機関ボタン",
                timeout=5,
                required=False
            )
            
            if transit_clicked:
                time.sleep(2)  # UI安定化待機
            
            # 2. 時刻オプションボタンをクリック
            time_option_clicked = self._click_element_fast(
                selectors=[
                    "//span[contains(text(), 'すぐに出発')]/..",  # 実績あり
                    "//button[contains(@aria-label, '出発時刻')]",
                    "//button[contains(text(), '出発')]",
                ],
                action_name="時刻オプションボタン",
                timeout=5,
                required=False
            )
            
            if time_option_clicked:
                time.sleep(1)
                
                # 3. 到着時刻オプションを選択（短縮）
                self._click_element_fast(
                    selectors=[
                        "//div[contains(text(), '到着時刻')]",
                        "//div[contains(text(), '到着')]",
                        "//div[@role='option'][contains(text(), '到着')]",
                    ],
                    action_name="到着時刻オプション",
                    timeout=3,
                    required=False
                )
                time.sleep(1)
            
            # 4. 日付・時刻入力（高速化）
            return self._input_datetime_fast(arrival_time)
            
        finally:
            # implicit waitを元に戻す
            self.driver.implicitly_wait(original_implicit_wait)
            logger.info("時刻設定処理完了")
    
    def _click_element_fast(self, selectors, action_name, timeout=10, required=False):  # 5→10秒
        """
        高速化された要素クリック
        """
        wait = WebDriverWait(self.driver, timeout)
        
        # 各セレクタに割り当てる時間
        time_per_selector = max(1, timeout / len(selectors))
        
        for i, selector in enumerate(selectors):
            try:
                # 短い個別タイムアウトで試行
                element = WebDriverWait(self.driver, time_per_selector).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                logger.info(f"{action_name}をクリック（セレクタ{i+1}）")
                return True
                
            except TimeoutException:
                continue
            except Exception as e:
                logger.debug(f"セレクタ{i+1}エラー: {e}")
                continue
        
        if required:
            logger.error(f"{action_name}が見つかりません")
            return False
        else:
            logger.warning(f"{action_name}が見つからない - URLパラメータで設定済み")
            return False
    
    def _input_datetime_fast(self, arrival_time):
        """
        高速化された日付・時刻入力
        """
        try:
            jst = pytz.timezone('Asia/Tokyo')
            arrival_jst = arrival_time.astimezone(jst)
            date_str = arrival_jst.strftime('%Y/%m/%d')
            time_str = arrival_jst.strftime('%H:%M')
            
            # 日付入力（最小限のセレクタ）
            date_success = self._input_field_fast(
                selectors=[
                    "//input[@type='date']",
                    "//input[@aria-label='日付を選択']",
                ],
                value=date_str,
                field_name="日付",
                timeout=3
            )
            
            # 時刻入力（最小限のセレクタ）
            time_success = self._input_field_fast(
                selectors=[
                    "//input[@type='time']",
                    "//input[@aria-label='時刻を選択']",
                ],
                value=time_str,
                field_name="時刻",
                timeout=3,
                send_return=True
            )
            
            if date_success or time_success:
                time.sleep(3)  # 処理完了待機
                logger.info("時刻設定完了")
                return True
            else:
                logger.warning("日付・時刻の入力フィールドなし（URLパラメータで設定済み）")
                return True
                
        except Exception as e:
            logger.error(f"日付・時刻入力エラー: {e}")
            return False
    
    def _input_field_fast(self, selectors, value, field_name, timeout=6, send_return=False):  # 3→6秒
        """
        高速化されたフィールド入力
        """
        time_per_selector = max(0.5, timeout / len(selectors))
        
        for i, selector in enumerate(selectors):
            try:
                element = WebDriverWait(self.driver, time_per_selector).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                element.clear()
                element.send_keys(value)
                if send_return:
                    element.send_keys(Keys.RETURN)
                logger.info(f"{field_name}を入力: {value}")
                return True
                
            except TimeoutException:
                continue
            except Exception:
                continue
        
        logger.debug(f"{field_name}の入力フィールドが見つかりません")
        return False
    
    def scrape_route(self, origin, destination, dest_name, arrival_time):
        """
        ルート情報をスクレイピング（最適化版）
        """
        # キャッシュチェック
        normalized_origin = self.normalize_address(origin)
        normalized_dest = self.normalize_address(destination)
        cache_key = f"{normalized_origin}→{normalized_dest}"
        
        if cache_key in self.route_cache:
            logger.info(f"⚡ キャッシュからルート取得: {dest_name}")
            cached = self.route_cache[cache_key].copy()
            cached['from_cache'] = True
            return cached
        
        try:
            # Place IDを事前取得
            origin_place_id = self.get_place_id(origin, "出発地")
            dest_place_id = self.get_place_id(destination, dest_name)
            
            # タイムスタンプ付きURLを構築
            timestamp = int(arrival_time.timestamp())
            
            # URLパス部分（表示用の名前）
            url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/"
            
            # Place IDを使ったdataブロブを構築
            if origin_place_id and dest_place_id:
                # Place IDをdataブロブに埋め込む（正しい形式）
                # !1m5!1m1!1s{place_id} が場所指定の正しい形式
                origin_blob = f"!1m5!1m1!1s{origin_place_id}"
                dest_blob = f"!1m5!1m1!1s{dest_place_id}"
                time_blob = f"!2m3!6e1!7e2!8j{timestamp}"  # !6e1=到着時刻
                transit_mode = "!3e3"  # 公共交通機関
                
                # dataブロブを結合
                url += f"data=!4m14!4m13{origin_blob}{dest_blob}{time_blob}{transit_mode}"
            else:
                # Place IDがない場合は従来のパラメータ
                url += f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
            
            logger.info(f"📍 ルート検索: {dest_name}...")
            self.driver.get(url)
            time.sleep(5)  # 初期ロード待機
            
            # 最適化されたクリック操作
            self.click_transit_and_set_time_optimized(arrival_time)
            
            # ルート情報を取得
            result = self._extract_route_info(dest_name)
            
            if result['success']:
                # キャッシュに保存
                self.route_cache[cache_key] = result.copy()
                result['from_cache'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'destination': dest_name
            }
        finally:
            # メモリクリーンアップ（統合版のcleanup_after_routeを使用）
            self.cleanup_after_route()
    
    def _extract_route_info(self, dest_name):
        """ルート情報の抽出"""
        try:
            # ルート要素を待機（タイムアウトを延長）
            wait = WebDriverWait(self.driver, 40)  # 20→40秒
            route_elements = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
            )
            
            logger.info(f"{len(route_elements)}個のルートを検出")
            
            if not route_elements:
                return {
                    'success': False,
                    'error': 'ルートが見つかりません',
                    'destination': dest_name
                }
            
            # 全ルート情報を収集
            all_routes = []
            
            for i, element in enumerate(route_elements[:6], 1):
                try:
                    route_text = element.text
                    route_info = self._parse_route_text(route_text, i)
                    
                    if route_info:
                        all_routes.append(route_info)
                        
                        # ログ出力
                        logger.info(
                            f"ルート{i}: {route_info['travel_time']}分 "
                            f"({route_info['route_type']}) "
                            f"料金:{route_info.get('fare')}円 "
                            f"路線:{','.join(route_info.get('train_lines', []))}"
                        )
                        
                except Exception as e:
                    logger.warning(f"ルート{i}の解析エラー: {e}")
                    continue
            
            if not all_routes:
                return {
                    'success': False,
                    'error': 'ルート情報の解析に失敗',
                    'destination': dest_name
                }
            
            # 最適ルートを選択（公共交通機関優先、次に時間）
            best_route = self._select_best_route(all_routes)
            
            return {
                'success': True,
                'destination': dest_name,
                'travel_time': best_route['travel_time'],
                'route_type': best_route['route_type'],
                'train_lines': best_route.get('train_lines', []),
                'fare': best_route.get('fare'),
                'departure_time': best_route.get('departure_time'),
                'arrival_time': best_route.get('arrival_time'),
                'all_routes': all_routes[:3]  # 上位3ルートを保存
            }
            
        except TimeoutException:
            logger.error("ルート情報の取得タイムアウト")
            return {
                'success': False,
                'error': 'タイムアウト',
                'destination': dest_name
            }
        except Exception as e:
            logger.error(f"ルート情報取得エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'destination': dest_name
            }
    
    def _parse_route_text(self, text, route_num):
        """ルートテキストの解析"""
        try:
            # 時間の抽出
            time_patterns = [
                r'(\d+)\s*時間\s*(\d+)\s*分',
                r'(\d+)\s*分',
                r'(\d+)\s*min',
                r'(\d+)\s*hour[s]?\s*(\d+)\s*min'
            ]
            
            travel_time = None
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 2:
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        travel_time = hours * 60 + minutes
                    else:
                        travel_time = int(match.group(1))
                    break
            
            if travel_time is None:
                return None
            
            # ルートタイプの判定
            route_type = self._determine_route_type(text)
            
            # 路線情報の抽出
            train_lines = self._extract_train_lines(text)
            
            # 料金の抽出
            fare = self._extract_fare(text)
            
            # 時刻の抽出
            times = self._extract_times(text)
            
            return {
                'travel_time': travel_time,
                'route_type': route_type,
                'train_lines': train_lines,
                'fare': fare,
                'departure_time': times.get('departure'),
                'arrival_time': times.get('arrival'),
                'route_number': route_num
            }
            
        except Exception as e:
            logger.warning(f"ルートテキスト解析エラー: {e}")
            return None
    
    def _determine_route_type(self, text):
        """ルートタイプの判定"""
        text_lower = text.lower()
        
        # 判定キーワード
        if any(word in text for word in ['線', '駅', 'バス', '電車', '地下鉄']):
            return '公共交通機関'
        elif '徒歩' in text or 'walk' in text_lower:
            if '分' in text:
                time_match = re.search(r'(\d+)\s*分', text)
                if time_match and int(time_match.group(1)) > 20:
                    return '徒歩のみ'
            return '徒歩'
        elif '車' in text or '高速' in text or 'drive' in text_lower:
            return '車'
        elif '自転車' in text or 'bike' in text_lower or 'bicycle' in text_lower:
            return '自転車'
        else:
            return '不明'
    
    def _extract_train_lines(self, text):
        """路線名の抽出"""
        lines = []
        
        # 一般的な路線パターン
        line_patterns = [
            r'([^\s、,]+線)',  # ○○線
            r'([^\s、,]+ライン)',  # ○○ライン
            r'JR([^\s、,]+)',  # JR○○
            r'([^\s、,]+急行)',  # ○○急行
            r'([^\s、,]+特急)',  # ○○特急
        ]
        
        for pattern in line_patterns:
            matches = re.findall(pattern, text)
            lines.extend(matches)
        
        # 重複を除去して順序を保持
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return unique_lines
    
    def _extract_fare(self, text):
        """料金の抽出"""
        # 料金パターン
        fare_patterns = [
            r'¥\s*(\d+)',
            r'(\d+)\s*円',
            r'(\d+)\s*yen',
            r'￥\s*(\d+)'
        ]
        
        for pattern in fare_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_times(self, text):
        """時刻の抽出"""
        times = {}
        
        # 時刻パターン（例: 9:25、09:25）
        time_pattern = r'(\d{1,2}:\d{2})'
        time_matches = re.findall(time_pattern, text)
        
        if len(time_matches) >= 2:
            times['departure'] = time_matches[0]
            times['arrival'] = time_matches[-1]
        elif len(time_matches) == 1:
            times['arrival'] = time_matches[0]
        
        return times
    
    def _select_best_route(self, routes):
        """最適ルートの選択"""
        if not routes:
            return None
        
        # 優先順位：
        # 1. 公共交通機関のルート
        # 2. 所要時間が短い
        # 3. 料金情報がある
        
        public_routes = [r for r in routes if r['route_type'] == '公共交通機関']
        
        if public_routes:
            # 公共交通機関の中で最短時間
            return min(public_routes, key=lambda x: x['travel_time'])
        else:
            # 全ルートの中で最短時間
            return min(routes, key=lambda x: x['travel_time'])
    
    def cleanup_after_route(self):
        """各ルート処理後のメモリクリーンアップ（v5から統合）"""
        try:
            # ページをabout:blankにしてメモリ解放
            self.driver.execute_script("window.location.href='about:blank'")
            time.sleep(0.5)
            
            # ガベージコレクション実行
            gc.collect()
            
            # 9ルートごとにWebDriverを再起動（1物件分）
            self.route_count += 1
            if self.route_count >= 9:
                logger.info("9ルート処理完了。WebDriverを再起動します...")
                self.restart_driver()
                self.route_count = 0
                
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")
    
    def restart_driver(self):
        """WebDriverを再起動する（v5から統合）"""
        try:
            if self.driver:
                self.driver.quit()
            self.setup_driver()
            logger.info("WebDriver再起動完了")
        except Exception as e:
            logger.error(f"WebDriver再起動エラー: {e}")
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver終了")


# テスト用のメイン関数
if __name__ == "__main__":
    # テスト実行
    from datetime import datetime, timedelta
    import pytz
    
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    scraper = GoogleMapsScraperV5Optimized()
    
    try:
        scraper.setup_driver()
        
        # テストルート
        result = scraper.scrape_route(
            "東京都千代田区神田須田町1-20-1",
            "東京都新宿区西早稲田1-6-11",
            "早稲田大学",
            arrival_time
        )
        
        if result['success']:
            print(f"✅ 成功: {result['travel_time']}分 ({result['route_type']})")
            if result.get('train_lines'):
                print(f"   路線: {', '.join(result['train_lines'])}")
        else:
            print(f"❌ 失敗: {result['error']}")
            
    finally:
        scraper.close()