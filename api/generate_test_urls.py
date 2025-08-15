#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用URLを生成（手動確認用）
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import quote

def generate_test_urls():
    """テスト用のGoogle Maps URLを生成"""
    
    # 基本情報
    origin = "東京都千代田区神田須田町1-20-1"  # ルフォンプログレ
    destinations = [
        ("Shizenkan", "東京都中央区日本橋２丁目５−１"),
        ("東京駅", "JR東京駅"),
        ("府中", "東京都府中市住吉町5-22-5")
    ]
    
    # 明日の10時到着
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
    timestamp = int(arrival_10am.timestamp())
    
    print("=" * 60)
    print("Google Maps テスト用URL")
    print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
    print(f"タイムスタンプ: {timestamp}")
    print("=" * 60)
    
    for name, dest in destinations:
        print(f"\n### {name}")
        print(f"出発: {origin}")
        print(f"到着: {dest}")
        print()
        
        # 1. 基本URL（時刻指定なし）
        basic_url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(dest)}"
        print("1. 基本URL:")
        print(basic_url)
        print()
        
        # 2. 公共交通機関モード
        transit_url = f"{basic_url}/data=!3e3"
        print("2. 公共交通機関モード:")
        print(transit_url)
        print()
        
        # 3. 時刻指定付き（シンプル版）
        time_url = f"{basic_url}/data=!3e3!5m2!6e1!8j{timestamp}"
        print("3. 時刻指定付き（シンプル）:")
        print(time_url)
        print()
        
        # 4. 完全版（座標付き）
        # ルフォンプログレの座標: 35.6949994, 139.768563
        if name == "Shizenkan":
            dest_lat, dest_lng = "35.6811282", "139.7712416"
        elif name == "東京駅":
            dest_lat, dest_lng = "35.6812405", "139.7649361"
        else:  # 府中
            dest_lat, dest_lng = "35.6559218", "139.452395"
            
        full_url = (
            f"{basic_url}/data="
            f"!4m18!4m17"
            f"!1m5!2m2!1d139.768563!2d35.6949994"
            f"!1m5!2m2!1d{dest_lng}!2d{dest_lat}"
            f"!2m3!6e1!7e2!8j{timestamp}"
            f"!3e3"
        )
        print("4. 完全版（座標・時刻指定）:")
        print(full_url)
        print()
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("手動テスト方法:")
    print("1. 上記URLをブラウザで開く")
    print("2. 公共交通機関モードになっているか確認")
    print("3. 時刻が「明日10:00到着」になっているか確認")
    print("4. ルート情報が表示されるか確認")
    print("=" * 60)

if __name__ == "__main__":
    generate_test_urls()