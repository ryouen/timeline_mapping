#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特定の住所でのルート検索をテスト
実際のSeleniumの動作を確認
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

def test_route_with_different_urls(origin, destination):
    """異なるURLパラメータでテスト"""
    
    # Chrome設定
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=ja')
    
    results = []
    
    # テストするURLパターン
    url_patterns = [
        ("現在の方式", f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!3m1!4b1!4m2!4m1!3e0"),
        ("シンプル", f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/?travelmode=transit"),
        ("パラメータなし", f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/")
    ]
    
    for pattern_name, url in url_patterns:
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            print(f"\n=== {pattern_name} ===")
            print(f"URL: {url}")
            
            start_time = time.time()
            driver.get(url)
            wait = WebDriverWait(driver, 30)
            time.sleep(5)
            
            # ページタイトルを確認
            title = driver.title
            print(f"ページタイトル: {title}")
            
            # エラーメッセージをチェック
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            if "ルートが見つかりません" in page_text or "経路が見つかりません" in page_text:
                print("❌ ルートが見つかりません")
                results.append({
                    "pattern": pattern_name,
                    "status": "no_route",
                    "error": "ルートが見つかりません"
                })
            else:
                # directions panelを探す
                try:
                    panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="main"]')))
                    panel_text = panel.text
                    
                    # 最初の5行を表示
                    lines = panel_text.split('\n')[:5]
                    print("パネルの内容（最初の5行）:")
                    for line in lines:
                        print(f"  {line}")
                    
                    # 総時間を探す
                    import re
                    time_match = re.search(r'(\d+)\s*分', panel_text)
                    if time_match:
                        total_time = int(time_match.group(1))
                        print(f"✅ 総時間: {total_time}分")
                        results.append({
                            "pattern": pattern_name,
                            "status": "success",
                            "total_time": total_time
                        })
                    else:
                        print("⚠️ 時間が見つかりません")
                        results.append({
                            "pattern": pattern_name,
                            "status": "no_time",
                            "error": "時間が見つかりません"
                        })
                        
                except Exception as e:
                    print(f"❌ パネル取得エラー: {str(e)}")
                    results.append({
                        "pattern": pattern_name,
                        "status": "error",
                        "error": str(e)
                    })
            
            elapsed = time.time() - start_time
            print(f"処理時間: {elapsed:.2f}秒")
            
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            results.append({
                "pattern": pattern_name,
                "status": "error",
                "error": str(e)
            })
            
        finally:
            driver.quit()
            time.sleep(2)
    
    return results

def main():
    print("テラス月島の住所問題を詳細分析")
    print("=" * 60)
    
    # テストケース
    test_cases = [
        {
            "name": "テラス月島（問題のある住所）",
            "origin": "東京都中央区佃2丁目 22-3",
            "destination": "東京駅"
        },
        {
            "name": "リベルテ月島（正常動作）",
            "origin": "東京都中央区佃2丁目 12-1", 
            "destination": "東京駅"
        }
    ]
    
    all_results = []
    
    for test in test_cases:
        print(f"\n{'#' * 60}")
        print(f"テスト: {test['name']}")
        print(f"出発: {test['origin']}")
        print(f"到着: {test['destination']}")
        print('#' * 60)
        
        results = test_route_with_different_urls(test['origin'], test['destination'])
        all_results.append({
            "test": test,
            "results": results
        })
    
    # 結果サマリー
    print("\n\n" + "=" * 60)
    print("結果サマリー:")
    print("=" * 60)
    
    for test_result in all_results:
        test = test_result["test"]
        results = test_result["results"]
        
        print(f"\n{test['name']}:")
        for result in results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"  {status_icon} {result['pattern']}: {result['status']}")
            if result["status"] == "success":
                print(f"     時間: {result['total_time']}分")
            elif "error" in result:
                print(f"     エラー: {result['error']}")
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/var/www/japandatascience.com/timeline-mapping/data/address_test_results_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n結果を保存: {filename}")

if __name__ == "__main__":
    main()