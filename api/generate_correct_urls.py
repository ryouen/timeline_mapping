#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps用の正しいURLを生成するスクリプト
Place IDを含む完全なURL構造を再現
"""

from datetime import datetime
import pytz
from urllib.parse import quote

def generate_google_maps_timestamp(year, month, day, hour, minute):
    """
    Google Maps用のタイムスタンプを生成
    重要: JSTの時刻をUTC基準で計算（タイムゾーン無視）
    """
    # UTC時刻として作成（タイムゾーンを無視）
    utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
    return int(utc_time.timestamp())

def build_complete_url(origin_info, dest_info, arrival_time=None):
    """
    Place IDを含む完全なGoogle Maps URLを構築
    
    Args:
        origin_info: dict with keys: address, place_id, lat, lon, postal_code, building_name
        dest_info: dict with keys: address, place_id, lat, lon, postal_code, name
        arrival_time: dict with keys: year, month, day, hour, minute (JST)
    
    Returns:
        Complete Google Maps URL with all parameters
    """
    
    # 1. 基本URLの構築（郵便番号付き住所）
    if origin_info.get('postal_code'):
        origin_str = f"〒{origin_info['postal_code']}+{quote(origin_info['address'])}"
        if origin_info.get('building_name'):
            origin_str += f"+{quote(origin_info['building_name'])}"
    else:
        origin_str = quote(origin_info['address'])
    
    if dest_info.get('postal_code'):
        dest_str = f"〒{dest_info['postal_code']}+{quote(dest_info['address'])}"
        if dest_info.get('name'):
            dest_str += f"+{quote(dest_info['name'])}"
    else:
        dest_str = quote(dest_info['address'])
    
    # 2. 中心座標の計算
    center_lat = (float(origin_info['lat']) + float(dest_info['lat'])) / 2
    center_lon = (float(origin_info['lon']) + float(dest_info['lon'])) / 2
    
    # 3. URLの構築
    url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
    url += f"@{center_lat},{center_lon},16z/"
    
    # 4. dataパラメータの構築
    data_parts = []
    
    # モード指定（重要）
    data_parts.append("!3m1!4b1")  # 追加のモード指定
    
    # ルート情報
    data_parts.append("!4m18!4m17")
    
    # 出発地情報
    data_parts.append("!1m5!1m1")
    data_parts.append(f"!1s{origin_info['place_id']}")
    data_parts.append(f"!2m2!1d{origin_info['lon']}!2d{origin_info['lat']}")
    
    # 目的地情報
    data_parts.append("!1m5!1m1")
    data_parts.append(f"!1s{dest_info['place_id']}")
    data_parts.append(f"!2m2!1d{dest_info['lon']}!2d{dest_info['lat']}")
    
    # 時刻指定
    if arrival_time:
        timestamp = generate_google_maps_timestamp(
            arrival_time['year'],
            arrival_time['month'],
            arrival_time['day'],
            arrival_time['hour'],
            arrival_time['minute']
        )
        data_parts.append(f"!2m3!6e1!7e2!8j{timestamp}")
    
    # 公共交通機関モード（最後に追加）
    data_parts.append("!3e3")
    
    url += "data=" + "".join(data_parts)
    
    return url

def test_url_generation():
    """URL生成のテスト"""
    
    # ルフォンプログレ（出発地）
    origin = {
        'address': '東京都千代田区神田須田町１丁目２０−１',
        'postal_code': '101-0041',
        'building_name': '吉川ビル',
        'place_id': '0x60188c02f64e1cd9:0x987c1c7aa7e7f84a',
        'lat': '35.6949994',
        'lon': '139.7711379'
    }
    
    # テスト目的地
    destinations = [
        {
            'name': 'Shizenkan',
            'address': '東京都中央区日本橋２丁目５−１',
            'postal_code': '103-6199',
            'place_id': '0x601889d738b39701:0x996fd0bd4cfffd56',
            'lat': '35.6814238',
            'lon': '139.773935'
        },
        {
            'name': '東京アメリカンクラブ',
            'address': '東京都中央区日本橋室町３丁目２−１',
            'postal_code': '103-0022',
            'place_id': '0x60188bffe47b594f:0xf5b2351645635f1e',
            'lat': '35.6879088',
            'lon': '139.772537'
        },
        {
            'name': 'Axle御茶ノ水',
            'address': '東京都千代田区神田小川町３丁目２８−５',
            'postal_code': '101-0052',
            'place_id': '0x60188c1a868823d9:0x2a3ffeb1adb0d843',
            'lat': '35.6960075',
            'lon': '139.7631297'
        }
    ]
    
    # 2025年8月16日 10:00 JST到着
    arrival_time = {
        'year': 2025,
        'month': 8,
        'day': 16,
        'hour': 10,
        'minute': 0
    }
    
    print("="*60)
    print("Google Maps URL生成テスト")
    print(f"到着時刻: {arrival_time['year']}/{arrival_time['month']}/{arrival_time['day']} {arrival_time['hour']:02d}:{arrival_time['minute']:02d} JST")
    print("="*60)
    
    for dest in destinations:
        print(f"\n### {dest['name']}")
        url = build_complete_url(origin, dest, arrival_time)
        print(f"生成URL:")
        print(url)
        print()
        
        # 詳細表示版も生成
        detail_url = url.replace("/@", "/am=t/@")
        print(f"詳細表示URL:")
        print(detail_url)
        print("-"*40)

if __name__ == "__main__":
    test_url_generation()