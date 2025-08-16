#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID取得テスト - v5方式
住所を正規化して直接検索する改良版
"""

import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_address(address):
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

def get_place_id_direct(address, name=None):
    """
    住所を直接検索してPlace IDを取得（改良版）
    """
    driver = None
    try:
        # Seleniumドライバー設定
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
        
        # 住所を正規化
        normalized_address = normalize_address(address)
        logger.info(f"元の住所: {address}")
        logger.info(f"正規化後: {normalized_address}")
        
        # Google Mapsで住所を直接検索
        url = f"https://www.google.com/maps/search/{quote(normalized_address)}"
        logger.info(f"検索URL: {url}")
        
        driver.get(url)
        time.sleep(5)  # ページロード待機
        
        # 結果のURLを取得
        current_url = driver.current_url
        logger.info(f"結果URL: {current_url[:150]}...")
        
        # Place IDを抽出（複数のパターンに対応）
        place_id = None
        
        # パターン1: URLから直接抽出
        place_id_match = re.search(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
        if place_id_match:
            place_id = place_id_match.group(1)
            logger.info(f"✅ Place ID取得成功（パターン1）: {place_id}")
        else:
            # パターン2: place/の後のPlace ID
            place_match = re.search(r'/place/[^/]+/@[^/]+/data=.*!1s(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
            if place_match:
                place_id = place_match.group(1)
                logger.info(f"✅ Place ID取得成功（パターン2）: {place_id}")
            else:
                # パターン3: ftidパラメータ
                ftid_match = re.search(r'ftid=(0x[0-9a-f]+:0x[0-9a-f]+)', current_url)
                if ftid_match:
                    place_id = ftid_match.group(1)
                    logger.info(f"✅ Place ID取得成功（パターン3）: {place_id}")
        
        # 座標を抽出
        lat, lon = None, None
        coord_match = re.search(r'@([\d.]+),([\d.]+)', current_url)
        if coord_match:
            lat = coord_match.group(1)
            lon = coord_match.group(2)
            logger.info(f"座標: {lat}, {lon}")
        
        result = {
            'address': address,
            'normalized_address': normalized_address,
            'place_id': place_id,
            'lat': lat,
            'lon': lon,
            'url': current_url
        }
        
        return result
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        return {
            'address': address,
            'normalized_address': normalize_address(address),
            'place_id': None,
            'lat': None,
            'lon': None,
            'error': str(e)
        }
    finally:
        if driver:
            driver.quit()

def test_place_ids():
    """1-2件でPlace ID取得をテスト"""
    
    print("\n" + "="*60)
    print("Place ID取得テスト（v5方式）")
    print("="*60)
    
    # テストデータ（まず2件）
    test_cases = [
        {
            'name': 'ルフォンプログレ神田プレミア',
            'address': '東京都千代田区 神田須田町１丁目２０−１'
        },
        {
            'name': 'Shizenkan University',
            'address': '東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階'
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n[{test['name']}]")
        result = get_place_id_direct(test['address'], test['name'])
        
        if result['place_id']:
            print(f"✅ Place ID取得成功")
            print(f"  Place ID: {result['place_id']}")
            print(f"  座標: {result['lat']}, {result['lon']}")
            print(f"  正規化: {result['normalized_address']}")
        else:
            print(f"❌ Place ID取得失敗")
            if 'error' in result:
                print(f"  エラー: {result['error']}")
        
        results.append(result)
        time.sleep(2)  # レート制限対策
    
    return results

if __name__ == "__main__":
    results = test_place_ids()
    
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    
    success_count = sum(1 for r in results if r['place_id'])
    print(f"成功: {success_count}/{len(results)}")
    
    for result in results:
        status = "✅" if result['place_id'] else "❌"
        print(f"{status} {result['address'][:30]}... → {result.get('place_id', 'N/A')}")