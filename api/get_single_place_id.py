#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
単一の目的地のPlace IDを取得
"""

from selenium import webdriver
import time
import re
from urllib.parse import quote
import sys

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
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    return driver

def get_place_info(address):
    """住所からPlace IDを取得"""
    driver = None
    try:
        driver = setup_driver()
        
        # 出発地（ルフォンプログレ）
        origin = "東京都千代田区神田須田町1-20-1"
        
        # Google Maps URLを構築
        url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(address)}/data=!3e3!5m2!6e1!8j1755338400"
        
        print(f"アクセス中: {address}")
        driver.get(url)
        time.sleep(5)
        
        # URLからPlace IDを抽出
        current_url = driver.current_url
        
        # Place IDパターン: !1s(0x...:0x...)
        # URLには2つのPlace IDがある（出発地と目的地）
        # 2番目のPlace IDが目的地
        place_id_matches = re.findall(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
        
        if len(place_id_matches) >= 2:
            place_id_match = place_id_matches[1]  # 2番目が目的地
        elif place_id_matches:
            place_id_match = place_id_matches[0]
        else:
            place_id_match = None
        
        # 座標パターン
        coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
        
        if place_id_match:
            place_id = place_id_match
            print(f"Place ID: {place_id}")
        else:
            print("Place ID: 見つかりません")
            place_id = None
            
        if coord_match:
            lat = coord_match.group(1)
            lon = coord_match.group(2)
            print(f"座標: {lat}, {lon}")
        else:
            # 別のパターンを試す
            lat_match = re.search(r'!2d[\d.]+!2d([\d.]+)', current_url)
            lon_match = re.search(r'!2d([\d.]+)', current_url)
            if lat_match and lon_match:
                lat = lat_match.group(1)
                lon = lon_match.group(1)
                print(f"座標: {lat}, {lon}")
            else:
                print("座標: 見つかりません")
                lat, lon = None, None
        
        return {
            'address': address,
            'place_id': place_id,
            'lat': lat,
            'lon': lon,
            'url': current_url
        }
        
    except Exception as e:
        print(f"エラー: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def main():
    # テストする住所（Yawara）
    test_address = "東京都渋谷区神宮前１丁目８−１０"
    
    print("="*60)
    print(f"Place ID取得テスト")
    print("="*60)
    
    result = get_place_info(test_address)
    
    if result and result['place_id']:
        print("\n成功！")
        print(f"Place ID: {result['place_id']}")
        print(f"座標: {result['lat']}, {result['lon']}")
    else:
        print("\n失敗 - Place IDを取得できませんでした")

if __name__ == "__main__":
    main()