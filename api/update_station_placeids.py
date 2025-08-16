#!/usr/bin/env python3
"""東京駅と羽田空港のPlace IDを更新"""

import sys
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')

from collect_place_ids import PlaceIdCollector
import json

collector = PlaceIdCollector()
collector.setup_driver()

# 東京駅と羽田空港だけ更新
stations = [
    {
        "name": "東京駅",
        "address": "東京都千代田区丸の内１丁目９番１号",
        "category": "station"
    },
    {
        "name": "羽田空港",
        "address": "東京都大田区羽田空港3-3-2",
        "category": "airport"
    }
]

print("=" * 60)
print("駅・空港のPlace ID更新")
print("=" * 60)

for station in stations:
    result = collector.extract_place_id(
        station['address'], 
        station['name'], 
        station['category']
    )
    
    print(f"\n{station['name']}:")
    print(f"  Place ID: {result['place_id']}")
    print(f"  Format: {result['place_id_format']}")

# destinations.jsonを更新
with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for dest in data['destinations']:
    if dest['name'] == "東京駅":
        dest['place_id'] = "ChIJC3Cf2PuLGGAROO00ukl8JwA"
        dest['place_id_format'] = "ChIJ"
        print(f"\n✅ 東京駅を更新: {dest['place_id']}")
    elif dest['name'] == "羽田空港":
        dest['place_id'] = "ChIJ45IxpAtkGGAR3_hG0anDMg0"
        dest['place_id_format'] = "ChIJ"
        print(f"✅ 羽田空港を更新: {dest['place_id']}")

# ファイル保存
with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

collector.close()

print("\n更新完了！")