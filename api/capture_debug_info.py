#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デバッグ用スクリーンショットとHTML保存（文字コード対応版）
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import os
import codecs

def setup_driver():
    """Selenium WebDriverのセットアップ"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--accept-language=ja-JP,ja;q=0.9')
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    driver.implicitly_wait(10)
    return driver

def capture_page_state(driver, name, debug_dir):
    """ページの状態をキャプチャ"""
    
    # スクリーンショット保存
    screenshot_path = f"{debug_dir}/{name}_screenshot.png"
    driver.save_screenshot(screenshot_path)
    print(f"✓ スクリーンショット: {name}_screenshot.png")
    
    # HTML保存（UTF-8で保存、BOM付きで文字化け防止）
    html_path = f"{debug_dir}/{name}_page.html"
    page_source = driver.page_source
    
    # HTMLにメタタグを追加して文字コードを明示
    if '<head>' in page_source:
        page_source = page_source.replace(
            '<head>',
            '<head>\n<meta charset="UTF-8">\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
        )
    
    with codecs.open(html_path, 'w', encoding='utf-8-sig') as f:  # BOM付きUTF-8
        f.write(page_source)
    print(f"✓ HTML保存: {name}_page.html (UTF-8 with BOM)")
    
    # ページ情報を収集
    info = {
        'url': driver.current_url,
        'title': driver.title,
        'elements': {}
    }
    
    # 要素の存在確認
    try:
        # 公共交通機関ボタン
        transit_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, '公共交通') or contains(@aria-label, 'Transit')]")
        info['elements']['transit_buttons'] = len(transit_btns)
        
        # 時刻表示
        time_displays = driver.find_elements(By.XPATH, "//*[contains(text(), '到着') or contains(text(), '出発')]")
        info['elements']['time_displays'] = len(time_displays)
        
        # ルート要素
        routes = driver.find_elements(By.XPATH, "//div[@data-trip-index]")
        info['elements']['routes'] = len(routes)
        
        # 最初のルートのテキスト（もしあれば）
        if routes:
            first_route_text = routes[0].text[:200]
            info['first_route_preview'] = first_route_text
            
    except Exception as e:
        info['error'] = str(e)
    
    return info

def main():
    """メイン処理"""
    
    # デバッグディレクトリ作成
    debug_dir = "/app/output/japandatascience.com/timeline-mapping/api/debug_capture"
    os.makedirs(debug_dir, exist_ok=True)
    
    # 結果HTMLの準備
    result_html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>デバッグキャプチャ結果</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f5f5f5; }
        .test-case { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .url { background: #f0f0f0; padding: 10px; border-radius: 4px; word-break: break-all; font-family: monospace; font-size: 12px; }
        .screenshot { max-width: 600px; border: 1px solid #ddd; margin: 10px 0; }
        .info { background: #e8f4f8; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .error { background: #fee; padding: 10px; border-radius: 4px; color: #c00; }
    </style>
</head>
<body>
    <h1>🔍 Google Maps スクレイピング デバッグキャプチャ</h1>
    <p>実行時刻: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
"""
    
    driver = None
    try:
        driver = setup_driver()
        
        # テストケース
        origin = "東京都千代田区神田須田町1-20-1"
        destination = "東京都中央区日本橋２丁目５−１"
        
        # 明日の10時到着
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
        timestamp = int(arrival_10am.timestamp())
        
        print("=" * 60)
        print("デバッグキャプチャ開始")
        print(f"到着時刻: {(arrival_10am + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')} JST")
        print("=" * 60)
        
        # テストケース
        test_cases = [
            {
                'name': 'basic',
                'desc': '基本URL（時刻指定なし）',
                'url': f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}"
            },
            {
                'name': 'transit',
                'desc': '公共交通機関モード',
                'url': f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!3e3"
            },
            {
                'name': 'with_time',
                'desc': '時刻指定付き',
                'url': f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/data=!4m18!4m17!1m5!2m2!1d139.768563!2d35.6949994!1m5!2m2!1d139.7712416!2d35.6811282!2m3!6e1!7e2!8j{timestamp}!3e3"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n[{i}/3] {test['desc']}")
            print(f"URL: {test['url'][:80]}...")
            
            # ページアクセス
            start_time = time.time()
            driver.get(test['url'])
            load_time = time.time() - start_time
            
            # 追加の待機
            time.sleep(5)
            
            # 状態キャプチャ
            info = capture_page_state(driver, test['name'], debug_dir)
            
            print(f"  読み込み時間: {load_time:.1f}秒")
            print(f"  公共交通機関ボタン: {info['elements'].get('transit_buttons', 0)}個")
            print(f"  時刻表示要素: {info['elements'].get('time_displays', 0)}個")
            print(f"  ルート数: {info['elements'].get('routes', 0)}個")
            
            # 結果HTMLに追加
            result_html += f"""
    <div class="test-case">
        <h2>{i}. {test['desc']}</h2>
        <div class="url">URL: {test['url']}</div>
        <div class="info">
            <strong>読み込み時間:</strong> {load_time:.1f}秒<br>
            <strong>公共交通機関ボタン:</strong> {info['elements'].get('transit_buttons', 0)}個<br>
            <strong>時刻表示要素:</strong> {info['elements'].get('time_displays', 0)}個<br>
            <strong>ルート数:</strong> {info['elements'].get('routes', 0)}個
        </div>
        <h3>スクリーンショット:</h3>
        <img src="{test['name']}_screenshot.png" class="screenshot" alt="{test['desc']}">
        <p><a href="{test['name']}_page.html">HTMLファイルを表示</a></p>
    </div>
"""
            
            if load_time > 10:
                print(f"  ⚠️ 警告: 読み込みが遅い（{load_time:.1f}秒）")
                result_html += f'<div class="error">⚠️ 読み込みが遅い: {load_time:.1f}秒</div>'
        
        result_html += """
</body>
</html>"""
        
        # 結果HTML保存
        result_path = f"{debug_dir}/index.html"
        with codecs.open(result_path, 'w', encoding='utf-8-sig') as f:
            f.write(result_html)
        
        print("\n" + "=" * 60)
        print("✅ デバッグキャプチャ完了")
        print(f"保存先: {debug_dir}")
        print("ファイル一覧:")
        print("  - index.html (結果サマリー)")
        for test in test_cases:
            print(f"  - {test['name']}_screenshot.png")
            print(f"  - {test['name']}_page.html")
        print("\nブラウザで確認:")
        print("https://japandatascience.com/timeline-mapping/api/debug_capture/index.html")
        print("=" * 60)
        
    except Exception as e:
        print(f"エラー: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("Seleniumセッション終了")

if __name__ == "__main__":
    main()