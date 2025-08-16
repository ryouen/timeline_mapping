#!/usr/bin/env python3
"""詳細なデバッグ情報取得"""

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

# URLアクセス（新しい東京駅Place ID使用）
url = ("https://www.google.com/maps/dir/"
       "東京都千代田区神田須田町1-20-1/"
       "東京都千代田区丸の内１丁目９番１号/"
       "data=!4m18!4m17!1m5!1m1!1s"
       "ChIJ2RxO9gKMGGARSvjnp3ocfJg"  # ルフォンプログレ
       "!2m2!1d139.7711!2d35.6950"
       "!1m5!1m1!1s"
       "ChIJGWlcqP6LGGARddFD1M78MhU"  # 東京駅（新）
       "!2m2!1d139.7676!2d35.6812"
       "!2m3!6e1!7e2!8j1755511200!3e3")

print("=" * 60)
print("詳細デバッグ情報")
print("=" * 60)

driver.get(url)
time.sleep(5)

print(f"ページタイトル: {driver.title}\n")

# ルート要素を取得
route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
print(f"ルート要素数: {len(route_elements)}個\n")

if route_elements:
    # 最初の3つのルートの詳細を確認
    for i in range(min(3, len(route_elements))):
        print(f"--- ルート {i+1} ---")
        elem = route_elements[i]
        
        # 属性を確認
        trip_index = elem.get_attribute('data-trip-index')
        print(f"data-trip-index: {trip_index}")
        
        # テキスト内容
        text = elem.text
        print(f"テキスト長: {len(text)}文字")
        
        if text:
            lines = text.split('\n')
            print(f"行数: {len(lines)}")
            print("内容（最初の10行）:")
            for j, line in enumerate(lines[:10]):
                print(f"  {j+1}: {line}")
        else:
            print("⚠️ テキストが空です")
            
            # 子要素を確認
            child_divs = elem.find_elements(By.XPATH, ".//div")
            print(f"子div要素数: {len(child_divs)}")
            
            spans = elem.find_elements(By.XPATH, ".//span")
            print(f"子span要素数: {len(spans)}")
            if spans:
                print("spanのテキスト（最初の5個）:")
                for span in spans[:5]:
                    if span.text:
                        print(f"  - {span.text}")
        
        print()

# 時間・運賃要素を別の方法で探す
print("--- 別のセレクタで要素を探索 ---")

# aria-labelを使った検索
elements_with_aria = driver.find_elements(By.XPATH, "//*[@aria-label]")
time_related = []
fare_related = []

for elem in elements_with_aria:
    label = elem.get_attribute('aria-label')
    if '分' in label or '時間' in label or '時' in label:
        time_related.append(label)
    if '円' in label or '料金' in label:
        fare_related.append(label)

print(f"時間関連のaria-label: {len(time_related)}個")
for label in time_related[:5]:
    print(f"  - {label}")

print(f"\n運賃関連のaria-label: {len(fare_related)}個")
for label in fare_related[:5]:
    print(f"  - {label}")

driver.quit()