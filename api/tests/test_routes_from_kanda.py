#!/usr/bin/env python3
"""
ルフォンプログレ神田プレミアから8つの目的地へのルートテスト
"""
import subprocess
import json
import sys
from datetime import datetime

# テスト対象
ORIGIN = "千代田区神田須田町1-20-1"
DESTINATIONS = [
    ("Shizenkan University", "東京都中央区日本橋２丁目５−１"),
    ("東京アメリカンクラブ", "東京都中央区日本橋室町３丁目２−１"),
    ("axle御茶ノ水", "東京都千代田区神田小川町３丁目２８−５"),
    ("Yawara", "東京都渋谷区神宮前１丁目８−１０"),
    ("東京駅", "東京駅"),
    ("羽田空港", "羽田空港"),
    ("神谷町(EE)", "東京都港区虎ノ門４丁目２−６"),
    ("早稲田大学", "東京都新宿区西早稲田１丁目６")
]

def test_route(origin, destination_name, destination_address):
    """単一ルートのテスト"""
    print(f"\n{'='*60}")
    print(f"テスト: {origin} → {destination_name}")
    print(f"住所: {destination_address}")
    print(f"{'='*60}")
    
    cmd = [
        "python",
        "/app/output/japandatascience.com/timeline-mapping/api/google_maps_combined.py",
        origin,
        destination_address
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # print(f"標準出力: {result.stdout[:200]}...")  # デバッグ用
            data = json.loads(result.stdout)
            return analyze_result(destination_name, destination_address, data)
        else:
            print(f"エラー: {result.stderr}")
            # print(f"標準出力: {result.stdout}")  # デバッグ用
            return {
                "destination": destination_name,
                "address": destination_address,
                "status": "error",
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        print("タイムアウト")
        return {
            "destination": destination_name,
            "address": destination_address,
            "status": "timeout"
        }
    except Exception as e:
        print(f"例外: {str(e)}")
        return {
            "destination": destination_name,
            "address": destination_address,
            "status": "exception",
            "error": str(e)
        }

def analyze_result(destination_name, destination_address, data):
    """結果の分析"""
    result = {
        "destination": destination_name,
        "address": destination_address,
        "status": data.get("status", "unknown")
    }
    
    if data.get("status") == "success":
        # ルート情報の取得
        route = data.get("route", {})
        
        # 総所要時間
        total_duration = route.get("total_time", route.get("duration", 0))
        result["total_duration_min"] = total_duration
        
        # 詳細情報の取得
        details = route.get("details", {})
        
        # ルートタイプの判定
        if "trains" in details or "train" in str(details):
            result["route_type"] = "電車"
        elif "walk_time" in route or ("trains" not in details and total_duration > 0):
            result["route_type"] = "徒歩"
        else:
            result["route_type"] = "不明"
        
        # セグメント詳細（新しい形式に対応）
        result["segments"] = []
        
        # 駅までの徒歩
        if details.get("walk_to_station"):
            result["segments"].append({
                "type": "walk",
                "duration": details["walk_to_station"],
                "to": details.get("station_used", "駅")
            })
        
        # 電車移動
        if "trains" in details:
            for train in details["trains"]:
                result["segments"].append({
                    "type": "train",
                    "duration": train.get("time", 0),
                    "line": train.get("line", ""),
                    "from": train.get("from", ""),
                    "to": train.get("to", "")
                })
        
        # 駅からの徒歩
        if details.get("walk_from_station"):
            result["segments"].append({
                "type": "walk",
                "duration": details["walk_from_station"],
                "from": "駅"
            })
        
        # 徒歩のみの場合
        if result["route_type"] == "徒歩" and route.get("walk_time"):
            result["segments"] = [{
                "type": "walk",
                "duration": route["walk_time"],
                "distance": route.get("distance", "")
            }]
        
        # 詳細表示
        print(f"\n成功: {result['route_type']}ルート")
        print(f"総所要時間: {total_duration}分")
        print("\nルート詳細:")
        for i, seg in enumerate(result["segments"], 1):
            if seg["type"] == "train":
                print(f"  {i}. 電車: {seg['line']} ({seg['from']} → {seg['to']}) - {seg['duration']}分")
            elif seg["type"] == "walk":
                if seg.get("to"):
                    print(f"  {i}. 徒歩: {seg['to']}まで - {seg['duration']}分")
                elif seg.get("from"):
                    print(f"  {i}. 徒歩: {seg['from']}から目的地まで - {seg['duration']}分")
                else:
                    print(f"  {i}. 徒歩: {seg.get('distance', '')} - {seg['duration']}分")
    
    else:
        print(f"\nステータス: {result['status']}")
        if "message" in data:
            print(f"メッセージ: {data['message']}")
            result["message"] = data["message"]
    
    return result

def format_results_table(results):
    """結果を表形式で表示"""
    print("\n\n" + "="*80)
    print("テスト結果サマリー")
    print("="*80)
    print(f"{'目的地':<20} {'ステータス':<10} {'ルート種別':<10} {'所要時間':<10} {'備考':<30}")
    print("-"*80)
    
    for r in results:
        destination = r["destination"][:20]
        status = r.get("status", "unknown")
        route_type = r.get("route_type", "-")
        duration = f"{r.get('total_duration_min', '-')}分" if r.get('total_duration_min') else "-"
        note = r.get("message", r.get("error", ""))[:30] if status != "success" else ""
        
        print(f"{destination:<20} {status:<10} {route_type:<10} {duration:<10} {note:<30}")
    
    print("-"*80)
    
    # 成功率の計算
    success_count = sum(1 for r in results if r.get("status") == "success")
    total_count = len(results)
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

def main():
    results = []
    
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"出発地: {ORIGIN}")
    
    for dest_name, dest_address in DESTINATIONS:
        result = test_route(ORIGIN, dest_name, dest_address)
        results.append(result)
    
    format_results_table(results)
    
    print(f"\n終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()