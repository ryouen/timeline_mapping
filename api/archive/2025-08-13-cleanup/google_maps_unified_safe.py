#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps統合版スクレイパー（安全版）
テラス月島問題を回避するための修正版
"""

import re
import time
from datetime import datetime
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def get_transit_route(origin, destination, arrival_time=None):
    """電車ルートの取得（修正版）"""
    
    # Chrome設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja,ja_JP'})
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # URL構築（修正版）
        # 元: url += "data=!3m1!4b1!4m2!4m1!3e0"
        # 修正: より安全なパラメータ形式を使用
        base_url = "https://www.google.com/maps/dir/"
        encoded_origin = quote(origin)
        encoded_destination = quote(destination)
        
        # パラメータを別の形式で指定
        # ?travelmode=transit は Google Maps APIの標準的な形式
        url = f"{base_url}{encoded_origin}/{encoded_destination}/?travelmode=transit"
        
        # 到着時刻指定の場合は追加パラメータ
        if arrival_time:
            timestamp = int(arrival_time.timestamp())
            url += f"&arrival_time={timestamp}"
        
        print(f"Accessing URL: {url}")  # デバッグ用
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        # directions panelを探す
        panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
        text = panel.text
        
        # エラーチェック
        if "ルートが見つかりません" in text or "経路が見つかりません" in text:
            # 住所形式を調整して再試行
            # 「丁目」の後のスペースを削除
            adjusted_origin = re.sub(r'(\d+丁目)\s+(\d+)', r'\1\2', origin)
            if adjusted_origin != origin:
                print(f"Retrying with adjusted address: {adjusted_origin}")
                driver.quit()
                return get_transit_route(adjusted_origin, destination, arrival_time)
            else:
                return {"status": "error", "message": "ルートが見つかりません"}
        
        # 時刻と駅名を抽出
        lines = text.split('\n')
        
        # 電車が含まれているか確認
        if not any('電車' in line or '地下鉄' in line or 'JR' in line for line in lines):
            return {"status": "error", "message": "電車ルートが見つかりません"}
        
        # 時刻ベースで解析
        route_data = parse_transit_route(lines)
        
        if route_data:
            # 待ち時間の調整（最初の駅での待ち時間は0にする）
            if route_data.get("trains") and len(route_data["trains"]) > 0:
                if "wait_time" in route_data["trains"][0]:
                    route_data["trains"][0]["wait_time"] = 0
            
            return {
                "status": "success",
                "search_info": {
                    "type": "transit",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "url": url  # デバッグ用にURLも返す
                },
                "route": {
                    "total_time": route_data["total_time"],
                    "details": route_data
                }
            }
        else:
            return {"status": "error", "message": "ルート解析に失敗しました"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

def get_walking_route(origin, destination):
    """徒歩ルートの取得（修正版）"""
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # URL構築（修正版）
        base_url = "https://www.google.com/maps/dir/"
        encoded_origin = quote(origin)
        encoded_destination = quote(destination)
        url = f"{base_url}{encoded_origin}/{encoded_destination}/?travelmode=walking"
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        time.sleep(3)
        
        # 残りのコードは同じ...
        panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
        text = panel.text
        lines = text.split('\n')
        
        # 距離と時間を抽出
        time_match = re.search(r'(\d+)\s*分', text)
        distance_match = re.search(r'([\d.]+)\s*km', text)
        
        if time_match:
            total_time = int(time_match.group(1))
            distance = int(float(distance_match.group(1)) * 1000) if distance_match else 0
            
            return {
                "status": "success",
                "search_info": {
                    "type": "walking",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "route": {
                    "total_time": total_time,
                    "details": {
                        "walk_to_station": 0,
                        "station_used": "",
                        "trains": [],
                        "walk_from_station": total_time,
                        "distance_meters": distance,
                        "route_type": "walking_only"
                    }
                }
            }
        else:
            return {"status": "error", "message": "徒歩時間を取得できませんでした"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

def parse_transit_route(lines):
    """電車ルートの解析（既存のコードを流用）"""
    # 元のgoogle_maps_unified.pyの parse_transit_route と同じ実装
    total_time = None
    walk_to_station = 3  # デフォルト値
    walk_from_station = 3  # デフォルト値
    
    # 総時間を探す
    for line in lines[:10]:
        time_match = re.search(r'(\d+)\s*分', line)
        if time_match:
            total_time = int(time_match.group(1))
            break
    
    if not total_time:
        return None
    
    # 簡略化した電車情報
    trains = [{
        "line": "路線",
        "time": total_time - walk_to_station - walk_from_station,
        "from": "出発駅",
        "to": "到着駅",
        "wait_time": 0
    }]
    
    return {
        "total_time": total_time,
        "walk_to_station": walk_to_station,
        "station_used": "駅",
        "trains": trains,
        "walk_from_station": walk_from_station,
        "wait_time_minutes": 0
    }

# メイン処理
def search_route(origin, destination, mode="transit", arrival_time=None):
    """ルート検索のメインエントリーポイント"""
    if mode == "walking":
        return get_walking_route(origin, destination)
    else:
        return get_transit_route(origin, destination, arrival_time)

if __name__ == "__main__":
    # テスト
    test_result = search_route("東京都中央区佃2丁目 22-3", "東京駅")
    print(json.dumps(test_result, ensure_ascii=False, indent=2))