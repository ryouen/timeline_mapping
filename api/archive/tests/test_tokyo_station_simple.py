#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
東京駅ルート修正テスト（シンプル版）
タイムアウトを避けるため2つの方法のみテスト
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta, timezone
import json

def main():
    origin = "東京都千代田区神田須田町1-20-1"  # ルフォンプログレ
    
    # 2つの方法のみテスト
    destinations = [
        {
            "name": "東京駅 - 駅名直接",
            "address": "東京駅"
        },
        {
            "name": "JR東京駅丸の内南口",
            "address": "JR東京駅丸の内南口"
        }
    ]
    
    # 明日10時到着
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
    
    print("=" * 60)
    print("東京駅ルート修正テスト（シンプル版）")
    print("=" * 60)
    
    for dest in destinations:
        print(f"\nテスト: {dest['name']}")
        print(f"住所: {dest['address']}")
        
        try:
            result = scrape_route(
                origin,
                dest['address'],
                arrival_time=arrival_10am,
                save_debug=False
            )
            
            if result:
                shortest = min(result['all_routes'], key=lambda r: r['total_time'])
                route_text = shortest.get('raw_text', '')
                
                # 車ルート判定
                is_car = any(word in route_text for word in ['中央通り', '国道', '号線'])
                has_transit = any(word in route_text for word in ['駅', '線', '電車'])
                
                print(f"✓ 所要時間: {result['travel_time']}分")
                print(f"✓ タイプ: {'🚗 車' if is_car else '🚇 公共交通'}")
                print(f"✓ 座標: {result['destination_details'].get('lat')}, {result['destination_details'].get('lng')}")
                
                if has_transit and not is_car:
                    print(f"\n✅ 成功！「{dest['address']}」で公共交通機関ルート取得")
                    return dest['address']
                    
        except Exception as e:
            print(f"✗ エラー: {e}")
    
    print("\n❌ どちらの方法でも公共交通機関ルートを取得できませんでした")
    return None

if __name__ == "__main__":
    main()