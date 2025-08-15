#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib.parse import unquote

url = "https://www.google.com/maps/dir/%25E6%259D%25B1%25E4%25BA%25AC%25E9%2583%25BD%25E5%258D%2583%25E4%25BB%25A3%25E7%2594%25B0%25E5%258C%25BA%25E7%25A5%259E%25E7%2594%25B0%25E9%25A0%2588%25E7%2594%25B0%25E7%2594%25BA1-20-1/%25E6%259D%25B1%25E4%25BA%25AC%25E9%2583%25BD%25E4%25B8%25AD%25E5%25A4%25AE%25E5%258C%25BA%25E6%2597%25A5%25E6%259C%25AC%25E6%25A9%258B%25EF%25BC%2592%25E4%25B8%2581%25E7%259B%25AE%25EF%25BC%2595%25E2%2588%2592%25EF%25BC%2591%2520%25E9%25AB%2599%25E5%25B3%25B6%25E5%25B1%258B%25E4%25B8%2589%25E4%25BA%2595%25E3%2583%2593%25E3%2583%25AB%25E3%2583%2587%25E3%2582%25A3%25E3%2583%25B3%25E3%2582%25B0%252017%25E9%259A%258E/data%3D!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0!2m2!1d139.7711379!2d35.6949994!1m5!2m2!1d139.7738165!2d35.6811282!2m3!6e1!7e2!8j1755252000!3e3"

# ダブルエンコードされているので2回デコード
decoded_once = unquote(url)
decoded_twice = unquote(decoded_once)

print("元のURL:")
print(url)
print("\n1回デコード:")
print(decoded_once)
print("\n2回デコード:")
print(decoded_twice)

# data部分の確認
if "data=" in decoded_twice:
    data_part = decoded_twice.split("data=")[1].split("&")[0]
    print("\ndata部分:")
    print(data_part)