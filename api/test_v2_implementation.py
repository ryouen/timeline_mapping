#!/usr/bin/env python3
"""
google_maps_transit_docker_v2.pyの動作テスト
"""

import subprocess
import json
from datetime import datetime, timedelta

def run_test(origin, destination, time_arg):
    """テストを実行して結果を返す"""
    cmd = [
        'docker', 'exec', 'vps_project-scraper-1',
        'python', '/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker_v2.py',
        origin, destination, time_arg
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON", "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """メインテスト処理"""
    print("=== Google Maps Transit v2 実装テスト ===\n")
    
    # テストケース
    test_cases = [
        {
            "name": "現在時刻での検索",
            "origin": "東京駅",
            "destination": "新宿駅",
            "time_arg": "now"
        },
        {
            "name": "明日の朝8時出発",
            "origin": "東京駅",
            "destination": "渋谷駅",
            "time_arg": f"departure:{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')} 08:00:00"
        },
        {
            "name": "明日の午後2時到着",
            "origin": "品川駅",
            "destination": "横浜駅",
            "time_arg": f"arrival:{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')} 14:00:00"
        }
    ]
    
    # 各テストケースを実行
    for i, test_case in enumerate(test_cases):
        print(f"テスト {i+1}: {test_case['name']}")
        print(f"  ルート: {test_case['origin']} → {test_case['destination']}")
        print(f"  時刻指定: {test_case['time_arg']}")
        
        result = run_test(test_case['origin'], test_case['destination'], test_case['time_arg'])
        
        if result['status'] == 'success':
            print("  ✓ 成功")
            
            # 検索情報
            search_info = result.get('search_info', {})
            print(f"  検索タイプ: {search_info.get('type', 'unknown')}")
            if search_info.get('requested_time'):
                print(f"  リクエスト時刻: {search_info['requested_time']}")
            
            # ルート情報
            route = result.get('route', {})
            details = route.get('details', {})
            print(f"  総所要時間: {route.get('total_time', 0)}分")
            
            if details.get('departure_time'):
                print(f"  出発時刻: {details['departure_time']}")
            if details.get('arrival_time'):
                print(f"  到着時刻: {details['arrival_time']}")
            
            # 経路詳細
            trains = details.get('trains', [])
            if trains:
                print(f"  利用路線数: {len(trains)}")
                for j, train in enumerate(trains):
                    print(f"    {j+1}. {train['line']} ({train['from']} → {train['to']}) - {train['time']}分")
        else:
            print("  ✗ エラー")
            print(f"  メッセージ: {result.get('message', 'Unknown error')}")
            if 'stdout' in result:
                print(f"  標準出力: {result['stdout']}")
            if 'stderr' in result:
                print(f"  エラー出力: {result['stderr']}")
        
        print()
    
    # 結果を保存
    output_path = "/var/www/japandatascience.com/timeline-mapping/api/test_v2_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "test_cases": test_cases
        }, f, ensure_ascii=False, indent=2)
    
    print(f"テスト結果を保存: {output_path}")

if __name__ == '__main__':
    main()