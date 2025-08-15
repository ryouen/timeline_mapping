#!/usr/bin/env python3
"""
府中ルートのデバッグ用スクリプト
HTMLから正確な経路情報を抽出するための新しいアプローチを試す
"""

import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
import sys

def extract_route_info_from_html(html_path):
    """HTMLファイルから経路情報を抽出"""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"HTMLファイルサイズ: {len(html_content):,} bytes")
    
    # 1. 総時間の抽出 - 複数のパターンを試す
    patterns = [
        # パターン1: "1 時間 7 分" のような形式
        r'(\d+)\s*時間\s*(\d+)\s*分',
        # パターン2: 到着時刻形式 "8:43 - 9:52"
        r'(\d+):(\d+)\s*-\s*(\d+):(\d+)',
        # パターン3: aria-labelからの抽出
        r'aria-label="[^"]*(\d+)\s*時間\s*(\d+)\s*分',
        # パターン4: 括弧内の時間 "（1 時間 9 分）"
        r'（\s*(\d+)\s*時間\s*(\d+)\s*分\s*）'
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\nパターン{i+1}でマッチ: {matches[:5]}")  # 最初の5件を表示
    
    # 2. 駅名と路線の抽出
    # 駅名パターン
    station_patterns = [
        r'([^<>]+駅)から\s*(\d+):(\d+)',  # "小川町駅から 9:09"
        r'(\d+):(\d+)\s*([^<>]+駅)',      # "9:44 中河原駅"
        r'<span[^>]*>([^<>]+駅)</span>',   # spanタグ内の駅名
    ]
    
    for i, pattern in enumerate(station_patterns):
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\n駅名パターン{i+1}でマッチ: {matches[:5]}")
    
    # 3. 路線名の抽出
    line_patterns = [
        r'(地下鉄[^<>]+線|京王[^<>]+線|中央線[^<>]+|JR[^<>]+線)',
        r'<span[^>]*class="[^"]*">([^<>]+線)</span>',
        r'aria-label="[^"]*([^"]+線)[^"]*"'
    ]
    
    for i, pattern in enumerate(line_patterns):
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\n路線パターン{i+1}でマッチ: {list(set(matches[:10]))}")
    
    # 4. 徒歩時間の抽出
    walk_patterns = [
        r'徒歩[^<>]*約\s*(\d+)\s*分',
        r'約\s*(\d+)\s*分[^<>]*徒歩',
        r'徒歩</[^>]+>[^<]*(\d+)\s*分',
        r'(\d+)\s*分[^<>]*m\s*徒歩'
    ]
    
    for i, pattern in enumerate(walk_patterns):
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\n徒歩パターン{i+1}でマッチ: {matches}")
    
    # 5. 料金の抽出
    price_patterns = [
        r'(\d+)円',
        r'料金:\s*(\d+)円'
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            print(f"\n料金: {matches}")
            break
    
    # 6. BeautifulSoupでより詳細な解析
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # div要素から情報を探す
    divs_with_time = soup.find_all('div', string=re.compile(r'\d+:\d+'))
    print(f"\n時刻を含むdiv要素: {len(divs_with_time)}個")
    
    # spanから路線情報を探す
    spans_with_line = soup.find_all('span', string=re.compile(r'線'))
    print(f"\n「線」を含むspan要素: {len(spans_with_line)}個")
    for span in spans_with_line[:5]:
        print(f"  - {span.text.strip()}")

if __name__ == "__main__":
    # 最新のデバッグファイルを使用
    debug_file = "/app/output/japandatascience.com/timeline-mapping/api/debug/page_source_東京都千代田区神田須-東京都府中市住吉町5-20250814_144627.html"
    
    if Path(debug_file).exists():
        print(f"デバッグファイル: {debug_file}")
        extract_route_info_from_html(debug_file)
    else:
        print(f"ファイルが見つかりません: {debug_file}")