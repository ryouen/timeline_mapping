#!/usr/bin/env python3
"""タイムアウト問題の詳細調査"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# URLアクセス（東京駅の新Place ID使用）
url = ("https://www.google.com/maps/dir/"
       "東京都千代田区神田須田町1-20-1/"
       "東京駅/"
       "data=!4m18!4m17!1m5!1m1!1s"
       "ChIJ2RxO9gKMGGARSvjnp3ocfJg"  # ルフォンプログレ
       "!2m2!1d139.7711!2d35.6950"
       "!1m5!1m1!1s"
       "ChIJC3Cf2PuLGGAROO00ukl8JwA"  # 東京駅（駅専用）
       "!2m2!1d139.7671!2d35.6812"
       "!2m3!6e1!7e2!8j1755511200!3e3")

print("=" * 60)
print("タイムアウト問題の詳細調査")
print("=" * 60)

driver.get(url)
time.sleep(5)

print(f"ページタイトル: {driver.title}\n")

# 1. find_elementsで要素を確認（タイムアウトしない）
print("【方法1】find_elements（待機なし）:")
route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
print(f"  要素数: {len(route_elements)}個")

if route_elements:
    # 最初の要素のテキストを確認
    first_text = route_elements[0].text
    if first_text:
        lines = first_text.split('\n')
        print(f"  最初の要素のテキスト（{len(lines)}行）:")
        for line in lines[:5]:
            print(f"    {line}")
        
        # 正規表現パターンのテスト
        print("\n【正規表現テスト】:")
        
        # 所要時間
        minute_match = re.search(r'(\d+)\s*分', first_text)
        if minute_match:
            print(f"  ✅ 所要時間マッチ: {minute_match.group(0)}")
        else:
            print(f"  ❌ 所要時間マッチせず")
        
        # 時刻
        time_pattern = r'(\d{1,2}:\d{2})[^\d]*(?:\([^)]+\)[^\d]*)?\s*-\s*(\d{1,2}:\d{2})'
        time_match = re.search(time_pattern, first_text)
        if time_match:
            print(f"  ✅ 時刻マッチ: {time_match.group(0)}")
        else:
            print(f"  ❌ 時刻マッチせず")
            # 別のパターンを試す
            simple_pattern = r'(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})'
            simple_match = re.search(simple_pattern, first_text)
            if simple_match:
                print(f"  ✅ 簡易パターンでマッチ: {simple_match.group(0)}")
        
        # 運賃
        fare_match = re.search(r'([\d,]+)\s*円', first_text)
        if fare_match:
            print(f"  ✅ 運賃マッチ: {fare_match.group(0)}")
        else:
            print(f"  ❌ 運賃マッチせず")

print("\n【方法2】WebDriverWait（20秒待機）:")
try:
    wait = WebDriverWait(driver, 20)
    wait_elements = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
    )
    print(f"  ✅ WebDriverWait成功: {len(wait_elements)}個の要素")
except Exception as e:
    print(f"  ❌ WebDriverWaitタイムアウト: {e}")

print("\n【クリックテスト】:")
if route_elements:
    print(f"  クリック前: {len(route_elements)}個")
    try:
        route_elements[0].click()
        time.sleep(2)
        after_click = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        print(f"  クリック後: {len(after_click)}個")
        
        # クリック後の要素を再確認
        if after_click:
            for i, elem in enumerate(after_click[:2]):
                text = elem.text
                if text:
                    print(f"\n  ルート{i+1}のテキスト:")
                    lines = text.split('\n')
                    for line in lines[:3]:
                        print(f"    {line}")
    except Exception as e:
        print(f"  クリックエラー: {e}")

driver.quit()