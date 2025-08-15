#!/usr/bin/env python3
"""
府中ルートのスクレイピングテスト
ゴールデンデータと比較して正しい結果が取得できるか確認
"""

import subprocess
import json
import sys

def test_fuchu_route():
    """府中ルートをテスト"""
    
    # ゴールデンデータ（ユーザーから提供された正しいデータ）
    golden_data_9am = {
        "total_time": 67,  # 1時間7分
        "route": "小川町駅→新宿線→京王線→中河原駅",
        "walk_to_station": 11,
        "walk_from_station": 5
    }
    
    golden_data_10am = {
        "total_time": 69,  # 1時間9分
        "route": "神田駅→中央線→京王線→中河原駅",
        "walk_to_station": 4,
        "walk_from_station": 5
    }
    
    print("=== 府中ルート スクレイピングテスト ===")
    print("\nゴールデンデータ:")
    print(f"9時出発: {golden_data_9am}")
    print(f"10時到着: {golden_data_10am}")
    
    # テスト対象の府中ルート
    test_params = {
        "origin": "東京都千代田区神田須田町1-20-1",
        "destination": "東京都府中市住吉町5-22-5",
        "property_id": "fuchu"
    }
    
    # google_maps_scraper.pyを実行
    print(f"\n\nスクレイピング実行中...")
    print(f"Origin: {test_params['origin']}")
    print(f"Destination: {test_params['destination']}")
    
    try:
        # 実際のスクレイピングを実行
        cmd = [
            'python3', '/app/output/japandatascience.com/timeline-mapping/api/google_maps_scraper.py',
            test_params['origin'],
            test_params['destination'],
            test_params['property_id']
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\n=== スクレイピング結果 ===")
        print("標準出力:")
        print(result.stdout)
        
        if result.stderr:
            print("\n標準エラー:")
            print(result.stderr)
        
        print(f"\n終了コード: {result.returncode}")
        
        # 結果を解析
        if "Error:" in result.stdout or result.returncode != 0:
            print("\n❌ スクレイピング失敗")
            print("現在のスクレイパーでは府中ルートを正しく取得できません")
            print("\n必要な改善点:")
            print("1. 複数路線（新宿線→京王線 または 中央線→京王線）への対応")
            print("2. 長距離ルートのHTML構造に対応したセレクタの追加")
            print("3. より詳細なデバッグログの出力")
        else:
            # JSONを解析してみる
            try:
                lines = result.stdout.strip().split('\n')
                json_line = None
                for line in lines:
                    if line.strip().startswith('{'):
                        json_line = line
                        break
                
                if json_line:
                    result_data = json.loads(json_line)
                    print("\n解析されたJSON:")
                    print(json.dumps(result_data, indent=2, ensure_ascii=False))
                    
                    # ゴールデンデータと比較
                    if 'total_time' in result_data:
                        actual_time = result_data['total_time']
                        expected_time_range = (golden_data_9am['total_time'], golden_data_10am['total_time'])
                        
                        if expected_time_range[0] <= actual_time <= expected_time_range[1]:
                            print(f"\n✅ 総時間は正しい範囲内: {actual_time}分")
                        else:
                            print(f"\n❌ 総時間が不正: {actual_time}分 (期待値: {expected_time_range[0]}-{expected_time_range[1]}分)")
                    
            except json.JSONDecodeError as e:
                print(f"\nJSON解析エラー: {e}")
        
    except Exception as e:
        print(f"\n実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fuchu_route()