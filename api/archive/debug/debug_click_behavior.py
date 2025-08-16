#!/usr/bin/env python3
"""クリック前後のURL変化を調査"""

import time
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

# 初期URL
initial_url = ("https://www.google.com/maps/dir/"
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
print("クリック前後のURL変化調査")
print("=" * 60)

driver.get(initial_url)
time.sleep(5)

print("【クリック前】")
print(f"URL: {driver.current_url[:150]}...")
print(f"ページタイトル: {driver.title}")

# ルート要素を確認
route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
print(f"ルート要素数: {len(route_elements)}個")

if route_elements:
    # 最初の要素の内容
    first_text = route_elements[0].text
    lines = first_text.split('\n')
    print("最初のルート内容:")
    for line in lines[:5]:
        print(f"  {line}")

    # クリック実行
    print("\n>>> ルート要素をクリック...")
    route_elements[0].click()
    time.sleep(3)
    
    print("\n【クリック後】")
    print(f"URL: {driver.current_url[:150]}...")
    print(f"ページタイトル: {driver.title}")
    
    # クリック後の要素を確認
    after_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
    print(f"ルート要素数: {len(after_elements)}個")
    
    # URL変化の確認
    if initial_url != driver.current_url:
        print("\n⚠️ URLが変化しました！")
        print("変化した部分を確認中...")
    else:
        print("\n✅ URLは変化していません")
    
    # ページ内の他の要素を確認
    print("\n【その他の要素確認】")
    
    # 詳細パネルを探す
    detail_panels = driver.find_elements(By.XPATH, "//div[@role='main']//div[@jsaction]")
    print(f"詳細パネル候補: {len(detail_panels)}個")
    
    # 時刻表示を探す
    time_elements = driver.find_elements(By.XPATH, "//*[contains(text(), ':')]")
    time_texts = [elem.text for elem in time_elements if ':' in elem.text and len(elem.text) < 20]
    print(f"時刻表示: {time_texts[:5]}")
    
    # 料金表示を探す
    fare_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '円')]")
    fare_texts = [elem.text for elem in fare_elements if '円' in elem.text and len(elem.text) < 20]
    print(f"料金表示: {fare_texts[:3]}")

driver.quit()

print("\n" + "=" * 60)
print("HTMLに出力するURL:")
print("=" * 60)
print(f"クリック前URL:\n{initial_url}")
print(f"\nクリック後URL:\n（上記の【クリック後】セクション参照）")