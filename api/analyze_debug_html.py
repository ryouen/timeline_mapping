#!/usr/bin/env python3
"""
デバッグHTMLファイルから新しい抽出パターンを探索するスクリプト
"""

import re
import json
from pathlib import Path

def analyze_html(file_path):
    """HTMLファイルから様々なパターンを探索"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"\n=== Analyzing {file_path} ===\n")
    
    # 1. 時間パターンの探索
    print("1. 時間パターン（分）:")
    time_patterns = [
        r'(\d+)\s*時間\s*(\d+)\s*分',
        r'（\s*(\d+)\s*分\s*）',
        r'>(\d+)\s*分<',
        r'"(\d+)\s*分"',
        r'(\d+)\s*分\s*（'
    ]
    
    for pattern in time_patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"  Pattern '{pattern}': {matches[:5]}...")
    
    # 2. 駅名パターンの探索
    print("\n2. 駅名パターン:")
    station_keywords = ['神田', '小川町', '新宿', '笹塚', '府中', '分倍河原', '中河原']
    
    for keyword in station_keywords:
        # 駅名の前後のコンテキストを探索
        pattern = f'.{{0,50}}{keyword}.{{0,50}}'
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\n  {keyword}:")
            for match in matches[:3]:
                # スクリプトタグやスタイルタグを除外
                if 'script' not in match and 'style' not in match:
                    print(f"    {match}")
    
    # 3. 路線名パターンの探索
    print("\n3. 路線名パターン:")
    line_keywords = ['中央線', '新宿線', '京王線', '京王新線']
    
    for keyword in line_keywords:
        count = html_content.count(keyword)
        if count > 0:
            print(f"  {keyword}: {count}回出現")
            # 最初の出現箇所のコンテキストを表示
            idx = html_content.find(keyword)
            if idx != -1:
                context = html_content[max(0, idx-30):idx+30]
                print(f"    Context: ...{context}...")
    
    # 4. ルート情報の可能性がある構造を探索
    print("\n4. 配列構造の探索:")
    
    # 時刻表パターン (例: "9:08", "9:40")
    time_table_pattern = r'"(\d+:\d+)"'
    time_matches = re.findall(time_table_pattern, html_content)
    if time_matches:
        print(f"  時刻表: {time_matches[:10]}...")
    
    # 駅コードパターン (例: "JC02", "KO01")
    station_code_pattern = r'"([A-Z]{1,2}\d{2})"'
    code_matches = re.findall(station_code_pattern, html_content)
    if code_matches:
        print(f"  駅コード: {code_matches[:10]}...")
    
    # 5. データ構造の探索
    print("\n5. JSON-like構造の探索:")
    
    # 配列構造を探す
    array_pattern = r'\[\[.*?\]\]'
    arrays = re.findall(array_pattern, html_content[:10000])  # 最初の10KB
    
    for i, array in enumerate(arrays[:5]):
        if any(station in array for station in station_keywords):
            print(f"\n  Array {i+1} (contains station names):")
            print(f"    {array[:200]}...")
    
    # 6. 新しいルート要素の探索
    print("\n6. ルート要素の探索:")
    
    # Hk4XGb class（以前見つけたルート要素のクラス）
    hk4xgb_pattern = r'class="Hk4XGb"[^>]*>(.*?)</div>'
    hk4xgb_matches = re.findall(hk4xgb_pattern, html_content, re.DOTALL)
    
    if hk4xgb_matches:
        print(f"  Found {len(hk4xgb_matches)} Hk4XGb elements")
        for i, match in enumerate(hk4xgb_matches[:3]):
            if len(match) < 500:  # 短いものだけ表示
                print(f"\n  Element {i+1}:")
                print(f"    {match}")
    
    # 7. 新しいパターン：時刻付きの駅情報
    print("\n7. 時刻付き駅情報の探索:")
    
    # 駅名と時刻のパターン
    station_time_pattern = r'\["([^"]+駅)","[^"]*",(?:null,)*\[\d+,"Asia/Tokyo","(\d+:\d+)"'
    station_matches = re.findall(station_time_pattern, html_content)
    
    if station_matches:
        print(f"  Found {len(station_matches)} stations with times:")
        for station, time in station_matches[:10]:
            print(f"    {station} - {time}")
    
    # 8. 乗車時間パターンの探索
    print("\n8. 乗車時間パターンの探索:")
    
    # [720,"12 分",720] のようなパターン
    duration_pattern = r'\[(\d+),"(\d+) 分",\d+\]'
    duration_matches = re.findall(duration_pattern, html_content)
    
    if duration_matches:
        print(f"  Found {len(duration_matches)} duration entries:")
        for seconds, minutes in duration_matches[:10]:
            print(f"    {minutes}分 ({seconds}秒)")
    
    # 9. 路線情報と組み合わせたパターン
    print("\n9. 路線情報の詳細パターン:")
    
    # 路線名と色コードのパターン
    line_pattern = r'\[5,\["([^"]+)",1,"(#[a-f0-9]+)","#[a-f0-9]+"\]\]'
    line_matches = re.findall(line_pattern, html_content)
    
    if line_matches:
        print(f"  Found {len(line_matches)} line entries:")
        for line_name, color in line_matches[:10]:
            print(f"    {line_name} (色: {color})")

def extract_route_info(html_content):
    """HTMLから具体的なルート情報を抽出"""
    
    print("\n=== ルート情報の抽出 ===")
    
    # 総所要時間を探す
    total_time_pattern = r'\[(\d+),"1 時間 (\d+) 分",\d+\]'
    total_match = re.search(total_time_pattern, html_content)
    if total_match:
        total_seconds = int(total_match.group(1))
        additional_minutes = int(total_match.group(2))
        total_minutes = 60 + additional_minutes
        print(f"\n総所要時間: {total_minutes}分 ({total_seconds}秒)")
    
    # 最初の徒歩時間
    walk_pattern = r'\[2,null,null,\[(\d+),"(\d+) 分",\d+\].*?徒歩'
    walk_match = re.search(walk_pattern, html_content)
    if walk_match:
        walk_seconds = int(walk_match.group(1))
        walk_minutes = int(walk_match.group(2))
        print(f"最初の徒歩: {walk_minutes}分")
    
    # 電車の経路を抽出
    print("\n電車経路:")
    
    # パターン1: 小川町→笹塚（新宿線）
    if '小川町駅' in html_content and '笹塚駅' in html_content:
        print("  1. 地下鉄新宿線: 小川町→笹塚")
    
    # パターン2: 笹塚での乗り換え（京王新線）
    if '京王新線' in html_content:
        print("  2. 京王新線: 笹塚駅（直通）")
    
    # パターン3: 府中への特急
    if '京王線' in html_content and '特急' in html_content and '府中駅' in html_content:
        print("  3. 京王線（特急）: 笹塚→府中")
    
    # パターン4: 府中→中河原（各停）
    if '府中駅' in html_content and '中河原駅' in html_content and '各停' in html_content:
        print("  4. 京王線（各停）: 府中→中河原")

def main():
    # デバッグファイルのパス
    debug_file = "/app/output/japandatascience.com/timeline-mapping/api/debug/page_source_東京都千代田区神田須-東京都府中市住吉町5-20250814_082239.html"
    
    if Path(debug_file).exists():
        analyze_html(debug_file)
        
        # ルート情報も抽出
        with open(debug_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        extract_route_info(html_content)
    else:
        print(f"Debug file not found: {debug_file}")
    
    # ゴールデンルートの表示
    golden_file = "/app/output/japandatascience.com/timeline-mapping/api/golden_routes.json"
    if Path(golden_file).exists():
        with open(golden_file, 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
        
        print("\n\n=== Golden Route Information ===")
        for route in golden_data['golden_routes']:
            print(f"\n{route['search_type'].upper()} at {route['search_time']}:")
            print(f"  Total time: {route['route_info']['total_time']} minutes")
            print(f"  First station: {route['route_info']['station_used']}")
            print(f"  Number of trains: {len(route['route_info']['trains'])}")

if __name__ == "__main__":
    main()