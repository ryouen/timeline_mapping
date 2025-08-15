#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各目的地のPlace IDを取得するスクリプト
住所ベースで正確な場所を検索
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from urllib.parse import quote

def setup_driver():
    """Selenium WebDriverのセットアップ"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    driver.implicitly_wait(10)
    return driver

def get_place_id_from_url(url):
    """URLからPlace IDを抽出"""
    # Pattern: !1s0x...:0x...
    match = re.search(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', url)
    if match:
        return match.group(1)
    return None

def get_coordinates_from_url(url):
    """URLから座標を抽出"""
    # Pattern: !2d139.xxx!2d35.xxx
    lon_match = re.search(r'!2d([\d.]+)', url)
    lat_match = re.search(r'!2d[\d.]+!2d([\d.]+)', url)
    if lon_match and lat_match:
        return lat_match.group(1), lon_match.group(1)
    
    # Alternative pattern: @35.xxx,139.xxx
    coord_match = re.search(r'@([\d.]+),([\d.]+)', url)
    if coord_match:
        return coord_match.group(1), coord_match.group(2)
    
    return None, None

def test_destination(driver, origin, dest_name, dest_address):
    """各目的地のテスト"""
    print(f"\n{'='*60}")
    print(f"目的地: {dest_name}")
    print(f"住所: {dest_address}")
    print('='*60)
    
    # URLを構築（住所を使用）
    base_url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(dest_address)}"
    
    # タイムスタンプ（2025年8月16日 10:00 JST = 10:00 UTC）
    timestamp = 1755338400
    
    # 公共交通機関モード、時刻指定付きURL
    url_with_params = f"{base_url}/data=!3e3!5m2!6e1!8j{timestamp}"
    
    print(f"アクセスURL: {url_with_params[:100]}...")
    
    driver.get(url_with_params)
    time.sleep(3)
    
    # 現在のURLを取得
    current_url = driver.current_url
    
    # Place IDを抽出
    place_id = get_place_id_from_url(current_url)
    lat, lon = get_coordinates_from_url(current_url)
    
    print(f"Place ID: {place_id}")
    print(f"座標: {lat}, {lon}")
    
    # 完全なURLを構築
    if place_id and lat and lon:
        # 出発地のPlace ID（ルフォンプログレ）
        origin_place_id = "0x60188c02f64e1cd9:0x987c1c7aa7e7f84a"
        origin_lat, origin_lon = "35.6949994", "139.7711379"
        
        complete_url = (
            f"https://www.google.com/maps/dir/"
            f"{quote(origin)}/{quote(dest_address)}/"
            f"@{lat},{lon},16z/"
            f"data=!4m18!4m17"
            f"!1m5!1m1!1s{origin_place_id}!2m2!1d{origin_lon}!2d{origin_lat}"
            f"!1m5!1m1!1s{place_id}!2m2!1d{lon}!2d{lat}"
            f"!2m3!6e1!7e2!8j{timestamp}!3e3"
        )
        
        print(f"\n完全なURL:")
        print(complete_url)
    else:
        print("Place IDまたは座標の取得に失敗")
    
    return {
        'name': dest_name,
        'address': dest_address,
        'place_id': place_id,
        'lat': lat,
        'lon': lon,
        'url': complete_url if place_id else url_with_params
    }

def main():
    """メイン処理"""
    
    # 出発地
    origin = "東京都千代田区神田須田町1-20-1"
    
    # 目的地リスト（正しい住所）
    destinations = [
        ("Shizenkan University", "東京都中央区日本橋２丁目５−１"),
        ("東京アメリカンクラブ", "東京都中央区日本橋室町３丁目２−１"),
        ("axle 御茶ノ水", "東京都千代田区神田小川町３丁目２８−５"),
        ("Yawara", "東京都渋谷区神宮前１丁目８−１０"),
        ("神谷町(EE)", "東京都港区虎ノ門４丁目２−６"),
        ("早稲田大学", "東京都新宿区西早稲田１丁目６−１"),
        ("府中オフィス", "東京都府中市住吉町５丁目２２−５"),
        ("東京駅", "東京都千代田区丸の内１丁目"),
        ("羽田空港", "東京都大田区羽田空港3-3-2")
    ]
    
    driver = None
    results = []
    
    try:
        driver = setup_driver()
        
        for dest_name, dest_address in destinations:
            result = test_destination(driver, origin, dest_name, dest_address)
            results.append(result)
            time.sleep(2)  # レート制限対策
        
        # 結果をまとめて表示
        print("\n" + "="*60)
        print("完全なURL一覧")
        print("="*60)
        
        for r in results:
            print(f"\n{r['name']}:")
            print(r['url'])
            
    except Exception as e:
        print(f"エラー: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("\nSeleniumセッション終了")

if __name__ == "__main__":
    main()