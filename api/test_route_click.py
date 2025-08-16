#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ルートクリックのテスト
最初のルート要素（data-trip-index="0"）をクリックして詳細が展開されるかテスト
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json
from datetime import datetime, timedelta
import pytz

def test_route_click():
    """ルートクリックで詳細が展開されるかテスト"""
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    try:
        # テストルート：ルフォンプログレ神田 → 東京駅
        origin = "東京都千代田区神田須田町1-20-1"
        destination = "東京都千代田区丸の内1-9-1"
        
        # 明日の10時到着
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.now(jst) + timedelta(days=1)
        arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        timestamp = int(arrival_time.timestamp())
        
        # URL構築
        url = f"https://www.google.com/maps/dir/{origin}/{destination}/@35.6880527,139.7674084,16z/data=!3m1!4b1!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0x987c1c7aa7e7f84a!2m2!1d139.7711379!2d35.6949994!1m5!1m1!1s0x601889d738b39701:0x996fd0bd4cfffd56!2m2!1d139.773935!2d35.6814238!2m3!6e1!7e2!8j{timestamp}!3e3"
        
        print(f"🔍 URL: {url[:100]}...")
        driver.get(url)
        time.sleep(5)
        
        # ルート要素を探す
        route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        print(f"\n✅ {len(route_elements)}個のルート要素を検出")
        
        if route_elements:
            # クリック前のテキストを取得
            before_text = route_elements[0].text
            print(f"\n【クリック前】")
            print(f"テキストの長さ: {len(before_text)}文字")
            print(f"最初の200文字: {before_text[:200]}...")
            
            # 最初のルートをクリック
            print(f"\n🖱️ 最初のルート要素をクリック...")
            route_elements[0].click()
            time.sleep(3)
            
            # クリック後のテキストを取得（要素が変わる可能性があるので再検索）
            time.sleep(1)
            try:
                # まず同じセレクタで探す
                after_element = driver.find_element(By.XPATH, "//div[@data-trip-index='0']")
                after_text = after_element.text
            except:
                # 要素が変わった場合は、展開されたコンテナを探す
                try:
                    after_element = driver.find_element(By.XPATH, "//div[contains(@class, 'section-directions-trip-0')]")
                    after_text = after_element.text
                except:
                    # それでも見つからない場合は、ページ全体から関連要素を探す
                    after_element = driver.find_element(By.XPATH, "//div[contains(@class, 'm6QErb')]")
                    after_text = after_element.text
            print(f"\n【クリック後】")
            print(f"テキストの長さ: {len(after_text)}文字")
            
            # 詳細情報が増えたか確認
            if len(after_text) > len(before_text):
                print(f"✅ 詳細が展開されました！ (+{len(after_text) - len(before_text)}文字)")
                
                # 詳細情報を抽出してみる
                print("\n【抽出された詳細情報】")
                
                # 徒歩時間を探す
                walk_matches = re.findall(r'徒歩.*?(\d+)\s*分', after_text)
                if walk_matches:
                    print(f"徒歩時間: {walk_matches}")
                
                # 駅名を探す
                station_matches = re.findall(r'([^\s]+駅)', after_text)
                if station_matches:
                    print(f"駅: {list(set(station_matches))}")
                
                # 路線名を探す
                line_matches = re.findall(r'([^\s]+線)', after_text)
                if line_matches:
                    print(f"路線: {list(set(line_matches))}")
                
                # 時刻を探す
                time_matches = re.findall(r'(\d+:\d+)', after_text)
                if time_matches:
                    print(f"時刻: {time_matches[:10]}")  # 最初の10個
                
                # 料金を探す
                fare_matches = re.findall(r'([\d,]+)\s*円', after_text)
                if fare_matches:
                    print(f"料金: {fare_matches[0]}円")
                
            else:
                print(f"⚠️ 詳細が展開されていない可能性があります")
                
                # 詳細ボタンを探す
                detail_selectors = [
                    "//span[text()='詳細']",
                    "//button[contains(text(), '詳細')]",
                    "//div[contains(@id, 'section-directions-trip-details')]//span"
                ]
                
                for selector in detail_selectors:
                    try:
                        detail_btn = driver.find_element(By.XPATH, selector)
                        if detail_btn.is_displayed():
                            print(f"📍 詳細ボタンを発見: {selector}")
                            detail_btn.click()
                            time.sleep(2)
                            
                            # 再度テキストを取得
                            try:
                                final_text = driver.find_element(By.XPATH, "//div[@data-trip-index='0']").text
                            except:
                                final_text = driver.find_element(By.XPATH, "//div[contains(@class, 'm6QErb')]").text
                            if len(final_text) > len(after_text):
                                print(f"✅ 詳細ボタンクリック後、詳細が展開されました！")
                            break
                    except:
                        continue
            
            # HTMLを保存
            with open('/app/output/japandatascience.com/timeline-mapping/api/test_route_click.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("\n💾 HTMLを保存しました: test_route_click.html")
            
        else:
            print("❌ ルート要素が見つかりません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("=" * 60)
    print("ルートクリックテスト")
    print("=" * 60)
    test_route_click()