#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タイムゾーンの確認
"""

from datetime import datetime, timedelta
import pytz

# 日本時間のタイムゾーン
jst = pytz.timezone('Asia/Tokyo')

# 明日の10時（日本時間）
tomorrow = datetime.now(jst) + timedelta(days=1)
tomorrow_10am_jst = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

print(f"現在時刻（JST）: {datetime.now(jst)}")
print(f"明日の10時（JST）: {tomorrow_10am_jst}")
print(f"タイムスタンプ: {int(tomorrow_10am_jst.timestamp())}")
print()

# UTCでの確認
tomorrow_10am_utc = tomorrow_10am_jst.astimezone(pytz.UTC)
print(f"明日の10時（UTC）: {tomorrow_10am_utc}")
print()

# タイムゾーンなしの場合（問題のある可能性）
tomorrow_naive = datetime.now() + timedelta(days=1)
tomorrow_10am_naive = tomorrow_naive.replace(hour=10, minute=0, second=0, microsecond=0)
print(f"タイムゾーンなし: {tomorrow_10am_naive}")
print(f"タイムスタンプ（naive）: {int(tomorrow_10am_naive.timestamp())}")