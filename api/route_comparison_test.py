#!/usr/bin/env python3
"""
ルート比較テスト
transit_finalとunifiedの結果を比較
"""
import json
import subprocess
import time
from datetime import datetime

def test_with_script(script_name, from_addr, to_addr, test_name):
    """指定したスクリプトでテスト実行"""
    print(f"\n{'-'*40}")
    print(f"スクリプト: {script_name}")
    
    try:
        cmd = [
            'python',
            f'/app/output/japandatascience.com/timeline-mapping/api/{script_name}',
            from_addr,
            to_addr
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"実行時間: {elapsed:.1f}秒")
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"✅ 成功")
                print(f"結果: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                return data
            except:
                print(f"❌ JSONパースエラー")
                print(result.stdout[:200])
                return None
        else:
            print(f"❌ 実行エラー")
            print(result.stderr[:200])
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ タイムアウト (30秒)")
        return None
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return None

def main():
    """メイン処理"""
    print("ルート比較テストを開始します...")
    
    # テストケース
    test_cases = [
        {
            "name": "電車ルート（神田→日本橋）",
            "from": "東京都千代田区神田",
            "to": "東京都中央区日本橋"
        },
        {
            "name": "徒歩ルート（神田→axle御茶ノ水）",
            "from": "東京都千代田区神田須田町1-20-1",
            "to": "東京都千代田区神田小川町３丁目２８−５"
        }
    ]
    
    # 使用するスクリプト
    scripts = [
        "google_maps_transit_final.py",
        "google_maps_walking_final.py",
        "google_maps_transfer_debug.py"
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"テストケース: {test_case['name']}")
        
        test_results = {
            "test_name": test_case["name"],
            "results": {}
        }
        
        for script in scripts:
            result = test_with_script(
                script,
                test_case["from"],
                test_case["to"],
                test_case["name"]
            )
            
            test_results["results"][script] = result
            
            # サーバー負荷軽減
            time.sleep(3)
        
        results.append(test_results)
    
    # 結果の保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/app/output/japandatascience.com/timeline-mapping/data/route_comparison_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": timestamp,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"結果保存: {output_file}")

if __name__ == "__main__":
    main()