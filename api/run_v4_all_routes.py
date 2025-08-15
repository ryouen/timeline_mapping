#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4スクレイパーで全ルートを実行
明日10時到着で全9目的地の所要時間を取得
"""

import json
import sys
import os
from datetime import datetime, timedelta
import pytz

# v4スクレイパーをインポート
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper_v4_complete import GoogleMapsScraperV4

def load_destinations():
    """destinations.jsonを読み込み"""
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['destinations']

def generate_html_report(results, execution_time):
    """HTML形式のレポートを生成"""
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>Google Maps v4 スクレイピング結果</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin: 0 0 10px 0;
        }
        .info {
            color: #666;
            font-size: 14px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #2196F3;
        }
        .stat-label {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }
        .results {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            color: #333;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .success {
            color: #4CAF50;
            font-weight: bold;
        }
        .error {
            color: #f44336;
            font-weight: bold;
        }
        .route-type {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
        }
        .transit {
            background: #e3f2fd;
            color: #1976d2;
        }
        .walking {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        .place-id {
            font-family: monospace;
            font-size: 11px;
            color: #888;
        }
        .summary {
            margin-top: 20px;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ Google Maps v4 スクレイピング結果</h1>
        <div class="info">
            実行日時: {execution_time}<br>
            到着時刻設定: 2025年8月16日（土）10:00 JST<br>
            出発地: ルフォンプログレ（東京都千代田区神田須田町1-20-1）
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{total_count}</div>
            <div class="stat-label">総ルート数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{success_count}</div>
            <div class="stat-label">成功</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{error_count}</div>
            <div class="stat-label">失敗</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{success_rate}%</div>
            <div class="stat-label">成功率</div>
        </div>
    </div>
    
    <div class="results">
        <h2>📊 詳細結果</h2>
        <table>
            <thead>
                <tr>
                    <th>目的地</th>
                    <th>住所</th>
                    <th>状態</th>
                    <th>所要時間</th>
                    <th>ルートタイプ</th>
                    <th>料金</th>
                    <th>時刻</th>
                    <th>Place ID</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # 統計情報の計算
    total_count = len(results)
    success_count = sum(1 for r in results if r['success'])
    error_count = total_count - success_count
    success_rate = round(success_count / total_count * 100) if total_count > 0 else 0
    
    # 各結果を行として追加
    for result in results:
        if result['success']:
            status = '<span class="success">✅ 成功</span>'
            travel_time = f"{result['travel_time']}分"
            
            # ルートタイプのスタイル
            if result['route_type'] == '公共交通機関':
                route_type = '<span class="route-type transit">🚇 公共交通機関</span>'
            elif result['route_type'] == '徒歩のみ':
                route_type = '<span class="route-type walking">🚶 徒歩のみ</span>'
            else:
                route_type = f'<span class="route-type">{result["route_type"]}</span>'
            
            fare = f"{result['fare']}円" if result.get('fare') else '-'
            
            # 時刻情報
            times = []
            if result.get('departure_time'):
                times.append(f"発 {result['departure_time']}")
            if result.get('arrival_time'):
                times.append(f"着 {result['arrival_time']}")
            time_info = ' → '.join(times) if times else '-'
            
            place_id = f'<span class="place-id">{result.get("place_id", "N/A")}</span>'
        else:
            status = '<span class="error">❌ 失敗</span>'
            travel_time = '-'
            route_type = '-'
            fare = '-'
            time_info = '-'
            place_id = '-'
        
        html += f"""
                <tr>
                    <td><strong>{result['destination_name']}</strong></td>
                    <td>{result['destination']}</td>
                    <td>{status}</td>
                    <td>{travel_time}</td>
                    <td>{route_type}</td>
                    <td>{fare}</td>
                    <td>{time_info}</td>
                    <td>{place_id}</td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
    </div>
    
    <div class="summary">
        <h3>📝 サマリー</h3>
        <p>
            v4スクレイパーにより、{success_count}/{total_count}のルートの取得に成功しました（成功率{success_rate}%）。<br>
            Place IDを使用した確実なURL構築により、時刻指定と公共交通機関モードが正しく機能しています。
        </p>
    </div>
</body>
</html>
"""
    
    # プレースホルダーを置換
    html = html.format(
        execution_time=execution_time,
        total_count=total_count,
        success_count=success_count,
        error_count=error_count,
        success_rate=success_rate
    )
    
    return html

def main():
    """メイン処理"""
    print("="*60)
    print("Google Maps v4 スクレイパー - 全ルート実行")
    print("="*60)
    
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    
    # 目的地データを読み込み
    destinations = load_destinations()
    print(f"目的地数: {len(destinations)}")
    
    # 出発地
    origin_address = "東京都千代田区神田須田町1-20-1"
    
    # スクレイパー初期化
    scraper = GoogleMapsScraperV4()
    results = []
    
    try:
        scraper.setup_driver()
        
        for i, dest in enumerate(destinations, 1):
            print(f"\n[{i}/{len(destinations)}] {dest['name']}")
            print(f"  住所: {dest['address']}")
            
            # スクレイピング実行
            result = scraper.scrape_route(
                origin_address=origin_address,
                dest_address=dest['address'],
                dest_name=dest['name'],
                arrival_time=arrival_time
            )
            
            results.append(result)
            
            if result['success']:
                print(f"  ✅ 成功: {result['travel_time']}分 ({result['route_type']})")
            else:
                print(f"  ❌ 失敗: {result.get('error')}")
            
            # レート制限対策
            if i < len(destinations):
                import time
                time.sleep(3)
        
    finally:
        scraper.close()
    
    # 結果サマリー
    print("\n" + "="*60)
    print("実行結果サマリー")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"成功: {success_count}/{len(results)}")
    
    # 成功したルートの詳細
    print("\n所要時間一覧:")
    for result in results:
        if result['success']:
            print(f"  {result['destination_name']}: {result['travel_time']}分")
        else:
            print(f"  {result['destination_name']}: 失敗")
    
    # HTMLレポート生成
    execution_time = datetime.now(jst).strftime('%Y年%m月%d日 %H:%M:%S')
    html_report = generate_html_report(results, execution_time)
    
    # HTMLファイル保存
    output_path = '/app/output/japandatascience.com/timeline-mapping/api/v4_results.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"\n✅ HTMLレポート保存: v4_results.html")
    print("📊 結果確認: https://japandatascience.com/timeline-mapping/api/v4_results.html")
    
    # properties.json更新用のデータを出力
    print("\n" + "="*60)
    print("properties.json 更新用データ")
    print("="*60)
    
    for result in results:
        if result['success']:
            print(f"{result['destination_name']}: {result['travel_time']}分")

if __name__ == "__main__":
    main()