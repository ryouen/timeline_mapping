# Google Maps Scraper 統合計画書 - v3
作成日: 2025-08-16
最終更新: 2025-08-16 23:00

## 現状と問題

### 基本構成
```
/var/www/japandatascience.com/timeline-mapping/api/
├── google_maps_scraper.py         # v5（時刻抽出OK、ChIJ非対応）
├── google_maps_scraper_v5_cur.py  # 改良版バックアップ（ChIJ対応）
└── google_maps_scraper_improved.py # 複数路線対応版
```

### 主要な問題
1. **キャッシュが開発を妨害** - デバッグ時に古いデータで動作
2. **Place ID取得が非効率** - 207回実行（本来32回で済む）
3. **責任の混在** - scrape_route()内でPlace ID取得とルート検索を実施
4. **ChIJ形式非対応** - 新Google Maps形式のPlace IDが取得不可

## 優先順位付きタスクリスト

### Phase 0: 即座に実施【5分】
#### 0-1. キャッシュ無効化
```python
# google_maps_scraper.py でコメントアウト
# L35-36: インスタンス変数
# self.place_id_cache = {}  # 無効化
# self.route_cache = {}      # 無効化

# L105-107: place_id_cache参照
# if normalized in self.place_id_cache:
#     logger.debug(f"⚡ キャッシュからPlace ID取得...")
#     return self.place_id_cache[normalized]

# L149-150: place_id_cache保存
# self.place_id_cache[normalized] = result

# L472-476: route_cache参照
# if cache_key in self.route_cache:
#     ...
#     return cached_result

# L529-530: route_cache保存
# self.route_cache[cache_key] = result
```

### Phase 1: 基盤修正【30分】
#### 1-1. クラス名統一
```python
# google_maps_scraper.py
L38: class GoogleMapsScraperV5: → class GoogleMapsScraper:
L594: scraper = GoogleMapsScraperV5() → scraper = GoogleMapsScraper()
```

#### 1-2. ChIJ形式Place ID対応
```python
# google_maps_scraper.py get_place_id()メソッド
# L120の後に追加（0x形式の前に）
chij_match = re.search(r'(ChIJ[a-zA-Z0-9\-\_\.]{23})', self.driver.page_source)
if chij_match:
    place_id = chij_match.group(1)
    logger.info(f"   ✅ Place ID取得（ChIJ形式）: {place_id}")
```

#### 1-3. ビル名削除処理
```python
# google_maps_scraper.py get_place_id()メソッド内
# L110の後に追加
def simplify_for_place_id(normalized):
    simplified = normalized
    # ビル名パターンを削除
    patterns = [
        r'\s*\d+階.*$',           # 階数
        r'髙島屋.*$',             # 特定ビル名
        r'三井ビルディング.*$',
        r'ルフォンプログレ.*$',
        r'La\s+Belle.*$',
    ]
    for pattern in patterns:
        simplified = re.sub(pattern, '', simplified, flags=re.IGNORECASE)
    return simplified.strip()

# L111を変更
url = f"https://www.google.com/maps/search/{quote(normalized)}"
↓
simplified = simplify_for_place_id(normalized)
url = f"https://www.google.com/maps/search/{quote(simplified)}"
```

#### 1-4. メモリ管理改善
```python
# google_maps_scraper.py
L441: if self.route_count >= 30: → if self.route_count >= 9:
```

### Phase 2: Place ID分離【1時間】
#### 2-1. Place ID事前取得スクリプト作成
```python
# 新規: collect_place_ids.py
import json
import sys
sys.path.append('/var/www/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

def collect_and_save_place_ids():
    """全物件・目的地のPlace IDを取得してJSONに保存"""
    
    # 1. JSONファイル読み込み
    with open('data/properties_base.json', 'r', encoding='utf-8') as f:
        properties = json.load(f)['properties']
    
    with open('data/destinations.json', 'r', encoding='utf-8') as f:
        destinations = json.load(f)['destinations']
    
    # 2. Place ID取得
    scraper = GoogleMapsScraper()
    scraper.setup_driver()
    
    print(f"物件{len(properties)}件のPlace ID取得中...")
    for i, prop in enumerate(properties, 1):
        result = scraper.get_place_id(prop['address'], prop['name'])
        prop['place_id'] = result.get('place_id')
        prop['lat'] = result.get('lat')
        prop['lon'] = result.get('lon')
        print(f"  {i}/{len(properties)}: {prop['name']}")
    
    print(f"目的地{len(destinations)}件のPlace ID取得中...")
    for i, dest in enumerate(destinations, 1):
        result = scraper.get_place_id(dest['address'], dest['name'])
        dest['place_id'] = result.get('place_id')
        dest['lat'] = result.get('lat')
        dest['lon'] = result.get('lon')
        print(f"  {i}/{len(destinations)}: {dest['name']}")
    
    scraper.close()
    
    # 3. JSONファイル更新
    with open('data/properties_base.json', 'w', encoding='utf-8') as f:
        json.dump({'properties': properties}, f, ensure_ascii=False, indent=2)
    
    with open('data/destinations.json', 'w', encoding='utf-8') as f:
        json.dump({'destinations': destinations}, f, ensure_ascii=False, indent=2)
    
    print("✅ Place ID収集完了")
    return properties, destinations
```

