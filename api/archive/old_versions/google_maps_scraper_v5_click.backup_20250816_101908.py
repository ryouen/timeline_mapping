#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps スクレイピングツール v5
Seleniumクリック操作による時刻指定版

主な改善点：
1. 時刻指定をSeleniumのクリック操作で実現
2. 公共交通機関ボタンを確実にクリック
3. 詳細情報の取得改善
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_driver():
    """Selenium WebDriverのセットアップ"""
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
    driver.implicitly_wait(10)
    return driver

def click_transit_and_set_time(driver, arrival_time):
    """
    公共交通機関ボタンをクリックし、時刻を設定
    
    Args:
        driver: Seleniumドライバー
        arrival_time: 到着時刻（datetime）
    """
    logger.info("公共交通機関モードと時刻設定を開始")
    
    # 1. 公共交通機関ボタンをクリック
    transit_clicked = False
    transit_selectors = [
        "//button[@aria-label='公共交通機関']",
        "//button[@aria-label='Transit']",
        "//button[@data-travel-mode='3']",
        "//div[@data-value='3']//button",
        "//img[@aria-label='公共交通機関']/..",
        "//span[contains(text(), '電車')]/..",
        "//button[contains(@class, 'transit')]"
    ]
    
    for selector in transit_selectors:
        try:
            transit_btn = driver.find_element(By.XPATH, selector)
            if transit_btn.is_displayed():
                transit_btn.click()
                logger.info(f"公共交通機関ボタンをクリック: {selector}")
                transit_clicked = True
                time.sleep(2)
                break
        except:
            continue
    
    if not transit_clicked:
        logger.warning("公共交通機関ボタンが見つからない")
    
    # 2. 時刻オプションボタンを探してクリック
    time_option_clicked = False
    time_selectors = [
        "//button[contains(@aria-label, '出発時刻')]",
        "//button[contains(@aria-label, 'Depart at')]",
        "//button[contains(text(), '出発')]",
        "//button[contains(text(), 'すぐに出発')]",
        "//span[contains(text(), 'すぐに出発')]/..",
        "//div[contains(@class, 'time-selection')]//button",
        "//button[@data-value='0']"  # 時刻選択ボタン
    ]
    
    for selector in time_selectors:
        try:
            time_btn = driver.find_element(By.XPATH, selector)
            if time_btn.is_displayed():
                time_btn.click()
                logger.info(f"時刻オプションボタンをクリック: {selector}")
                time_option_clicked = True
                time.sleep(1)
                break
        except:
            continue
    
    if not time_option_clicked:
        logger.warning("時刻オプションボタンが見つからない")
        return False
    
    # 3. 「到着時刻」を選択
    try:
        # ドロップダウンから「到着時刻」を選択
        arrival_option_selectors = [
            "//div[contains(text(), '到着時刻')]",
            "//div[contains(text(), '到着')]",
            "//span[contains(text(), '到着')]",
            "//div[@role='option'][contains(text(), '到着')]",
            "//div[contains(text(), 'Arrive by')]"
        ]
        
        for selector in arrival_option_selectors:
            try:
                arrival_option = driver.find_element(By.XPATH, selector)
                if arrival_option.is_displayed():
                    arrival_option.click()
                    logger.info("「到着時刻」を選択")
                    time.sleep(1)
                    break
            except:
                continue
                
    except Exception as e:
        logger.warning(f"到着時刻オプションの選択に失敗: {e}")
    
    # 4. 日付・時刻を入力
    try:
        # 日付入力フィールドを探す
        date_selectors = [
            "//input[@aria-label='日付を選択']",
            "//input[@type='date']",
            "//input[contains(@aria-label, '日付')]",
            "//input[contains(@placeholder, '日付')]"
        ]
        
        # 明日の日付を設定
        tomorrow_jst = arrival_time + timedelta(hours=9)  # JSTに変換
        date_str = tomorrow_jst.strftime('%Y/%m/%d')
        
        for selector in date_selectors:
            try:
                date_input = driver.find_element(By.XPATH, selector)
                if date_input.is_displayed():
                    date_input.clear()
                    date_input.send_keys(date_str)
                    logger.info(f"日付を入力: {date_str}")
                    break
            except:
                continue
        
        # 時刻入力フィールドを探す
        time_selectors = [
            "//input[@aria-label='時刻を選択']",
            "//input[@type='time']",
            "//input[contains(@aria-label, '時刻')]",
            "//input[contains(@placeholder, '時刻')]"
        ]
        
        time_str = tomorrow_jst.strftime('%H:%M')
        
        for selector in time_selectors:
            try:
                time_input = driver.find_element(By.XPATH, selector)
                if time_input.is_displayed():
                    time_input.clear()
                    time_input.send_keys(time_str)
                    logger.info(f"時刻を入力: {time_str}")
                    # Enterキーで確定
                    time_input.send_keys(Keys.RETURN)
                    break
            except:
                continue
                
    except Exception as e:
        logger.error(f"日付・時刻の入力に失敗: {e}")
        return False
    
    # 5. 設定完了を待つ
    time.sleep(3)
    logger.info("時刻設定完了")
    return True

