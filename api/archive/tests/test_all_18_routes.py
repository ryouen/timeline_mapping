#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
18ルートテスト - 2つの出発地点から全目的地へ
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta
import json
import os

def load_destinations():
    """destinations.jsonを読み込む"""
    dest_file = '/app/output/japandatascience.com/timeline-mapping/data/destinations.json'
    with open(dest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

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
    
    print(f"=== 18ルートテスト ===")
    print(f"到着時刻: {arrival_10am.strftime('%Y-%m-%d %H:%M')}")
    print(f"出発地数: {len(origins)}")
    print(f"目的地数: {len(destinations)}")
    print(f"総ルート数: {len(origins) * len(destinations)}")
    print("=" * 50)
    
    all_results = []
    total_success = 0
    total_failed = 0
    
    for origin in origins:
        print(f"\n=== 出発地: {origin['name']} ===")
        print(f"住所: {origin['address']}")
        
        origin_results = {
            'origin': origin,
            'routes': []
        }
        
        for i, dest in enumerate(destinations, 1):
            dest_name = dest['name']
            dest_address = dest['address']
            dest_id = dest['id']
            
            print(f"\n[{i}/{len(destinations)}] {dest_name}")
            
            try:
                # v3で検索
                result = scrape_route(
                    origin['address'], 
                    dest_address, 
                    arrival_time=arrival_10am,
                    save_debug=False  # デバッグファイルは保存しない
                )
                
                if result and result.get('travel_time'):
                    print(f"  ✓ 成功: {result['travel_time']}分")
                    
                    # 最短ルートの詳細を取得
                    shortest_route = min(result['all_routes'], key=lambda r: r['total_time'])
                    
                    route_data = {
                        'destination_id': dest_id,
                        'destination_name': dest_name,
                        'travel_time': result['travel_time'],
                        'url': result.get('url', ''),
                        'route_details': shortest_route.get('trains', []),
                        'route_count': len(result.get('all_routes', [])),
                        'status': 'success'
                    }
                    origin_results['routes'].append(route_data)
                    total_success += 1
                else:
                    print(f"  ✗ 失敗: ルート情報を取得できませんでした")
                    origin_results['routes'].append({
                        'destination_id': dest_id,
                        'destination_name': dest_name,
                        'travel_time': None,
                        'url': '',
                        'status': 'failed',
                        'error': 'No route found'
                    })
                    total_failed += 1
                    
            except Exception as e:
                print(f"  ✗ エラー: {str(e)}")
                origin_results['routes'].append({
                    'destination_id': dest_id,
                    'destination_name': dest_name,
                    'travel_time': None,
                    'url': '',
                    'status': 'failed',
                    'error': str(e)
                })
                total_failed += 1
        
        all_results.append(origin_results)
    
    # 結果を保存
    output_file = f'/app/output/japandatascience.com/timeline-mapping/api/v3_18routes_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'arrival_time': arrival_10am.isoformat(),
            'total_routes': len(origins) * len(destinations),
            'successful': total_success,
            'failed': total_failed,
            'success_rate': f"{(total_success / (len(origins) * len(destinations)) * 100):.1f}%",
            'results': all_results
        }, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"完了!")
    print(f"成功: {total_success}/{len(origins) * len(destinations)} ({(total_success / (len(origins) * len(destinations)) * 100):.1f}%)")
    print(f"結果ファイル: {output_file}")
    
    # HTMLサマリーを生成
    generate_html_summary(all_results, arrival_10am, output_file)

def generate_html_summary(all_results, arrival_time, json_file):
    """改善されたHTMLサマリーを生成"""
    html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>v3スクレイパー 18ルート結果</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .summary {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .origin-section {
            margin-bottom: 30px;
        }
        .origin-header {
            background: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .success {
            background-color: #e8f5e9;
        }
        .failure {
            background-color: #ffebee;
        }
        .route-details {
            font-size: 0.9em;
            color: #555;
        }
        .time {
            font-weight: bold;
            color: #2196F3;
        }
        a {
            color: #1976D2;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        .stat-box {
            text-align: center;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 5px;
            flex: 1;
            margin: 0 10px;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>v3スクレイパー 18ルート テスト結果</h1>
        
        <div class="summary">
            <h2>実行条件</h2>
            <p><strong>到着時刻:</strong> ''' + arrival_time.strftime('%Y年%m月%d日 %H:%M') + '''</p>
            <p><strong>実行時刻:</strong> ''' + datetime.now().strftime('%Y年%m月%d日 %H:%M:%S') + '''</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">18</div>
                <div>総ルート数</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="success-count">-</div>
                <div>成功</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="success-rate">-</div>
                <div>成功率</div>
            </div>
        </div>
'''
    
    success_count = 0
    
    for origin_result in all_results:
        origin = origin_result['origin']
        html_content += f'''
        <div class="origin-section">
            <div class="origin-header">
                <h2>出発地: {origin['name']}</h2>
                <p>{origin['address']}</p>
            </div>
            
            <table>
                <tr>
                    <th width="20%">目的地</th>
                    <th width="10%">所要時間</th>
                    <th width="50%">経路詳細</th>
                    <th width="10%">ルート候補数</th>
                    <th width="10%">Google Maps</th>
                </tr>
'''
        
        for route in origin_result['routes']:
            if route['status'] == 'success':
                success_count += 1
                row_class = 'success'
                time_display = f'<span class="time">{route["travel_time"]}分</span>'
                route_details = ' → '.join(route.get('route_details', ['詳細なし']))
                if not route_details or route_details == '詳細なし':
                    route_details = '(経路情報取得中)'
                map_link = f'<a href="{route["url"]}" target="_blank">地図を開く</a>' if route.get('url') else '-'
                route_count = route.get('route_count', '-')
            else:
                row_class = 'failure'
                time_display = '-'
                route_details = f'エラー: {route.get("error", "不明")}'
                map_link = '-'
                route_count = '-'
            
            html_content += f'''
                <tr class="{row_class}">
                    <td>{route['destination_name']}</td>
                    <td>{time_display}</td>
                    <td class="route-details">{route_details}</td>
                    <td>{route_count}</td>
                    <td>{map_link}</td>
                </tr>
'''
        
        html_content += '''
            </table>
        </div>
'''
    
    success_rate = (success_count / 18 * 100)
    
    html_content += f'''
        <div style="margin-top: 30px; text-align: center;">
            <p><a href="{os.path.basename(json_file)}">詳細なJSONデータを見る</a></p>
        </div>
    </div>
    
    <script>
        document.getElementById('success-count').textContent = '{success_count}';
        document.getElementById('success-rate').textContent = '{success_rate:.1f}%';
    </script>
</body>
</html>
'''
    
    html_file = '/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nHTMLサマリー: {html_file}")

if __name__ == "__main__":
    main()