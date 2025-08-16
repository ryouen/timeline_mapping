#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps の HTML を段階的に取得して解析
各フェーズでの DOM 構造を確認
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote
import re

def save_html_phase(driver, phase_name):
    """HTMLを保存して要素を分析"""
    html = driver.page_source
    
    print(f"\n【{phase_name}】")
    print(f"  HTML長さ: {len(html)}文字")
    
    # ボタン要素の検索
    button_patterns = [
        r'aria-label="公共交通機関"',
        r'aria-label="Transit"',
        r'data-travel-mode="3"',
        r'すぐに出発',
        r'出発時刻',
        r'到着時刻',
    ]
    
    for pattern in button_patterns:
        matches = re.findall(pattern, html)
        if matches:
            print(f"  ✓ '{pattern}' found: {len(matches)}回")
            # 周辺のHTMLを表示
            index = html.find(pattern)
            if index > 0:
                start = max(0, index - 100)
                end = min(len(html), index + 200)
                context = html[start:end]
                # タグ構造を抽出
                print(f"    コンテキスト: ...{context}...")
    
    # input要素の検索
    input_patterns = [
        r'<input[^>]*type="date"[^>]*>',
        r'<input[^>]*type="time"[^>]*>',
        r'<input[^>]*aria-label="[^"]*日付[^"]*"[^>]*>',
        r'<input[^>]*aria-label="[^"]*時刻[^"]*"[^>]*>',
    ]
    
    for pattern in input_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"  ✓ Input found: {pattern[:30]}...")
            for match in matches[:2]:
                print(f"    {match[:100]}...")
    
    # ルート情報
    route_pattern = r'data-trip-index'
    route_matches = re.findall(route_pattern, html)
    if route_matches:
        print(f"  ✓ ルート要素: {len(route_matches)}個")
    
    # HTML保存（デバッグ用）
    filename = f"/app/output/japandatascience.com/timeline-mapping/api/debug_{phase_name.replace(' ', '_')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  💾 HTML保存: {filename}")
    
    return html

def main():
    # 明日の10時到着
    jst = pytz.timezone('Asia/Tokyo')
    tomorrow = datetime.now(jst) + timedelta(days=1)
    arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("="*80)
    print("📄 HTML段階取得デバッグ")
    print(f"📅 到着時刻: {arrival_time.strftime('%Y年%m月%d日 %H:%M')} JST")
    print("="*80)
    
    # WebDriver設定
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
    driver.implicitly_wait(3)  # 短めに設定
    
    try:
        origin = '東京都千代田区神田須田町1-20-1'
        destination = '東京都新宿区西早稲田1-6-11'
        
        # Phase 1: 基本URLアクセス（時刻パラメータなし）
        print("\n===== Phase 1: 基本URL =====")
        basic_url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(destination)}/"
        driver.get(basic_url)
        time.sleep(5)
        html1 = save_html_phase(driver, "phase1_basic")
        
        # Phase 2: 公共交通機関モード付きURL
        print("\n===== Phase 2: 公共交通機関モード付きURL =====")
        transit_url = basic_url + "data=!3e3"  # 3e3 = transit mode
        driver.get(transit_url)
        time.sleep(5)
        html2 = save_html_phase(driver, "phase2_transit")
        
        # Phase 3: タイムスタンプ付きURL
        print("\n===== Phase 3: タイムスタンプ付きURL =====")
        timestamp = int(arrival_time.timestamp())
        timed_url = basic_url + f"data=!2m3!6e1!7e2!8j{timestamp}!3e3"
        driver.get(timed_url)
        time.sleep(5)
        html3 = save_html_phase(driver, "phase3_timed")
        
        # Phase 4: 公共交通機関ボタンクリック試行
        print("\n===== Phase 4: クリック操作試行 =====")
        try:
            # いくつかのセレクタを試す
            selectors = [
                "//button[@aria-label='公共交通機関']",
                "//button[@aria-label='Transit']",
                "//button[@data-travel-mode='3']",
                "//div[@data-travel_mode='3']//button",
                "//img[@aria-label='公共交通機関']/parent::button",
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    btn = driver.find_element(By.XPATH, selector)
                    if btn.is_displayed():
                        btn.click()
                        print(f"  ✓ クリック成功: {selector}")
                        clicked = True
                        time.sleep(3)
                        break
                except:
                    print(f"  ✗ クリック失敗: {selector}")
            
            if clicked:
                html4 = save_html_phase(driver, "phase4_after_click")
        except Exception as e:
            print(f"  クリック操作エラー: {e}")
        
        # Phase 5: JavaScript実行でボタン要素を探す
        print("\n===== Phase 5: JavaScript で要素探索 =====")
        js_script = """
        var buttons = document.querySelectorAll('button');
        var results = [];
        for (var i = 0; i < buttons.length && i < 20; i++) {
            var btn = buttons[i];
            results.push({
                index: i,
                text: btn.innerText || '',
                ariaLabel: btn.getAttribute('aria-label') || '',
                className: btn.className || '',
                isVisible: btn.offsetParent !== null
            });
        }
        return results;
        """
        
        try:
            js_results = driver.execute_script(js_script)
            print(f"  JavaScriptで{len(js_results)}個のボタン発見:")
            for r in js_results[:10]:
                if r['text'] or r['ariaLabel']:
                    print(f"    {r['index']}: text='{r['text'][:20]}', aria='{r['ariaLabel'][:30]}', visible={r['isVisible']}")
        except Exception as e:
            print(f"  JavaScript実行エラー: {e}")
        
        # 比較分析
        print("\n===== HTML比較分析 =====")
        if 'html1' in locals() and 'html3' in locals():
            print(f"  Phase1→Phase3 サイズ変化: {len(html1)} → {len(html3)} ({len(html3)-len(html1):+d}文字)")
            
            # 新しく追加された要素を探す
            for pattern in ['data-trip-index', 'aria-label="公共交通機関"', 'すぐに出発']:
                count1 = html1.count(pattern)
                count3 = html3.count(pattern)
                if count1 != count3:
                    print(f"  '{pattern}': {count1} → {count3} ({count3-count1:+d})")
        
    finally:
        driver.quit()
        print("\n✅ デバッグ完了")

if __name__ == "__main__":
    main()