#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JST対応の完全性検証
"""

from datetime import datetime, timedelta, timezone

print("=" * 60)
print("JST対応検証")
print("=" * 60)

# 現在のUTC時刻
now_utc = datetime.now(timezone.utc)
print(f"\n現在時刻（UTC）: {now_utc}")
print(f"現在時刻（JST）: {now_utc + timedelta(hours=9)}")

# test_lufon_9routes_incremental.pyの実装を検証
tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
arrival_10am = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)  # UTC 01:00 = JST 10:00

print(f"\n【計算結果】")
print(f"arrival_10am (UTC): {arrival_10am}")
print(f"arrival_10am (JST): {arrival_10am + timedelta(hours=9)}")
print(f"タイムスタンプ: {int(arrival_10am.timestamp())}")

# タイムスタンプから逆算
timestamp = int(arrival_10am.timestamp())
recovered_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
print(f"\n【タイムスタンプからの復元】")
print(f"復元（UTC）: {recovered_dt}")
print(f"復元（JST）: {recovered_dt + timedelta(hours=9)}")

# Google Mapsでの期待動作
print(f"\n【Google Mapsでの期待動作】")
print(f"URLに含まれるタイムスタンプ: {timestamp}")
print(f"Google Mapsが解釈する時刻（JST）: {(recovered_dt + timedelta(hours=9)).strftime('%H:%M')}")

# 正しいかチェック
jst_time = recovered_dt + timedelta(hours=9)
if jst_time.hour == 10 and jst_time.minute == 0:
    print("\n✅ JST 10:00に正しく設定されています")
else:
    print(f"\n❌ エラー: JST {jst_time.hour:02d}:{jst_time.minute:02d}になっています（10:00であるべき）")