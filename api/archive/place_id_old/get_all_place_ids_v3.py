#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID事前取得スクリプト v3
住所を正しい形式で検索し、Place IDを取得

重要な変更点:
- 住所形式を正規化 (1丁目20-1 → 1-20-1)
- 物件名を使わず、住所のみで検索
- 目的地も住所のみで検索（名前は補助情報）
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
    
    def normalize_address(self, address):
        """住所を正規化（Google Maps検索用）"""
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
    
    def get_place_id_by_address(self, address, name=None):
        """住所でPlace IDを取得"""
        try:
            # 住所を正規化
            normalized_address = self.normalize_address(address)
            
            # Google Mapsで住所を検索
            url = f"https://www.google.com/maps/search/{quote(normalized_address)}"
            
            logger.info(f"🔍 Place ID取得中: {normalized_address}")
            if name:
                logger.info(f"   (施設名: {name})")
            
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
                    logger.warning(f"⚠️ Place ID取得失敗: {normalized_address}")
            
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
                'normalized_address': normalized_address,
                'original_address': address,
                'url': current_url
            }
            
        except Exception as e:
            logger.error(f"❌ エラー ({address}): {e}")
            return {
                'place_id': None,
                'lat': None,
                'lon': None,
                'normalized_address': self.normalize_address(address),
                'original_address': address,
                'url': None
            }
    
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
            'unique_addresses': {},  # 重複しない住所のPlace ID
            'timestamp': datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("🎯 目的地のPlace ID取得（住所ベース）")
        print("="*60)
        
        # 目的地のPlace IDを取得（住所のみで検索）
        for dest in destinations_data['destinations']:
            name = dest['name']
            address = dest['address']
            
            info = self.get_place_id_by_address(address, name)
            results['destinations'][name] = info
            
            # unique_addressesにも保存
            if info['normalized_address'] not in results['unique_addresses']:
                results['unique_addresses'][info['normalized_address']] = {
                    'place_id': info['place_id'],
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'original_address': info['original_address']
                }
            
            time.sleep(2)  # レート制限対策
        
        print("\n" + "="*60)
        print("🏢 物件のPlace ID取得（住所ベース）")
        print("="*60)
        
        # 物件のPlace IDを取得（重複する住所はスキップ）
        processed_addresses = set()
        
        for prop in properties_data['properties']:
            address = prop['address']
            name = prop['name']
            
            # 正規化した住所で重複チェック
            normalized = self.normalize_address(address)
            
            if normalized in processed_addresses:
                logger.info(f"⏭️ スキップ（既処理）: {name} ({normalized})")
                continue
            
            processed_addresses.add(normalized)
            
            info = self.get_place_id_by_address(address, name)
            results['properties'][name] = info
            
            # unique_addressesにも保存
            if info['normalized_address'] not in results['unique_addresses']:
                results['unique_addresses'][info['normalized_address']] = {
                    'place_id': info['place_id'],
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'original_address': info['original_address']
                }
            
            time.sleep(2)  # レート制限対策
        
        return results
    
    def save_results(self, results):
        """結果を保存"""
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/place_ids_v3.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 結果を保存: {output_file}")
        
        # サマリー表示
        print("\n" + "="*60)
        print("📊 Place ID取得結果サマリー")
        print("="*60)
        
        dest_total = len(results['destinations'])
        dest_success = sum(1 for d in results['destinations'].values() if d['place_id'])
        
        prop_total = len(results['properties'])
        prop_success = sum(1 for p in results['properties'].values() if p['place_id'])
        
        unique_total = len(results['unique_addresses'])
        unique_success = sum(1 for u in results['unique_addresses'].values() if u['place_id'])
        
        print(f"\n目的地:")
        print(f"  総数: {dest_total}")
        print(f"  Place ID取得: {dest_success}/{dest_total} ({dest_success*100//dest_total if dest_total else 0}%)")
        
        print(f"\n物件:")
        print(f"  総数: {prop_total}")
        print(f"  Place ID取得: {prop_success}/{prop_total} ({prop_success*100//prop_total if prop_total else 0}%)")
        
        print(f"\n一意な住所:")
        print(f"  総数: {unique_total}")
        print(f"  Place ID取得: {unique_success}/{unique_total} ({unique_success*100//unique_total if unique_total else 0}%)")
        
        # 失敗したものをリスト
        failed_destinations = [name for name, info in results['destinations'].items() if not info['place_id']]
        if failed_destinations:
            print("\n⚠️ Place ID取得失敗（目的地）:")
            for name in failed_destinations:
                info = results['destinations'][name]
                print(f"  - {name}")
                print(f"    元住所: {info['original_address']}")
                print(f"    正規化: {info['normalized_address']}")
        
        failed_properties = [name for name, info in results['properties'].items() if not info['place_id']]
        if failed_properties:
            print("\n⚠️ Place ID取得失敗（物件）:")
            for name in failed_properties:
                info = results['properties'][name]
                print(f"  - {name}")
                print(f"    元住所: {info['original_address']}")
                print(f"    正規化: {info['normalized_address']}")
        
        # 正規化の例を表示
        print("\n📝 住所正規化の例:")
        examples = list(results['destinations'].values())[:3] + list(results['properties'].values())[:2]
        for info in examples:
            if info['original_address'] != info['normalized_address']:
                print(f"  {info['original_address']}")
                print(f"  → {info['normalized_address']}")
        
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
        print("🚀 Place ID事前取得スクリプト v3 開始")
        print("📌 住所を正規化して検索します")
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