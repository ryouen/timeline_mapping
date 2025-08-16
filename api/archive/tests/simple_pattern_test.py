#!/usr/bin/env python3
"""
シンプルパターンテスト
基本的な3パターンのルートをテスト
"""
import json
import subprocess
import time
from datetime import datetime

def test_route(from_addr, to_addr, test_name):
    """ルートをテストして詳細情報を表示"""
    print(f"\n{'='*60}")
    print(f"テスト: {test_name}")
    
    try:
        # 通常版で実行
        cmd = [
            'python',
            '/app/output/japandatascience.com/timeline-mapping/api/google_maps_unified.py',
            from_addr,
            to_addr
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            if data["status"] == "success":
                print("✅ 成功")
                
                # ルート情報の表示
                if data.get("route") and len(data["route"]) > 0:
                    route = data["route"][0]
                    
                    print(f"\n【ルート詳細】")
                    print(f"総時間: {route.get('total_time', '不明')}分")
                    
                    if route.get("walk_to_station"):
                        print(f"駅まで徒歩: {route['walk_to_station']}分")
                    
                    if "trains" in route:
                        print(f"電車区間: {len(route['trains'])}本")
                        for i, train in enumerate(route['trains']):
                            print(f"  電車{i+1}: {train.get('line', '不明')} ({train.get('duration', '不明')}分)")
                            if train.get("wait_time"):
                                print(f"    待ち時間: {train['wait_time']}分")
                    
                    if "transfer_walks" in route:
                        print(f"乗り換え徒歩: {len(route['transfer_walks'])}回")
                        for i, tw in enumerate(route['transfer_walks']):
                            print(f"  乗り換え{i+1}: {tw.get('duration', '不明')}分")
                    
                    if route.get("walk_from_station"):
                        print(f"駅から徒歩: {route['walk_from_station']}分")
                
                elif data.get("search_info", {}).get("type") == "walking":
                    # 徒歩のみの場合
                    print(f"\n【徒歩ルート】")
                    print(f"総時間: {data['route'][0]['total_time']}分")
                    print(f"距離: {data['route'][0].get('distance', '不明')}")
                
                return data
            else:
                print(f"❌ エラー: {data.get('message', '不明')}")
                return None
                
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return None

def main():
    """メイン処理"""
    print("シンプルパターンテストを開始します...")
    
    # 3つの基本パターン
    test_cases = [
        {
            "name": "パターン1: 乗り換えなし（神田→日本橋）",
            "from": "東京都千代田区神田",
            "to": "東京都中央区日本橋"
        },
        {
            "name": "パターン2: 乗り換えあり（神田→神谷町）",
            "from": "東京都千代田区神田",
            "to": "東京都港区神谷町"
        },
        {
            "name": "パターン3: 徒歩のみ（神田→axle御茶ノ水）",
            "from": "東京都千代田区神田須田町1-20-1",
            "to": "東京都千代田区神田小川町３丁目２８−５"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        result = test_route(
            test_case["from"],
            test_case["to"],
            test_case["name"]
        )
        
        if result:
            results.append({
                "test_name": test_case["name"],
                "data": result
            })
        
        # 最後のテスト以外は待機
        if i < len(test_cases) - 1:
            print("\n⏳ 5秒待機中...")
            time.sleep(5)
    
    # 結果の保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/app/output/japandatascience.com/timeline-mapping/data/simple_pattern_test_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": timestamp,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"テスト完了: {len(results)}/3 成功")
    print(f"結果保存: {output_file}")
    
    # パターン分析
    print("\n【パターン分析】")
    for result in results:
        test_name = result["test_name"]
        data = result["data"]
        
        if data.get("search_info", {}).get("type") == "walking":
            print(f"{test_name}: 徒歩ルート")
        else:
            route = data["route"][0] if data.get("route") else {}
            trains = route.get("trains", [])
            transfer_walks = route.get("transfer_walks", [])
            
            print(f"{test_name}:")
            print(f"  - 電車: {len(trains)}本")
            print(f"  - 乗り換え: {len(transfer_walks)}回")
            
            # 乗り換え徒歩時間の詳細
            if transfer_walks:
                print("  - 乗り換え徒歩時間:")
                for tw in transfer_walks:
                    print(f"    {tw.get('duration', '不明')}分")

if __name__ == "__main__":
    main()