# Google Maps スクレイピング完全ガイド

## 作成日
2025年8月15日

## 🎯 重要な発見と解決策

### 1. Place IDの必須性
**問題**: 住所だけのURLでは時刻指定やモード指定が不安定
**解決**: Place IDを含む完全なURL構造が必要

### 2. タイムスタンプの特殊仕様
**問題**: JSTとUTCの変換で混乱
**解決**: Google MapsはJSTの時刻をUTC基準で計算（タイムゾーン無視）

```python
# 例：2025年8月16日 10:00 JST到着
# 通常の計算: 2025-08-16 01:00 UTC = 1755306000
# Google Maps: 2025-08-16 10:00 UTC = 1755338400 ← これを使用！
```

### 3. 住所での検索の重要性
**問題**: 施設名での検索は別の場所を取得する可能性
**解決**: 正確な住所でPlace IDを取得

## 📐 正しいURL構造

### 完全なURLテンプレート
```
https://www.google.com/maps/dir/
[出発地（郵便番号+住所+建物名）]/
[目的地（郵便番号+住所+施設名）]/
@[中心座標],16z/
data=!3m1!4b1              # モード指定（重要）
!4m18!4m17                  # ルート情報
!1m5!1m1!1s[出発地Place ID]!2m2!1d[経度]!2d[緯度]
!1m5!1m1!1s[目的地Place ID]!2m2!1d[経度]!2d[緯度]
!2m3!6e1!7e2!8j[timestamp]  # 時刻指定
!3e3                        # 公共交通機関モード
```

### 実例（検証済み）
```
https://www.google.com/maps/dir/
〒101-0041+東京都千代田区神田須田町１丁目２０−１+吉川ビル/
〒103-6199+東京都中央区日本橋２丁目５−１/
@35.6880527,139.7674084,16z/
data=!4m18!4m17
!1m5!1m1!1s0x60188c02f64e1cd9:0x987c1c7aa7e7f84a!2m2!1d139.7711379!2d35.6949994
!1m5!1m1!1s0x601889d738b39701:0x996fd0bd4cfffd56!2m2!1d139.773935!2d35.6814238
!2m3!6e1!7e2!8j1755338400!3e3
```
結果: 9:48出発 → 9:56到着（銀座線、8分、180円）

## 🔧 実装方法

### 1. Place ID取得
```python
def get_place_id(driver, address):
    """住所からPlace IDを取得"""
    origin = "東京都千代田区神田須田町1-20-1"
    url = f"https://www.google.com/maps/dir/{quote(origin)}/{quote(address)}/data=!3e3"
    
    driver.get(url)
    time.sleep(5)
    
    # URLから2番目のPlace IDを抽出（1番目は出発地）
    place_id_matches = re.findall(r'!1s(0x[0-9a-f]+:0x[0-9a-f]+)', driver.current_url)
    
    if len(place_id_matches) >= 2:
        return place_id_matches[1]  # 目的地のPlace ID
    return None
```

### 2. タイムスタンプ生成
```python
def generate_google_maps_timestamp(year, month, day, hour, minute):
    """
    Google Maps用のタイムスタンプを生成
    重要: JSTの時刻をUTC基準で計算（タイムゾーン無視）
    """
    from datetime import datetime
    import pytz
    
    # UTC時刻として作成（タイムゾーンを無視）
    utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
    return int(utc_time.timestamp())

# 例: 2025年8月16日 10:00 JST到着
timestamp = generate_google_maps_timestamp(2025, 8, 16, 10, 0)
# → 1755338400
```

### 3. 完全なURL構築
```python
def build_complete_url(origin_info, dest_info, arrival_time):
    """Place IDを含む完全なGoogle Maps URLを構築"""
    
    # 郵便番号付き住所
    origin_str = f"〒{origin_info['postal_code']}+{quote(origin_info['address'])}"
    dest_str = f"〒{dest_info['postal_code']}+{quote(dest_info['address'])}"
    
    # 中心座標
    center_lat = (float(origin_info['lat']) + float(dest_info['lat'])) / 2
    center_lon = (float(origin_info['lon']) + float(dest_info['lon'])) / 2
    
    # URL構築
    url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
    url += f"@{center_lat},{center_lon},16z/"
    
    # dataパラメータ
    data_parts = [
        "!3m1!4b1",  # モード指定（重要）
        "!4m18!4m17",
        f"!1m5!1m1!1s{origin_info['place_id']}!2m2!1d{origin_info['lon']}!2d{origin_info['lat']}",
        f"!1m5!1m1!1s{dest_info['place_id']}!2m2!1d{dest_info['lon']}!2d{dest_info['lat']}",
        f"!2m3!6e1!7e2!8j{timestamp}",  # 時刻指定
        "!3e3"  # 公共交通機関
    ]
    
    url += "data=" + "".join(data_parts)
    return url
```

## 📊 取得済みPlace ID一覧

| 目的地 | Place ID | 住所 |
|--------|----------|------|
| Shizenkan | 0x601889d738b39701:0x996fd0bd4cfffd56 | 東京都中央区日本橋２丁目５−１ |
| 東京アメリカンクラブ | 0x60188bffe47b594f:0xf5b2351645635f1e | 東京都中央区日本橋室町３丁目２−１ |
| axle御茶ノ水 | 0x60188c1a868823d9:0x2a3ffeb1adb0d843 | 東京都千代田区神田小川町３丁目２８−５ |
| Yawara | 0x60188ca49985cf27:0x84d5e5011192e5f0 | 東京都渋谷区神宮前１丁目８−１０ |
| 神谷町(EE) | 0x60188b96cc9f5a69:0xd4e1c1848935ef8e | 東京都港区虎ノ門４丁目２−６ |
| 早稲田大学 | 0x60188d1b65b68f05:0x548ad5986c6f7ee1 | 東京都新宿区西早稲田１丁目６−１ |
| 府中オフィス | 0x6018e499970c7047:0xdb690c7138c3ab0a | 東京都府中市住吉町５丁目２２−５ |
| 東京駅 | 0x60188bf97912d02d:0xee1220ee8337117 | 東京都千代田区丸の内１丁目 |
| 羽田空港 | 0x601863eeef4a0561:0x3c6803c1bc151e2 | 東京都大田区羽田空港3-3-2 |

## ⚠️ 重要な注意点

1. **Place IDは必須** - 住所だけでは不十分
2. **タイムスタンプはUTC基準** - JSTの時刻値をそのまま使用
3. **住所での検索** - 施設名は避ける
4. **!3m1!4b1パラメータ** - モード指定の安定化に重要
5. **パラメータの順序** - Place ID → 座標 → 時刻 → !3e3

## 🚀 次のステップ

1. v4スクレイパーの実装
   - Place ID取得ロジック
   - 正しいURL構築
   - タイムスタンプ生成の修正

2. テストと検証
   - 全9ルートでの動作確認
   - 時刻指定の確認
   - 公共交通機関モードの確認

## まとめ

Google Mapsスクレイピングの成功には：
- **Place IDの取得**が最重要
- **タイムスタンプの特殊仕様**を理解
- **正確な住所**での検索
- **完全なURL構造**の構築

これらの要素を正しく実装することで、確実に動作するスクレイパーが作成できる。