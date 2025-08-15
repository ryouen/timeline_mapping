#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ルフォンプログレから9目的地へのテスト（明日の日付・メモリ管理改善版）
"""

from google_maps_scraper_v3 import setup_driver, get_place_details, build_complete_url, wait_for_routes_to_load, extract_all_routes
from datetime import datetime, timedelta, timezone
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_destinations():
    """destinations.jsonを読み込む"""
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['destinations']

def update_html(results, arrival_time):
    """HTML結果ファイルを更新"""
    
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
    
    success_count = sum(1 for r in results if r.get('success'))
    
    html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>v3スクレイパー実行結果 - 明日の日付版 ({(arrival_time + timedelta(hours=9)).strftime('%Y-%m-%d')})</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .success {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .time-badge {{ background: #007bff; color: white; padding: 2px 8px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>🚇 v3スクレイパー実行結果 - 明日の日付版</h1>
    <p><strong>到着時刻:</strong> {(arrival_time + timedelta(hours=9)).strftime('%Y年%m月%d日 %H:%M')} JST</p>
    <p><strong>実行時刻:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
    <p><strong>成功率:</strong> {success_count}/{len(results)} ({(success_count/len(results)*100):.0f}%)</p>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>目的地</th>
                <th>所要時間</th>
                <th>詳細</th>
                <th>ステータス</th>
            </tr>
        </thead>
        <tbody>'''
    
    for i, (dest_id, result) in enumerate(results.items(), 1):
        dest_name = destinations.get(dest_id, dest_id)
        
        if result.get('success'):
            row_class = 'success'
            time_display = f'<span class="time-badge">{result["travel_time"]}分</span>'
            
            # 詳細情報の処理
            if result.get('route_details'):
                details = ', '.join(result['route_details'][:3])
            elif result.get('is_walking_only'):
                details = '徒歩のみ'
            else:
                details = '詳細なし'
                
            status = '成功'
        else:
            row_class = 'failed'
            time_display = '-'
            details = result.get('error', '不明なエラー')
            status = '失敗'
        
        html_content += f'''
            <tr class="{row_class}">
                <td>{i}</td>
                <td><strong>{dest_name}</strong></td>
                <td>{time_display}</td>
                <td>{details}</td>
                <td>{status}</td>
            </tr>'''
    
    html_content += '''
        </tbody>
    </table>
    <p style="margin-top: 20px; color: #666;">
        <small>メモリ管理改善版 - Seleniumセッションは各ルート後に適切にクリーンアップされます</small>
    </p>
</body>
</html>'''
    
    with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_tomorrow.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTMLを更新しました: v3_results_tomorrow.html")

def main():
    # 明日の10時到着（JST）
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00
    
    print("=" * 60)
    print("ルフォンプログレから9目的地へのテスト（明日の日付版）")
    print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
    print(f"タイムスタンプ: {int(arrival_10am.timestamp())}")
    print("=" * 60)
    
    origin = {
        "address": "東京都千代田区神田須田町1-20-1"
    }
    
    destinations = load_destinations()
    results = {}
    
    # 単一のドライバーインスタンスを使用
    driver = None
    try:
        driver = setup_driver()
        
        # 出発地の情報を一度だけ取得
        print("\n出発地を解決中...")
        origin_info = get_place_details(origin['address'], driver)
        
        for i, dest in enumerate(destinations, 1):
            print(f"\n[{i}/9] {dest['name']}へのルート検索...")
            
            try:
                # 目的地の情報を取得
                dest_info = get_place_details(dest['address'], driver)
                
                if not (origin_info.get('lat') and dest_info.get('lat')):
                    raise Exception("場所の解決に失敗")
                
                # URL構築とアクセス
                url = build_complete_url(origin_info, dest_info, arrival_time=arrival_10am)
                driver.get(url)
                
                # ルート読み込み待機
                if wait_for_routes_to_load(driver, timeout=15):
                    routes = extract_all_routes(driver)
                    
                    if routes:
                        shortest = min(routes, key=lambda r: r['total_time'])
                        
                        # 詳細情報の処理
                        route_details = []
                        if shortest.get('trains'):
                            route_details = shortest['trains']
                        else:
                            raw_text = shortest.get('raw_text', '')
                            if '徒歩' in raw_text and '駅' not in raw_text:
                                route_details = ['徒歩のみ']
                        
                        results[dest['id']] = {
                            'success': True,
                            'travel_time': shortest['total_time'],
                            'route_details': route_details,
                            'is_walking_only': '徒歩' in raw_text and '駅' not in raw_text if 'raw_text' in shortest else False
                        }
                        print(f"  ✓ 成功: {shortest['total_time']}分")
                    else:
                        results[dest['id']] = {
                            'success': False,
                            'error': 'ルート取得失敗'
                        }
                        print(f"  ✗ ルート取得失敗")
                else:
                    results[dest['id']] = {
                        'success': False,
                        'error': 'タイムアウト'
                    }
                    print(f"  ✗ タイムアウト")
                    
            except Exception as e:
                results[dest['id']] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"  ✗ エラー: {e}")
            
            # 次のリクエストまで少し待機
            if i < len(destinations):
                time.sleep(2)
    
    finally:
        # ドライバーを確実に終了
        if driver:
            try:
                driver.quit()
                print("\n✅ Seleniumセッションを正常に終了")
            except:
                pass
    
    # HTML更新
    update_html(results, arrival_10am)
    
    # サマリー
    success_count = sum(1 for r in results.values() if r.get('success'))
    print(f"\n完了！ 成功: {success_count}/9")
    print(f"結果: https://japandatascience.com/timeline-mapping/api/v3_results_tomorrow.html")

if __name__ == "__main__":
    main()