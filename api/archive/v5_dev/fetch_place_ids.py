#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
すべての目的地と物件のPlace IDを事前に取得して保存するスクリプト
これにより、メインのルート検索時に各Place ID取得で5秒×(物件数+目的地数)の時間を節約できる
"""

import json
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
import re

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaceIDFetcher:
    """Place ID取得専用クラス"""
    
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Selenium WebDriverのセットアップ"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
        
        self.driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        
    def get_place_info(self, address, name=None):
        """
        住所からPlace IDと座標を取得
        
        Args:
            address: 住所
            name: 施設名（オプション）
        
        Returns:
            dict: place_id, lat, lon
        """
        try:
            # Google Maps URLを構築（単一の場所を検索）
            search_query = f"{name} {address}" if name else address
            url = f"https://www.google.com/maps/search/{quote(search_query)}"
            
            logger.info(f"Place ID取得中: {name or address}")
            self.driver.get(url)
            time.sleep(3)  # ページ読み込み待機
            
            # URLからPlace IDを抽出
            current_url = self.driver.current_url
            place_id_match = re.search(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
            
            if place_id_match:
                place_id = place_id_match.group(1)
            else:
                place_id = None
                logger.warning(f"Place ID取得失敗: {name or address}")
            
            # 座標を抽出
            coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
            if coord_match:
                lat = coord_match.group(1)
                lon = coord_match.group(2)
            else:
                lat, lon = None, None
                logger.warning(f"座標取得失敗: {name or address}")
            
            result = {
                'place_id': place_id,
                'lat': lat,
                'lon': lon
            }
            
            logger.info(f"  Place ID: {place_id}")
            logger.info(f"  座標: ({lat}, {lon})")
            
            return result
            
        except Exception as e:
            logger.error(f"Place ID取得エラー ({name or address}): {e}")
            return {'place_id': None, 'lat': None, 'lon': None}
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("Seleniumセッション終了")

def main():
    """メイン処理"""
    
    print("="*60)
    print("Place ID取得処理開始")
    print("="*60)
    
    # 既存のデータを読み込み
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        dest_data = json.load(f)
        destinations = dest_data['destinations']
    
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties_base.json', 'r', encoding='utf-8') as f:
        prop_data = json.load(f)
        if isinstance(prop_data, dict) and 'properties' in prop_data:
            properties = prop_data['properties']
        else:
            properties = prop_data
    
    fetcher = PlaceIDFetcher()
    
    try:
        fetcher.setup_driver()
        
        # 目的地のPlace ID取得
        print("\n【目的地のPlace ID取得】")
        for dest in destinations:
            if 'place_id' not in dest:
                info = fetcher.get_place_info(dest['address'], dest['name'])
                dest.update(info)
                time.sleep(2)  # レート制限対策
            else:
                logger.info(f"既存Place ID: {dest['name']} - {dest.get('place_id')}")
        
        # 物件のPlace ID取得
        print("\n【物件のPlace ID取得】")
        for prop in properties:
            # dictか文字列かチェック
            if isinstance(prop, dict):
                if 'place_id' not in prop:
                    info = fetcher.get_place_info(prop['address'], prop.get('name'))
                    prop.update(info)
                    time.sleep(2)  # レート制限対策
                else:
                    logger.info(f"既存Place ID: {prop.get('name', 'Unknown')} - {prop.get('place_id')}")
        
        # 更新したデータを保存
        print("\n【データ保存】")
        
        # destinations.jsonを更新
        with open('/app/output/japandatascience.com/timeline-mapping/data/destinations_with_placeids.json', 'w', encoding='utf-8') as f:
            json.dump(dest_data, f, ensure_ascii=False, indent=2)
        print("✅ destinations_with_placeids.json 保存完了")
        
        # properties_base.jsonを更新
        if isinstance(prop_data, dict) and 'properties' in prop_data:
            save_data = prop_data
        else:
            save_data = {"properties": properties}
            
        with open('/app/output/japandatascience.com/timeline-mapping/data/properties_base_with_placeids.json', 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print("✅ properties_base_with_placeids.json 保存完了")
        
    finally:
        fetcher.close()
    
    print("\n" + "="*60)
    print("Place ID取得処理完了！")
    print("="*60)

if __name__ == "__main__":
    main()