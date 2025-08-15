#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
18ルートテスト - API経由で効率的に
"""

import requests
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def load_destinations():
    """destinations.jsonを読み込む"""
    with open('/var/www/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

def call_api(origin, destination, arrival_time):
    """APIを呼び出してルート情報を取得"""
    url = "http://localhost:8000/api/transit"
    data = {
        "action": "getSingleRoute",
        "origin": origin,
        "destination": destination,
        "arrivalTime": arrival_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        response = requests.post(url, json=data, timeout=60)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_route(origin_info, dest_info, arrival_time):
    """単一ルートを処理"""
    start_time = time.time()
    result = call_api(origin_info['address'], dest_info['address'], arrival_time)
    elapsed_time = time.time() - start_time
    
    return {
        'origin': origin_info,
        'destination': dest_info,
        'result': result,
        'elapsed_time': elapsed_time
    }

def main():
    # 2つの出発地点
    origins = [
        {
            "id": "lufon_progres",
            "name": "ルフォンプログレ",
            "address": "東京都千代田区神田須田町1-20-1"
        },
        {
            "id": "la_belle_mitsukoshimae",
            "name": "La Belle 三越前 702",
            "address": "東京都中央区日本橋本町1丁目"
        }
    ]
    
    # 明日の10時到着
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # 目的地を読み込む
    destinations = load_destinations()
    
    print(f"=== 18ルートテスト (API経由) ===")
    print(f"到着時刻: {arrival_10am.strftime('%Y-%m-%d %H:%M')}")
    print(f"総ルート数: {len(origins) * len(destinations)}")
    print("=" * 50)
    
    all_results = []
    start_time = time.time()
    
    # 並列処理で効率化
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        # すべてのルートのタスクを作成
        for origin in origins:
            for dest in destinations:
                future = executor.submit(process_route, origin, dest, arrival_10am)
                futures.append(future)
        
        # 結果を収集
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            all_results.append(result)
            
            # 進捗表示
            if result['result'].get('success'):
                travel_time = result['result'].get('route', {}).get('total_time', 'N/A')
                print(f"[{completed}/{len(futures)}] ✓ {result['origin']['name']} → {result['destination']['name']}: {travel_time}分 ({result['elapsed_time']:.1f}秒)")
            else:
                print(f"[{completed}/{len(futures)}] ✗ {result['origin']['name']} → {result['destination']['name']}: 失敗 ({result['elapsed_time']:.1f}秒)")
    
    total_time = time.time() - start_time
    
    # 結果を整理
    results_by_origin = {}
    for origin in origins:
        results_by_origin[origin['id']] = {
            'origin': origin,
            'routes': []
        }
    
    success_count = 0
    for result in all_results:
        origin_id = result['origin']['id']
        dest = result['destination']
        api_result = result['result']
        
        if api_result.get('success') and api_result.get('route'):
            route_data = api_result['route']
            success_count += 1
            
            results_by_origin[origin_id]['routes'].append({
                'destination_id': dest['id'],
                'destination_name': dest['name'],
                'travel_time': route_data.get('total_time'),
                'route_details': route_data.get('details', {}),
                'status': 'success'
            })
        else:
            results_by_origin[origin_id]['routes'].append({
                'destination_id': dest['id'],
                'destination_name': dest['name'],
                'travel_time': None,
                'status': 'failed',
                'error': api_result.get('error', 'Unknown error')
            })
    
    # サマリー表示
    print("\n" + "=" * 50)
    print(f"完了! 総処理時間: {total_time:.1f}秒")
    print(f"成功: {success_count}/{len(all_results)} ({success_count/len(all_results)*100:.1f}%)")
    
    # 結果を保存
    output_data = {
        'test_time': datetime.now().isoformat(),
        'arrival_time': arrival_10am.isoformat(),
        'total_routes': len(all_results),
        'successful': success_count,
        'failed': len(all_results) - success_count,
        'success_rate': f"{success_count/len(all_results)*100:.1f}%",
        'total_elapsed_time': total_time,
        'results': list(results_by_origin.values())
    }
    
    output_file = f'/var/www/japandatascience.com/timeline-mapping/api/v3_18routes_api_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果ファイル: {output_file}")

if __name__ == "__main__":
    main()