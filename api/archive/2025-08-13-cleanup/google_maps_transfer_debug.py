#!/usr/bin/env python3
"""
Google Maps 乗り換え徒歩時間デバッグツール
乗り換え時の徒歩時間と待ち時間を正確に分析するための詳細デバッグ版
"""
import json
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys

def extract_minutes_from_text(text):
    """テキストから分数を抽出（例: "約5分" → 5）"""
    match = re.search(r'約?(\d+)\s*分', text)
    if match:
        return int(match.group(1))
    return None

def parse_time(time_str):
    """時刻文字列をdatetimeオブジェクトに変換"""
    try:
        # "午後1:30"のような形式に対応
        time_str = time_str.replace('午前', 'AM').replace('午後', 'PM')
        return datetime.strptime(time_str, "%p%I:%M")
    except:
        try:
            # "13:30"のような形式に対応
            return datetime.strptime(time_str, "%H:%M")
        except:
            return None

def calculate_time_diff(start_time, end_time):
    """2つの時刻の差を分単位で計算"""
    if start_time and end_time:
        diff = (end_time - start_time).total_seconds() / 60
        # 負の値の場合は24時間を加算（日またぎ）
        if diff < 0:
            diff += 24 * 60
        return int(diff)
    return None

def analyze_transfer_route(from_address, to_address):
    """乗り換えルートの詳細分析"""
    # Chromeオプション設定
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=ja')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    try:
        # Google Mapsで検索（電車優先）
        url = f"https://www.google.com/maps/dir/{from_address}/{to_address}/data=!4m2!4m1!3e3"
        print(f"アクセスURL: {url}")
        driver.get(url)
        
        # ページロード待機
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
        time.sleep(3)
        
        # 最初のルートオプションをクリック
        route_options = driver.find_elements(By.CSS_SELECTOR, '[data-trip-index]')
        if not route_options:
            return {"status": "error", "message": "ルートが見つかりませんでした"}
        
        route_options[0].click()
        time.sleep(2)
        
        # directions_panelの内容を取得
        panel = driver.find_element(By.CSS_SELECTOR, 'div[role="main"]')
        
        # デバッグ用：全体のHTMLを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_html_path = f"/app/output/japandatascience.com/timeline-mapping/data/transfer_debug_html_{timestamp}.html"
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(panel.get_attribute('outerHTML'))
        print(f"デバッグHTML保存: {debug_html_path}")
        
        # セグメント情報を収集
        segments = []
        
        # 時刻情報を含む要素を全て取得
        time_elements = panel.find_elements(By.CSS_SELECTOR, '[aria-label*=":"], [aria-label*="午前"], [aria-label*="午後"]')
        
        # テキスト要素も含めて収集
        all_text_elements = panel.find_elements(By.CSS_SELECTOR, 'span, div')
        
        # デバッグ情報を収集
        debug_info = {
            "time_elements": [],
            "walk_texts": [],
            "all_segments": []
        }
        
        # 時刻要素の情報
        for elem in time_elements:
            aria_label = elem.get_attribute('aria-label') or ""
            text = elem.text.strip()
            if aria_label or text:
                debug_info["time_elements"].append({
                    "aria_label": aria_label,
                    "text": text,
                    "tag": elem.tag_name,
                    "class": elem.get_attribute('class')
                })
        
        # 徒歩関連のテキストを検索
        for elem in all_text_elements:
            text = elem.text.strip()
            if '徒歩' in text or '分' in text:
                debug_info["walk_texts"].append({
                    "text": text,
                    "tag": elem.tag_name,
                    "class": elem.get_attribute('class')
                })
        
        # セグメントごとの詳細分析
        segment_index = 0
        prev_arrival_time = None
        
        # パネル内の主要な区切り要素を探す
        route_segments = panel.find_elements(By.CSS_SELECTOR, 'div[role="button"], div[data-transit-mode]')
        
        for i, segment in enumerate(route_segments):
            segment_text = segment.text.strip()
            if not segment_text:
                continue
                
            segment_info = {
                "index": segment_index,
                "raw_text": segment_text,
                "type": "unknown",
                "duration_text": None,
                "duration_minutes": None,
                "start_time": None,
                "end_time": None,
                "calculated_duration": None
            }
            
            # セグメントタイプの判定
            if '徒歩' in segment_text:
                segment_info["type"] = "walk"
            elif '線' in segment_text or '駅' in segment_text:
                segment_info["type"] = "train"
            
            # 時間情報の抽出
            duration_match = extract_minutes_from_text(segment_text)
            if duration_match:
                segment_info["duration_text"] = f"{duration_match}分"
                segment_info["duration_minutes"] = duration_match
            
            # 関連する時刻要素を探す
            parent = segment.find_element(By.XPATH, '..')
            time_in_parent = parent.find_elements(By.CSS_SELECTOR, '[aria-label*=":"]')
            
            for time_elem in time_in_parent:
                time_label = time_elem.get_attribute('aria-label') or ""
                if '出発' in time_label or 'Depart' in time_label:
                    time_match = re.search(r'(\d{1,2}:\d{2})', time_label)
                    if time_match:
                        segment_info["start_time"] = time_match.group(1)
                elif '到着' in time_label or 'Arrive' in time_label:
                    time_match = re.search(r'(\d{1,2}:\d{2})', time_label)
                    if time_match:
                        segment_info["end_time"] = time_match.group(1)
            
            # 前のセグメントの到着時刻と現在の出発時刻から待ち時間を計算
            if prev_arrival_time and segment_info["start_time"]:
                prev_time = parse_time(prev_arrival_time)
                curr_time = parse_time(segment_info["start_time"])
                wait_time = calculate_time_diff(prev_time, curr_time)
                
                if wait_time and wait_time > 0:
                    # 待ち時間セグメントを挿入
                    wait_segment = {
                        "index": segment_index,
                        "type": "wait",
                        "duration_minutes": wait_time,
                        "calculated_from": f"{prev_arrival_time} → {segment_info['start_time']}"
                    }
                    segments.append(wait_segment)
                    debug_info["all_segments"].append(wait_segment)
                    segment_index += 1
            
            # 時刻差から実際の所要時間を計算
            if segment_info["start_time"] and segment_info["end_time"]:
                start = parse_time(segment_info["start_time"])
                end = parse_time(segment_info["end_time"])
                calculated = calculate_time_diff(start, end)
                segment_info["calculated_duration"] = calculated
            
            segments.append(segment_info)
            debug_info["all_segments"].append(segment_info)
            
            # 次の待ち時間計算のために到着時刻を保存
            if segment_info["end_time"]:
                prev_arrival_time = segment_info["end_time"]
            
            segment_index += 1
        
        # デバッグ情報をJSON形式で保存
        debug_json_path = f"/app/output/japandatascience.com/timeline-mapping/data/transfer_debug_json_{timestamp}.json"
        with open(debug_json_path, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)
        print(f"デバッグJSON保存: {debug_json_path}")
        
        # 分析結果のサマリー
        result = {
            "status": "success",
            "route": f"{from_address} → {to_address}",
            "segments_count": len(segments),
            "segments": segments,
            "analysis": {
                "walk_segments": [s for s in segments if s.get("type") == "walk"],
                "train_segments": [s for s in segments if s.get("type") == "train"],
                "wait_segments": [s for s in segments if s.get("type") == "wait"],
                "transfer_walks": []  # 乗り換え徒歩を特定
            }
        }
        
        # 乗り換え徒歩の特定（電車→徒歩→電車のパターン）
        for i in range(1, len(segments) - 1):
            if (segments[i].get("type") == "walk" and 
                i > 0 and segments[i-1].get("type") == "train" and 
                i < len(segments) - 1 and segments[i+1].get("type") in ["train", "wait"]):
                result["analysis"]["transfer_walks"].append(segments[i])
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: python google_maps_transfer_debug.py <出発地> <目的地>")
        sys.exit(1)
    
    from_addr = sys.argv[1]
    to_addr = sys.argv[2]
    
    result = analyze_transfer_route(from_addr, to_addr)
    print(json.dumps(result, ensure_ascii=False, indent=2))