#!/usr/bin/env python3
"""
クイックルートテスト
様々なパターンのルートを素早くテスト
"""
import json
import subprocess
from datetime import datetime

def run_single_test(from_addr, to_addr, test_name):
    """単一のルートテストを実行"""
    print(f"\n{'='*50}")
    print(f"テスト: {test_name}")
    print(f"From: {from_addr}")
    print(f"To: {to_addr}")
    
    try:
        # デバッグ版で実行
        cmd = [
            'python',
            '/app/output/japandatascience.com/timeline-mapping/api/google_maps_transfer_debug.py',
            from_addr,
            to_addr
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data["status"] == "success":
                    print(f"✅ 成功: {data['segments_count']}セグメント")
                    
                    # 乗り換え徒歩の分析
                    transfer_walks = data["analysis"]["transfer_walks"]
                    if transfer_walks:
                        print(f"  乗り換え徒歩: {len(transfer_walks)}回")
                        for tw in transfer_walks:
                            print(f"    - {tw.get('duration_text', '不明')} (計算値: {tw.get('calculated_duration')}分)")
                    
                    return data
                else:
                    print(f"❌ エラー: {data.get('message', '不明')}")
                    return None
            except:
                print(f"❌ JSONパースエラー")
                print(result.stdout[:200])
                return None
        else:
            print(f"❌ 実行エラー: {result.stderr[:200]}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ タイムアウト")
        return None
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return None

def main():
    """メイン処理"""
    print("クイックルートテストを開始します...")
    
    # テストケース定義（多様なパターンを含む）
    test_cases = [
        # 1. 乗り換えなし（短距離）
        {
            "name": "乗り換えなし・短距離",
            "from": "東京都千代田区神田",
            "to": "東京都中央区日本橋"
        },
        # 2. 乗り換えあり（標準）
        {
            "name": "乗り換えあり・標準",
            "from": "東京都千代田区神田",
            "to": "東京都港区神谷町"
        },
        # 3. 徒歩のみ
        {
            "name": "徒歩のみ",
            "from": "東京都千代田区神田須田町1-20-1",
            "to": "東京都千代田区神田小川町３丁目２８−５"
        },
        # 4. 複数乗り換え
        {
            "name": "複数乗り換え",
            "from": "東京都千代田区神田",
            "to": "東京都渋谷区神宮前"
        },
        # 5. 長距離
        {
            "name": "長距離",
            "from": "東京都品川区東五反田",
            "to": "東京都渋谷区神宮前"
        },
        # 6. 別の乗り換えパターン
        {
            "name": "別の乗り換えパターン",
            "from": "東京都港区白金台",
            "to": "東京都港区虎ノ門"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        result = run_single_test(
            test_case["from"],
            test_case["to"],
            test_case["name"]
        )
        if result:
            results.append({
                "test_name": test_case["name"],
                "result": result
            })
        
        # サーバー負荷軽減のため待機（最後のテストでは待機しない）
        if i < len(test_cases) - 1:
            print("  ⏳ 5秒待機中...")
            import time
            time.sleep(5)
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/app/output/japandatascience.com/timeline-mapping/data/quick_test_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": timestamp,
            "test_count": len(test_cases),
            "success_count": len(results),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"テスト完了: {len(results)}/{len(test_cases)} 成功")
    print(f"結果保存: {output_file}")
    
    # パターン分析
    print("\n【発見されたパターン】")
    for result in results:
        test_name = result["test_name"]
        data = result["result"]
        
        walk_segments = data["analysis"]["walk_segments"]
        train_segments = data["analysis"]["train_segments"]
        wait_segments = data["analysis"]["wait_segments"]
        transfer_walks = data["analysis"]["transfer_walks"]
        
        print(f"\n{test_name}:")
        print(f"  - 徒歩: {len(walk_segments)}回")
        print(f"  - 電車: {len(train_segments)}回")
        print(f"  - 待機: {len(wait_segments)}回")
        print(f"  - 乗り換え徒歩: {len(transfer_walks)}回")

if __name__ == "__main__":
    main()