#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Place ID形式（0x vs ChIJ）のURL生成テスト
ルフォンプログレから3つの目的地へのURLを生成
"""

import sys
import json
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote

# パスを追加
sys.path.append('/var/www/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

def generate_google_maps_timestamp(year, month, day, hour, minute):
    """Google Maps用のタイムスタンプを生成"""
    utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
    return int(utc_time.timestamp())

def build_url_v5_style(origin_address, dest_address, origin_place_id_0x, dest_place_id_0x, 
                        origin_lat, origin_lon, dest_lat, dest_lon, timestamp):
    """v5スタイル（0x形式）のURL構築"""
    origin_str = quote(origin_address)
    dest_str = quote(dest_address)
    
    url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
    
    # dataパラメータ（0x形式）
    data_parts = []
    if origin_place_id_0x and dest_place_id_0x:
        data_parts.append("!4m18!4m17")
        data_parts.append("!1m5!1m1")
        data_parts.append(f"!1s{origin_place_id_0x}")
        if origin_lon and origin_lat:
            data_parts.append(f"!2m2!1d{origin_lon}!2d{origin_lat}")
        data_parts.append("!1m5!1m1")
        data_parts.append(f"!1s{dest_place_id_0x}")
        if dest_lon and dest_lat:
            data_parts.append(f"!2m2!1d{dest_lon}!2d{dest_lat}")
    
    # 時刻指定
    data_parts.append(f"!2m3!6e1!7e2!8j{timestamp}")
    # 公共交通機関
    data_parts.append("!3e3")
    
    url += "data=" + "".join(data_parts)
    return url

def build_url_chij_style(origin_address, dest_address, origin_place_id_chij, dest_place_id_chij, 
                        origin_lat, origin_lon, dest_lat, dest_lon, timestamp):
    """ChIJ形式のURL構築（v5_curスタイル）"""
    origin_str = quote(origin_address)
    dest_str = quote(dest_address)
    
    url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
    
    # dataパラメータ（ChIJ形式）
    data_parts = []
    if origin_place_id_chij and dest_place_id_chij:
        data_parts.append("!4m18!4m17")
        data_parts.append("!1m5!1m1")
        data_parts.append(f"!1s{origin_place_id_chij}")
        if origin_lon and origin_lat:
            data_parts.append(f"!2m2!1d{origin_lon}!2d{origin_lat}")
        data_parts.append("!1m5!1m1")
        data_parts.append(f"!1s{dest_place_id_chij}")
        if dest_lon and dest_lat:
            data_parts.append(f"!2m2!1d{dest_lon}!2d{dest_lat}")
    
    # 時刻指定
    data_parts.append(f"!2m3!6e1!7e2!8j{timestamp}")
    # 公共交通機関
    data_parts.append("!3e3")
    
    url += "data=" + "".join(data_parts)
    return url

def main():
    # ルフォンプログレの情報
    property_info = {
        "name": "ルフォンプログレ神田プレミア",
        "address": "東京都千代田区神田須田町1-20-1"
    }
    
    # 3つの目的地
    destinations = [
        {
            "name": "Shizenkan University",
            "address": "東京都中央区日本橋2-5-1"
        },
        {
            "name": "東京駅",
            "address": "東京都千代田区丸の内1-9-1"
        },
        {
            "name": "早稲田大学",
            "address": "東京都新宿区西早稲田1-6-11"
        }
    ]
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    timestamp = generate_google_maps_timestamp(
        arrival_time.year,
        arrival_time.month,
        arrival_time.day,
        arrival_time.hour,
        arrival_time.minute
    )
    
    print("Place ID取得中...")
    
    # スクレイパー初期化
    scraper = GoogleMapsScraper()
    
    try:
        scraper.setup_driver()
        
        # ルフォンプログレのPlace ID取得
        print(f"物件: {property_info['name']}")
        origin_result = scraper.get_place_id(property_info['address'], property_info['name'])
        
        # 実際に取得したPlace ID（0x形式）
        origin_place_id_0x = origin_result.get('place_id')
        origin_lat = origin_result.get('lat')
        origin_lon = origin_result.get('lon')
        
        print(f"  0x形式: {origin_place_id_0x}")
        
        # ChIJ形式（仮想的に生成 - 実際にはページソースから取得する必要がある）
        # ここではデモ用に固定値を使用
        origin_place_id_chij = "ChIJx5NHs0-JGGAR3vMpqQl3kx4"  # 仮のChIJ形式
        print(f"  ChIJ形式（仮）: {origin_place_id_chij}")
        
        # 各目的地のPlace ID取得とURL生成
        urls_data = []
        
        for dest in destinations:
            print(f"\n目的地: {dest['name']}")
            dest_result = scraper.get_place_id(dest['address'], dest['name'])
            
            # 0x形式
            dest_place_id_0x = dest_result.get('place_id')
            dest_lat = dest_result.get('lat')
            dest_lon = dest_result.get('lon')
            print(f"  0x形式: {dest_place_id_0x}")
            
            # ChIJ形式（仮）
            if dest['name'] == "Shizenkan University":
                dest_place_id_chij = "ChIJNdiBOdeJGGARVkZf7dQu-fc"
            elif dest['name'] == "東京駅":
                dest_place_id_chij = "ChIJGWlcqP6LGGARddFD1M78MhU"
            else:  # 早稲田大学
                dest_place_id_chij = "ChIJ05IRjKuMGGARnh5k1rqQjmE"
            print(f"  ChIJ形式（仮）: {dest_place_id_chij}")
            
            # v5スタイルURL（0x形式）
            url_v5 = build_url_v5_style(
                property_info['address'], dest['address'],
                origin_place_id_0x, dest_place_id_0x,
                origin_lat, origin_lon, dest_lat, dest_lon,
                timestamp
            )
            
            # ChIJ形式URL
            url_chij = build_url_chij_style(
                property_info['address'], dest['address'],
                origin_place_id_chij, dest_place_id_chij,
                origin_lat, origin_lon, dest_lat, dest_lon,
                timestamp
            )
            
            urls_data.append({
                'destination': dest['name'],
                'url_v5': url_v5,
                'url_chij': url_chij,
                'origin_0x': origin_place_id_0x,
                'origin_chij': origin_place_id_chij,
                'dest_0x': dest_place_id_0x,
                'dest_chij': dest_place_id_chij
            })
        
        # HTML生成
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Place ID形式比較テスト（0x vs ChIJ）</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4285f4;
            padding-bottom: 10px;
        }}
        .info {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .route-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #1a73e8;
            margin-top: 0;
        }}
        .url-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        .url-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #dadce0;
        }}
        .url-box h3 {{
            margin-top: 0;
            color: #5f6368;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .place-id {{
            font-family: monospace;
            background: #fff;
            padding: 5px 8px;
            border-radius: 3px;
            border: 1px solid #dadce0;
            font-size: 12px;
            word-break: break-all;
            margin: 5px 0;
        }}
        .v5-style {{
            border-left: 4px solid #34a853;
        }}
        .chij-style {{
            border-left: 4px solid #ea4335;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            background: #1a73e8;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 10px;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #1557b0;
        }}
        .url-preview {{
            font-family: monospace;
            font-size: 10px;
            color: #5f6368;
            background: #f1f3f4;
            padding: 8px;
            border-radius: 3px;
            margin-top: 10px;
            word-break: break-all;
            max-height: 100px;
            overflow-y: auto;
        }}
        .timestamp-info {{
            background: #e8f0fe;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <h1>🗺️ Place ID形式比較テスト</h1>
    
    <div class="info">
        <h2>テスト概要</h2>
        <p><strong>出発地:</strong> {property_info['name']}<br>
        <strong>住所:</strong> {property_info['address']}</p>
        <div class="timestamp-info">
            <strong>到着時刻:</strong> {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST<br>
            <strong>タイムスタンプ:</strong> {timestamp}
        </div>
        <p><strong>目的:</strong> v5（0x形式）とv5_cur（ChIJ形式）のPlace IDでURLが正しく動作するか検証</p>
    </div>
"""
        
        for data in urls_data:
            html_content += f"""
    <div class="route-section">
        <h2>📍 {data['destination']}</h2>
        
        <div class="url-comparison">
            <div class="url-box v5-style">
                <h3>v5スタイル（0x形式）</h3>
                <p><strong>出発地Place ID:</strong></p>
                <div class="place-id">{data['origin_0x'] or 'なし'}</div>
                <p><strong>目的地Place ID:</strong></p>
                <div class="place-id">{data['dest_0x'] or 'なし'}</div>
                <a href="{data['url_v5']}" target="_blank" class="btn">🚀 Google Mapsで開く</a>
                <div class="url-preview">{data['url_v5']}</div>
            </div>
            
            <div class="url-box chij-style">
                <h3>v5_curスタイル（ChIJ形式）</h3>
                <p><strong>出発地Place ID:</strong></p>
                <div class="place-id">{data['origin_chij']}</div>
                <p><strong>目的地Place ID:</strong></p>
                <div class="place-id">{data['dest_chij']}</div>
                <a href="{data['url_chij']}" target="_blank" class="btn">🚀 Google Mapsで開く</a>
                <div class="url-preview">{data['url_chij']}</div>
            </div>
        </div>
    </div>
"""
        
        html_content += """
    <div class="info">
        <h2>テスト方法</h2>
        <ol>
            <li>各ルートの「Google Mapsで開く」ボタンをクリック</li>
            <li>v5（0x形式）とv5_cur（ChIJ形式）の両方で同じルートが表示されるか確認</li>
            <li>到着時刻が10:00に設定されているか確認</li>
            <li>公共交通機関モードが選択されているか確認</li>
        </ol>
        
        <h2>期待される結果</h2>
        <ul>
            <li>✅ 両方のPlace ID形式で同じ場所が認識される</li>
            <li>✅ ルート検索が正常に動作する</li>
            <li>✅ 時刻指定が反映される</li>
            <li>✅ 公共交通機関モードが選択される</li>
        </ul>
    </div>
</body>
</html>
"""
        
        # HTMLファイル保存
        html_path = '/var/www/japandatascience.com/timeline-mapping/api/test_place_id_formats.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nHTMLファイルを生成しました: {html_path}")
        print(f"ブラウザで開く: https://japandatascience.com/timeline-mapping/api/test_place_id_formats.html")
        
        # JSON形式でも保存
        json_path = '/var/www/japandatascience.com/timeline-mapping/api/test_place_id_urls.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'property': property_info,
                'destinations': destinations,
                'arrival_time': arrival_time.isoformat(),
                'timestamp': timestamp,
                'urls': urls_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"URLデータを保存しました: {json_path}")
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()