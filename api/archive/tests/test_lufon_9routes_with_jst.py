#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ルフォンプログレから9目的地へのテスト（JST明示版）
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta
import json
import time

def load_destinations():
    """destinations.jsonを読み込む"""
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

def get_jst_timestamp(hour=10, minute=0, days_from_today=1):
    """
    日本時間（JST）のタイムスタンプを取得
    
    Dockerコンテナ内はUTCなので、JSTとの時差（9時間）を考慮
    例：JST 10:00 = UTC 01:00
    """
    # 現在のUTC時刻
    now_utc = datetime.utcnow()
    
    # 指定日数後の日付
    target_date = now_utc + timedelta(days=days_from_today)
    
    # UTC時刻を設定（JST - 9時間）
    # JST 10:00 = UTC 01:00
    utc_hour = hour - 9
    if utc_hour < 0:
        utc_hour += 24
        target_date -= timedelta(days=1)
    
    target_time_utc = target_date.replace(hour=utc_hour, minute=minute, second=0, microsecond=0)
    
    # タイムスタンプに変換
    timestamp = int(target_time_utc.timestamp())
    
    # デバッグ情報
    print(f"Target JST: {hour:02d}:{minute:02d}")
    print(f"Target UTC: {target_time_utc}")
    print(f"Timestamp: {timestamp}")
    
    return target_time_utc, timestamp

def main():
    # ルフォンプログレの情報
    origin = {
        "id": "lufon_progres",
        "name": "ルフォンプログレ",
        "address": "東京都千代田区神田須田町1-20-1"
    }
    
    # 明日の10時到着（日本時間）
    arrival_time_utc, timestamp = get_jst_timestamp(hour=10, minute=0, days_from_today=1)
    
    # 目的地を読み込む
    destinations = load_destinations()
    
    print("=" * 60)
    print("ルフォンプログレから9目的地へのスクレイピングテスト")
    print(f"到着時刻（JST）: 明日の10:00")
    print(f"到着時刻（UTC）: {arrival_time_utc}")
    print(f"タイムスタンプ: {timestamp}")
    print("=" * 60)
    
    # Shizenkanのみテスト
    shizenkan = next(d for d in destinations if d['id'] == 'shizenkan_university')
    
    print(f"\n{shizenkan['name']}へのルートを検索中...")
    
    result = scrape_route(
        origin['address'], 
        shizenkan['address'], 
        arrival_time=arrival_time_utc,
        save_debug=True
    )
    
    if result:
        print(f"\n✓ 成功: {result['travel_time']}分")
        print(f"URL: {result['url']}")
        
        # URLのタイムスタンプを確認
        if f"8j{timestamp}" in result['url']:
            print("✓ タイムスタンプが正しく設定されています")
        else:
            print("✗ タイムスタンプが間違っています")
            
        # ルート詳細
        shortest_route = min(result['all_routes'], key=lambda r: r['total_time'])
        print(f"ルート詳細: {shortest_route.get('trains', [])} ")
    else:
        print("✗ スクレイピング失敗")

if __name__ == "__main__":
    main()