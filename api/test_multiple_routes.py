#!/usr/bin/env python3
"""
複数ルートの一括テスト
理想的なJSONと比較して精度を確認
"""
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_maps_transit_final import scrape_google_maps_route

# テストケース（1つ目の拠点から各目的地へ）
test_cases = [
    {
        "name": "神田→Shizenkan University",
        "origin": "東京都千代田区神田須田町1-20-1",
        "destination": "東京都中央区日本橋2-5-1 髙島屋三井ビルディング 17階",
        "expected": {
            "total_time": 13,
            "walk_to_station": 4,
            "trains": [{"line": "銀座線", "time": 2}],
            "walk_from_station": 7
        }
    },
    {
        "name": "神田→東京アメリカンクラブ", 
        "origin": "東京都千代田区神田須田町1-20-1",
        "destination": "東京都中央区日本橋室町3-2-1",
        "expected": {
            "total_time": 8,
            "walk_to_station": 4,
            "trains": [{"line": "銀座線", "time": 2}],
            "walk_from_station": 2
        }
    },
    {
        "name": "神田→axle御茶ノ水",
        "origin": "東京都千代田区神田須田町1-20-1",
        "destination": "東京都千代田区神田小川町3-28-5",
        "expected": {
            "total_time": 13,
            "walk_only": True,
            "walk_time": 13
        }
    },
    {
        "name": "神田→神谷町(EE)",
        "origin": "東京都千代田区神田須田町1-20-1",
        "destination": "東京都港区虎ノ門4-2-6 第二扇屋ビル 1F",
        "expected": {
            "total_time": 25,
            "walk_to_station": 3,
            "trains": [
                {"line": "銀座線", "time": 6, "transfer_after": {"time": 1}},
                {"line": "日比谷線", "time": 6}
            ],
            "walk_from_station": 3
        }
    }
]

def compare_results(actual, expected):
    """実際の結果と期待値を比較"""
    diffs = []
    
    # 総時間の比較
    actual_total = actual.get('route', {}).get('total_time', 0)
    expected_total = expected.get('total_time', 0)
    if abs(actual_total - expected_total) > 2:
        diffs.append(f"総時間: 実際={actual_total}分, 期待={expected_total}分")
    
    # 詳細の比較
    actual_details = actual.get('route', {}).get('details', {})
    
    # 徒歩のみの場合
    if expected.get('walk_only'):
        if not actual_details.get('walk_only'):
            diffs.append("徒歩のみのルートが電車ルートとして認識された")
    else:
        # 駅までの徒歩
        actual_walk_to = actual_details.get('walk_to_station', 0)
        expected_walk_to = expected.get('walk_to_station', 0)
        if abs(actual_walk_to - expected_walk_to) > 1:
            diffs.append(f"駅まで徒歩: 実際={actual_walk_to}分, 期待={expected_walk_to}分")
        
        # 駅からの徒歩
        actual_walk_from = actual_details.get('walk_from_station', 0)
        expected_walk_from = expected.get('walk_from_station', 0)
        if abs(actual_walk_from - expected_walk_from) > 1:
            diffs.append(f"駅から徒歩: 実際={actual_walk_from}分, 期待={expected_walk_from}分")
        
        # 電車の本数
        actual_trains = actual_details.get('trains', [])
        expected_trains = expected.get('trains', [])
        if len(actual_trains) != len(expected_trains):
            diffs.append(f"電車数: 実際={len(actual_trains)}本, 期待={len(expected_trains)}本")
    
    return diffs

def main():
    arrival_time = "2025-08-11 10:00:00"
    results = []
    
    print("=== Google Maps Transit スクレイピング精度テスト ===\n")
    
    for test_case in test_cases:
        print(f"テスト: {test_case['name']}")
        
        # スクレイピング実行
        result = scrape_google_maps_route(
            test_case['origin'],
            test_case['destination'],
            arrival_time
        )
        
        if result['status'] == 'success':
            # 期待値との比較
            diffs = compare_results(result, test_case['expected'])
            
            test_result = {
                "name": test_case['name'],
                "status": "success",
                "actual": result['route'],
                "expected": test_case['expected'],
                "differences": diffs
            }
            
            if not diffs:
                print("  ✅ 完全一致")
            else:
                print("  ⚠️  差異あり:")
                for diff in diffs:
                    print(f"    - {diff}")
        else:
            test_result = {
                "name": test_case['name'],
                "status": "error",
                "message": result['message']
            }
            print(f"  ❌ エラー: {result['message']}")
        
        results.append(test_result)
        print()
    
    # 結果をJSONファイルに保存
    output_file = "/app/output/japandatascience.com/timeline-mapping/data/test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": arrival_time,
            "total_tests": len(results),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"結果を保存: {output_file}")

if __name__ == "__main__":
    main()