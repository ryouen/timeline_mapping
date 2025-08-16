#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID一括取得スクリプト v5
全目的地と物件のPlace IDを事前取得し、重複を排除して効率化

主な特徴：
1. 住所の正規化（1丁目20-1形式）
2. 住所のみで検索（施設名は使わない）
3. 重複住所をスキップ
4. バックグラウンド実行対応
"""

import json
import time
import logging
import re
from datetime import datetime
from selenium import webdriver
from urllib.parse import quote

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaceIdFetcherV5:
    def __init__(self):
        self.driver = None
        self.place_id_cache = {}  # 住所をキーにしたキャッシュ
        self.processed_count = 0
        
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
        
        # ビル名などの余分な情報を削除（最初の建物番号まで）
        # 例: "東京都中央区日本橋2-5-1 髙島屋三井ビルディング" → "東京都中央区日本橋2-5-1"
        normalized = re.sub(r'^([^\s]+(?:\d+-\d+-\d+|\d+-\d+)).*', r'\1', normalized)
        
        return normalized
    
    def get_place_id_by_address(self, address, name=None):
        """
        住所のみでPlace IDを取得（v5方式）
        """
        # 正規化した住所でキャッシュチェック
        normalized_address = self.normalize_address(address)
        
        if normalized_address in self.place_id_cache:
            logger.info(f"⚡ キャッシュから取得: {name or address[:30]}...")
            return self.place_id_cache[normalized_address]
        
        try:
            # Google Mapsで住所を直接検索
            url = f"https://www.google.com/maps/search/{quote(normalized_address)}"
            
            logger.info(f"🔍 Place ID取得中 [{self.processed_count+1}]: {name or address[:30]}...")
            logger.debug(f"   正規化: {normalized_address}")
            
            self.driver.get(url)
            time.sleep(3)  # ページロード待機
            
            # 結果のURLを取得
            current_url = self.driver.current_url
            
            # Place IDを抽出
            place_id = None
            place_id_patterns = [
                r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)',  # 標準パターン
                r'/place/[^/]+/@[^/]+/data=.*!1s(0x[0-9a-f]+:0x[0-9a-f]+)',  # placeパターン
                r'ftid=(0x[0-9a-f]+:0x[0-9a-f]+)'  # ftidパターン
            ]
            
            for pattern in place_id_patterns:
                match = re.search(pattern, current_url)
                if match:
                    place_id = match.group(1) if '(' in pattern else match.group(1)
                    logger.info(f"   ✅ Place ID: {place_id}")
                    break
            
            if not place_id:
                logger.warning(f"   ⚠️ Place ID取得失敗")
            
            # 座標を抽出
            lat, lon = None, None
            coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
            if coord_match:
                lat = coord_match.group(1)
                lon = coord_match.group(2)
                logger.debug(f"   座標: {lat}, {lon}")
            
            result = {
                'place_id': place_id,
                'lat': lat,
                'lon': lon,
                'normalized_address': normalized_address,
                'original_address': address
            }
            
            # キャッシュに保存
            self.place_id_cache[normalized_address] = result
            self.processed_count += 1
            
            return result
            
        except Exception as e:
            logger.error(f"   ❌ エラー: {e}")
            return {
                'place_id': None,
                'lat': None,
                'lon': None,
                'normalized_address': normalized_address,
                'original_address': address,
                'error': str(e)
            }
    
    def process_all(self):
        """全目的地と物件のPlace IDを取得"""
        
        # データファイルを読み込み
        with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
            destinations = json.load(f)['destinations']
        
        with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as f:
            properties = json.load(f)['properties']
        
        results = {
            'destinations': {},
            'properties': {},
            'unique_addresses': {},
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_destinations': len(destinations),
                'total_properties': len(properties),
                'unique_addresses': 0,
                'success_count': 0,
                'failed_count': 0
            }
        }
        
        print("\n" + "="*60)
        print("🎯 目的地のPlace ID取得")
        print("="*60)
        
        # 目的地のPlace IDを取得
        for dest in destinations:
            info = self.get_place_id_by_address(dest['address'], dest['name'])
            results['destinations'][dest['name']] = info
            
            # 統計更新
            if info['place_id']:
                results['stats']['success_count'] += 1
            else:
                results['stats']['failed_count'] += 1
            
            time.sleep(1)  # レート制限対策
        
        print("\n" + "="*60)
        print("🏢 物件のPlace ID取得")
        print("="*60)
        
        # 物件のPlace IDを取得（重複住所はスキップ）
        processed_addresses = set()
        
        for prop in properties:
            normalized = self.normalize_address(prop['address'])
            
            # 既に処理済みの住所はスキップ
            if normalized in processed_addresses:
                logger.info(f"⏭️ スキップ（重複）: {prop['name']}")
                continue
            
            processed_addresses.add(normalized)
            
            info = self.get_place_id_by_address(prop['address'], prop['name'])
            results['properties'][prop['name']] = info
            
            # unique_addressesに追加
            if normalized not in results['unique_addresses']:
                results['unique_addresses'][normalized] = {
                    'place_id': info['place_id'],
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'names': [prop['name']]  # この住所を使う物件名リスト
                }
            else:
                results['unique_addresses'][normalized]['names'].append(prop['name'])
            
            # 統計更新
            if info['place_id']:
                results['stats']['success_count'] += 1
            else:
                results['stats']['failed_count'] += 1
            
            time.sleep(1)  # レート制限対策
        
        results['stats']['unique_addresses'] = len(results['unique_addresses'])
        
        return results
    
    def save_results(self, results):
        """結果を保存"""
        output_file = '/app/output/japandatascience.com/timeline-mapping/data/place_ids_v5.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 結果を保存: {output_file}")
        
        # サマリー表示
        print("\n" + "="*60)
        print("📊 Place ID取得結果サマリー")
        print("="*60)
        
        stats = results['stats']
        print(f"\n処理統計:")
        print(f"  目的地数: {stats['total_destinations']}")
        print(f"  物件数: {stats['total_properties']}")
        print(f"  ユニーク住所数: {stats['unique_addresses']}")
        print(f"  成功: {stats['success_count']}")
        print(f"  失敗: {stats['failed_count']}")
        print(f"  成功率: {stats['success_count']*100/(stats['success_count']+stats['failed_count']):.1f}%")
        
        # 失敗した項目をリスト
        failed_destinations = [name for name, info in results['destinations'].items() if not info['place_id']]
        failed_properties = [name for name, info in results['properties'].items() if not info['place_id']]
        
        if failed_destinations:
            print(f"\n⚠️ Place ID取得失敗（目的地）: {len(failed_destinations)}件")
            for name in failed_destinations[:5]:  # 最初の5件のみ表示
                print(f"  - {name}")
        
        if failed_properties:
            print(f"\n⚠️ Place ID取得失敗（物件）: {len(failed_properties)}件")
            for name in failed_properties[:5]:  # 最初の5件のみ表示
                print(f"  - {name}")
        
        # 重複住所の情報
        duplicates = [addr for addr, info in results['unique_addresses'].items() if len(info.get('names', [])) > 1]
        if duplicates:
            print(f"\n📍 重複住所（効率化済み）: {len(duplicates)}件")
            for addr in duplicates[:3]:  # 最初の3件のみ表示
                names = results['unique_addresses'][addr]['names']
                print(f"  {addr[:30]}... → {', '.join(names[:2])}")
        
        return results
    
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            logger.info("Seleniumセッション終了")

def main():
    """メイン処理"""
    fetcher = PlaceIdFetcherV5()
    
    try:
        print("🚀 Place ID一括取得スクリプト v5")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📌 住所のみで検索（施設名は使用しない）")
        
        fetcher.setup_driver()
        results = fetcher.process_all()
        fetcher.save_results(results)
        
        print("\n✅ 処理完了!")
        print(f"処理時間: 約{fetcher.processed_count * 4 / 60:.1f}分")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        fetcher.close()

if __name__ == "__main__":
    main()