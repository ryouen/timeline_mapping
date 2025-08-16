#!/usr/bin/env python3
"""新しい東京駅Place IDでルート取得テスト"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from datetime import datetime, timedelta
import pytz

# 明日の10時到着
jst = pytz.timezone('Asia/Tokyo')
tomorrow = datetime.now(jst) + timedelta(days=1)
arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

scraper = GoogleMapsScraper()
scraper.setup_driver()

print("=" * 60)
print("東京駅Place IDテスト")
print("=" * 60)

# ルフォンプログレから東京駅（駅専用Place ID）
result = scraper.scrape_route(
    origin_address="東京都千代田区神田須田町1-20-1",
    dest_address="東京駅",
    dest_name="東京駅",
    arrival_time=arrival_time,
    origin_place_id="ChIJ2RxO9gKMGGARSvjnp3ocfJg",  # ルフォンプログレ
    dest_place_id="ChIJC3Cf2PuLGGAROO00ukl8JwA",    # 東京駅（駅専用）
    origin_lat=35.6950,
    origin_lon=139.7711,
    dest_lat=35.6812,
    dest_lon=139.7671
)

if result['success']:
    print(f"✅ 成功!")
    print(f"  所要時間: {result['travel_time']}分")
    print(f"  出発時刻: {result.get('departure_time', 'N/A')}")
    print(f"  到着時刻: {result.get('arrival_time', 'N/A')}")
    print(f"  運賃: {result.get('fare', 'N/A')}円")
    print(f"  ルートタイプ: {result['route_type']}")
    if result.get('train_lines'):
        print(f"  路線: {', '.join(result['train_lines'])}")
else:
    print(f"❌ 失敗: {result.get('error', 'Unknown error')}")

scraper.close()