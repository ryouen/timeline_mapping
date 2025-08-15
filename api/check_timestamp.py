#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タイムスタンプの確認
"""

from datetime import datetime, timedelta

# 問題のタイムスタンプ
timestamp = 1755338400

# タイムスタンプを日時に変換
dt = datetime.fromtimestamp(timestamp)
print(f"問題のタイムスタンプ: {timestamp}")
print(f"変換後の日時: {dt}")
print(f"曜日: {dt.strftime('%A')}")
print()

# 正しいタイムスタンプ（明日の10時）を計算
tomorrow = datetime.now() + timedelta(days=1)
correct_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
correct_timestamp = int(correct_10am.timestamp())

print(f"正しい明日の10時: {correct_10am}")
print(f"正しいタイムスタンプ: {correct_timestamp}")
print()

# 差を計算
diff_seconds = correct_timestamp - timestamp
diff_hours = diff_seconds / 3600
print(f"差: {diff_hours}時間")