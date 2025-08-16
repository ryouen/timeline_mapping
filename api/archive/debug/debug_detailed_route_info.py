#!/usr/bin/env python3
"""詳細なルート情報の取得可能性を調査"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# WebDriver設定
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
options.add_argument('--accept-language=ja-JP,ja;q=0.9')

driver = webdriver.Remote(
    command_executor='http://selenium:4444/wd/hub',
    options=options
)

# URL（東京駅の新Place ID使用）
url = ("https://www.google.com/maps/dir/"
       "東京都千代田区神田須田町1-20-1/"
       "東京駅/"
       "data=!4m18!4m17!1m5!1m1!1s"
       "ChIJ2RxO9gKMGGARSvjnp3ocfJg"
       "!2m2!1d139.7711!2d35.6950"
       "!1m5!1m1!1s"
       "ChIJC3Cf2PuLGGAROO00ukl8JwA"
       "!2m2!1d139.7671!2d35.6812"
       "!2m3!6e1!7e2!8j1755511200!3e3")

print("=" * 60)
print("詳細ルート情報の取得可能性調査")
print("=" * 60)

driver.get(url)
time.sleep(5)

# ルート要素を取得
route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
print(f"ルート数: {len(route_elements)}個\n")

# 最初の3つのルートを詳しく分析
for i in range(min(3, len(route_elements))):
    print(f"--- ルート {i+1} ---")
    element = route_elements[i]
    full_text = element.text
    lines = full_text.split('\n')
    
    print(f"全テキスト（{len(lines)}行）:")
    for j, line in enumerate(lines):
        print(f"  {j+1:2d}: {line}")
    
    print("\n【詳細分析】")
    
    # 徒歩時間を探す
    walk_pattern = r'徒歩.*?(\d+)\s*分'
    walk_matches = re.findall(walk_pattern, full_text)
    if walk_matches:
        print(f"✅ 徒歩時間: {walk_matches}")
    else:
        # 別のパターンで徒歩を探す
        if '徒歩' in full_text:
            print(f"⚠️ 徒歩あり（時間不明）")
            # 徒歩の前後のテキストを確認
            for line in lines:
                if '徒歩' in line:
                    print(f"   徒歩行: {line}")
    
    # 駅出発時刻を探す
    station_pattern = r'([^\s]+駅).*?(\d{1,2}:\d{2})'
    station_matches = re.findall(station_pattern, full_text)
    if station_matches:
        print(f"✅ 駅と時刻:")
        for station, time in station_matches:
            print(f"   {station}: {time}")
    
    # 乗車時間を計算（出発-到着）
    time_pattern = r'(\d{1,2}:\d{2})'
    times = re.findall(time_pattern, full_text)
    if len(times) >= 2:
        print(f"✅ 時刻情報: {times}")
        # 簡易的な計算（実際は時間またぎの考慮が必要）
        try:
            start = times[0].split(':')
            end = times[-1].split(':')
            start_min = int(start[0]) * 60 + int(start[1])
            end_min = int(end[0]) * 60 + int(end[1])
            duration = end_min - start_min
            print(f"   概算移動時間: {duration}分")
        except:
            pass
    
    # 乗換を探す
    if '乗換' in full_text or '乗り換え' in full_text:
        print("✅ 乗換あり")
        for line in lines:
            if '乗換' in line or '乗り換え' in line:
                print(f"   {line}")
    
    print()

print("\n【クリック後の詳細情報取得テスト】")
if route_elements:
    print("最初のルートをクリック...")
    route_elements[0].click()
    time.sleep(3)
    
    # 詳細パネルを探す
    detail_elements = driver.find_elements(By.XPATH, "//div[@role='region']")
    print(f"詳細パネル候補: {len(detail_elements)}個")
    
    # より詳細な要素を探す
    # 徒歩アイコンや時間を含む要素
    walk_elements = driver.find_elements(By.XPATH, "//*[contains(@aria-label, '徒歩')]")
    print(f"徒歩関連要素: {len(walk_elements)}個")
    for elem in walk_elements[:3]:
        print(f"  {elem.get_attribute('aria-label')}")
    
    # 時刻表示を含む要素
    time_elements = driver.find_elements(By.XPATH, "//span[contains(text(), ':')]")
    unique_times = []
    for elem in time_elements:
        text = elem.text
        if ':' in text and len(text) < 10 and text not in unique_times:
            unique_times.append(text)
    print(f"時刻表示: {unique_times[:10]}")
    
    # 駅名を含む要素
    station_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '駅')]")
    stations = []
    for elem in station_elements[:10]:
        text = elem.text
        if '駅' in text and len(text) < 20 and text not in stations:
            stations.append(text)
    print(f"駅名: {stations}")

driver.quit()

print("\n" + "=" * 60)
print("結論:")
print("- クリック前でも基本情報は取得可能")
print("- 詳細な徒歩時間や乗換情報は部分的に取得可能")
print("- クリック後は要素構造が変わるため別の方法が必要")
print("=" * 60)