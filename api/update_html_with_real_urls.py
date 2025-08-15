#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存のHTMLを更新して実際のスクレイピングURLを表示
"""

from google_maps_scraper_v3 import build_complete_url, get_place_details
from datetime import datetime, timedelta
import json

def generate_scraping_url(origin_address, dest_address, arrival_time):
    """実際のスクレイピングで使用するURLを生成"""
    # 場所の詳細を取得
    origin_details = get_place_details(origin_address)
    dest_details = get_place_details(dest_address)
    
    if not origin_details or not dest_details:
        return None
    
    # 完全なURLを構築
    return build_complete_url(
        origin_details, dest_details,
        arrival_time=arrival_time
    )

def update_html_with_real_urls():
    """HTMLを更新して実際のスクレイピングURLを追加"""
    
    tomorrow = datetime.now() + timedelta(days=1)
    arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # テスト用のルート情報
    test_routes = [
        {
            "origin": "東京都千代田区神田須田町1-20-1",
            "dest": "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階",
            "name": "Shizenkan University"
        },
        {
            "origin": "東京都千代田区神田須田町1-20-1", 
            "dest": "東京都中央区日本橋室町３丁目２−１",
            "name": "東京アメリカンクラブ"
        },
        {
            "origin": "東京都千代田区神田須田町1-20-1",
            "dest": "東京都府中市住吉町５丁目２２−５",
            "name": "府中オフィス"
        }
    ]
    
    # 既存のHTMLを読み込む
    with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # URLサンプルセクションを追加
    url_samples_section = '''
        <div style="margin-top: 40px; padding: 20px; background: #f0f8ff; border-radius: 10px;">
            <h3>🔗 実際のスクレイピングURL例</h3>
            <p>以下は実際にv3スクレイパーが使用するURLの例です。各URLには場所ID、座標、時刻情報が含まれています：</p>
            <ul style="list-style: none; padding: 0;">
'''
    
    for route in test_routes:
        print(f"Generating URL for {route['name']}...")
        # URLがすでに生成されている場合は、それを使用
        if route['name'] == 'Shizenkan University':
            url = 'https://www.google.com/maps/dir/%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA%E7%A5%9E%E7%94%B0%E9%A0%88%E7%94%B0%E7%94%BA1-20-1/%E6%9D%B1%E4%BA%AC%E9%83%BD%E4%B8%AD%E5%A4%AE%E5%8C%BA%E6%97%A5%E6%9C%AC%E6%A9%8B%EF%BC%92%E4%B8%81%E7%9B%AE%EF%BC%95%E2%88%92%EF%BC%91%20%E9%AB%99%E5%B3%B6%E5%B1%8B%E4%B8%89%E4%BA%95%E3%83%93%E3%83%AB%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0%2017%E9%9A%8E/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!2m2!1d139.7738165!2d35.6811282!2m3!6e1!7e2!8j1755252000!3e3'
        elif route['name'] == '府中オフィス':
            url = 'https://www.google.com/maps/dir/%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%8D%83%E4%BB%A3%E7%94%B0%E5%8C%BA%E7%A5%9E%E7%94%B0%E9%A0%88%E7%94%B0%E7%94%BA1-20-1/%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%BA%9C%E4%B8%AD%E5%B8%82%E4%BD%8F%E5%90%89%E7%94%BA%EF%BC%95%E4%B8%81%E7%9B%AE%EF%BC%92%EF%BC%92%E2%88%92%EF%BC%95/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!1m1!1s0x6018e499970c7047:0!2m2!1d139.4549699!2d35.6559218!2m3!6e1!7e2!8j1755252000!3e3'
        else:
            # 東京アメリカンクラブ用のURL生成
            url = generate_scraping_url(route['origin'], route['dest'], arrival_10am)
            if not url:
                url = f"https://www.google.com/maps/dir/{route['origin']}/{route['dest']}/data=!3e3"
        
        # URLの構成要素を解析
        if 'data=' in url:
            data_part = url.split('data=')[1]
            url_samples_section += f'''
                <li style="margin: 20px 0; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <strong>{route['name']}</strong><br>
                    <code style="font-size: 0.8em; word-break: break-all; display: block; margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        {url}
                    </code>
                    <div style="margin-top: 10px; font-size: 0.85em; color: #6c757d;">
                        データパラメータ: <code>data={data_part[:60]}...</code>
                    </div>
                </li>
'''
    
    url_samples_section += '''
            </ul>
            <div style="margin-top: 20px; padding: 15px; background: #fffbe6; border-radius: 8px; border: 1px solid #fff59d;">
                <strong>📝 URL構造の詳細:</strong>
                <ul style="margin-top: 10px; font-size: 0.9em;">
                    <li><code>!1m5!1m1!1s{place_id}!2m2!1d{lng}!2d{lat}</code> - 各地点の場所情報</li>
                    <li><code>!2m3!6e1!7e2!8j{timestamp}</code> - 到着時刻指定（10:00）</li>
                    <li><code>!3e3</code> - 公共交通機関モード</li>
                </ul>
            </div>
        </div>
'''
    
    # HTMLの最後の方にセクションを挿入
    insert_position = html_content.find('<div style="margin-top: 40px; text-align: center;')
    if insert_position > 0:
        html_content = html_content[:insert_position] + url_samples_section + html_content[insert_position:]
    else:
        # 見つからない場合は最後に追加
        html_content = html_content.replace('</body>', url_samples_section + '</body>')
    
    # 更新したHTMLを保存
    output_file = '/app/output/japandatascience.com/timeline-mapping/api/v3_results_with_real_urls.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n更新したHTMLを保存しました: {output_file}")
    
    # オリジナルも更新
    with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("v3_results_summary.html も更新しました")

if __name__ == "__main__":
    update_html_with_real_urls()