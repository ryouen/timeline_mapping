#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID取得のデバッグ
"""
import sys
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import quote

def debug_place_id():
    """Place ID取得の詳細デバッグ"""
    
    # テスト住所
    address = "東京都中央区日本橋2-5-1"
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    try:
        print(f"検索住所: {address}")
        search_url = f"https://www.google.com/maps/search/{quote(address)}"
        print(f"検索URL: {search_url}")
        
        driver.get(search_url)
        time.sleep(3)
        
        current_url = driver.current_url
        print(f"現在のURL: {current_url}")
        
        # パターン1: /place/の後
        match1 = re.search(r'[!/]place/([^/]+)', current_url)
        if match1:
            print(f"  パターン1マッチ: {match1.group(0)}")
            print(f"  group(1): {match1.group(1)}")
        else:
            print("  パターン1: マッチなし")
        
        # パターン2: 0x形式
        match2 = re.search(r'0x[0-9a-f]+:0x[0-9a-f]+', current_url)
        if match2:
            print(f"  パターン2マッチ: {match2.group(0)}")
        else:
            print("  パターン2: マッチなし")
        
        # data-placeid属性
        try:
            element = driver.find_element(By.XPATH, "//*[@data-placeid]")
            placeid = element.get_attribute("data-placeid")
            print(f"  data-placeid: {placeid}")
        except:
            print("  data-placeid: 見つからない")
        
        # URLのパス部分を分析
        from urllib.parse import urlparse
        parsed = urlparse(current_url)
        print(f"  URLパス: {parsed.path}")
        print(f"  URLクエリ: {parsed.query}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_place_id()