#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ルフォンプログレから9目的地へのテスト（1件ずつHTMLを更新）
"""

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta, timezone
import json
import time
from urllib.parse import quote

def load_destinations():
    """destinations.jsonを読み込む"""
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

def update_html_after_each_route(results, arrival_time, current_index, total_routes):
    """各ルート完了後にHTMLを更新"""
    
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
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    
    html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>v3スクレイパー実行結果 - ルフォンプログレから9目的地（リアルタイム更新）</title>
    <meta http-equiv="refresh" content="10">
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
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 30px;
            margin-bottom: 30px;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        .pending {
            background-color: #f8f9fa;
            color: #6c757d;
        }
        .processing {
            background-color: #cfe2ff;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
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
        .golden-route {
            background-color: #fff3cd;
            font-weight: bold;
        }
        .time-info {
            font-size: 0.85em;
            color: #6c757d;
        }
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #28a745;
            border-radius: 50%;
            margin-left: 10px;
            animation: blink 1.5s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🚇 v3スクレイパー実行中 - ルフォンプログレから9目的地
            <span class="live-indicator"></span>
        </h1>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: ''' + f"{(current_index/total_routes)*100:.1f}%" + '''">
                ''' + f"{current_index}/{total_routes} 完了" + '''
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📊 実行状況</h2>
            <p>
                <strong>出発地:</strong> ルフォンプログレ（東京都千代田区神田須田町1-20-1）<br>
                <strong>到着時刻:</strong> ''' + (arrival_time + timedelta(hours=9)).strftime('%Y年%m月%d日 %H:%M') + '''<br>
                <strong>実行開始時刻:</strong> ''' + datetime.now().strftime('%Y年%m月%d日 %H:%M:%S') + '''<br>
                <strong>進捗:</strong> ''' + f"{current_index}/{total_routes}" + ''' ルート完了
                ''' + (f"（成功: {success_count}件）" if current_index > 0 else "") + '''
            </p>
        </div>

        <table>
            <thead>
                <tr>
                    <th width="3%">#</th>
                    <th width="15%">目的地</th>
                    <th width="8%">所要時間</th>
                    <th width="12%">時刻情報</th>
                    <th width="35%">経路</th>
                    <th width="10%">ステータス</th>
                    <th width="17%">実際のURL</th>
                </tr>
            </thead>
            <tbody>
'''
    
    for i, (dest, result) in enumerate(zip(load_destinations(), results), 1):
        dest_name = destinations.get(dest['id'], dest['name'])
        
        if result['status'] == 'processing':
            row_class = 'processing'
            time_display = '<span style="color: #0066cc;">検索中...</span>'
            route_html = '<span style="color: #0066cc;">🔍 スクレイピング実行中...</span>'
            status = '処理中'
            url_display = '-'
            time_info = '-'
        elif result['status'] == 'pending':
            row_class = 'pending'
            time_display = '-'
            route_html = '<span style="color: #6c757d;">待機中</span>'
            status = '未実行'
            url_display = '-'
            time_info = '-'
        elif result['status'] == 'success':
            row_class = 'success'
            travel_time = result['travel_time']
            
            # 府中の特別処理
            if dest['id'] == 'fuchu_office' and travel_time == 69:
                row_class = 'golden-route'
                time_display = f'<span class="time-badge" style="background: #ffc107; color: #212529;">✨ {travel_time}分</span>'
            else:
                time_display = f'<span class="time-badge">{travel_time}分</span>'
            
            # 経路詳細
            route_details = result.get('route_details', [])
            if route_details:
                route_html = '<div class="route-path">'
                for j, step in enumerate(route_details):
                    if j > 0:
                        route_html += '<span class="route-arrow">→</span>'
                    route_html += f'<span class="route-step">{step}</span>'
                route_html += '</div>'
            else:
                route_html = '<span style="color: #6c757d;">詳細なし</span>'
            
            status = '成功'
            
            # URL表示（完全なURLをクリック可能なリンクとして）
            if result.get('url'):
                # URLを短縮表示（最初の50文字 + ... + 最後の30文字）
                url_str = result['url']
                if len(url_str) > 100:
                    display_text = url_str[:50] + '...' + url_str[-30:]
                else:
                    display_text = url_str
                url_display = f'<a href="{result["url"]}" target="_blank" class="url-display" style="color: #007bff; text-decoration: none; display: block;">{display_text}</a>'
            else:
                url_display = '-'
            
            # 時刻情報（到着時刻から逆算）
            departure_time = arrival_time - timedelta(minutes=travel_time)
            # JSTとして表示（UTC+9時間）
            departure_time_jst = departure_time + timedelta(hours=9)
            arrival_time_jst = arrival_time + timedelta(hours=9)
            time_info = f'<div class="time-info">{departure_time_jst.strftime("%H:%M")}発<br>↓<br>{arrival_time_jst.strftime("%H:%M")}着</div>'
        else:
            row_class = 'failure'
            time_display = '<span style="color: #dc3545;">失敗</span>'
            route_html = f'<span style="color: #dc3545;">エラー: {result.get("error", "不明")}</span>'
            status = '失敗'
            # 失敗時もURLを表示
            attempted_url = result.get('attempted_url', '')
            if attempted_url:
                url_display = f'<div class="url-display" style="color: #dc3545;">{attempted_url}</div>'
            else:
                url_display = '-'
            time_info = '-'
        
        html_content += f'''
                <tr class="{row_class}">
                    <td style="text-align: center;">{i}</td>
                    <td><strong>{dest_name}</strong></td>
                    <td>{time_display}</td>
                    <td>{time_info}</td>
                    <td>{route_html}</td>
                    <td>{status}</td>
                    <td>{url_display}</td>
                </tr>
'''
    
    html_content += '''
            </tbody>
        </table>
        
        <div style="margin-top: 40px; text-align: center; color: #6c757d;">
            <p>Generated by Google Maps Scraper v3 - Auto-updating every 10 seconds</p>
            <p>最終更新: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
        </div>
    </div>
</body>
</html>
'''
    
    with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTMLを更新しました（{current_index}/{total_routes}完了）")

def main():
    # ルフォンプログレの情報
    origin = {
        "id": "lufon_progres",
        "name": "ルフォンプログレ",
        "address": "東京都千代田区神田須田町1-20-1"
    }
    
    # 明日の10時到着（日本時間）
    # DockerコンテナはUTCなので、日本時間の10時はUTCの1時
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00
    
    # デバッグ情報
    print(f"\nタイムスタンプ確認:")
    print(f"UTC: {arrival_10am}")
    print(f"Timestamp: {int(arrival_10am.timestamp())}")
    
    # 目的地を読み込む
    destinations = load_destinations()
    
    # 結果を初期化（全て pending）
    results = [{'status': 'pending'} for _ in destinations]
    
    print("=" * 60)
    print("ルフォンプログレから9目的地へのスクレイピングテスト")
    print(f"到着時刻: {arrival_10am.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 初期HTMLを生成
    update_html_after_each_route(results, arrival_10am, 0, len(destinations))
    
    # 各目的地をテスト
    for i, dest in enumerate(destinations):
        print(f"\n[{i+1}/9] {dest['name']}へのルートを検索中...")
        
        # 現在処理中のルートを表示
        results[i] = {'status': 'processing'}
        update_html_after_each_route(results, arrival_10am, i, len(destinations))
        
        # スクレイピング実行
        start_time = time.time()
        try:
            result = scrape_route(
                origin['address'], 
                dest['address'], 
                arrival_time=arrival_10am,
                save_debug=True
            )
            
            if result:
                # 最短ルートの詳細を取得
                shortest_route = min(result['all_routes'], key=lambda r: r['total_time'])
                
                results[i] = {
                    'destination_id': dest['id'],
                    'destination_name': dest['name'],
                    'travel_time': result['travel_time'],
                    'url': result.get('url'),
                    'route_details': shortest_route.get('trains', []),
                    'status': 'success'
                }
                print(f"  ✓ 成功: {result['travel_time']}分")
            else:
                results[i] = {
                    'destination_id': dest['id'],
                    'destination_name': dest['name'],
                    'status': 'failed',
                    'error': 'ルート取得失敗',
                    'attempted_url': f"Failed to get URL from scraper"
                }
                print(f"  ✗ 失敗")
        except Exception as e:
            results[i] = {
                'destination_id': dest['id'],
                'destination_name': dest['name'],
                'status': 'failed',
                'error': str(e)
            }
            print(f"  ✗ エラー: {e}")
        
        elapsed = time.time() - start_time
        print(f"  処理時間: {elapsed:.1f}秒")
        
        # HTMLを更新
        update_html_after_each_route(results, arrival_10am, i+1, len(destinations))
        
        # 次のリクエストまで少し待機
        if i < len(destinations) - 1:
            print("  次のルートまで3秒待機...")
            time.sleep(3)
    
    # 最終結果
    success_count = sum(1 for r in results if r['status'] == 'success')
    print("\n" + "=" * 60)
    print(f"完了！ 成功: {success_count}/9")
    print(f"HTMLファイル: /app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html")

if __name__ == "__main__":
    main()