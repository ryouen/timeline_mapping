# アーキテクチャ再設計 - シニアエンジニアの視点

## 根本的な設計の欠陥

### 現在の腐敗した設計
```python
# 1つのクラスが多重責任を持つ（SRP違反）
class GoogleMapsScraper:
    - Place ID取得
    - ルート検索
    - URL構築
    - メモリ管理
    - キャッシュ管理
```

### あるべき設計
```python
# 責任を分離
class PlaceIdResolver:
    """Place IDの取得に専念"""
    
class RouteSearcher:
    """ルート検索に専念"""
    
class BatchProcessor:
    """バッチ処理の制御に専念"""
```

## なぜv5の設計が腐敗したか

### 1. 密結合の罪
```python
# 悪い例（現在）
def scrape_route(self, origin_address, dest_address):
    origin_info = self.get_place_id(origin_address)  # 密結合！
    dest_info = self.get_place_id(dest_address)      # 密結合！
    
# 良い例（あるべき姿）
def scrape_route(self, origin_place_id, dest_place_id):
    # Place IDは外から注入される（依存性逆転）
```

### 2. キャッシュの誤用
```python
# 悪い例（現在）
self.place_id_cache = {}  # インスタンス変数でキャッシュ

# なぜ悪いか：
# - テスト困難
# - 状態依存
# - 予測不可能な動作
```

### 3. 処理フローの混乱
```
現在のフロー（腐敗）：
ルート1: 物件A→目的地1（Place ID取得×2）
ルート2: 物件A→目的地2（Place ID取得×2、Aは重複！）
ルート3: 物件A→目的地3（Place ID取得×2、Aは重複！）
...207回繰り返し

あるべきフロー：
Phase1: 全Place ID取得（32個）
Phase2: 全ルート検索（207個、Place ID渡す）
```

## 段階的改善計画

### Level 1: 最小限の手術（30分）
```python
# Step 1: キャッシュを殺す
# self.place_id_cache = {}  # コメントアウト
# self.route_cache = {}      # コメントアウト

# Step 2: Place ID取得を外部化
def get_all_place_ids(properties, destinations):
    """処理開始時に1回だけ実行"""
    place_ids = {}
    scraper = GoogleMapsScraper()
    scraper.setup_driver()
    
    for prop in properties:
        place_ids[prop['address']] = scraper.get_place_id(prop['address'])
    
    for dest in destinations:
        place_ids[dest['address']] = scraper.get_place_id(dest['address'])
    
    scraper.close()
    return place_ids

# Step 3: scrape_routeを改修
def scrape_route_with_place_ids(self, origin, destination, place_ids):
    """Place IDを外から受け取る"""
    origin_place_id = place_ids.get(origin)
    dest_place_id = place_ids.get(destination)
```

### Level 2: 責任分離（2時間）
```python
# place_id_resolver.py
class PlaceIdResolver:
    def __init__(self):
        self.driver = None
        
    def resolve_all(self, addresses):
        """住所リストからPlace ID辞書を作成"""
        self.setup_driver()
        place_ids = {}
        for address in addresses:
            place_ids[address] = self._get_place_id(address)
        self.close()
        return place_ids

# route_searcher.py  
class RouteSearcher:
    def __init__(self, place_ids):
        self.place_ids = place_ids  # 注入
        self.driver = None
        
    def search_route(self, origin, destination):
        """Place IDを使ってルート検索"""
        origin_id = self.place_ids[origin]
        dest_id = self.place_ids[destination]
        # ルート検索のみに専念

# batch_processor.py
class BatchProcessor:
    def process_all(self):
        # Phase 1: Place ID解決
        resolver = PlaceIdResolver()
        place_ids = resolver.resolve_all(all_addresses)
        
        # Phase 2: ルート検索
        searcher = RouteSearcher(place_ids)
        for origin, dest in routes:
            searcher.search_route(origin, dest)
```

### Level 3: 完全な再設計（8時間）
- イベント駆動アーキテクチャ
- 非同期処理
- リトライ機構
- 監視・ロギング

## キャッシュを消す本当の理由

### 新人の理解
「キャッシュがあるとデバッグしにくい」

### 中級者の理解
「キャッシュの無効化タイミングが不明確」

### シニアの理解
**「キャッシュの存在が設計の腐敗を隠蔽している」**

キャッシュは症状であって原因ではない。
- キャッシュが必要 = 設計が悪い
- 同じPlace IDを何度も取得 = 責任が混在
- インスタンス変数でキャッシュ = 状態管理の失敗

## 今すぐやるべきこと

### 1. キャッシュを消す（5分）
```python
# 以下をコメントアウト
# self.place_id_cache = {}
# self.route_cache = {}
# キャッシュ参照箇所もすべて
```

### 2. Place ID事前取得スクリプト（30分）
```python
# collect_place_ids.py
def main():
    properties = load_json('properties_base.json')
    destinations = load_json('destinations.json')
    
    scraper = GoogleMapsScraper()
    scraper.setup_driver()
    
    # Place IDを収集してJSONに保存
    for prop in properties:
        prop['place_id'] = scraper.get_place_id(prop['address'])
    
    for dest in destinations:
        dest['place_id'] = scraper.get_place_id(dest['address'])
    
    save_json('properties_with_place_id.json', properties)
    save_json('destinations_with_place_id.json', destinations)
    
    scraper.close()
```

### 3. scrape_route改修（30分）
```python
def scrape_route(self, origin_address, dest_address, 
                 origin_place_id=None, dest_place_id=None):
    """
    Place IDを外から受け取れるように改修
    後方互換性のため、なければ取得
    """
    if not origin_place_id:
        origin_info = self.get_place_id(origin_address)
        origin_place_id = origin_info.get('place_id')
    
    if not dest_place_id:
        dest_info = self.get_place_id(dest_address)
        dest_place_id = dest_info.get('place_id')
```

## テスタビリティの向上

### Before（テスト困難）
```python
def test_scrape_route():
    scraper = GoogleMapsScraper()
    # Place ID取得もルート検索も全部実行される
    result = scraper.scrape_route(origin, dest)
```

### After（テスト容易）
```python
def test_scrape_route():
    # Place IDをモック
    mock_place_ids = {'origin': 'ChIJ...', 'dest': 'ChIJ...'}
    
    scraper = GoogleMapsScraper()
    # ルート検索のみテスト
    result = scraper.scrape_route(origin, dest, place_ids=mock_place_ids)
```

## 結論

**キャッシュ削除は始まりに過ぎない**

本当の問題：
1. 責任の混在（SRP違反）
2. 密結合
3. テスト困難
4. 状態管理の失敗

解決策：
1. まずキャッシュを消す（症状を取り除く）
2. Place ID取得を分離（責任を分ける）
3. 依存性を注入（テスト可能にする）

これがシニアエンジニアの視点です。