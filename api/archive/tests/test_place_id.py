#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID取得のテスト
"""
import sys
sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper

def test_place_id():
    """Place ID取得をテスト"""
    
    test_addresses = [
        ("東京都中央区日本橋2-5-1髙島屋三井ビルディング17階", "Shizenkan University"),
        ("東京都中央区日本橋室町3-2-1", "東京アメリカンクラブ"),
        ("東京都千代田区神田小川町3-28-5 Axle御茶ノ水", "axle御茶ノ水"),
        ("東京都渋谷区神宮前1-8-10 The Ice Cubes 9階", "Yawara"),
    ]
    
    scraper = GoogleMapsScraper()
    
    try:
        scraper.setup_driver()
        print("Place ID取得テスト")
        print("=" * 60)
        
        for address, name in test_addresses:
            print(f"\n📍 {name}")
            print(f"   元の住所: {address}")
            
            result = scraper.get_place_id(address, name)
            
            if result:
                if result.startswith('0x') or result.startswith('ChIJ'):
                    print(f"   ✅ Place ID取得成功: {result}")
                else:
                    print(f"   ⚠️ 住所で代用: {result}")
            else:
                print(f"   ❌ 取得失敗")
        
    finally:
        scraper.close()
        print("\n" + "=" * 60)
        print("テスト完了")

if __name__ == "__main__":
    test_place_id()