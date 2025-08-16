#!/usr/bin/env python3
"""
包括的ルートテスト
ルフォンプログレ神田プレミアから8つの目的地へのルートを検証
"""
import json
import subprocess
import time
from datetime import datetime

def test_route(origin, destination_name, destination_address):
    """単一ルートのテスト"""
    cmd = [
        "python",
        "/app/output/japandatascience.com/timeline-mapping/api/google_maps_combined.py",
        origin,
        destination_address if destination_address else destination_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            # デバッグ用に出力を確認
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return {"status": "error", "message": f"JSON decode error: {e}\nOutput: {result.stdout[:200]}"}
        else:
            return {"status": "error", "message": f"Script error: {result.stderr}"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Script timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def format_route_result(destination_name, result):
    """ルート結果を読みやすい形式にフォーマット"""
    print(f"\n{'='*60}")
    print(f"目的地: {destination_name}")
    print(f"{'='*60}")
    
    if result.get("status") == "success":
        route = result.get("route", {})
        route_type = "徒歩のみ" if route.get("details", {}).get("route_type") == "walking_only" else "電車利用"
        
        print(f"ルートタイプ: {route_type}")
        print(f"総所要時間: {route.get('total_time', 'N/A')}分")
        
        details = route.get("details", {})
        if details.get("trains"):
            print(f"\n電車ルート詳細:")
            print(f"  駅まで徒歩: {details.get('walk_to_station', 0)}分")
            print(f"  利用駅: {details.get('station_used', 'N/A')}")
            
            for i, train in enumerate(details.get("trains", [])):
                print(f"\n  電車 {i+1}:")
                print(f"    路線: {train.get('line', 'N/A')}")
                print(f"    区間: {train.get('from', 'N/A')} → {train.get('to', 'N/A')}")
                print(f"    所要時間: {train.get('time', 'N/A')}分")
                if train.get('wait_time', 0) > 0:
                    print(f"    待ち時間: {train.get('wait_time', 0)}分")
            
            print(f"\n  駅から徒歩: {details.get('walk_from_station', 0)}分")
        
        elif details.get("route_type") == "walking_only":
            print(f"  徒歩距離: {details.get('distance_meters', 'N/A')}m")
            
    else:
        print(f"エラー: {result.get('message', 'Unknown error')}")

def main():
    # 出発地
    origin_name = "ルフォンプログレ神田プレミア"
    origin_address = "千代田区神田須田町1-20-1"
    
    # 目的地リスト
    destinations = [
        ("Shizenkan University", "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階"),
        ("東京アメリカンクラブ", "東京都中央区日本橋室町３丁目２−１"),
        ("axle御茶ノ水", "東京都千代田区神田小川町３丁目２８−５"),
        ("Yawara", "東京都渋谷区神宮前１丁目８−１０ Ｔｈｅ Ｉｃｅ Ｃｕｂｅｓ 9階"),
        ("東京駅", ""),
        ("羽田空港", ""),
        ("神谷町(EE)", "東京都港区虎ノ門４丁目２−６ 第二扇屋ビル 1F"),
        ("早稲田大学", "東京都新宿区西早稲田１丁目６ 11号館")
    ]
    
    print(f"出発地: {origin_name}")
    print(f"住所: {origin_address}")
    print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} テスト開始")
    
    # 結果を保存
    results = []
    
    for dest_name, dest_address in destinations:
        print(f"\n{dest_name}へのルートを検索中...")
        result = test_route(origin_address, dest_name, dest_address)
        format_route_result(dest_name, result)
        
        results.append({
            "destination": dest_name,
            "result": result
        })
        
        # API負荷軽減のため待機
        time.sleep(3)
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/app/output/japandatascience.com/timeline-mapping/data/comprehensive_test_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "origin": origin_name,
            "origin_address": origin_address,
            "test_time": timestamp,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n\nテスト結果を保存しました: {output_file}")

if __name__ == "__main__":
    main()