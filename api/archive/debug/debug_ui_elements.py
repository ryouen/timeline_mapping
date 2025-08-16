#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps UIの要素を詳細にデバッグ
実際にどんな要素が存在するか確認
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote

def debug_ui_elements():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🔍 Google Maps UI要素デバッグ")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # WebDriver設定
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    driver.implicitly_wait(5)
    
    try:
        origin = '東京都千代田区神田須田町1-20-1'
        destination = '東京都新宿区西早稲田1-6-11'
        
        # タイムスタンプ付きURL（公共交通機関モード）
        timestamp = int(arrival_time.timestamp())
        url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/"
        url += f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
        
        print(f"\nアクセス中...")
        print(f"URL: {url[:100]}...")
        driver.get(url)
        time.sleep(5)  # ページ完全ロード待機
        
        print("\n【ボタン要素の検索】")
        
        # 1. 公共交通機関ボタンの存在確認
        print("\n1. 公共交通機関ボタン:")
        transit_buttons = [
            ("aria-label='公共交通機関'", "//button[@aria-label='公共交通機関']"),
            ("aria-label='Transit'", "//button[@aria-label='Transit']"),
            ("data-travel-mode='3'", "//button[@data-travel-mode='3']"),
            ("class contains transit", "//button[contains(@class, 'transit')]"),
            ("画像付きボタン", "//img[@aria-label='公共交通機関']/.."),
        ]
        
        for desc, xpath in transit_buttons:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"  ✓ {desc}: {len(elements)}個見つかりました")
                    for i, elem in enumerate(elements[:2]):
                        print(f"    要素{i+1}: 表示={elem.is_displayed()}, クリック可能={elem.is_enabled()}")
                else:
                    print(f"  ✗ {desc}: 見つかりません")
            except Exception as e:
                print(f"  ✗ {desc}: エラー {e}")
        
        # 2. 時刻関連ボタンの存在確認
        print("\n2. 時刻オプションボタン:")
        time_buttons = [
            ("出発時刻", "//button[contains(@aria-label, '出発時刻')]"),
            ("すぐに出発", "//button[contains(text(), 'すぐに出発')]"),
            ("出発", "//button[contains(text(), '出発')]"),
            ("Depart at", "//button[contains(@aria-label, 'Depart at')]"),
            ("spanのすぐに出発", "//span[contains(text(), 'すぐに出発')]"),
        ]
        
        for desc, xpath in time_buttons:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"  ✓ {desc}: {len(elements)}個見つかりました")
                    for i, elem in enumerate(elements[:2]):
                        print(f"    要素{i+1}: テキスト='{elem.text[:30]}...', 表示={elem.is_displayed()}")
                else:
                    print(f"  ✗ {desc}: 見つかりません")
            except Exception as e:
                print(f"  ✗ {desc}: エラー {e}")
        
        # 3. 全てのボタンを列挙
        print("\n3. ページ内の全ボタン（最初の10個）:")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"  合計: {len(all_buttons)}個のボタン")
        
        for i, button in enumerate(all_buttons[:10]):
            try:
                aria_label = button.get_attribute("aria-label") or "なし"
                text = button.text[:30] if button.text else "テキストなし"
                displayed = button.is_displayed()
                print(f"  ボタン{i+1}: aria-label='{aria_label}', text='{text}', 表示={displayed}")
            except:
                pass
        
        # 4. 入力フィールドの確認
        print("\n4. 入力フィールド:")
        input_fields = [
            ("type='date'", "//input[@type='date']"),
            ("type='time'", "//input[@type='time']"),
            ("日付選択", "//input[@aria-label='日付を選択']"),
            ("時刻選択", "//input[@aria-label='時刻を選択']"),
            ("全input", "//input"),
        ]
        
        for desc, xpath in input_fields:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"  ✓ {desc}: {len(elements)}個見つかりました")
                    for i, elem in enumerate(elements[:3]):
                        input_type = elem.get_attribute("type") or "なし"
                        aria_label = elem.get_attribute("aria-label") or "なし"
                        print(f"    入力{i+1}: type='{input_type}', aria-label='{aria_label}'")
                else:
                    print(f"  ✗ {desc}: 見つかりません")
            except Exception as e:
                print(f"  ✗ {desc}: エラー {e}")
        
        # 5. divとspanの特定テキスト
        print("\n5. 特定テキストを含む要素:")
        text_elements = [
            ("到着時刻div", "//div[contains(text(), '到着')]"),
            ("出発時刻div", "//div[contains(text(), '出発')]"),
            ("公共交通機関span", "//span[contains(text(), '公共交通機関')]"),
            ("電車span", "//span[contains(text(), '電車')]"),
        ]
        
        for desc, xpath in text_elements:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"  ✓ {desc}: {len(elements)}個見つかりました")
                else:
                    print(f"  ✗ {desc}: 見つかりません")
            except:
                pass
        
        # 6. ルート情報の確認
        print("\n6. ルート情報:")
        try:
            route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
            print(f"  ルート数: {len(route_elements)}個")
            
            if route_elements:
                text = route_elements[0].text[:200]
                print(f"  最初のルート: {text}...")
        except:
            print("  ルート情報取得エラー")
        
    finally:
        driver.quit()
        print("\n✅ デバッグ完了")

if __name__ == "__main__":
    debug_ui_elements()