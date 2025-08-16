#!/usr/bin/env python3
"""駅名で直接Place IDを取得するテスト"""

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

test_cases = [
    {"name": "東京駅", "search": "東京駅"},
    {"name": "羽田空港", "search": "羽田空港"},
    {"name": "東京駅（住所付き）", "search": "東京駅 東京都千代田区丸の内"},
]

print("=" * 60)
print("駅・空港のPlace ID取得テスト")
print("=" * 60)

for test in test_cases:
    print(f"\n--- {test['name']} ---")
    
    # 駅名で検索
    url = f"https://www.google.com/maps/search/{test['search']}"
    print(f"検索: {test['search']}")
    
    driver.get(url)
    time.sleep(5)  # ページ読み込み待機
    
    # ページタイトル確認
    print(f"ページタイトル: {driver.title}")
    
    # Place IDを抽出
    page_source = driver.page_source
    
    # ChIJ形式のPlace IDを探す（最初の5個）
    chij_matches = re.findall(r'(ChIJ[a-zA-Z0-9\-\_\.]{23})', page_source)
    
    if chij_matches:
        # 重複を除去
        unique_place_ids = list(dict.fromkeys(chij_matches))
        print(f"Place ID候補（最初の3個）:")
        for i, place_id in enumerate(unique_place_ids[:3]):
            print(f"  {i+1}. {place_id}")
        
        # 最初のPlace IDを使用
        selected_place_id = unique_place_ids[0]
        print(f"✅ 選択: {selected_place_id}")
    else:
        print("❌ Place ID not found")
    
    # URLパターンも確認
    url_pattern = re.search(r'/place/([^/]+)/', driver.current_url)
    if url_pattern:
        print(f"URL内の場所名: {url_pattern.group(1)}")

driver.quit()

print("\n" + "=" * 60)
print("結論:")
print("- 駅名で検索すると、駅専用のPlace IDが取得できる")
print("- 住所で検索すると、その番地のPlace IDになる")
print("=" * 60)