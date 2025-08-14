#!/usr/bin/env python3
"""
大規模ルートテスト
3物件×8目的地の組み合わせでGoogle Mapsスクレイピングをテスト
"""
import json
import time
import subprocess
from datetime import datetime
import os

def load_test_data():
    """テスト用のデータを読み込み"""
    # properties.jsonから物件情報を取得
    with open('/app/output/japandatascience.com/timeline-mapping/data/properties.json', 'r', encoding='utf-8') as f:
        properties_data = json.load(f)
    
    # destinations.jsonから目的地情報を取得
    with open('/app/output/japandatascience.com/timeline-mapping/data/destinations.json', 'r', encoding='utf-8') as f:
        destinations_data = json.load(f)
    
    # テスト用に最初の3物件を選択
    test_properties = properties_data['properties'][:3]
    
    # 全8目的地を使用
    test_destinations = destinations_data['destinations']
    
    return test_properties, test_destinations

def run_route_test(property_info, destination_info):
    """単一のルートテストを実行"""
    property_name = property_info['name']
    property_address = "東京都" + property_info['address']
    
    dest_name = destination_info['name']
    dest_address = destination_info['address']
    
    print(f"\n{'='*60}")
    print(f"テスト: {property_name} → {dest_name}")
    print(f"住所: {property_address} → {dest_address}")
    
    try:
        # スクレイピング実行
        cmd = [
            'python',
            '/app/output/japandatascience.com/timeline-mapping/api/google_maps_unified.py',
            property_address,
            dest_address
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            try:
                route_data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "property": property_name,
                    "destination": dest_name,
                    "data": route_data
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "property": property_name,
                    "destination": dest_name,
                    "error": "JSONパースエラー",
                    "output": result.stdout
                }
        else:
            return {
                "status": "error",
                "property": property_name,
                "destination": dest_name,
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "property": property_name,
            "destination": dest_name,
            "error": "タイムアウト"
        }
    except Exception as e:
        return {
            "status": "error",
            "property": property_name,
            "destination": dest_name,
            "error": str(e)
        }

def analyze_results(results):
    """結果を分析してパターンを抽出"""
    analysis = {
        "total_tests": len(results),
        "success_count": 0,
        "error_count": 0,
        "route_types": {
            "transit": 0,
            "walking": 0
        },
        "transfer_patterns": [],
        "error_patterns": {},
        "time_statistics": {
            "min_total_time": float('inf'),
            "max_total_time": 0,
            "avg_total_time": 0
        }
    }
    
    total_time_sum = 0
    success_with_time = 0
    
    for result in results:
        if result["status"] == "success":
            analysis["success_count"] += 1
            
            route_data = result["data"]
            
            # ルートタイプの集計
            if route_data.get("search_info", {}).get("type") == "walking":
                analysis["route_types"]["walking"] += 1
            else:
                analysis["route_types"]["transit"] += 1
            
            # 時間統計
            if "route" in route_data and route_data["route"]:
                route = route_data["route"][0]
                if "total_time" in route:
                    total_time = route["total_time"]
                    analysis["time_statistics"]["min_total_time"] = min(
                        analysis["time_statistics"]["min_total_time"], 
                        total_time
                    )
                    analysis["time_statistics"]["max_total_time"] = max(
                        analysis["time_statistics"]["max_total_time"], 
                        total_time
                    )
                    total_time_sum += total_time
                    success_with_time += 1
                
                # 乗り換えパターンの分析
                if "trains" in route and len(route["trains"]) > 1:
                    transfer_count = len(route["trains"]) - 1
                    transfer_info = {
                        "property": result["property"],
                        "destination": result["destination"],
                        "transfer_count": transfer_count,
                        "transfer_times": []
                    }
                    
                    # 乗り換え時間を抽出
                    for i in range(len(route["trains"]) - 1):
                        if i < len(route.get("transfer_walks", [])):
                            transfer_walk = route["transfer_walks"][i]
                            transfer_info["transfer_times"].append({
                                "walk_time": transfer_walk.get("duration", 0),
                                "wait_time": route["trains"][i+1].get("wait_time", 0)
                            })
                    
                    analysis["transfer_patterns"].append(transfer_info)
        
        else:
            analysis["error_count"] += 1
            error_msg = result.get("error", "不明なエラー")
            if error_msg not in analysis["error_patterns"]:
                analysis["error_patterns"][error_msg] = []
            analysis["error_patterns"][error_msg].append(
                f"{result['property']} → {result['destination']}"
            )
    
    # 平均時間の計算
    if success_with_time > 0:
        analysis["time_statistics"]["avg_total_time"] = round(
            total_time_sum / success_with_time, 1
        )
    
    return analysis

