# Google Maps URL フォーマット仕様書

## 概要
Google Mapsで公共交通機関ルートを時刻指定付きで検索するための正しいURLフォーマット。

## 動作確認済みのURL例

```
https://www.google.com/maps/dir/東京都千代田区神田須田町1-20-1/東京都千代田区丸の内１丁目９番１号/data=!4m18!4m17!1m5!1m1!1sChIJ2RxO9gKMGGARSvjnp3ocfJg!2m2!1d139.7711!2d35.6950!1m5!1m1!1sChIJGWlcqP6LGGARddFD1M78MhU!2m2!1d139.7676!2d35.6812!2m3!6e1!7e2!8j1755511200!3e3
```

## URL構造

### 基本構造
```
https://www.google.com/maps/dir/{出発地住所}/{目的地住所}/data={dataパラメータ}
```

### dataパラメータの詳細構造

```
!4m18!4m17                                      // ヘッダー（固定）
!1m5!1m1!1s{出発地Place ID}!2m2!1d{経度}!2d{緯度}  // 出発地ブロック
!1m5!1m1!1s{目的地Place ID}!2m2!1d{経度}!2d{緯度}  // 目的地ブロック  
!2m3!6e1!7e2!8j{タイムスタンプ}                    // 時刻指定ブロック
!3e3                                            // 公共交通機関モード
```

## 重要なポイント

### 1. Place ID形式
- **ChIJ形式**: `ChIJ2RxO9gKMGGARSvjnp3ocfJg` ✅ 動作確認済み
- **0x形式**: `0x60188c02f64e1cd9:0x987c1c7aa7e7f84a` ✅ 動作確認済み

### 2. タイムスタンプの計算方法

**重要**: JSTの時刻をUTC基準で計算する（タイムゾーンを無視）

```python
from datetime import datetime
import pytz

def generate_google_maps_timestamp(year, month, day, hour, minute):
    """
    Google Maps用のタイムスタンプを生成
    重要: JSTの時刻をUTC基準で計算（タイムゾーン無視）
    """
    # UTC時刻として作成（タイムゾーンを無視）
    utc_time = datetime(year, month, day, hour, minute, 0, tzinfo=pytz.UTC)
    return int(utc_time.timestamp())

# 例: 2025年8月18日 10:00 JST
timestamp = generate_google_maps_timestamp(2025, 8, 18, 10, 0)
# → 1755511200
```

### 3. 緯度経度の形式
- 小数点4桁まで: `139.7711`, `35.6950`
- 順序に注意: `!1d{経度}!2d{緯度}`

### 4. パラメータの順序（重要）

正しい順序:
1. ヘッダー (`!4m18!4m17`)
2. 出発地ブロック
3. 目的地ブロック
4. 時刻指定ブロック
5. 公共交通機関モード (`!3e3`)

**注意**: `!3e3`を時刻指定の前に配置すると動作しない

## 動作しないパターン

### ❌ API形式での直接Place ID指定
```
https://www.google.com/maps/dir/?api=1&origin=place_id:ChIJ...&destination=place_id:ChIJ...
```
→ ルート要素が表示されない

### ❌ タイムスタンプ計算を正しくJSTで行う
```python
jst = pytz.timezone('Asia/Tokyo')
jst_time = jst.localize(datetime(year, month, day, hour, minute, 0))
return int(jst_time.timestamp())
```
→ タイムスタンプが9時間ずれる（1755478800になってしまう）

## 実装例

```python
def build_url_with_timestamp(origin_info, dest_info, arrival_time):
    """
    タイムスタンプ付きURLを構築
    """
    from urllib.parse import quote
    import pytz
    
    # 住所をエンコード
    origin_str = quote(origin_info['normalized_address'])
    dest_str = quote(dest_info['normalized_address'])
    
    # 基本URL
    url = f"https://www.google.com/maps/dir/{origin_str}/{dest_str}/"
    
    # dataパラメータの構築
    data_parts = []
    
    if origin_info.get('place_id') and dest_info.get('place_id'):
        data_parts.append("!4m18!4m17")
        
        # 出発地ブロック
        data_parts.append("!1m5!1m1")
        data_parts.append(f"!1s{origin_info['place_id']}")
        if origin_info.get('lon') and origin_info.get('lat'):
            data_parts.append(f"!2m2!1d{float(origin_info['lon']):.4f}!2d{float(origin_info['lat']):.4f}")
        
        # 目的地ブロック
        data_parts.append("!1m5!1m1")
        data_parts.append(f"!1s{dest_info['place_id']}")
        if dest_info.get('lon') and dest_info.get('lat'):
            data_parts.append(f"!2m2!1d{float(dest_info['lon']):.4f}!2d{float(dest_info['lat']):.4f}")
        
        # 時刻指定
        if arrival_time:
            jst = pytz.timezone('Asia/Tokyo')
            arrival_jst = arrival_time.astimezone(jst)
            # UTC基準で計算（重要）
            utc_time = datetime(
                arrival_jst.year, arrival_jst.month, arrival_jst.day,
                arrival_jst.hour, arrival_jst.minute, 0, 
                tzinfo=pytz.UTC
            )
            timestamp = int(utc_time.timestamp())
            data_parts.append(f"!2m3!6e1!7e2!8j{timestamp}")
        
        # 公共交通機関モード（最後）
        data_parts.append("!3e3")
    
    if data_parts:
        url += "data=" + "".join(data_parts)
    
    return url
```

## テスト済み動作環境
- 作成日: 2025年8月17日
- テスト環境: Google Maps (日本語版)
- ブラウザ: Chrome (Headless)
- Selenium WebDriver

## 既知の問題
- ルート要素をクリック後、`data-trip-index`属性が消えてDOM構造が変わる
- 解決策: クリック前にデータを取得するか、クリック後の新しいDOM構造に対応する必要がある