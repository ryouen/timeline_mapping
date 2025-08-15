#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
googleusercontent.comでの情報取得をデバッグ
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
import time
import re

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ja")
    
    driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )
    return driver

def debug_googleusercontent(address):
    """googleusercontent.comでの検索結果を詳しく調査"""
    driver = setup_driver()
    
    try:
        # 住所で検索
        search_url = f"http://googleusercontent.com/maps/search/{quote(address)}"
        print(f"\n検索URL: {search_url}")
        
        driver.get(search_url)
        time.sleep(5)  # ページの読み込みを待つ
        
        # 現在のURL
        current_url = driver.current_url
        print(f"\nリダイレクト後のURL: {current_url}")
        
        # URLから情報を抽出
        print("\n=== URL解析 ===")
        
        # 座標パターン1: @lat,lng
        coord_match1 = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
        if coord_match1:
            print(f"座標(@パターン): {coord_match1.group(1)}, {coord_match1.group(2)}")
        else:
            print("座標(@パターン): 見つかりません")
        
        # 座標パターン2: !3dlat!4dlng
        coord_match2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', current_url)
        if coord_match2:
            print(f"座標(!3d!4dパターン): {coord_match2.group(1)}, {coord_match2.group(2)}")
        else:
            print("座標(!3d!4dパターン): 見つかりません")
        
        # Place IDパターン
        place_id_match = re.search(r'!1s([A-Za-z0-9_-]+)', current_url)
        if place_id_match:
            print(f"Place ID: {place_id_match.group(1)}")
        else:
            print("Place ID: 見つかりません")
        
        # ページソースから情報を探す
        print("\n=== ページソース解析 ===")
        page_source = driver.page_source
        
        # ChIJ形式のPlace IDを検索
        chij_matches = re.findall(r'"(ChIJ[A-Za-z0-9_-]+)"', page_source)
        if chij_matches:
            print(f"ChIJ形式のPlace ID: {chij_matches[0]}")
        else:
            print("ChIJ形式のPlace ID: 見つかりません")
        
        # data-place-id属性
        place_id_attr = re.search(r'data-place-id="([^"]+)"', page_source)
        if place_id_attr:
            print(f"data-place-id属性: {place_id_attr.group(1)}")
        else:
            print("data-place-id属性: 見つかりません")
        
        # 座標情報をJSONから探す
        coord_json = re.search(r'"location":\s*{\s*"lat":\s*(-?\d+\.?\d*),\s*"lng":\s*(-?\d+\.?\d*)', page_source)
        if coord_json:
            print(f"JSON座標: {coord_json.group(1)}, {coord_json.group(2)}")
        else:
            print("JSON座標: 見つかりません")
        
        # スクリーンショットとHTMLを保存
        driver.save_screenshot(f"/app/output/japandatascience.com/timeline-mapping/api/debug/googleusercontent_debug.png")
        with open("/app/output/japandatascience.com/timeline-mapping/api/debug/googleusercontent_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        
        print("\nデバッグファイルを保存しました:")
        print("- googleusercontent_debug.png")
        print("- googleusercontent_debug.html")
        
    finally:
        driver.quit()

# テスト実行
if __name__ == "__main__":
    test_addresses = [
        "東京都千代田区神田須田町1-20-1",  # ルフォンプログレ
        "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階"  # Shizenkan
    ]
    
    for addr in test_addresses:
        debug_googleusercontent(addr)