def main():
    """メイン処理"""
    print("大規模ルートテストを開始します...")
    
    # テストデータの読み込み
    properties, destinations = load_test_data()
    
    print(f"テスト対象: {len(properties)}物件 × {len(destinations)}目的地 = {len(properties) * len(destinations)}ルート")
    
    # 結果を格納するリスト
    all_results = []
    
    # 各組み合わせでテスト実行
    for prop in properties:
        for dest in destinations:
            result = run_route_test(prop, dest)
            all_results.append(result)
            
            # API制限を考慮して待機
            time.sleep(2)
    
    # 結果の分析
    analysis = analyze_results(all_results)
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 詳細結果
    detail_file = f"/app/output/japandatascience.com/timeline-mapping/data/bulk_test_results_{timestamp}.json"
    with open(detail_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": timestamp,
            "results": all_results,
            "analysis": analysis
        }, f, ensure_ascii=False, indent=2)
    
    # サマリーレポート
    summary_file = f"/app/output/japandatascience.com/timeline-mapping/data/bulk_test_summary_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"大規模ルートテスト結果サマリー\n")
        f.write(f"実施日時: {timestamp}\n")
        f.write(f"{'='*60}\n\n")
        
        f.write(f"【テスト結果】\n")
        f.write(f"総テスト数: {analysis['total_tests']}\n")
        f.write(f"成功: {analysis['success_count']} ({analysis['success_count']/analysis['total_tests']*100:.1f}%)\n")
        f.write(f"失敗: {analysis['error_count']} ({analysis['error_count']/analysis['total_tests']*100:.1f}%)\n\n")
        
        f.write(f"【ルートタイプ】\n")
        f.write(f"電車ルート: {analysis['route_types']['transit']}\n")
        f.write(f"徒歩ルート: {analysis['route_types']['walking']}\n\n")
        
        f.write(f"【時間統計】\n")
        f.write(f"最短時間: {analysis['time_statistics']['min_total_time']}分\n")
        f.write(f"最長時間: {analysis['time_statistics']['max_total_time']}分\n")
        f.write(f"平均時間: {analysis['time_statistics']['avg_total_time']}分\n\n")
        
        if analysis['transfer_patterns']:
            f.write(f"【乗り換えパターン】\n")
            for pattern in analysis['transfer_patterns'][:5]:  # 最初の5件のみ表示
                f.write(f"- {pattern['property']} → {pattern['destination']}: ")
                f.write(f"{pattern['transfer_count']}回乗り換え\n")
                for i, transfer in enumerate(pattern['transfer_times']):
                    f.write(f"  乗り換え{i+1}: 徒歩{transfer['walk_time']}分 + 待ち{transfer['wait_time']}分\n")
        
        if analysis['error_patterns']:
            f.write(f"\n【エラーパターン】\n")
            for error, routes in analysis['error_patterns'].items():
                f.write(f"- {error}: {len(routes)}件\n")
                for route in routes[:3]:  # 最初の3件のみ表示
                    f.write(f"  - {route}\n")
    
    print(f"\n結果を保存しました:")
    print(f"- 詳細: {detail_file}")
    print(f"- サマリー: {summary_file}")
    
    # コンソールにもサマリーを表示
    print(f"\n{'='*60}")
    print(f"テスト完了: 成功 {analysis['success_count']}/{analysis['total_tests']} ({analysis['success_count']/analysis['total_tests']*100:.1f}%)")
    print(f"電車: {analysis['route_types']['transit']}, 徒歩: {analysis['route_types']['walking']}")
    print(f"平均所要時間: {analysis['time_statistics']['avg_total_time']}分")

if __name__ == "__main__":
    main()