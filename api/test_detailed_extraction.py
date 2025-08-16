#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合テスト: v5 + improved詳細抽出機能（ハードコード削除版）
"""

import json
import sys
import os
from datetime import datetime, timedelta
import pytz

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_maps_scraper import GoogleMapsScraper

def test_detailed_extraction():
    """詳細抽出機能のテスト"""
    
    # 明日の17時到着に設定
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=17, minute=0, second=0, microsecond=0)
    
    print("=" * 60)
    print("Google Maps 詳細抽出テスト")
    print(f"到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
    print("=" * 60)
    
    # テストケース: ルフォンプログレ → 東京駅
    test_case = {
        'origin': '東京都千代田区神田須田町1-20-1',
        'destination': '東京駅',
        'name': '東京駅'
    }
    
    scraper = GoogleMapsScraper()
    
    try:
        scraper.setup_driver()
        
        print(f"\n🚀 テスト開始: {test_case['origin']} → {test_case['destination']}")
        print("-" * 60)
        
        result = scraper.scrape_route(
            test_case['origin'],
            test_case['destination'],
            test_case['name'],
            arrival_time
        )
        
        if result['success']:
            print("✅ 基本情報取得成功")
            print(f"  所要時間: {result.get('travel_time')}分")
            print(f"  ルートタイプ: {result.get('route_type')}")
            print(f"  料金: {result.get('fare')}円")
            print(f"  時刻: {result.get('departure_time')} → {result.get('arrival_time')}")
            
            # 詳細情報の確認
            if 'details' in result:
                print("\n📋 詳細情報:")
                details = result['details']
                
                if 'walk_to_station' in details:
                    print(f"  駅までの徒歩: {details['walk_to_station']}分")
                else:
                    print("  ⚠️ 駅までの徒歩: 取得できず")
                
                if 'station_used' in details:
                    print(f"  利用駅: {details['station_used']}")
                else:
                    print("  ⚠️ 利用駅: 取得できず")
                
                if 'trains' in details:
                    print(f"  電車情報 ({len(details['trains'])}本):")
                    for i, train in enumerate(details['trains'], 1):
                        print(f"    {i}. {train.get('line', '路線不明')}")
                        print(f"       {train.get('from', '?')} → {train.get('to', '?')}")
                        print(f"       乗車時間: {train.get('time', '?')}分")
                else:
                    print("  ⚠️ 電車情報: 取得できず")
                
                if 'walk_from_station' in details:
                    print(f"  駅からの徒歩: {details['walk_from_station']}分")
                else:
                    print("  ⚠️ 駅からの徒歩: 取得できず")
                
                if 'wait_time_minutes' in details:
                    print(f"  待ち時間: {details['wait_time_minutes']}分")
                else:
                    print("  ℹ️ 待ち時間: データなし")
                
            else:
                print("\n⚠️ 詳細情報が取得できませんでした")
            
            # デバッグ情報
            if 'debug_info' in result:
                print(f"\n🔍 デバッグ情報:")
                print(f"  ステップ数: {result['debug_info'].get('steps_found', 0)}")
                print(f"  ルート数: {result['debug_info'].get('routes_found', 0)}")
            
            # ハードコード値のチェック
            print("\n🔎 ハードコード値チェック:")
            suspicious_values = []
            
            if 'details' in result:
                details = result['details']
                # 5分の徒歩時間（ハードコード値）
                if details.get('walk_to_station') == 5:
                    suspicious_values.append("walk_to_station = 5")
                if details.get('walk_from_station') == 5:
                    suspicious_values.append("walk_from_station = 5")
                # 3分の待ち時間（ハードコード値）
                if details.get('wait_time_minutes') == 3:
                    suspicious_values.append("wait_time_minutes = 3")
                # 「不明」という文字列
                if details.get('station_used') == '不明':
                    suspicious_values.append("station_used = '不明'")
                # 電車情報のチェック
                if 'trains' in details:
                    for train in details['trains']:
                        if train.get('line') == '電車':
                            suspicious_values.append("line = '電車'")
                        if train.get('time') == 10:
                            suspicious_values.append("time = 10")
                        if train.get('from') == '不明':
                            suspicious_values.append("from = '不明'")
                        if train.get('to') == '不明':
                            suspicious_values.append("to = '不明'")
            
            if suspicious_values:
                print("  ❌ ハードコード値が検出されました:")
                for val in suspicious_values:
                    print(f"     - {val}")
            else:
                print("  ✅ ハードコード値は検出されませんでした")
            
            # JSON出力
            print("\n📄 完全なJSON出力:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        else:
            print(f"❌ 失敗: {result.get('error')}")
            if 'debug_info' in result:
                print(f"デバッグ情報: {result['debug_info']}")
                
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        scraper.close()

if __name__ == "__main__":
    test_detailed_extraction()