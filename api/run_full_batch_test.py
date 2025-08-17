#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全バッチテスト：Place ID取得からルート検索まで
"""

import subprocess
import sys
import json
from datetime import datetime

def run_command(command, description):
    """コマンドを実行して結果を表示"""
    print(f"\n{'=' * 60}")
    print(f"🚀 {description}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("エラー出力:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 80)
    print("🎯 完全バッチテスト開始")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Step 1: Place ID収集
    success = run_command(
        "python /app/output/japandatascience.com/timeline-mapping/api/batch_place_id_collection.py",
        "Step 1: Place ID一括取得"
    )
    
    if not success:
        print("\n❌ Place ID取得に失敗しました")
        return
    
    # Step 2: ルート検索
    success = run_command(
        "python /app/output/japandatascience.com/timeline-mapping/api/batch_route_search.py",
        "Step 2: ルート一括検索"
    )
    
    if not success:
        print("\n❌ ルート検索に失敗しました")
        return
    
    # 結果を確認
    try:
        with open('/var/www/japandatascience.com/timeline-mapping/data/properties_test.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print("\n" + "=" * 80)
        print("📊 最終結果")
        print("=" * 80)
        print(f"処理物件数: {len(results['properties'])}")
        
        for prop in results['properties']:
            print(f"\n{prop['name']}:")
            print(f"  取得ルート数: {len(prop['routes'])}")
            for route in prop['routes']:
                print(f"    - {route['destination_name']}: {route['total_time']}分")
        
        total_routes = sum(len(p['routes']) for p in results['properties'])
        print(f"\n総ルート数: {total_routes}")
        
    except Exception as e:
        print(f"\n⚠️ 結果ファイルの読み込みエラー: {e}")
    
    print("\n" + "=" * 80)
    print("✅ 完全バッチテスト完了")
    print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()