#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タイムアウトデバッグ用スクリプト
各ステップで進捗を出力して、どこでタイムアウトしているか特定
"""

import sys
import time
import json
from datetime import datetime, timedelta
import pytz

def log(message):
    """タイムスタンプ付きログ出力"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", file=sys.stderr)
    sys.stderr.flush()

def main():
    try:
        log("スクリプト開始")
        
        # パラメータ取得
        origin = sys.argv[1] if len(sys.argv) > 1 else '東京都千代田区神田須田町1-20-1'
        destination = sys.argv[2] if len(sys.argv) > 2 else '東京駅'
        
        log(f"パラメータ: {origin} → {destination}")
        
        # インポート（ここでタイムアウトする可能性）
        log("モジュールインポート開始")
        
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        log("google_maps_scraperをインポート中...")
        from google_maps_scraper import GoogleMapsScraper
        log("インポート完了")
        
        # スクレイパー初期化
        log("スクレイパー初期化開始")
        scraper = GoogleMapsScraper()
        log("スクレイパー初期化完了")
        
        # WebDriver設定（ここでタイムアウトする可能性大）
        log("WebDriver設定開始")
        scraper.setup_driver()
        log("WebDriver設定完了")
        
        # 到着時刻設定
        jst = pytz.timezone('Asia/Tokyo')
        tomorrow = datetime.now(jst) + timedelta(days=1)
        arrival_time = tomorrow.replace(hour=17, minute=0, second=0, microsecond=0)
        log(f"到着時刻: {arrival_time}")
        
        # スクレイピング実行（ここでタイムアウトする可能性大）
        log("スクレイピング開始")
        result = scraper.scrape_route(
            origin,
            destination,
            destination,
            arrival_time
        )
        log("スクレイピング完了")
        
        # 結果を出力
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # クリーンアップ
        log("クリーンアップ開始")
        scraper.close()
        log("クリーンアップ完了")
        
    except Exception as e:
        log(f"エラー発生: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        
        # エラー時もJSON形式で出力
        print(json.dumps({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }, ensure_ascii=False))
        
        sys.exit(1)

if __name__ == "__main__":
    main()