def scrape_route_v5(origin, destination, arrival_time=None):
    """
    v5: クリック操作による時刻指定版スクレイピング
    """
    driver = None
    try:
        driver = setup_driver()
        
        # 基本的なルート検索URL（時刻指定なし）
        base_url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}"
        logger.info(f"アクセスURL: {base_url}")
        
        driver.get(base_url)
        time.sleep(3)
        
        # 時刻指定が必要な場合
        if arrival_time:
            success = click_transit_and_set_time(driver, arrival_time)
            if not success:
                logger.warning("時刻設定が完全ではない可能性があります")
        
        # ルート情報の読み込みを待つ
        wait = WebDriverWait(driver, 20)
        try:
            route_elements = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@data-trip-index]"))
            )
            logger.info(f"{len(route_elements)}個のルートを検出")
        except TimeoutException:
            logger.error("ルート情報の読み込みタイムアウト")
            return None
        
        # ルート情報を抽出
        routes = []
        for i, element in enumerate(route_elements):
            try:
                text = element.text
                
                # 所要時間を抽出
                time_match = re.search(r'(\d+)\s*分', text)
                if time_match:
                    travel_time = int(time_match.group(1))
                    
                    # 出発・到着時刻を抽出
                    departure_match = re.search(r'(\d{1,2}:\d{2})\s*発', text)
                    arrival_match = re.search(r'(\d{1,2}:\d{2})\s*着', text)
                    
                    route_info = {
                        'travel_time': travel_time,
                        'departure_time': departure_match.group(1) if departure_match else None,
                        'arrival_time': arrival_match.group(1) if arrival_match else None,
                        'raw_text': text[:200]  # 最初の200文字
                    }
                    
                    # 徒歩のみチェック
                    if '徒歩' in text and '駅' not in text:
                        route_info['route_type'] = '徒歩のみ'
                    elif any(word in text for word in ['線', '駅', '電車', 'バス']):
                        route_info['route_type'] = '公共交通機関'
                    else:
                        route_info['route_type'] = '不明'
                    
                    routes.append(route_info)
                    logger.info(f"ルート{i+1}: {travel_time}分 ({route_info['route_type']})")
                    
            except Exception as e:
                logger.error(f"ルート{i+1}の抽出エラー: {e}")
        
        if routes:
            shortest = min(routes, key=lambda r: r['travel_time'])
            return {
                'origin': origin,
                'destination': destination,
                'travel_time': shortest['travel_time'],
                'departure_time': shortest.get('departure_time'),
                'arrival_time': shortest.get('arrival_time'),
                'route_type': shortest.get('route_type'),
                'all_routes': routes,
                'url': base_url
            }
        
        return None
        
    except Exception as e:
        logger.error(f"スクレイピングエラー: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()
            logger.info("Seleniumセッション終了")

def test_v5_click_method():
    """v5クリック方式のテスト"""
    
    # 明日の10時到着
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00
    
    print("=" * 60)
    print("v5スクレイパーテスト - クリック操作による時刻指定")
    print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
    print("=" * 60)
    
    # テストケース
    test_cases = [
        {
            "name": "Shizenkan（短距離）",
            "origin": "東京都千代田区神田須田町1-20-1",
            "destination": "東京都中央区日本橋２丁目５−１"
        },
        {
            "name": "府中（長距離）",
            "origin": "東京都千代田区神田須田町1-20-1", 
            "destination": "東京都府中市住吉町5-22-5"
        }
    ]
    
    for test in test_cases:
        print(f"\n[{test['name']}]")
        result = scrape_route_v5(
            test['origin'],
            test['destination'],
            arrival_time=arrival_10am
        )
        
        if result:
            print(f"✅ 成功")
            print(f"  所要時間: {result['travel_time']}分")
            print(f"  ルートタイプ: {result['route_type']}")
            if result['departure_time']:
                print(f"  出発時刻: {result['departure_time']}")
            if result['arrival_time']:
                print(f"  到着時刻: {result['arrival_time']}")
        else:
            print(f"❌ 失敗")

if __name__ == "__main__":
    test_v5_click_method()