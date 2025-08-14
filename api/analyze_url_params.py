#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Maps URLパラメータの影響を分析
"""

from urllib.parse import quote

def generate_urls(origin, destination):
    """様々なURLパラメータパターンを生成"""
    
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    base = f"https://www.google.com/maps/dir/{encoded_origin}/{encoded_destination}"
    
    patterns = {
        "シンプル（パラメータなし）": f"{base}/",
        "電車優先（現在の方式）": f"{base}/data=!3m1!4b1!4m2!4m1!3e0",
        "電車優先（簡略版）": f"{base}/?travelmode=transit",
        "電車優先（@付き）": f"{base}/@35.6762,139.6503,12z/data=!3e0",
        "徒歩のみ": f"{base}/?travelmode=walking",
        "車": f"{base}/?travelmode=driving"
    }
    
    return patterns

def main():
    # 問題のある住所
    problem_cases = [
        ("東京都中央区佃2丁目 22-3", "東京駅", "スペースあり"),
        ("東京都中央区佃2丁目22-3", "東京駅", "スペースなし"),
        ("東京都中央区佃2-22-3", "東京駅", "ハイフン形式")
    ]
    
    # 正常に動作する住所（比較用）
    working_case = ("東京都中央区佃2丁目 12-1", "東京駅", "正常動作")
    
    print("Google Maps URLパラメータ分析")
    print("=" * 80)
    
    # 各ケースでURL生成
    all_cases = problem_cases + [working_case]
    
    for origin, destination, case_name in all_cases:
        print(f"\n【{case_name}】")
        print(f"出発: {origin}")
        print(f"到着: {destination}")
        print("-" * 60)
        
        urls = generate_urls(origin, destination)
        for pattern_name, url in urls.items():
            print(f"\n{pattern_name}:")
            print(f"{url}")
    
    print("\n\n分析結果：")
    print("-" * 60)
    print("現在使用しているURLパラメータ:")
    print("data=!3m1!4b1!4m2!4m1!3e0")
    print("\nこのパラメータの意味:")
    print("- !3m1, !4b1: マップのビュー設定")
    print("- !4m2, !4m1: ルート設定")  
    print("- !3e0: 交通手段（0=電車）")
    print("\n問題の可能性:")
    print("1. 複雑なパラメータが特定の住所形式と相性が悪い")
    print("2. 「22-3」という番地が「!」を含むパラメータと衝突")
    print("3. URLエンコーディングの問題")

if __name__ == "__main__":
    main()