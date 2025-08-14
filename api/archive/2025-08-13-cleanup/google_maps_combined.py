#!/usr/bin/env python3
"""
Google Maps 暫定統合ソリューション
transit_finalとwalking_finalを組み合わせて使用
既存の動作確認済みコードを活用することで安定性を確保
"""
import json
import sys
import subprocess
from datetime import datetime

def call_transit_script(origin, destination, arrival_time=None):
    """transit_final.pyを呼び出して電車ルートを取得"""
    cmd = [
        "python",
        "/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_final.py",
        origin,
        destination
    ]
    
    if arrival_time:
        cmd.append(arrival_time.strftime("%Y-%m-%d %H:%M"))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"status": "error", "message": result.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Transit script timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def call_walking_script(origin, destination):
    """walking_final.pyを呼び出して徒歩ルートを取得"""
    cmd = [
        "python",
        "/app/output/japandatascience.com/timeline-mapping/api/google_maps_walking_final.py",
        origin,
        destination
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"status": "error", "message": result.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Walking script timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_combined_route(origin, destination, arrival_time=None):
    """電車優先、徒歩フォールバックの統合ルート取得"""
    
    # まず電車ルートを試す
    # print(f"電車ルートを検索中: {origin} → {destination}")  # コメントアウト
    transit_result = call_transit_script(origin, destination, arrival_time)
    
    if transit_result.get("status") == "success":
        # print("電車ルートが見つかりました")  # コメントアウト
        return transit_result
    
    # 電車ルートが失敗した場合、徒歩ルートを試す
    # print("電車ルートが見つからないため、徒歩ルートを検索します...")  # コメントアウト
    walking_result = call_walking_script(origin, destination)
    
    if walking_result.get("status") == "success":
        # print("徒歩ルートが見つかりました")  # コメントアウト
        # 徒歩ルートの形式を調整（電車ルートと互換性を持たせる）
        if "route" in walking_result:
            route = walking_result["route"]
            # route_segmentsがない場合は作成
            if "route_segments" not in walking_result:
                walking_result["route_segments"] = [{
                    "type": "walk",
                    "departure_time": route.get("departure_time", ""),
                    "duration": route.get("duration", 0),
                    "distance": route.get("distance", ""),
                    "destination": destination
                }]
        return walking_result
    
    # 両方失敗した場合
    return {
        "status": "no_route",
        "message": "ルートが見つかりませんでした",
        "transit_error": transit_result.get("message", ""),
        "walking_error": walking_result.get("message", "")
    }

def main():
    if len(sys.argv) < 3:
        print("Usage: python google_maps_combined.py <origin> <destination> [arrival_time]")
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = None
    
    if len(sys.argv) > 3:
        # 到着時刻の処理
        arrival_time = datetime.strptime(sys.argv[3], "%Y-%m-%d %H:%M")
    
    result = get_combined_route(origin, destination, arrival_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()