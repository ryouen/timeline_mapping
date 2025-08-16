# キャッシュ削除の影響分析と対策
作成日: 2025-08-16

## 現在のキャッシュ実装

### 1. place_id_cache
```python
# google_maps_scraper.py
# 35行目
self.place_id_cache = {}  # Place IDキャッシュ

# 使用箇所
# 105-107行目（get_place_id内）
if normalized in self.place_id_cache:
    logger.debug(f"⚡ キャッシュからPlace ID取得: {name or address[:30]}...")
    return self.place_id_cache[normalized]

# 149-150行目（get_place_id内）
# キャッシュに保存
self.place_id_cache[normalized] = result
```

### 2. route_cache
```python
# google_maps_scraper.py
# 36行目
self.route_cache = {}  # ルート結果キャッシュ

# 使用箇所
# 472-476行目（scrape_route内）
if cache_key in self.route_cache:
    logger.info(f"⚡ キャッシュからルート取得: {dest_name or dest_address[:30]}...")
    cached_result = self.route_cache[cache_key].copy()
    cached_result['from_cache'] = True
    return cached_result

# 529-530行目（scrape_route内）
# キャッシュに保存
self.route_cache[cache_key] = result
```

## キャッシュ削除の影響

### 負の影響
1. **Place ID取得の重複**
   - 同じ物件/目的地を何度も検索
   - 207回中、多くが重複（23物件×9回、9目的地×23回）
   - 時間増加: 約175回 × 3秒 = 約9分増

2. **ルート検索の重複**
   - デバッグ時の再実行で同じルートを再検索
   - ただし本番では問題なし（各ルート1回のみ）

### 正の影響
1. **開発時のメリット**
   - 常に最新のデータで動作確認
   - キャッシュ由来のバグを排除
   - 動作の再現性を確保

2. **本番時のメリット**
   - Google Maps仕様変更を即座に検知
   - 古いデータによる誤動作を防止

## 対策：セッション内最適化

### 方法1: 事前Place ID収集（推奨）
```python
def collect_place_ids_for_session(properties, destinations):
    """
    1回の処理開始時に全Place IDを収集
    辞書として返す（キャッシュではなく明示的な事前処理）
    """
    place_ids = {}
    
    # 物件のPlace ID取得（23個）
    for prop in properties:
        place_id = get_place_id(prop['address'])
        place_ids[prop['address']] = place_id
    
    # 目的地のPlace ID取得（9個）
    for dest in destinations:
        place_id = get_place_id(dest['address'])
        place_ids[dest['address']] = place_id
    
    return place_ids  # 32個のPlace ID
```

### 方法2: 処理順序の最適化
```python
# 現在: 物件1→9目的地、物件2→9目的地...
# 改善案: 全Place ID取得→全ルート処理

def process_all_routes_optimized():
    # Step 1: Place ID収集（32回）
    all_place_ids = collect_place_ids_for_session()
    
    # Step 2: ルート処理（207回、Place ID取得なし）
    for property in properties:
        for destination in destinations:
            scrape_route_with_place_ids(
                property, 
                destination,
                all_place_ids
            )
```

## 実装優先順位（改訂）

### Phase 0: キャッシュ無効化【最優先】
```python
# google_maps_scraper.py
# コメントアウトする箇所：

# L35-36
# self.place_id_cache = {}  # 無効化
# self.route_cache = {}      # 無効化

# L105-107
# if normalized in self.place_id_cache:
#     logger.debug(f"⚡ キャッシュからPlace ID取得...")
#     return self.place_id_cache[normalized]

# L149-150
# self.place_id_cache[normalized] = result

# L472-476
# if cache_key in self.route_cache:
#     ...
#     return cached_result

# L529-530
# self.route_cache[cache_key] = result
```

### Phase 1: 基盤整備（キャッシュなしで動作）
1. クラス名変更
2. ChIJ対応
3. ビル名削除
4. メモリ管理

### Phase 2: 最適化（キャッシュの代替）
1. Place ID事前収集機能
2. バッチ処理の順序最適化

## キャッシュ削除のリスク評価

| リスク | 影響度 | 緩和策 |
|--------|--------|--------|
| 処理時間増加 | 中 | Place ID事前収集で対応 |
| メモリ使用量変化 | 低 | 影響なし |
| デバッグ効率 | 正の影響 | むしろ改善 |

## 結論

**キャッシュは即座にコメントアウトすべき**

理由：
1. 開発段階では害悪
2. 本番でも別日実行で問題
3. 代替手段（事前収集）が明確

対策：
1. まずキャッシュを無効化
2. 動作確認
3. その後、事前収集機能を実装