#### 2-2. scrape_route改修
```python
# google_maps_scraper.py scrape_route()メソッド
def scrape_route(self, origin_address, dest_address, dest_name=None, 
                 arrival_time=None, origin_place_id=None, dest_place_id=None):
    """
    Place IDを外部から受け取れるように改修
    引数追加: origin_place_id, dest_place_id
    """
    # Place IDが渡されていない場合のみ取得
    if origin_place_id:
        origin_info = {'place_id': origin_place_id, 'normalized_address': origin_address}
    else:
        origin_info = self.get_place_id(origin_address, "出発地")
    
    if dest_place_id:
        dest_info = {'place_id': dest_place_id, 'normalized_address': dest_address}
    else:
        dest_info = self.get_place_id(dest_address, dest_name)
    
    # 以降は既存処理
```

### Phase 3: バッチ処理改善【30分】
#### 3-1. Place ID付きバッチ処理
```python
# route_scraper_batch.py の改修
def process_all_routes():
    # 1. Place ID付きJSONを読み込み
    with open('data/properties_base.json', 'r') as f:
        properties = json.load(f)['properties']
    with open('data/destinations.json', 'r') as f:
        destinations = json.load(f)['destinations']
    
    # 2. ルート処理（Place IDを渡す）
    scraper = GoogleMapsScraper()
    scraper.setup_driver()
    
    for prop in properties:
        for dest in destinations:
            result = scraper.scrape_route(
                prop['address'],
                dest['address'],
                dest['name'],
                arrival_time,
                origin_place_id=prop.get('place_id'),  # Place IDを渡す
                dest_place_id=dest.get('place_id')     # Place IDを渡す
            )
```

### Phase 4: テストと本番処理【2時間】
#### 4-1. 動作確認
- 1物件×9目的地でテスト
- Place ID事前取得の動作確認
- 時刻抽出の確認

#### 4-2. 本番処理
- La Belle 7ルート再試行
- 残り6物件の処理
- 最終JSON生成

## 実装順序とタイムライン

| 時間 | Phase | 作業内容 | 所要時間 |
|------|-------|----------|----------|
| 即座 | 0 | キャッシュ無効化 | 5分 |
| +5分 | 1-1 | クラス名統一 | 1分 |
| +6分 | 1-2 | ChIJ対応 | 10分 |
| +16分 | 1-3 | ビル名削除 | 10分 |
| +26分 | 1-4 | メモリ管理 | 1分 |
| +27分 | テスト | 基盤動作確認 | 10分 |
| +37分 | 2-1 | Place ID収集スクリプト | 30分 |
| +67分 | 2-2 | scrape_route改修 | 20分 |
| +87分 | 3-1 | バッチ処理改修 | 20分 |
| +107分 | 4 | 本番処理 | 120分 |

## JSONファイル構造（更新後）

### properties_base.json
```json
{
  "properties": [
    {
      "id": "unique_id",
      "name": "物件名",
      "address": "東京都千代田区...",
      "place_id": "ChIJ...",  // 追加
      "lat": 35.123,          // 追加
      "lon": 139.456          // 追加
    }
  ]
}
```

### destinations.json
```json
{
  "destinations": [
    {
      "id": "unique_id",
      "name": "目的地名",
      "address": "東京都中央区...",
      "place_id": "ChIJ...",  // 追加
      "lat": 35.789,          // 追加
      "lon": 139.789          // 追加
    }
  ]
}
```

## エラー処理とログ

### Place ID取得失敗時
```python
if not place_id:
    logger.error(f"Place ID取得失敗: {address}")
    # 住所をそのまま使用（フォールバック）
    return {'place_id': None, 'normalized_address': normalized}
```

### ルート検索失敗時
```python
try:
    result = scraper.scrape_route(...)
except Exception as e:
    logger.error(f"ルート検索失敗: {origin} → {dest}: {e}")
    # エラーを記録して継続
    errors.append({'origin': origin, 'dest': dest, 'error': str(e)})
```

## 引き継ぎ事項

### 次回作業者への申し送り
1. **キャッシュは無効化済み** - 毎回新規取得される
2. **Place IDは事前取得推奨** - collect_place_ids.py実行後にバッチ処理
3. **メモリ管理** - 9ルートごとにWebDriver再起動
4. **エラー物件** - La Belle 三越前は要注意（番地確認済み）

### トラブルシューティング
| 症状 | 原因 | 対処 |
|------|------|------|
| Place ID取得失敗 | ビル名が邪魔 | simplify_for_place_id()に追加 |
| Chrome Renderer timeout | メモリリーク | 再起動間隔を短縮 |
| 料金が999円まで | カンマ非対応 | 正規表現修正（Phase 5で対応） |

## 改訂履歴
- v1: 初版作成
- v2: Place ID事前取得を追加
- v3: キャッシュ削除を最優先に変更、ファイル統合