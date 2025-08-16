#!/usr/bin/env python3
"""東京駅のPlace ID取得テスト"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

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

# 東京駅を検索
address = "東京都千代田区丸の内１丁目９番１号"
name = "東京駅"

url = f"https://www.google.com/maps/search/{address} {name}"
driver.get(url)
time.sleep(5)

# Place IDを抽出
page_source = driver.page_source

# ChIJ形式のPlace IDを探す
chij_match = re.search(r'(ChIJ[a-zA-Z0-9\-\_\.]{23})', page_source)
if chij_match:
    place_id = chij_match.group(1)
    print(f"✅ 東京駅のPlace ID: {place_id}")
else:
    print("❌ Place ID not found")

# ページタイトル確認
print(f"ページタイトル: {driver.title}")

driver.quit()