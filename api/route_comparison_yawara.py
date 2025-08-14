#!/usr/bin/env python3
"""
Yawaraへの複数ルート比較
銀座線→千代田線ルートと現在のルートを比較
"""
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_multiple_routes(origin, destination):
    """複数のルートオプションを取得"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    try:
        # URL構築（電車優先）
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origin}/{destination}/data=!4m2!4m1!3e3"
        
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        
        # ルートが読み込まれるまで待機
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="list"]')))
        time.sleep(3)
        
        # 複数のルートオプションを取得
        route_options = driver.find_elements(By.CSS_SELECTOR, 'div[data-trip-index]')
        
        routes = []
        for i, option in enumerate(route_options[:3]):  # 最大3つのルートを確認
            try:
                # ルートの概要を取得
                summary_elem = option.find_element(By.CSS_SELECTOR, 'div[aria-label*="経路"]')
                summary_text = summary_elem.text
                
                # 所要時間を取得
                duration_elem = option.find_element(By.CSS_SELECTOR, 'span[jstcache*="duration"]')
                duration_text = duration_elem.text if duration_elem else "不明"
                
                # 徒歩時間を探す
                walk_elements = option.find_elements(By.CSS_SELECTOR, 'span[aria-label*="徒歩"]')
                walk_times = [elem.text for elem in walk_elements]
                
                routes.append({
                    "route_index": i + 1,
                    "summary": summary_text,
                    "total_duration": duration_text,
                    "walk_segments": walk_times,
                    "full_text": option.text
                })
                
            except Exception as e:
                print(f"ルート{i+1}の取得エラー: {str(e)}")
                continue
        
        # デバッグ用にHTMLを保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"/app/output/japandatascience.com/timeline-mapping/data/yawara_routes_{timestamp}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        return {
            "status": "success",
            "origin": origin,
            "destination": destination,
            "routes_count": len(routes),
            "routes": routes,
            "debug_html": debug_file
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        driver.quit()

def main():
    origin = "千代田区神田須田町1-20-1"
    destination = "東京都渋谷区神宮前１丁目８−１０"
    
    print(f"ルフォンプログレ神田 → Yawaraの複数ルートを比較します...")
    
    result = get_multiple_routes(origin, destination)
    
    if result["status"] == "success":
        print(f"\n見つかったルート数: {result['routes_count']}")
        print("\n" + "="*70)
        
        for route in result["routes"]:
            print(f"\n【ルート {route['route_index']}】")
            print(f"総所要時間: {route['total_duration']}")
            print(f"徒歩区間: {', '.join(route['walk_segments']) if route['walk_segments'] else '詳細不明'}")
            print(f"\n詳細テキスト:\n{route['full_text'][:300]}...")
            print("\n" + "-"*70)
    else:
        print(f"エラー: {result.get('message', 'Unknown error')}")
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()