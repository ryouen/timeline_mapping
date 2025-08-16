#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URLを素早く確認するためのテスト
"""

from google_maps_scraper_v3 import build_complete_url
from datetime import datetime, timedelta

# ルフォンプログレとShizenkanの情報
origin_info = {
    'name': '東京都千代田区神田須田町1-20-1',
    'address': '東京都千代田区神田須田町1-20-1',
    'place_id': '0x60188c02f64e1cd9:0',
    'lat': 35.6949994,
    'lng': 139.768563
}

dest_info = {
    'name': '東京都中央区日本橋２丁目１６−３',
    'address': '東京都中央区日本橋２丁目１６−３',
    'place_id': '0x60188959cb85e96b:0',
    'lat': 35.6797443,
    'lng': 139.7730526
}

# 明日の10時到着
tomorrow = datetime.now() + timedelta(days=1)
arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

# URLを構築
url = build_complete_url(origin_info, dest_info, arrival_time=arrival_10am)

print("=" * 80)
print("構築されたURL:")
print(url)
print("=" * 80)
print("\nURL分析:")
print(f"- 出発地座標: {origin_info['lat']}, {origin_info['lng']}")
print(f"- 目的地座標: {dest_info['lat']}, {dest_info['lng']}")
print(f"- 到着時刻: {arrival_10am}")
print(f"- Place ID形式: {origin_info['place_id']} (0x形式)")
print("\n含まれるパラメータ:")
if '!3e3' in url:
    print("- !3e3 (公共交通機関モード) ✓")
if '!5e0' in url:
    print("- !5e0 (追加交通機関フラグ) ✓")
if 'travelmode=transit' in url:
    print("- travelmode=transit (明示的な公共交通機関) ✓")
if '!6e1' in url:
    print("- !6e1 (到着時刻指定) ✓")