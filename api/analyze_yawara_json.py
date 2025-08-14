#!/usr/bin/env python3
"""
properties.jsonからYawaraへのルートを詳細分析
"""
import json

def analyze_yawara_routes():
    """Yawaraへの全ルートを分析"""
    
    # properties.jsonを読み込み
    with open('/var/www/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Yawaraへのルートを収集
    yawara_routes = []
    
    # propertiesキーから物件リストを取得
    properties = data.get('properties', [])
    
    for property_data in properties:
        if isinstance(property_data, dict):
            property_name = property_data.get('name', 'Unknown')
            property_address = property_data.get('address', 'Unknown')
            
            # routes配列を探す
            routes = property_data.get('routes', [])
            for route in routes:
                if route.get('destination') == 'yawara_gym':
                    # 出発地の情報を追加
                    route['origin_property'] = property_name
                    route['origin_address'] = property_address
                    yawara_routes.append(route)
    
    # ルートを所要時間でソート
    yawara_routes.sort(key=lambda x: x['total_time'])
    
    print("="*80)
    print("Yawaraへの全ルート分析")
    print("="*80)
    
    # 統計情報
    print(f"\n総ルート数: {len(yawara_routes)}")
    
    # 使用路線の統計
    lines_used = {}
    stations_used = {}
    
    for route in yawara_routes:
        details = route.get('details', {})
        
        # 使用駅
        station = details.get('station_used', 'Unknown')
        stations_used[station] = stations_used.get(station, 0) + 1
        
        # 使用路線
        trains = details.get('trains', [])
        for train in trains:
            line = train.get('line', 'Unknown')
            lines_used[line] = lines_used.get(line, 0) + 1
    
    print("\n【使用路線ランキング】")
    for line, count in sorted(lines_used.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {line}: {count}回")
    
    print("\n【使用駅ランキング】")
    for station, count in sorted(stations_used.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {station}: {count}回")
    
    # 最速ルート上位10個
    print("\n【最速ルートTOP10】")
    for i, route in enumerate(yawara_routes[:10]):
        details = route.get('details', {})
        origin = route.get('origin_property', 'Unknown')
        total_time = route.get('total_time', 0)
        walk_to = details.get('walk_to_station', 0)
        station = details.get('station_used', 'Unknown')
        
        print(f"\n{i+1}. {origin} → Yawara: {total_time}分")
        print(f"   駅まで徒歩: {walk_to}分")
        print(f"   使用駅: {station}")
        
        trains = details.get('trains', [])
        for j, train in enumerate(trains):
            line = train.get('line', 'Unknown')
            time = train.get('time', 0)
            from_st = train.get('from', 'Unknown')
            to_st = train.get('to', 'Unknown')
            print(f"   [{j+1}] {line}: {from_st} → {to_st} ({time}分)")
            
            # 乗換情報
            transfer = train.get('transfer_after', {})
            if transfer:
                transfer_time = transfer.get('time', 0)
                to_line = transfer.get('to_line', '')
                print(f"       乗換: {to_line} ({transfer_time}分)")
    
    # 神田駅からのルートを探す
    print("\n【神田駅を使用するルート】")
    kanda_routes = [r for r in yawara_routes if '神田' in r.get('details', {}).get('station_used', '')]
    for route in kanda_routes[:5]:
        origin = route.get('origin_property', 'Unknown')
        total_time = route.get('total_time', 0)
        details = route.get('details', {})
        
        print(f"\n{origin} → Yawara: {total_time}分")
        trains = details.get('trains', [])
        for train in trains:
            line = train.get('line', 'Unknown')
            from_st = train.get('from', 'Unknown')
            to_st = train.get('to', 'Unknown')
            print(f"  {line}: {from_st} → {to_st}")
    
    # 銀座線を使用するルート
    print("\n【銀座線を使用するルート】")
    ginza_routes = []
    for route in yawara_routes:
        trains = route.get('details', {}).get('trains', [])
        for train in trains:
            if '銀座線' in train.get('line', ''):
                ginza_routes.append(route)
                break
    
    for route in ginza_routes[:5]:
        origin = route.get('origin_property', 'Unknown')
        total_time = route.get('total_time', 0)
        details = route.get('details', {})
        
        print(f"\n{origin} → Yawara: {total_time}分")
        trains = details.get('trains', [])
        for train in trains:
            line = train.get('line', 'Unknown')
            from_st = train.get('from', 'Unknown')
            to_st = train.get('to', 'Unknown')
            print(f"  {line}: {from_st} → {to_st}")
    
    # 千代田線ルートと他のルートの比較
    print("\n【千代田線ルート vs 他のルート】")
    chiyoda_routes = []
    other_routes = []
    
    for route in yawara_routes:
        trains = route.get('details', {}).get('trains', [])
        uses_chiyoda = any('千代田線' in train.get('line', '') for train in trains)
        
        if uses_chiyoda:
            chiyoda_routes.append(route)
        else:
            other_routes.append(route)
    
    print(f"千代田線使用ルート: {len(chiyoda_routes)}個")
    print(f"その他のルート: {len(other_routes)}個")
    
    if chiyoda_routes:
        avg_chiyoda = sum(r['total_time'] for r in chiyoda_routes) / len(chiyoda_routes)
        print(f"千代田線ルート平均所要時間: {avg_chiyoda:.1f}分")
    
    if other_routes:
        avg_other = sum(r['total_time'] for r in other_routes) / len(other_routes)
        print(f"その他ルート平均所要時間: {avg_other:.1f}分")

if __name__ == "__main__":
    analyze_yawara_routes()