#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place IDを使ったURL形式のテスト
"""
from selenium import webdriver
import time

def test_url_formats():
    """異なるURL形式をテスト"""
    
    # テストケース
    origin_place_id = "ChIJ2RxO9gKMGGARSvjnp3ocfJg"  # 神田
    dest_place_id = "ChIJAZezONeJGGARVv3_TL3Qb5k"    # Shizenkan
    
    test_urls = [
        # 形式1: Place IDを直接使用
        f"https://www.google.com/maps/dir/{origin_place_id}/{dest_place_id}/",
        
        # 形式2: place/を付ける
        f"https://www.google.com/maps/dir/place/{origin_place_id}/place/{dest_place_id}/",
        
        # 形式3: data属性でPlace ID指定
        f"https://www.google.com/maps/dir/?api=1&origin_place_id={origin_place_id}&destination_place_id={dest_place_id}",
        
        # 形式4: 混合（最初の成功例を参考）
        f"https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都中央区日本橋2-5-1/"
    ]
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    try:
        for i, url in enumerate(test_urls, 1):
            print(f"\n形式{i}: {url[:80]}...")
            driver.get(url)
            time.sleep(3)
            
            # URLが変換されたか確認
            current = driver.current_url
            print(f"  結果URL: {current[:80]}...")
            
            # ルート表示されているか確認
            try:
                elements = driver.find_elements("xpath", "//div[@data-trip-index]")
                if elements:
                    print(f"  ✅ ルート要素発見: {len(elements)}個")
                else:
                    print(f"  ❌ ルート要素なし")
            except:
                print(f"  ❌ エラー")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    test_url_formats()