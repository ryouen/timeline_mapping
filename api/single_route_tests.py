#!/usr/bin/env python3
"""
単体ルートテスト（詳細表示版）
"""
import subprocess
import json
import time

def test_single_route(origin, dest_name, dest_address):
    """単一ルートを詳細にテスト"""
    print(f"\n{'='*70}")
    print(f"テスト: {origin} → {dest_name}")
    print(f"{'='*70}")
    
    # コマンドを実行
    address = dest_address if dest_address else dest_name
    cmd = [
        "docker", "exec", "vps_project-scraper-1",
        "python", "/app/output/japandatascience.com/timeline-mapping/api/google_maps_combined.py",
        origin, address
    ]
    
    print(f"実行コマンド: {' '.join(cmd[3:])}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            if data.get("status") == "success":
                route = data.get("route", {})
                details = route.get("details", {})
                
                # ルートタイプの判定
                if details.get("route_type") == "walking_only":
                    print(f"\n✅ 徒歩ルート")
                    print(f"  総所要時間: {route.get('total_time', 'N/A')}分")
                    print(f"  距離: {details.get('distance_meters', 'N/A')}m")
                else:
                    print(f"\n✅ 電車ルート")
                    print(f"  総所要時間: {route.get('total_time', 'N/A')}分")
                    print(f"  内訳:")
                    print(f"    - 駅まで徒歩: {details.get('walk_to_station', 0)}分")
                    
                    for i, train in enumerate(details.get("trains", [])):
                        print(f"    - {train.get('line', 'N/A')}: {train.get('from', 'N/A')} → {train.get('to', 'N/A')} ({train.get('time', 'N/A')}分)")
                        if train.get('wait_time', 0) > 0:
                            print(f"      (待ち時間: {train.get('wait_time', 0)}分)")
                    
                    print(f"    - 駅から徒歩: {details.get('walk_from_station', 0)}分")
            else:
                print(f"\n❌ エラー: {data.get('message', 'Unknown error')}")
                
        else:
            print(f"\n❌ 実行エラー: {result.stderr}")
            
    except Exception as e:
        print(f"\n❌ 例外エラー: {str(e)}")
    
    time.sleep(2)  # API負荷軽減

def main():
    origin = "千代田区神田須田町1-20-1"
    
    destinations = [
        ("Shizenkan University", "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階"),
        ("東京アメリカンクラブ", "東京都中央区日本橋室町３丁目２−１"),
        ("axle御茶ノ水", "東京都千代田区神田小川町３丁目２８−５"),
        ("Yawara", "東京都渋谷区神宮前１丁目８−１０"),
        ("東京駅", ""),
        ("羽田空港", ""),
        ("神谷町(EE)", "東京都港区虎ノ門４丁目２−６"),
        ("早稲田大学", "東京都新宿区西早稲田１丁目６")
    ]
    
    print(f"出発地: ルフォンプログレ神田プレミア")
    print(f"住所: {origin}")
    
    for dest_name, dest_address in destinations:
        test_single_route(origin, dest_name, dest_address)

if __name__ == "__main__":
    main()