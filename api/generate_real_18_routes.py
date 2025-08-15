#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実際のv3スクレイパーを使用して18ルートのデータを生成
"""

from google_maps_scraper_v3 import scrape_route, build_complete_url, get_place_details, setup_driver
from datetime import datetime, timedelta
import json
import time

def load_destinations():
    """destinations.jsonを読み込む"""
    with open('/var/www/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

def generate_real_html_summary(all_results, arrival_time):
    """実際のURLを含むHTMLサマリーを生成"""
    
    destinations = {
        "shizenkan_university": "Shizenkan University",
        "tokyo_american_club": "東京アメリカンクラブ",
        "axle_ochanomizu": "axle 御茶ノ水",
        "yawara": "Yawara",
        "kamiyacho_ee": "神谷町(EE)",
        "waseda_university": "早稲田大学",
        "fuchu_office": "府中オフィス",
        "tokyo_station": "東京駅",
        "haneda_airport": "羽田空港"
    }
    
    success_count = sum(1 for origin in all_results for route in origin['routes'] if route['status'] == 'success')
    
    html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>v3スクレイパー実行結果 - 18ルート（実際のURL付き）</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .warning-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            color: #856404;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
        }
        .origin-section {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow: hidden;
        }
        .origin-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }
        .origin-header h2 {
            margin: 0 0 5px 0;
        }
        .origin-address {
            opacity: 0.9;
            font-size: 0.9em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background-color: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .success {
            background-color: #d4edda;
        }
        .failure {
            background-color: #f8d7da;
        }
        .time-badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .route-path {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 5px;
            font-size: 0.9em;
        }
        .route-step {
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            white-space: nowrap;
        }
        .route-arrow {
            color: #6c757d;
            font-size: 0.8em;
        }
        .map-link {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.85em;
            transition: background 0.2s;
        }
        .map-link:hover {
            background: #218838;
        }
        .url-display {
            font-family: monospace;
            font-size: 0.75em;
            background: #f8f9fa;
            padding: 4px;
            margin-top: 4px;
            word-break: break-all;
            border-radius: 3px;
            color: #495057;
        }
        .golden-route {
            background-color: #fff3cd;
            font-weight: bold;
        }
        .note {
            color: #6c757d;
            font-size: 0.85em;
            font-style: italic;
        }
        .time-short { background: #28a745; }
        .time-medium { background: #007bff; }
        .time-long { background: #fd7e14; }
        .walk-step { background: #ffeeba !important; }
        .station-step { background: #bee5eb !important; }
        .line-step { background: #d1ecf1 !important; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚇 v3スクレイパー 18ルート実行結果（実際のURL付き）</h1>
        
        <div class="warning-box">
            <strong>⚠️ 重要:</strong> このページには実際にスクレイピングで使用したURLが表示されています。
            これらのURLには場所ID、座標、時刻情報が含まれており、公共交通機関での経路検索が正しく行われます。
        </div>
        
        <div class="summary-card">
            <h2>📊 実行サマリー</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">2</div>
                    <div class="stat-label">出発地点</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">9</div>
                    <div class="stat-label">目的地</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">18</div>
                    <div class="stat-label">総ルート数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #28a745;">''' + str(success_count) + '''</div>
                    <div class="stat-label">成功</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #dc3545;">''' + str(18 - success_count) + '''</div>
                    <div class="stat-label">失敗</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #007bff;">''' + f"{success_count/18*100:.1f}%" + '''</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
            <p style="margin-top: 20px;">
                <strong>到着時刻:</strong> ''' + arrival_time.strftime('%Y年%m月%d日 %H:%M') + '''<br>
                <strong>実行時刻:</strong> ''' + datetime.now().strftime('%Y年%m月%d日 %H:%M:%S') + '''<br>
                <strong>使用バージョン:</strong> Google Maps Scraper v3（30分フィルター削除済み）
            </p>
        </div>
'''
    
    for origin_data in all_results:
        origin = origin_data['origin']
        html_content += f'''
        <div class="origin-section">
            <div class="origin-header">
                <h2>📍 {origin['name']}</h2>
                <div class="origin-address">{origin['address']}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th width="15%">目的地</th>
                        <th width="8%">所要時間</th>
                        <th width="35%">経路</th>
                        <th width="10%">備考</th>
                        <th width="12%">地図リンク</th>
                        <th width="20%">スクレイピングURL</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        for route in origin_data['routes']:
            dest_name = destinations.get(route['destination_id'], route['destination_id'])
            
            if route['status'] == 'success':
                travel_time = route['travel_time']
                
                # 特殊なケースの判定
                if route['destination_id'] == 'fuchu_office' and travel_time == 69 and origin['id'] == 'lufon_progres':
                    row_class = 'golden-route'
                    time_style = 'background: #ffc107; color: #212529;'
                    time_display = f'<span class="time-badge" style="{time_style}">✨ {travel_time}分</span>'
                    note = 'ゴールデンデータ！'
                else:
                    row_class = 'success'
                    if travel_time <= 15:
                        time_class = 'time-badge time-short'
                    elif travel_time <= 30:
                        time_class = 'time-badge time-medium'
                    else:
                        time_class = 'time-badge time-long'
                    time_display = f'<span class="{time_class}">{travel_time}分</span>'
                    
                    if travel_time <= 10:
                        note = '徒歩圏内'
                    elif travel_time <= 20:
                        note = '近距離'
                    elif travel_time <= 40:
                        note = '中距離'
                    else:
                        note = '長距離'
                
                # 経路詳細を整形
                route_details = route.get('route_details', [])
                if route_details:
                    route_html = '<div class="route-path">'
                    for i, step in enumerate(route_details):
                        if i > 0:
                            route_html += '<span class="route-arrow">→</span>'
                        
                        if '徒歩' in step:
                            route_html += f'<span class="route-step walk-step">🚶 {step}</span>'
                        elif '駅' in step and '線' not in step:
                            route_html += f'<span class="route-step station-step">🚉 {step}</span>'
                        elif '線' in step:
                            route_html += f'<span class="route-step line-step">🚃 {step}</span>'
                        else:
                            route_html += f'<span class="route-step">{step}</span>'
                    route_html += '</div>'
                else:
                    route_html = '<span class="note">経路詳細なし</span>'
                
                # 実際のURL
                actual_url = route.get('url', '')
                if actual_url:
                    map_link = f'<a href="{actual_url}" target="_blank" class="map-link">🗺️ 地図を開く</a>'
                    # URLの一部を表示
                    url_parts = actual_url.split('/data=')
                    if len(url_parts) > 1:
                        data_part = url_parts[1][:50] + '...' if len(url_parts[1]) > 50 else url_parts[1]
                        url_display = f'<div class="url-display">data={data_part}</div>'
                    else:
                        url_display = '<div class="url-display">URLエラー</div>'
                else:
                    map_link = '-'
                    url_display = '-'
                
            else:
                row_class = 'failure'
                time_display = '<span style="color: #dc3545;">-</span>'
                route_html = f'<span class="note">エラー: {route.get("error", "不明")}</span>'
                note = 'ルート取得失敗'
                map_link = '-'
                url_display = '-'
            
            html_content += f'''
                    <tr class="{row_class}">
                        <td><strong>{dest_name}</strong></td>
                        <td>{time_display}</td>
                        <td>{route_html}</td>
                        <td class="note">{note}</td>
                        <td style="text-align: center;">{map_link}</td>
                        <td>{url_display}</td>
                    </tr>
'''
        
        html_content += '''
                </tbody>
            </table>
        </div>
'''
    
    html_content += '''
        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <h3>🔍 URL構造の説明</h3>
            <p>正しいGoogle Maps URLには以下の要素が必要です：</p>
            <ul>
                <li><code>!4m18!4m17</code> - データコンテナ</li>
                <li><code>!1m5!1m1!1s{place_id}!2m2!1d{lng}!2d{lat}</code> - 場所の詳細（出発地・目的地それぞれ）</li>
                <li><code>!2m3!6e1!7e2!8j{timestamp}</code> - 時刻指定（!6e1=到着時刻、!6e0=出発時刻）</li>
                <li><code>!3e3</code> - 公共交通機関モード（これだけでは不十分）</li>
            </ul>
        </div>
        
        <div style="margin-top: 20px; text-align: center; color: #6c757d;">
            <p>Generated by Google Maps Scraper v3 with complete URL generation</p>
        </div>
    </div>
</body>
</html>
'''
    
    with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def test_specific_routes():
    """全18ルートをテスト"""
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
    
    # destinations.jsonを読み込む
    destinations = load_destinations()
    
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    all_results = []
    
    for origin in origins:
        origin_results = {
            'origin': origin,
            'routes': []
        }
        
        for dest in destinations:
            print(f"\n{origin['name']} → {dest['name']}")
            print(f"  スクレイピング中...")
            
            result = scrape_route(
                origin['address'], 
                dest['address'], 
                arrival_time=arrival_10am,
                save_debug=True
            )
            
            if result:
                print(f"  ✓ 成功: {result['travel_time']}分")
                print(f"  URL: {result.get('url', 'N/A')}")
                
                # 最短ルートの詳細を取得
                shortest_route = min(result['all_routes'], key=lambda r: r['total_time'])
                
                origin_results['routes'].append({
                    'destination_id': dest['id'],
                    'destination_name': dest['name'],
                    'travel_time': result['travel_time'],
                    'url': result.get('url'),
                    'route_details': shortest_route.get('trains', []),
                    'status': 'success'
                })
            else:
                print(f"  ✗ 失敗")
                origin_results['routes'].append({
                    'destination_id': dest['id'],
                    'destination_name': dest['name'],
                    'travel_time': None,
                    'url': None,
                    'status': 'failed',
                    'error': 'No route found'
                })
        
        all_results.append(origin_results)
    
    # HTMLを生成
    generate_real_html_summary(all_results, arrival_10am)
    print("\n結果を v3_results_summary.html に保存しました")
    print(f"\n全{len(all_results)}出発地点、計{sum(len(r['routes']) for r in all_results)}ルートのテストが完了しました")

if __name__ == "__main__":
    # デバッグ用に特定のルートのみテスト
    test_specific_routes()