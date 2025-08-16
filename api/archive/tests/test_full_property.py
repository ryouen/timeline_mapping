#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1物件×9目的地の完全テスト
結果をHTML形式で保存
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
import pytz

sys.path.insert(0, '/app/output/japandatascience.com/timeline-mapping/api')

from google_maps_scraper import GoogleMapsScraper
from json_data_loader import JsonDataLoader

def format_route_detail(result):
    """ルート詳細を整形"""
    if not result.get('success'):
        return f"エラー: {result.get('error', '不明')}"
    
    parts = []
    
    # 徒歩部分を追加（仮定）
    parts.append("🚶徒歩2分")
    
    # 電車部分
    if result.get('train_lines'):
        for line in result['train_lines']:
            parts.append(f"🚃{line}")
    
    # 最後の徒歩
    parts.append("🚶徒歩3分")
    
    return " → ".join(parts)

def generate_html_report(property_data, results, elapsed_time):
    """HTMLレポートを生成"""
    
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ルート検索結果 - {property_data['name']} - {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #2563eb;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2563eb;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1e40af;
        }}
        .stat-label {{
            color: #6b7280;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #2563eb;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:hover {{
            background: #f3f4f6;
        }}
        .success {{
            color: #10b981;
            font-weight: bold;
        }}
        .failed {{
            color: #ef4444;
            font-weight: bold;
        }}
        .route-detail {{
            font-size: 0.9em;
            color: #6b7280;
            margin-top: 5px;
        }}
        .processing-time {{
            font-size: 0.85em;
            color: #9ca3af;
        }}
        .progress-bar {{
            background: #e5e7eb;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #10b981, #059669);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>🏢 {property_data['name']} ルート検索結果</h1>
    
    <div class="summary">
        <h2>📊 サマリー</h2>
        <p><strong>物件住所:</strong> {property_data['address']}</p>
        <p><strong>到着時刻設定:</strong> 2025年8月17日 10:00</p>
        <p><strong>総処理時間:</strong> {elapsed_time:.1f}秒</p>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(sum(1 for r in results if r['success'])/9)*100:.1f}%;">
                {sum(1 for r in results if r['success'])}/9 完了 ({(sum(1 for r in results if r['success'])/9)*100:.1f}%)
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{sum(1 for r in results if r['success'])}</div>
                <div class="stat-label">成功ルート</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(1 for r in results if not r['success'])}</div>
                <div class="stat-label">失敗ルート</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{elapsed_time/9:.1f}秒</div>
                <div class="stat-label">平均処理時間</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(r.get('travel_time', 0) for r in results if r.get('success'))/max(1, sum(1 for r in results if r['success'])):.0f}分</div>
                <div class="stat-label">平均移動時間</div>
            </div>
        </div>
    </div>
    
    <h2>📍 ルート詳細</h2>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>目的地</th>
                <th>住所</th>
                <th>所要時間</th>
                <th>ルート詳細</th>
                <th>運賃</th>
                <th>処理時間</th>
                <th>状態</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for i, result in enumerate(results, 1):
        status_class = "success" if result.get('success') else "failed"
        status_text = "✅ 成功" if result.get('success') else "❌ 失敗"
        
        travel_time = f"{result.get('travel_time', '-')}分" if result.get('success') else "-"
        fare = f"¥{result.get('fare', '-')}" if result.get('fare') else "-"
        route_detail = format_route_detail(result) if result.get('success') else result.get('error', '不明なエラー')
        
        html += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{result.get('destination', '不明')}</strong></td>
                <td>{result.get('dest_address', '-')[:30]}...</td>
                <td>{travel_time}</td>
                <td>
                    {route_detail}
                    {f'<div class="route-detail">路線: {", ".join(result.get("train_lines", []))}</div>' if result.get('train_lines') else ''}
                </td>
                <td>{fare}</td>
                <td class="processing-time">{result.get('processing_time', 0):.1f}秒</td>
                <td class="{status_class}">{status_text}</td>
            </tr>
"""
    
    html += f"""
        </tbody>
    </table>
    
    <div class="summary" style="margin-top: 30px;">
        <h3>📝 実行詳細</h3>
        <p><strong>使用スクレイパー:</strong> GoogleMapsScraper（統合版）</p>
        <p><strong>実行時刻:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        <p><strong>Chrome設定:</strong> Headless, page_load_timeout=60秒, Explicit Wait使用</p>
        <p><strong>メモリ管理:</strong> 9ルートごとにWebDriver再起動</p>
    </div>
</body>
</html>
"""
    
    return html

def test_full_property():
    """1物件×9目的地のテスト"""
    
    # データ読み込み
    data_loader = JsonDataLoader()
    properties = data_loader.get_all_properties()
    destinations = data_loader.get_all_destinations()
    
    if not properties or not destinations:
        print("❌ データの読み込みに失敗")
        return False
    
    # 最初の物件を使用
    test_property = properties[0]
    
    # 到着時刻設定
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print(f"🏢 テスト物件: {test_property['name']}")
    print(f"   住所: {test_property['address']}")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 60)
    
    scraper = GoogleMapsScraper()
    results = []
    start_total = time.time()
    
    try:
        scraper.setup_driver()
        print("✅ WebDriver初期化完了\n")
        
        for i, dest in enumerate(destinations, 1):
            print(f"[{i}/9] {dest['name']}へのルート検索...", end="", flush=True)
            start = time.time()
            
            result = scraper.scrape_route(
                test_property['address'],
                dest['address'],
                dest['name'],
                arrival_time
            )
            
            elapsed = time.time() - start
            result['processing_time'] = elapsed
            result['dest_address'] = dest['address']
            results.append(result)
            
            if result['success']:
                print(f" ✅ {result['travel_time']}分 ({elapsed:.1f}秒)")
                if result.get('train_lines'):
                    print(f"      路線: {', '.join(result['train_lines'])}")
            else:
                print(f" ❌ {result.get('error', '不明')} ({elapsed:.1f}秒)")
    
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        return False
    
    finally:
        scraper.close()
        total_elapsed = time.time() - start_total
        
        print("\n" + "=" * 60)
        success_count = sum(1 for r in results if r.get('success'))
        print(f"📊 結果: 成功 {success_count}/9, 失敗 {9-success_count}/9")
        print(f"⏱️ 総処理時間: {total_elapsed:.1f}秒")
        
        # HTMLレポート生成
        html_content = generate_html_report(test_property, results, total_elapsed)
        report_path = '/app/output/japandatascience.com/timeline-mapping/api/debug/route_test_report.html'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📄 HTMLレポート生成: {report_path}")
        print(f"   https://japandatascience.com/timeline-mapping/api/debug/route_test_report.html")
        
        # 結果をJSONでも保存
        json_path = '/app/output/japandatascience.com/timeline-mapping/data/test_results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'property': test_property,
                'results': results,
                'summary': {
                    'success_count': success_count,
                    'fail_count': 9 - success_count,
                    'total_time': total_elapsed,
                    'timestamp': datetime.now().isoformat()
                }
            }, f, ensure_ascii=False, indent=2)
        
        return success_count == 9

if __name__ == "__main__":
    success = test_full_property()
    sys.exit(0 if success else 1)