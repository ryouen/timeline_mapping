# improvedから削除すべき害悪コード一覧

## 削除対象行番号と理由

### ハードコード初期値（402-407行）
```python
walk_to_station = 5      # ❌ 削除 - 固定値
walk_from_station = 5    # ❌ 削除 - 固定値  
wait_time_minutes = 3    # ❌ 削除 - 固定値
total_minutes = 30       # ❌ 削除 - 固定値
```

### デフォルト値の強制
- 417行: `'time': step.get('duration', 10)` → 10分デフォルト
- 450行: `train_time = max(..., 5)` → 最低5分強制
- 477行: `total_minutes = ... or 30` → 30分デフォルト
- 482行: `'time': max(train_time, 10)` → 最低10分強制
- 503行: `sum(train.get('time', 10) ...)` → 10分デフォルト

### 「不明」という偽データ
- 418-419行: `'from': step.get('station', '不明')`, `'to': '不明'`
- 430行: `if not station_used and train_info['from'] != '不明'`
- 452-453行: `from_station = '不明'`, `to_station = '不明'`
- 468行: `if not station_used and from_station != '不明'`
- 493行: `'station_used': station_used or '不明'`

### フォールバック処理全体（441-487行）
- サマリーフォールバック: 推定値を作る処理
- 最終フォールバック: 完全な嘘データ生成

### その他の偽データ
- 481行: `'line': '電車'` - 実際の路線名ではない
- 483-484行: 住所分割で駅名推定 - 住所≠駅名

## 移植する良い機能

### 詳細ボタンクリック（234-291行）
```python
def click_route_details(driver):
    # 複数セレクタで詳細ボタンを探す
    # クリックして詳細を展開
```

### ステップ抽出（176-232行）
```python
def extract_route_steps_detailed(driver):
    # 複数セレクタでステップを抽出
    # ただし「不明」やデフォルト値は使わない
```

## 重要な原則
- **取得できたデータのみを使用**
- **取得できない場合はエラーを返す**
- **推定・仮定・デフォルト値は一切使わない**