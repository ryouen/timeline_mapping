#!/usr/bin/env python3
"""目的地の問題を詳しくデバッグ"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_destination():
    """目的地が正しく認識されているか確認"""
    
    # WebDriver設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    
    test_cases = [
        {
            'name': '東京駅（住所のみ）',
            'url': 'https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都千代田区丸の内1丁目/'
        },
        {
            'name': '東京駅（Place IDあり）',
            'url': ('https://www.google.com/maps/dir/'
                   '東京都千代田区神田須田町1-20-1/'
                   '東京都千代田区丸の内1丁目/'
                   'data=!4m18!4m17!1m5!1m1!1s'
                   'ChIJ2RxO9gKMGGARSvjnp3ocfJg'  # ルフォンプログレ
                   '!2m2!1d139.7711!2d35.6950'
                   '!1m5!1m1!1s'
                   'ChIJLdASefmLGGARF3Ez6A4i4Q4'  # 東京駅
                   '!2m2!1d139.7676!2d35.6812'
                   '!2m3!6e1!7e2!8j1755511200!3e3')
        },
        {
            'name': '東京駅（場所名を明示）',
            'url': 'https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京駅/'
        }
    ]
    
    for test in test_cases:
        print("=" * 60)
        print(f"テスト: {test['name']}")
        print("-" * 60)
        
        driver.get(test['url'])
        time.sleep(5)
        
        print(f"ページタイトル: {driver.title}")
        
        # 出発地と目的地の表示を確認
        try:
            # 検索ボックスの値を確認
            inputs = driver.find_elements(By.XPATH, "//input[@aria-label]")
            for inp in inputs[:5]:
                label = inp.get_attribute('aria-label')
                value = inp.get_attribute('value')
                if value:
                    print(f"  {label}: {value}")
        except:
            pass
        
        # ルート要素の確認
        route_elements = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        print(f"ルート要素数: {len(route_elements)}個")
        
        if route_elements and len(route_elements) > 0:
            # 最初のルートの情報
            first_route = route_elements[0].text
            lines = first_route.split('\n')
            print("最初のルート（最初の3行）:")
            for line in lines[:3]:
                print(f"  {line}")
        
        print()
    
    driver.quit()

if __name__ == "__main__":
    debug_destination()