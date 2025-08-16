#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID事前取得スクリプト v2
9目的地 + 25物件の全Place IDを取得し、検証する

目的:
1. 全32箇所のPlace IDを取得
2. Place IDの正確性を検証
3. ルート検索の準備
"""

import json
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from urllib.parse import quote

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaceIdFetcher:
    def __init__(self):
        self.driver = None
        self.place_ids = {}
        
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
    
    def get_place_id(self, name, address):
        """指定された場所のPlace IDを取得"""
        try:
            # Google MapsでPlace IDを検索
            search_query = f"{name} {address}" if name else address
            url = f"https://www.google.com/maps/search/{quote(search_query)}"
            
            logger.info(f"🔍 Place ID取得中: {name or address}")
            self.driver.get(url)
            time.sleep(5)
            
            # URLからPlace IDを抽出
            current_url = self.driver.current_url
            
            # Place IDパターンを検索
            place_id_match = re.search(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
            
            if place_id_match:
                place_id = place_id_match.group(1)
                logger.info(f"✅ Place ID取得成功: {place_id}")
            else:
                # データIDパターンも試す
                data_match = re.search(r'/data=.*!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
                if data_match:
                    place_id = data_match.group(1)
                    logger.info(f"✅ Place ID取得成功 (data): {place_id}")
                else:
                    place_id = None
                    logger.warning(f"⚠️ Place ID取得失敗: {name or address}")
            
            # 座標も取得
            coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
            if coord_match:
                lat = coord_match.group(1)
                lon = coord_match.group(2)
            else:
                lat, lon = None, None
            
            return {
                'place_id': place_id,
                'lat': lat,
                'lon': lon,
                'url': current_url
            }
            
        except Exception as e:
            logger.error(f"❌ エラー ({name or address}): {e}")
            return {'place_id': None, 'lat': None, 'lon': None, 'url': None}
    
    def verify_place_id(self, name, address, place_id):
        """Place IDが正しいか検証"""
        try:
            if not place_id:
                return False
                
            # Place IDを使って直接アクセス
            url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            self.driver.get(url)
            time.sleep(3)
            
            # ページ内容を確認（簡易的な検証）
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            
            # 名前または住所の一部が含まれているか確認
            name_parts = name.lower().split() if name else []
            address_parts = address.lower().split() if address else []
            
            found = False
            for part in name_parts + address_parts:
                if len(part) > 2 and part in page_text:
                    found = True
                    break
            
            if found:
                logger.info(f"✅ Place ID検証成功: {name}")
                return True
            else:
                logger.warning(f"⚠️ Place ID検証失敗: {name}")
                return False
                
        except Exception as e:
            logger.error(f"検証エラー: {e}")
            return False
    
    def process_all_locations(self):
        """全ての目的地と物件のPlace IDを取得"""
        
        # destinations.jsonを読み込み
        with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
            destinations_data = json.load(f)
        
        # properties.jsonを読み込み
        with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as f:
            properties_data = json.load(f)
        
        results = {
            'destinations': {},
            'properties': {},
            'timestamp': datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("🎯 目的地のPlace ID取得")
        print("="*60)
        
        # 目的地のPlace IDを取得
        for dest in destinations_data['destinations']:
            name = dest['name']
            address = dest['address']
            
            info = self.get_place_id(name, address)
            results['destinations'][name] = {
                'address': address,
                'place_id': info['place_id'],
                'lat': info['lat'],
                'lon': info['lon'],
                'verified': False
            }
            
            # 検証
            if info['place_id']:
                verified = self.verify_place_id(name, address, info['place_id'])
                results['destinations'][name]['verified'] = verified
            
            time.sleep(2)  # レート制限対策
        
        print("\n" + "="*60)
        print("🏢 物件のPlace ID取得")
        print("="*60)
        
        # 物件のPlace IDを取得（重複する住所はスキップ）
        processed_addresses = set()
        
        for prop in properties_data['properties']:
            address = prop['address']
            
            if address in processed_addresses:
                logger.info(f"⏭️ スキップ（既処理）: {prop['name']}")
                continue
            
            processed_addresses.add(address)
            
            info = self.get_place_id(None, address)
            results['properties'][address] = {
                'place_id': info['place_id'],
                'lat': info['lat'],
                'lon': info['lon'],
                'verified': False
            }
            
            # 検証
            if info['place_id']:
                verified = self.verify_place_id(None, address, info['place_id'])
                results['properties'][address]['verified'] = verified
            
            time.sleep(2)  # レート制限対策
        
        return results
    
    def save_results(self, results):
        """結果を保存"""
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/place_ids_v2.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 結果を保存: {output_file}")
        
        # サマリー表示
        print("\n" + "="*60)
        print("📊 Place ID取得結果サマリー")
        print("="*60)
        
        dest_total = len(results['destinations'])
        dest_success = sum(1 for d in results['destinations'].values() if d['place_id'])
        dest_verified = sum(1 for d in results['destinations'].values() if d['verified'])
        
        prop_total = len(results['properties'])
        prop_success = sum(1 for p in results['properties'].values() if p['place_id'])
        prop_verified = sum(1 for p in results['properties'].values() if p['verified'])
        
        print(f"\n目的地:")
        print(f"  総数: {dest_total}")
        print(f"  Place ID取得: {dest_success}/{dest_total} ({dest_success*100//dest_total}%)")
        print(f"  検証済み: {dest_verified}/{dest_success}")
        
        print(f"\n物件:")
        print(f"  総数: {prop_total}")
        print(f"  Place ID取得: {prop_success}/{prop_total} ({prop_success*100//prop_total}%)")
        print(f"  検証済み: {prop_verified}/{prop_success}")
        
        # 失敗したものをリスト
        if dest_success < dest_total:
            print("\n⚠️ Place ID取得失敗（目的地）:")
            for name, info in results['destinations'].items():
                if not info['place_id']:
                    print(f"  - {name}")
        
        if prop_success < prop_total:
            print("\n⚠️ Place ID取得失敗（物件）:")
            for address, info in results['properties'].items():
                if not info['place_id']:
                    print(f"  - {address}")
        
        return results
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("Seleniumセッション終了")

def main():
    """メイン処理"""
    fetcher = PlaceIdFetcher()
    
    try:
        print("🚀 Place ID事前取得スクリプト v2 開始")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        fetcher.setup_driver()
        results = fetcher.process_all_locations()
        fetcher.save_results(results)
        
        print("\n✅ 完了!")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fetcher.close()

if __name__ == "__main__":
    main()