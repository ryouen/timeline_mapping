#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URLビルドのデバッグ - 何が構築されているか確認
"""

import sys
from datetime import datetime, timedelta
import pytz

sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

# 明日10時
jst = pytz.timezone('Asia/Tokyo')
tomorrow = datetime.now(jst) + timedelta(days=1)
arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

scraper = GoogleMapsScraper()

# Place ID情報を準備
origin_info = {
    'place_id': 'ChIJ2RxO9gKMGGARSvjnp3ocfJg',  # ルフォンプログレ
    'lat': '35.6950',
    'lon': '139.7711',
    'normalized_address': '東京都千代田区神田須田町1-20-1'
}

dest_info = {
    'place_id': 'ChIJLdASefmLGGARF3Ez6A4i4Q4',  # 東京駅
    'lat': '35.6812',
    'lon': '139.7676',
    'normalized_address': '東京都千代田区丸の内1丁目'
}

# URLを構築
url = scraper.build_url_with_timestamp(origin_info, dest_info, arrival_time)

print("="*60)
print("構築されたURL:")
print("="*60)
print(url)
print("\n")
print("URL要素の分解:")
print("-"*60)

# URLを分解して表示
if "data=" in url:
    base_url, data_params = url.split("data=")
    print(f"Base URL: {base_url}")
    print(f"\nDataパラメータ:")
    
    # !で区切って表示
    params = data_params.split("!")
    for i, param in enumerate(params):
        if param:
            print(f"  !{param}")
            # 特定のパラメータを解説
            if param.startswith("1sChIJ"):
                print(f"    → ChIJ形式のPlace ID")
            elif param.startswith("1s0x"):
                print(f"    → 0x形式のPlace ID")
            elif param.startswith("8j"):
                print(f"    → タイムスタンプ: {param[2:]}")
            elif param == "3e3":
                print(f"    → 公共交通機関モード")

print("\n" + "="*60)
print("このURLは正しく見えますか？")
print("ChIJ形式のPlace IDが含まれていますか？")