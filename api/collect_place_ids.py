#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID収集専用スクリプト
Google MapsのPlace IDを取得してJSONファイルを更新
"""

import sys
import json
import time
import re
import logging
from datetime import datetime
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaceIdCollector:
    """Place ID収集専用クラス"""
    
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
        logger.info("WebDriver初期化完了")
    
    def normalize_address(self, address):
        """
        住所を正規化（Google Maps検索用）
        例: "東京都千代田区 神田須田町１丁目２０−１" → "東京都千代田区神田須田町1-20-1"
        """
        # 全角スペースを削除
        normalized = address.replace('　', '').replace(' ', '')
        
        # 「丁目」を「-」に変換
        normalized = re.sub(r'(\d+)丁目(\d+)−(\d+)', r'\1-\2-\3', normalized)
        normalized = re.sub(r'(\d+)丁目(\d+)番(\d+)', r'\1-\2-\3', normalized)
        normalized = re.sub(r'(\d+)丁目(\d+)', r'\1-\2', normalized)
        
        # 「番」「号」を削除
        normalized = re.sub(r'(\d+)番(\d+)号', r'\1-\2', normalized)
        normalized = re.sub(r'(\d+)番', r'\1', normalized)
        normalized = re.sub(r'(\d+)号', r'\1', normalized)
        
        # 全角数字を半角に
        normalized = normalized.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        # 全角ハイフンを半角に
        normalized = normalized.replace('−', '-').replace('ー', '-')
        
        return normalized
    
    def extract_place_id(self, address, name=None, category=None):
        """
        住所からPlace IDを取得
        ChIJ形式を優先、次に0x形式
        駅・空港は名前で直接検索
        """
        try:
            # 駅・空港の場合は名前で検索
            if category in ['station', 'airport'] and name:
                search_query = name
                normalized = name  # 駅名をそのまま使用
                logger.info(f"🚉 駅/空港として検索: {name}")
            else:
                # 住所を正規化
                normalized = self.normalize_address(address)
                search_query = normalized
            
            # Google Mapsで検索
            url = f"https://www.google.com/maps/search/{quote(search_query)}"
            logger.info(f"🔍 Place ID取得中: {name or address[:30]}...")
            logger.debug(f"  URL: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # ページ読み込み待機
            
            # ChIJ形式のPlace IDを検索（ページソースから）
            place_id = None
            place_id_format = None
            
            page_source = self.driver.page_source
            
            # ChIJ形式を優先的に検索
            chij_match = re.search(r'(ChIJ[a-zA-Z0-9\-\_\.]{23})', page_source)
            if chij_match:
                place_id = chij_match.group(1)
                place_id_format = 'ChIJ'
                logger.info(f"  ✅ Place ID取得（ChIJ形式）: {place_id}")
            else:
                # 0x形式を検索（URLから）
                current_url = self.driver.current_url
                patterns = [
                    r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)',
                    r'/place/[^/]+/@[^/]+/data=.*!1s(0x[0-9a-f]+:0x[0-9a-f]+)',
                    r'ftid=(0x[0-9a-f]+:0x[0-9a-f]+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, current_url)
                    if match:
                        place_id = match.group(1)
                        place_id_format = '0x'
                        logger.info(f"  ✅ Place ID取得（0x形式）: {place_id}")
                        break
            
            # 座標を抽出
            lat, lon = None, None
            coord_match = re.search(r'@([\d.]+),([\d.]+)', self.driver.current_url)
            if coord_match:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                logger.debug(f"  座標: {lat}, {lon}")
            
            if not place_id:
                logger.warning(f"  ⚠️ Place ID取得失敗: {name or address}")
            
            return {
                'place_id': place_id,
                'place_id_format': place_id_format,
                'lat': lat,
                'lon': lon,
                'normalized_address': normalized
            }
            
        except Exception as e:
            logger.error(f"Place ID取得エラー: {e}")
            return {
                'place_id': None,
                'place_id_format': None,
                'lat': None,
                'lon': None,
                'normalized_address': normalized
            }
    
    def update_json_files(self):
        """JSONファイルを更新"""
        
        # バックアップ作成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # properties_base.json読み込み
        with open('/app/output/japandatascience.com/timeline-mapping/data/properties_base.json', 'r', encoding='utf-8') as f:
            properties_data = json.load(f)
        
        # バックアップ保存
        with open(f'/app/output/japandatascience.com/timeline-mapping/data/properties_base_backup_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, ensure_ascii=False, indent=2)
        
        # destinations.json読み込み
        with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
            destinations_data = json.load(f)
        
        # バックアップ保存
        with open(f'/app/output/japandatascience.com/timeline-mapping/data/destinations_backup_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(destinations_data, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*60)
        print("Place ID収集開始")
        print("="*60)
        
        # 物件のPlace ID取得
        print(f"\n物件: {len(properties_data['properties'])}件")
        for i, prop in enumerate(properties_data['properties'], 1):
            result = self.extract_place_id(prop['address'], prop['name'])
            
            # JSONに追加
            prop['place_id'] = result['place_id']
            prop['place_id_format'] = result['place_id_format']
            prop['lat'] = result['lat']
            prop['lon'] = result['lon']
            
            status = "✓" if result['place_id'] else "✗"
            print(f"  [{i:2d}/{len(properties_data['properties'])}] {status} {prop['name']}")
            
            # レート制限対策
            time.sleep(1)
        
        # 目的地のPlace ID取得
        print(f"\n目的地: {len(destinations_data['destinations'])}件")
        for i, dest in enumerate(destinations_data['destinations'], 1):
            # カテゴリも渡す
            result = self.extract_place_id(dest['address'], dest['name'], dest.get('category'))
            
            # JSONに追加
            dest['place_id'] = result['place_id']
            dest['place_id_format'] = result['place_id_format']
            dest['lat'] = result['lat']
            dest['lon'] = result['lon']
            
            status = "✓" if result['place_id'] else "✗"
            print(f"  [{i:2d}/{len(destinations_data['destinations'])}] {status} {dest['name']}")
            
            # レート制限対策
            time.sleep(1)
        
        # ファイル保存
        with open('/app/output/japandatascience.com/timeline-mapping/data/properties_base.json', 'w', encoding='utf-8') as f:
            json.dump(properties_data, f, ensure_ascii=False, indent=2)
        
        with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'w', encoding='utf-8') as f:
            json.dump(destinations_data, f, ensure_ascii=False, indent=2)
        
        # 統計
        props_with_id = sum(1 for p in properties_data['properties'] if p.get('place_id'))
        dests_with_id = sum(1 for d in destinations_data['destinations'] if d.get('place_id'))
        
        print("\n" + "="*60)
        print("Place ID収集完了")
        print(f"物件: {props_with_id}/{len(properties_data['properties'])}件成功")
        print(f"目的地: {dests_with_id}/{len(destinations_data['destinations'])}件成功")
        print("="*60)
        
        return properties_data, destinations_data
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Seleniumセッション終了")
            except:
                pass

def main():
    """メイン処理"""
    collector = PlaceIdCollector()
    
    try:
        collector.setup_driver()
        collector.update_json_files()
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()

if __name__ == "__main__":
    main()