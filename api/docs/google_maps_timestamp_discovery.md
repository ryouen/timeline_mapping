# Google Maps タイムスタンプの仕様に関する重要な発見

## 発見日時
2025年8月15日

## 概要
Google MapsのURL内のタイムスタンプ（`8j`パラメータ）は、特殊な仕様を持っていることが判明した。

## 重要な発見

### 1. タイムスタンプの特殊な仕様
- **表示される時刻**: ローカルタイム（JST）として扱われる
- **タイムスタンプの値**: UTC基準の同じ数値を使用

### 2. 具体例
2025年8月16日 10:00 JST到着を指定する場合：
- **期待される計算**: 2025-08-16 01:00 UTC → `1755306000`
- **実際に必要な値**: 2025-08-16 10:00 UTC → `1755338400`
- **結果**: JST環境で「10:00到着」として正しく表示される

### 3. 実証
```
実際のGoogle MapsのURL:
https://www.google.com/maps/dir/〒101-0041+東京都千代田区神田須田町１丁目２０−１+吉川ビル/〒103-6199+東京都中央区日本橋２丁目５−１/@35.6880527,139.7674084,16z/data=!4m18!4m17!1m5!1m1!1s0x60188c02f64e1cd9:0x987c1c7aa7e7f84a!2m2!1d139.7711379!2d35.6949994!1m5!1m1!1s0x601889d738b39701:0x996fd0bd4cfffd56!2m2!1d139.773935!2d35.6814238!2m3!6e1!7e2!8j1755338400!3e3

タイムスタンプ: 1755338400
= 2025-08-16 10:00:00 UTC
= 2025-08-16 19:00:00 JST

しかし、Google Mapsでは「2025/8/16 10:00到着」として表示され、
実際のルートは 9:48出発 → 9:56到着 となる。
```

## Python実装

```python
from datetime import datetime
import pytz

def generate_google_maps_timestamp(year, month, day, hour, minute):
    """
    Google Maps用のタイムスタンプを生成
    注意: 時刻はJSTとして指定するが、UTC基準で計算する
    """
    # UTC時刻として作成（タイムゾーンを無視）
    utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
    return int(utc_time.timestamp())

# 例: 2025年8月16日 10:00 JST到着
timestamp = generate_google_maps_timestamp(2025, 8, 16, 10, 0)
# → 1755338400
```

## Place IDの重要性

正しく動作するURLには以下が必要：
1. **Place ID**: 場所を一意に識別（例: `0x60188c02f64e1cd9:0x987c1c7aa7e7f84a`）
2. **座標**: `@35.6880527,139.7674084,16z`
3. **正しいタイムスタンプ**: UTC基準で計算した値

## 影響範囲

### 修正が必要なファイル
- `google_maps_scraper_v3.py`
- `google_maps_scraper_v4.py`
- `google_maps_scraper_v5_click.py`
- すべてのテストスクリプト

### 修正内容
タイムスタンプ生成ロジックを以下のように変更：
```python
# 誤った実装
arrival_10am = tomorrow.replace(hour=1, minute=0)  # UTC 01:00 = JST 10:00
timestamp = int(arrival_10am.timestamp())  # 1755306000

# 正しい実装
arrival_10am_utc = datetime(2025, 8, 16, 10, 0, tzinfo=pytz.UTC)
timestamp = int(arrival_10am_utc.timestamp())  # 1755338400
```

## まとめ
Google Mapsは、タイムゾーンの概念を持ちながらも、タイムスタンプについては「数値としての時刻」をそのままUTC基準で使用するという特殊な仕様を持っている。これはおそらく、世界中の異なるタイムゾーンで同じコードベースを使用するための設計と推測される。