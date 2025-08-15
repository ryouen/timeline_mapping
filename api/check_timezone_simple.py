#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タイムゾーンの簡単な確認
"""

from datetime import datetime, timedelta, timezone
import time

# システムのタイムゾーンを確認
print(f"システムタイムゾーン: {time.tzname}")
print(f"UTCオフセット: {time.timezone / 3600}時間")
print()

# 現在時刻
now = datetime.now()
print(f"現在時刻（ローカル）: {now}")
print(f"現在時刻（UTC）: {datetime.utcnow()}")
print()

# test_lufon_9routes_incremental.pyと同じ方法で計算
tomorrow = datetime.now() + timedelta(days=1)
arrival_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

print(f"明日の10時（計算）: {arrival_10am}")
print(f"タイムスタンプ: {int(arrival_10am.timestamp())}")
print()

# 実際のタイムスタンプを確認
actual_timestamp = 1755338400
actual_dt = datetime.fromtimestamp(actual_timestamp)
print(f"実際のタイムスタンプ: {actual_timestamp}")
print(f"実際の日時: {actual_dt}")
print(f"差: {(actual_dt - arrival_10am).total_seconds() / 3600}時間")