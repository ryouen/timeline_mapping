#!/usr/bin/env python3
"""
Yawaraへの複数ルート詳細分析
- 現在のルート（新御茶ノ水→千代田線）
- 銀座線を使った代替ルート
- 徒歩時間を削減できる可能性のあるルート
"""
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def analyze_route_details(driver, route_element, route_index):
    """ルートの詳細情報を解析"""
    try:
        # ルートをクリックして展開
        route_element.click()
        time.sleep(2)
        
        # 詳細パネルを取得
        details = driver.find_elements(By.CSS_SELECTOR, 'div[data-trip-index]')
        if route_index < len(details):
            detail_element = details[route_index]
            
            # 総所要時間
            duration_elem = detail_element.find_element(By.CSS_SELECTOR, 'span[jstcache*="duration"]')
            total_duration = duration_elem.text if duration_elem else "不明"
            
            # ルート概要（経由駅など）
            route_summary = []
            step_elements = detail_element.find_elements(By.CSS_SELECTOR, 'div[class*="step"]')
            
            for step in step_elements:
                step_text = step.text
                if step_text:
                    # 駅名、路線名、徒歩情報を抽出
                    if "駅" in step_text or "線" in step_text or "徒歩" in step_text:
                        route_summary.append(step_text)
            
            # 徒歩区間の詳細
            walk_segments = []
            walk_elements = detail_element.find_elements(By.CSS_SELECTOR, 'span[aria-label*="徒歩"]')
            for walk in walk_elements:
                walk_text = walk.get_attribute('aria-label')
                if walk_text:
                    walk_segments.append(walk_text)
            
            # 乗換駅の抽出
            transfer_stations = []
            transfer_elements = detail_element.find_elements(By.CSS_SELECTOR, 'span[class*="transfer"]')
            for transfer in transfer_elements:
                if transfer.text:
                    transfer_stations.append(transfer.text)
            
            return {
                "total_duration": total_duration,
                "route_summary": route_summary[:10],  # 最初の10ステップ
                "walk_segments": walk_segments,
                "transfer_stations": transfer_stations,
                "full_text": detail_element.text[:500]  # 最初の500文字
            }
            
    except Exception as e:
        print(f"ルート{route_index}の詳細取得エラー: {str(e)}")
        return None

def get_all_route_options(origin, destination):
    """すべてのルートオプションを取得して分析"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    results = {
        "origin": origin,
        "destination": destination,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "routes": []
    }
    
    try:
        # URL構築（電車優先）
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origin}/{destination}/data=!4m2!4m1!3e3"
        
        print(f"アクセスURL: {url}")
        driver.get(url)
        
        # ルートが読み込まれるまで待機
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="list"]')))
        time.sleep(5)  # 全ルートが表示されるまで待機
        
        # 複数のルートオプションを取得
        route_options = driver.find_elements(By.CSS_SELECTOR, 'div[data-trip-index]')
        print(f"見つかったルート数: {len(route_options)}")
        
        # 各ルートの詳細を取得
        for i, option in enumerate(route_options[:5]):  # 最大5つのルートを確認
            try:
                # 基本情報の取得
                route_info = {
                    "route_index": i + 1,
                    "basic_info": option.text[:200]
                }
                
                # 詳細情報の取得
                details = analyze_route_details(driver, option, i)
                if details:
                    route_info.update(details)
                
                # 特定の路線が含まれているかチェック
                route_text = option.text.lower()
                route_info["uses_ginza_line"] = "銀座線" in route_text
                route_info["uses_chiyoda_line"] = "千代田線" in route_text
                route_info["uses_hanzomon_line"] = "半蔵門線" in route_text
                route_info["station_shin_ochanomizu"] = "新御茶ノ水" in route_text
                route_info["station_kanda"] = "神田" in route_text
                route_info["station_omotesando"] = "表参道" in route_text
                
                results["routes"].append(route_info)
                
            except Exception as e:
                print(f"ルート{i+1}の処理エラー: {str(e)}")
                continue
        
        # デバッグ用にHTMLを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"/app/output/japandatascience.com/timeline-mapping/data/yawara_analysis_{timestamp}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        results["debug_html"] = debug_file
        
        # スクリーンショットも保存
        screenshot_file = f"/app/output/japandatascience.com/timeline-mapping/data/yawara_analysis_{timestamp}.png"
        driver.save_screenshot(screenshot_file)
        results["screenshot"] = screenshot_file
        
    except Exception as e:
        results["error"] = str(e)
        print(f"エラー発生: {str(e)}")
    finally:
        driver.quit()
    
    return results

def main():
    # ルフォンプログレ神田からYawaraへ
    origin = "千代田区神田須田町1-20-1"
    destination = "東京都渋谷区神宮前１丁目８−１０"
    
    print("="*70)
    print("Yawaraへの全ルート分析を開始します...")
    print(f"出発地: {origin}")
    print(f"目的地: {destination}")
    print("="*70)
    
    results = get_all_route_options(origin, destination)
    
    # 結果の表示
    if "routes" in results and results["routes"]:
        print(f"\n分析完了: {len(results['routes'])}個のルートを発見")
        print("\n" + "="*70)
        
        for route in results["routes"]:
            print(f"\n【ルート {route['route_index']}】")
            print(f"総所要時間: {route.get('total_duration', '不明')}")
            
            # 使用路線の表示
            lines = []
            if route.get("uses_ginza_line"):
                lines.append("銀座線")
            if route.get("uses_chiyoda_line"):
                lines.append("千代田線")
            if route.get("uses_hanzomon_line"):
                lines.append("半蔵門線")
            
            if lines:
                print(f"使用路線: {', '.join(lines)}")
            
            # 経由駅の表示
            stations = []
            if route.get("station_kanda"):
                stations.append("神田")
            if route.get("station_shin_ochanomizu"):
                stations.append("新御茶ノ水")
            if route.get("station_omotesando"):
                stations.append("表参道")
            
            if stations:
                print(f"主要経由駅: {', '.join(stations)}")
            
            # 徒歩区間
            if route.get("walk_segments"):
                print(f"徒歩区間: {', '.join(route['walk_segments'][:3])}")
            
            print("\n基本情報:")
            print(route.get("basic_info", "情報なし"))
            print("-"*70)
    
    # JSON形式で保存
    output_file = f"/app/output/japandatascience.com/timeline-mapping/data/yawara_route_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細な分析結果を保存しました: {output_file}")

if __name__ == "__main__":
    main()