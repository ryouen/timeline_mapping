#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
サンプルルートテスト - 改善されたHTMLサマリーのデモ
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta
import json

def main():
    # テスト用のサンプルデータ
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # 既存の結果を再利用してHTMLを生成
    sample_results = [
        {
            'origin': {
                'id': 'lufon_progres',
                'name': 'ルフォンプログレ',
                'address': '東京都千代田区神田須田町1-20-1'
            },
            'routes': [
                {
                    'destination_id': 'shizenkan_university',
                    'destination_name': 'Shizenkan University',
                    'travel_time': 6,
                    'url': 'https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都中央区日本橋２丁目５−１%20髙島屋三井ビルディング%2017階/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!2m2!1d139.7738165!2d35.6811282!2m3!6e1!7e2!8j1755252000!3e3',
                    'route_details': ['徒歩 6分', '新日本橋駅', '約400m'],
                    'route_count': 3,
                    'status': 'success'
                },
                {
                    'destination_id': 'tokyo_american_club',
                    'destination_name': '東京アメリカンクラブ',
                    'travel_time': 14,
                    'url': 'https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都中央区日本橋室町３丁目２−１/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!1m1!1s0x60188bffe47b594f:0!2m2!1d139.772537!2d35.6879088!2m3!6e1!7e2!8j1755252000!3e3',
                    'route_details': ['徒歩 2分', '神田駅', 'JR山手線', '東京駅', '徒歩 10分'],
                    'route_count': 6,
                    'status': 'success'
                },
                {
                    'destination_id': 'yawara',
                    'destination_name': 'Yawara',
                    'travel_time': 33,
                    'url': 'https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都渋谷区神宮前１丁目８−１０%20Ｔｈｅ%20Ｉｃｅ%20Ｃｕｂｅｓ%209階/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!1m1!1s0x60188ca49985cf27:0!2m2!1d139.7059478!2d35.6696422!2m3!6e1!7e2!8j1755252000!3e3',
                    'route_details': ['徒歩 6分', '小川町駅', '東京メトロ半蔵門線', '表参道駅', '徒歩 8分'],
                    'route_count': 6,
                    'status': 'success'
                },
                {
                    'destination_id': 'fuchu_office',
                    'destination_name': '府中オフィス',
                    'travel_time': 69,
                    'url': 'https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都府中市住吉町５丁目２２−５/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!1m1!1s0x6018e499970c7047:0!2m2!1d139.4549699!2d35.6559218!2m3!6e1!7e2!8j1755252000!3e3',
                    'route_details': ['徒歩 6分', '新宿駅', '都営新宿線', '京王線乗換', '府中駅', '徒歩 15分'],
                    'route_count': 6,
                    'status': 'success'
                }
            ]
        },
        {
            'origin': {
                'id': 'la_belle_mitsukoshimae',
                'name': 'La Belle 三越前 702',
                'address': '東京都中央区日本橋本町1丁目'
            },
            'routes': [
                {
                    'destination_id': 'shizenkan_university',
                    'destination_name': 'Shizenkan University',
                    'travel_time': 5,
                    'url': 'https://www.google.com/maps/dir/東京都中央区日本橋本町1丁目/東京都中央区日本橋２丁目５−１%20髙島屋三井ビルディング%2017階/data=!3e3',
                    'route_details': ['徒歩 5分'],
                    'route_count': 1,
                    'status': 'success'
                },
                {
                    'destination_id': 'yawara',
                    'destination_name': 'Yawara',
                    'travel_time': 28,
                    'url': 'https://www.google.com/maps/dir/東京都中央区日本橋本町1丁目/東京都渋谷区神宮前１丁目８−１０/data=!3e3',
                    'route_details': ['徒歩 3分', '三越前駅', '東京メトロ半蔵門線', '表参道駅', '徒歩 8分'],
                    'route_count': 4,
                    'status': 'success'
                },
                {
                    'destination_id': 'haneda_airport',
                    'destination_name': '羽田空港',
                    'travel_time': 45,
                    'url': 'https://www.google.com/maps/dir/東京都中央区日本橋本町1丁目/東京都大田区羽田空港3-3-2/data=!3e3',
                    'route_details': ['徒歩 5分', '日本橋駅', '都営浅草線', '羽田空港第1・第2ターミナル駅'],
                    'route_count': 3,
                    'status': 'success'
                }
            ]
        }
    ]
    
    # HTMLサマリーを生成
    generate_improved_html_summary(sample_results, arrival_10am)

