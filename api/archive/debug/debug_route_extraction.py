#!/usr/bin/env python3
"""ルート要素の内容を詳細にデバッグ"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_route_extraction():
    """ルート要素の抽出をデバッグ"""
    
    # WebDriver設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    # Seleniumハブに接続
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    try:
        # ChIJ形式のPlace IDを使用したURL
        url = ("https://www.google.com/maps/dir/"
               "東京都千代田区神田須田町1-20-1/"
               "東京都千代田区丸の内1丁目/"
               "data=!4m18!4m17!1m5!1m1!1s"
               "ChIJ2RxO9gKMGGARSvjnp3ocfJg"  # ルフォンプログレ
               "!2m2!1d139.7711!2d35.6950"
               "!1m5!1m1!1s"
               "ChIJLdASefmLGGARF3Ez6A4i4Q4"  # 東京駅
               "!2m2!1d139.7676!2d35.6812"
               "!2m3!6e1!7e2!8j1755511200!3e3")
        
        print("=" * 60)
        print("ルート要素デバッグ")
        print("=" * 60)
        print(f"URL: {url[:100]}...")
        
        driver.get(url)
        time.sleep(5)
        
        # ページタイトル
        print(f"\nページタイトル: {driver.title}")
        
        # ルート要素を探す
        route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        print(f"\nルート要素数: {len(route_elements)}個")
        
        if route_elements:
            print("\n最初のルート要素をクリック...")
            route_elements[0].click()
            time.sleep(3)
            
            # クリック後のルート要素を再取得
            route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
            print(f"クリック後のルート要素数: {len(route_elements)}個")
            
            for i, element in enumerate(route_elements[:3]):
                print(f"\n--- ルート {i+1} ---")
                text = element.text
                print(f"テキスト長: {len(text)}文字")
                
                if text:
                    lines = text.split('\n')
                    print(f"行数: {len(lines)}")
                    print("最初の5行:")
                    for line in lines[:5]:
                        print(f"  {line}")
                    
                    # 時間パターンの検索
                    hour_match = re.search(r'(\d+)\s*時間', text)
                    minute_match = re.search(r'(\d+)\s*分', text)
                    
                    if hour_match or minute_match:
                        hours = int(hour_match.group(1)) if hour_match else 0
                        minutes = int(minute_match.group(1)) if minute_match else 0
                        print(f"所要時間: {hours}時間{minutes}分")
                    
                    # 時刻パターンの検索
                    time_pattern = r'(\d{1,2}:\d{2})[^\d]*(?:\([^)]+\)[^\d]*)?\s*-\s*(\d{1,2}:\d{2})'
                    time_match = re.search(time_pattern, text)
                    if time_match:
                        print(f"時刻: {time_match.group(1)} - {time_match.group(2)}")
                    
                    # 運賃パターンの検索
                    fare_pattern = r'(\d{1,3}(?:,\d{3})*|\d+)\s*円'
                    fare_match = re.search(fare_pattern, text)
                    if fare_match:
                        print(f"運賃: {fare_match.group(0)}")
                else:
                    print("テキストなし")
        
        # その他の要素も確認
        print("\n--- その他の要素確認 ---")
        
        # 時間表示要素
        time_elements = driver.find_elements(By.XPATH, "//span[contains(text(), '分')]")
        print(f"時間表示要素: {len(time_elements)}個")
        for elem in time_elements[:3]:
            print(f"  {elem.text}")
        
        # 運賃表示要素
        fare_elements = driver.find_elements(By.XPATH, "//span[contains(text(), '円')]")
        print(f"運賃表示要素: {len(fare_elements)}個")
        for elem in fare_elements[:3]:
            print(f"  {elem.text}")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_route_extraction()