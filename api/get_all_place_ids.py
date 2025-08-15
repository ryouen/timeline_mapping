#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
すべての目的地のPlace IDを取得
"""

from selenium import webdriver
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
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    return driver

def get_place_info(driver, address, name):
    """住所からPlace IDを取得"""
    try:
        # 出発地（ルフォンプログレ）
        origin = "東京都千代田区神田須田町1-20-1"
        
        # Google Maps URLを構築
        url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(address)}/data=!3e3!5m2!6e1!8j1755338400"
        
        print(f"\n[{name}] アクセス中...")
        driver.get(url)
        time.sleep(5)
        
        # URLからPlace IDを抽出
        current_url = driver.current_url
        
        # Place IDパターン: 2番目が目的地
        place_id_matches = re.findall(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
        
        if len(place_id_matches) >= 2:
            place_id = place_id_matches[1]  # 2番目が目的地
        else:
            place_id = None
        
        # 座標も取得
        coord_matches = re.findall(r'!2d([\d.]+)', current_url)
        if len(coord_matches) >= 4:
            # 3番目と4番目が目的地の座標
            lon = coord_matches[2]
            lat = coord_matches[3]
        else:
            lat, lon = None, None
        
        if place_id:
            print(f"✓ Place ID: {place_id}")
            if lat and lon:
                print(f"  座標: {lat}, {lon}")
        else:
            print("✗ Place ID取得失敗")
        
        return {
            'name': name,
            'address': address,
            'place_id': place_id,
            'lat': lat,
            'lon': lon
        }
        
    except Exception as e:
        print(f"エラー ({name}): {e}")
        return None

def main():
    # 残りの目的地リスト
    destinations = [
        ("Yawara", "東京都渋谷区神宮前１丁目８−１０"),
        ("神谷町(EE)", "東京都港区虎ノ門４丁目２−６"),
        ("早稲田大学", "東京都新宿区西早稲田１丁目６−１"),
        ("府中オフィス", "東京都府中市住吉町５丁目２２−５"),
        ("東京駅", "東京都千代田区丸の内１丁目"),
        ("羽田空港", "東京都大田区羽田空港3-3-2")
    ]
    
    print("="*60)
    print("Place ID一括取得")
    print("="*60)
    
    driver = None
    results = []
    
    try:
        driver = setup_driver()
        
        for name, address in destinations:
            result = get_place_info(driver, address, name)
            if result:
                results.append(result)
            time.sleep(3)  # レート制限対策
        
        # 結果をまとめて表示
        print("\n" + "="*60)
        print("取得結果サマリー")
        print("="*60)
        
        for r in results:
            if r and r['place_id']:
                print(f"\n{r['name']}:")
                print(f"  Place ID: {r['place_id']}")
                print(f"  座標: {r['lat']}, {r['lon']}")
                print(f"  住所: {r['address']}")
            
    except Exception as e:
        print(f"エラー: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("\nSeleniumセッション終了")

if __name__ == "__main__":
    main()