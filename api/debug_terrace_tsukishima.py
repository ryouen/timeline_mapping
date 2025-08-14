#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テラス月島のルート検索デバッグ
実際のURLとHTMLを保存
"""

import time
import json
from datetime import datetime
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def debug_route_search(origin, destination, debug_name):
    """デバッグ情報を含むルート検索"""
    
    # Chrome設定
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=ja')
    chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'ja,ja_JP'})
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # URL構築
        encoded_origin = quote(origin)
        encoded_destination = quote(destination)
        url = f"https://www.google.com/maps/dir/{encoded_origin}/{encoded_destination}/"
        url += "data=!3m1!4b1!4m2!4m1!3e0"  # 3e0は電車優先
        
        print(f"\n=== {debug_name} ===")
        print(f"出発: {origin}")
        print(f"到着: {destination}")
        print(f"URL: {url}")
        
        # ページ読み込み
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        time.sleep(5)
        
        # スクリーンショット保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"/var/www/japandatascience.com/timeline-mapping/data/debug_{debug_name}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"スクリーンショット: {screenshot_path}")
        
        # HTML保存
        html_path = f"/var/www/japandatascience.com/timeline-mapping/data/debug_{debug_name}_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"HTML保存: {html_path}")
        
        # directions panelを探す
        try:
            panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
            text = panel.text
            
            # テキスト保存
            text_path = f"/var/www/japandatascience.com/timeline-mapping/data/debug_{debug_name}_{timestamp}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"抽出テキスト: {text_path}")
            
            # 最初の10行を表示
            lines = text.split('\n')
            print("\n最初の10行:")
            for i, line in enumerate(lines[:10]):
                print(f"  {i}: {line}")
            
            # エラーチェック
            if "ルートが見つかりません" in text or "経路が見つかりません" in text:
                print("\n❌ エラー: ルートが見つかりません")
                return {"status": "error", "message": "ルートが見つかりません"}
            
            # 電車ルートの存在確認
            has_train = any('電車' in line or '地下鉄' in line or 'JR' in line or '徒歩' in line for line in lines)
            print(f"\n電車ルート: {'あり' if has_train else 'なし'}")
            
            # 総時間を探す
            import re
            total_time = None
            for line in lines[:10]:
                time_match = re.search(r'(\d+)\s*分', line)
                if time_match:
                    total_time = int(time_match.group(1))
                    print(f"総時間: {total_time}分")
                    break
            
            return {
                "status": "success",
                "url": url,
                "screenshot": screenshot_path,
                "html": html_path,
                "text": text_path,
                "total_time": total_time,
                "has_train_route": has_train
            }
            
        except Exception as e:
            print(f"\n❌ パネル取得エラー: {str(e)}")
            return {"status": "error", "message": f"パネル取得エラー: {str(e)}"}
            
    except Exception as e:
        print(f"\n❌ エラー: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

def main():
    """メイン処理"""
    print("テラス月島ルート検索デバッグ")
    print("=" * 60)
    
    # テストケース
    test_cases = [
        {
            "origin": "東京都中央区佃2丁目 22-3",
            "destination": "東京駅",
            "name": "tsukishima_to_tokyo_chome"
        },
        {
            "origin": "東京都中央区佃2-22-3",
            "destination": "東京駅", 
            "name": "tsukishima_to_tokyo_hyphen"
        },
        {
            "origin": "月島駅",
            "destination": "東京駅",
            "name": "tsukishima_station_to_tokyo"
        },
        {
            "origin": "東京都中央区佃2丁目22番3号",
            "destination": "東京駅",
            "name": "tsukishima_to_tokyo_formal"
        }
    ]
    
    results = []
    
    for test in test_cases:
        result = debug_route_search(test["origin"], test["destination"], test["name"])
        results.append({
            "test": test,
            "result": result
        })
        time.sleep(5)  # Google Maps負荷対策
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("結果サマリー:")
    for r in results:
        test = r["test"]
        result = r["result"]
        status = "✅" if result["status"] == "success" else "❌"
        print(f"{status} {test['name']}: {test['origin']} → {test['destination']}")
        if result["status"] == "success":
            print(f"   総時間: {result.get('total_time', '不明')}分")
        else:
            print(f"   エラー: {result.get('message', '不明')}")
    
    # 結果をJSONで保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"/var/www/japandatascience.com/timeline-mapping/data/debug_terrace_results_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果JSON: {json_path}")

if __name__ == "__main__":
    main()