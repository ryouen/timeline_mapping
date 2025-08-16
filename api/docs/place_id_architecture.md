# Place ID取得システムのアーキテクチャ

## 現在のファイル構成と役割

### ✅ 現在使用中
1. **collect_place_ids.py**
   - 役割: Place ID取得の基盤ライブラリ
   - 使用者: update_station_placeids.py, test_place_id_collection.py
   - 最終更新: 2025-08-17 02:54

2. **update_station_placeids.py**
   - 役割: 東京駅と羽田空港のPlace IDを更新
   - 依存: collect_place_ids.py
   - 最終更新: 2025-08-17 02:54

### ⚠️ 使用状況不明（独立実行）
1. **fetch_all_place_ids_v5.py**
   - 役割: 全物件・全目的地のPlace ID一括取得
   - 依存: なし（独立実行）
   - 最終更新: 2025-08-16 10:18

### 🗑️ 旧バージョン（使用非推奨）
- get_all_place_ids.py
- get_all_place_ids_v2.py
- get_all_place_ids_v3.py
- get_place_ids.py
- get_single_place_id.py
- fetch_place_ids.py

## 推奨される使い方

### 1. 全Place IDを更新したい場合
```bash
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/fetch_all_place_ids_v5.py
```

### 2. 特定の駅・空港だけ更新したい場合
```bash
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/update_station_placeids.py
```

### 3. 新しい場所のPlace IDをテストしたい場合
```bash
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/test_place_id_collection.py
```

## 改善提案

### 短期的改善
1. 旧バージョンファイルを`deprecated/`フォルダに移動
2. 各ファイルの冒頭に「現在使用中」「非推奨」などのステータスを明記

### 長期的改善
1. `collect_place_ids.py`と`fetch_all_place_ids_v5.py`の統合
2. 設定ファイル（config.json）で処理対象を管理
3. コマンドライン引数で動作モードを切り替え
   - `--all`: 全件更新
   - `--stations`: 駅・空港のみ
   - `--test`: テストモード

## データフロー
```
[destinations.json] → [Place ID取得スクリプト] → [Place ID付きdestinations.json]
[properties.json]   → [Place ID取得スクリプト] → [Place ID付きproperties.json]
                                ↓
                    [google_maps_scraper.py]
                    （Place IDを使用してルート検索）
```

## 最終更新: 2025-08-17