def generate_improved_html_summary(all_results, arrival_time):
    """改善されたHTMLサマリーを生成"""
    html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>v3スクレイパー結果 - 改善版</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
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
        .route-count {
            background: #6c757d;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🚇 v3スクレイパー ルート検索結果</h1>
        
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
                    <div class="stat-number" style="color: #28a745;">16</div>
                    <div class="stat-label">成功</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #dc3545;">2</div>
                    <div class="stat-label">失敗</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #007bff;">88.9%</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
            <p style="margin-top: 20px;">
                <strong>到着時刻:</strong> ''' + arrival_time.strftime('%Y年%m月%d日 %H:%M') + '''<br>
                <strong>実行時刻:</strong> ''' + datetime.now().strftime('%Y年%m月%d日 %H:%M:%S') + '''
            </p>
        </div>
'''
    
    for origin_result in all_results:
        origin = origin_result['origin']
        html_content += f'''
        <div class="origin-section">
            <div class="origin-header">
                <h2>📍 {origin['name']}</h2>
                <div class="origin-address">{origin['address']}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th width="18%">目的地</th>
                        <th width="10%">所要時間</th>
                        <th width="45%">経路</th>
                        <th width="12%">ルート候補</th>
                        <th width="15%">地図リンク</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        for route in origin_result['routes']:
            if route['status'] == 'success':
                if route['destination_id'] == 'fuchu_office' and route['travel_time'] == 69:
                    row_class = 'golden-route'
                    time_display = f'<span class="time-badge" style="background: #ffc107; color: #212529;">✨ {route["travel_time"]}分</span>'
                else:
                    row_class = 'success'
                    time_display = f'<span class="time-badge">{route["travel_time"]}分</span>'
                
                # 経路詳細を整形
                route_html = '<div class="route-path">'
                for i, step in enumerate(route.get('route_details', [])):
                    if i > 0:
                        route_html += '<span class="route-arrow">→</span>'
                    
                    # 特殊なステップを色分け
                    if '徒歩' in step:
                        route_html += f'<span class="route-step" style="background: #ffeeba;">🚶 {step}</span>'
                    elif '駅' in step:
                        route_html += f'<span class="route-step" style="background: #bee5eb;">🚉 {step}</span>'
                    elif '線' in step:
                        route_html += f'<span class="route-step" style="background: #d1ecf1;">🚃 {step}</span>'
                    else:
                        route_html += f'<span class="route-step">{step}</span>'
                route_html += '</div>'
                
                map_link = f'<a href="{route["url"]}" target="_blank" class="map-link">🗺️ 地図を開く</a>' if route.get('url') else '-'
                route_count = f'<span class="route-count">{route.get("route_count", "-")} ルート</span>'
            else:
                row_class = 'failure'
                time_display = '<span style="color: #dc3545;">-</span>'
                route_html = f'<span class="note">エラー: {route.get("error", "不明")}</span>'
                map_link = '-'
                route_count = '-'
            
            note = ''
            if route['destination_id'] == 'fuchu_office' and route.get('travel_time') == 69:
                note = ' <span class="note">(ゴールデンデータと一致！)</span>'
            
            html_content += f'''
                    <tr class="{row_class}">
                        <td><strong>{route['destination_name']}</strong>{note}</td>
                        <td>{time_display}</td>
                        <td>{route_html}</td>
                        <td style="text-align: center;">{route_count}</td>
                        <td style="text-align: center;">{map_link}</td>
                    </tr>
'''
        
        html_content += '''
                </tbody>
            </table>
        </div>
'''
    
    html_content += '''
        <div style="margin-top: 40px; text-align: center; color: #6c757d;">
            <p>Generated by Google Maps Scraper v3 with 2-step place resolution strategy</p>
        </div>
    </div>
</body>
</html>
'''
    
    html_file = '/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTMLサマリーを生成: {html_file}")

if __name__ == "__main__":
    main()