#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最初の物件の3ルートクイックテスト
クリック操作のタイムアウトを短縮
"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pytz
import time
import re
from urllib.parse import quote

def test_quick():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("🚀 クイックテスト: 最初の3ルート")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    origin = '東京都千代田区神田須田町1-20-1'
    
    # 最初の3つの目的地
    destinations = [
        ('Shizenkan', '東京都中央区日本橋2-5-1'),
        ('早稲田大学', '東京都新宿区西早稲田1-6-11'),
        ('羽田空港', '東京都大田区羽田空港2-6-5')
    ]
    
    # WebDriver設定
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0')
    chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)  # 短縮
    
    try:
        for name, dest in destinations:
            print(f"\n[{name}]")
            
            # タイムスタンプ計算
            timestamp = int(arrival_time.timestamp())
            
            # URL構築（タイムスタンプ付き）
            url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(dest)}/"
            url += f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
            
            print(f"  アクセス中...")
            driver.get(url)
            time.sleep(3)  # 短縮
            
            # クリック操作（最小限）
            try:
                # 公共交通機関ボタンを1回だけ試す
                transit_btn = driver.find_element(By.XPATH, "//button[@aria-label='公共交通機関']")
                if transit_btn.is_displayed():
                    transit_btn.click()
                    print(f"  公共交通機関ボタンをクリック")
                    time.sleep(2)
            except:
                print(f"  URLパラメータで設定済み")
            
            # ルート情報取得
            try:
                wait = WebDriverWait(driver, 10)  # 短縮
                route_elements = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
                )
                
                print(f"  {len(route_elements)}個のルート検出")
                
                # 最初のルートのみ取得
                if route_elements:
                    text = route_elements[0].text
                    
                    # 時間抽出
                    time_match = re.search(r'(\d+)\s*分', text)
                    if time_match:
                        travel_time = int(time_match.group(1))
                        
                        # ルートタイプ判定
                        if any(word in text for word in ['線', '駅', 'バス']):
                            route_type = '公共交通機関'
                        elif '徒歩' in text:
                            route_type = '徒歩'
                        else:
                            route_type = '不明'
                        
                        print(f"  ✅ {travel_time}分 ({route_type})")
                        
                        # 路線検出
                        lines = re.findall(r'([^、\s]+線)', text)
                        if lines:
                            print(f"     路線: {', '.join(lines)}")
            except Exception as e:
                print(f"  ❌ エラー: {e}")
            
            # メモリクリーンアップ
            driver.execute_script("window.location.href='about:blank'")
            time.sleep(0.5)
    
    finally:
        driver.quit()
        print("\n✅ 完了")

if __name__ == "__main__":
    test_quick()