#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最適化されたクリック操作のテスト
動的待機時間制御版
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
import logging
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedClickTester:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """WebDriverのセットアップ"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0')
        chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
        
        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)  # デフォルト値
        logger.info("WebDriver初期化完了")
    
    def click_transit_and_set_time_optimized(self, arrival_time):
        """
        最適化されたクリック操作：動的待機時間制御
        """
        logger.info("公共交通機関モードと時刻設定を開始（最適化版）")
        
        # 一時的にimplicit waitを短縮
        original_implicit_wait = 10
        self.driver.implicitly_wait(2)  # 2秒に短縮
        
        try:
            # 1. 公共交通機関ボタンをクリック（優先度順）
            transit_clicked = self._click_element_with_selectors(
                selectors=[
                    "//button[@aria-label='公共交通機関']",  # 最も確実
                    "//button[@data-travel-mode='3']",      # データ属性
                    "//button[@aria-label='Transit']",      # 英語版
                ],
                action_name="公共交通機関ボタン",
                timeout=6,  # 合計6秒でタイムアウト
                required=False  # URLパラメータで設定済みの場合があるため
            )
            
            if transit_clicked:
                time.sleep(2)  # UIの安定化待機
            
            # 2. 時刻オプションボタンをクリック
            time_option_clicked = self._click_element_with_selectors(
                selectors=[
                    "//button[contains(@aria-label, '出発時刻')]",
                    "//button[contains(text(), 'すぐに出発')]",
                    "//span[contains(text(), 'すぐに出発')]/..",
                ],
                action_name="時刻オプションボタン",
                timeout=4,
                required=False
            )
            
            if time_option_clicked:
                time.sleep(1)
                
                # 3. 到着時刻オプションを選択
                self._click_element_with_selectors(
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
            
            # 4. 日付・時刻入力
            return self._input_datetime(arrival_time)
            
        finally:
            # implicit waitを元に戻す
            self.driver.implicitly_wait(original_implicit_wait)
            logger.info("implicit wait復元完了")
    
    def _click_element_with_selectors(self, selectors, action_name, timeout=5, required=True):
        """
        セレクタリストを使用した最適化された要素クリック
        """
        # 各セレクタに割り当てる時間を計算
        time_per_selector = max(1, timeout // len(selectors))
        
        for i, selector in enumerate(selectors):
            try:
                wait = WebDriverWait(self.driver, time_per_selector)
                element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                logger.info(f"{action_name}をクリック（セレクタ{i+1}/{len(selectors)}）")
                return True
                
            except TimeoutException:
                logger.debug(f"セレクタ{i+1}タイムアウト: {selector[:50]}...")
                continue
            except Exception as e:
                logger.debug(f"セレクタ{i+1}でエラー: {e}")
                continue
        
        if required:
            logger.error(f"{action_name}が見つかりません")
            return False
        else:
            logger.warning(f"{action_name}が見つからない - URLパラメータで設定済み")
            return False
    
    def _input_datetime(self, arrival_time):
        """
        最適化された日付・時刻入力
        """
        try:
            jst = pytz.timezone('Asia/Tokyo')
            arrival_jst = arrival_time.astimezone(jst)
            date_str = arrival_jst.strftime('%Y/%m/%d')
            time_str = arrival_jst.strftime('%H:%M')
            
            # 日付入力（優先度順）
            date_success = self._input_to_field(
                selectors=[
                    "//input[@type='date']",                    # 最も確実
                    "//input[@aria-label='日付を選択']",
                ],
                value=date_str,
                field_name="日付",
                timeout=3
            )
            
            # 時刻入力（優先度順）
            time_success = self._input_to_field(
                selectors=[
                    "//input[@type='time']",                    # 最も確実
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
                logger.warning("日付・時刻の入力に失敗（URLパラメータで設定済みの可能性）")
                return True  # URLパラメータで設定済みなので続行
                
        except Exception as e:
            logger.error(f"日付・時刻入力エラー: {e}")
            return False
    
    def _input_to_field(self, selectors, value, field_name, timeout=3, send_return=False):
        """
        最適化されたフィールド入力
        """
        time_per_selector = max(1, timeout // len(selectors))
        
        for i, selector in enumerate(selectors):
            try:
                wait = WebDriverWait(self.driver, time_per_selector)
                element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.clear()
                element.send_keys(value)
                if send_return:
                    element.send_keys(Keys.RETURN)
                logger.info(f"{field_name}を入力: {value}（セレクタ{i+1}/{len(selectors)}）")
                return True
                
            except TimeoutException:
                logger.debug(f"{field_name}セレクタ{i+1}タイムアウト")
                continue
            except Exception as e:
                logger.debug(f"{field_name}入力セレクタ{i+1}でエラー: {e}")
                continue
        
        logger.warning(f"{field_name}の入力フィールドが見つかりません")
        return False
    
    def test_route(self, origin, destination, dest_name, arrival_time):
        """ルートをテスト"""
        try:
            # タイムスタンプ付きURL
            timestamp = int(arrival_time.timestamp())
            url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/"
            url += f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
            
            logger.info(f"アクセス: {dest_name}")
            self.driver.get(url)
            time.sleep(3)  # 初期ロード待機
            
            # 最適化されたクリック操作
            start_time = time.time()
            self.click_transit_and_set_time_optimized(arrival_time)
            click_time = time.time() - start_time
            
            logger.info(f"クリック操作完了: {click_time:.1f}秒")
            
            # ルート情報を簡単に確認
            try:
                wait = WebDriverWait(self.driver, 10)
                route_elements = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
                )
                logger.info(f"{len(route_elements)}個のルート検出")
                return True, click_time
            except:
                logger.error("ルート情報取得失敗")
                return False, click_time
                
        except Exception as e:
            logger.error(f"テストエラー: {e}")
            return False, 0
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver終了")

def main():
    """メインテスト関数"""
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("⚡ 最適化クリック操作テスト")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    tester = OptimizedClickTester()
    
    try:
        tester.setup_driver()
        
        # テストケース
        test_cases = [
            ('Shizenkan', '東京都中央区日本橋2-5-1'),
            ('早稲田大学', '東京都新宿区西早稲田1-6-11'),
        ]
        
        origin = '東京都千代田区神田須田町1-20-1'
        total_time = 0
        
        for name, dest in test_cases:
            print(f"\n[{name}]")
            success, click_time = tester.test_route(origin, dest, name, arrival_time)
            
            if success:
                print(f"  ✅ 成功 - クリック操作: {click_time:.1f}秒")
                total_time += click_time
            else:
                print(f"  ❌ 失敗")
        
        print(f"\n合計クリック時間: {total_time:.1f}秒")
        print(f"平均: {total_time/len(test_cases):.1f}秒/ルート")
        
    finally:
        tester.close()

if __name__ == "__main__":
    main()