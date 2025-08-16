# Timeline Mapping API

## 現在使用中のファイル（2025-08-17更新）

### メインコンポーネント
- `google_maps_scraper.py` - 唯一のメインGoogleMapsスクレーパー（詳細情報取得対応）
- `google_maps_api_server.py` - FastAPI HTTPサーバー（Port 8000）
- `google_maps_integration.php` - PHP API（json-generator.htmlから使用）
- `collect_place_ids.py` - Place ID取得スクリプト

### テストファイル（今日作業中）
- `test_route_click.py` - ルートクリックテスト
- `test_timeout_debug.py` - タイムアウトデバッグ
- `test_detailed_extraction.py` - 詳細情報抽出テスト

### ユーティリティ
- `update_station_placeids.py` - 駅・空港のPlace ID更新

## アーカイブ済み
- `/archive/old_versions/` - 旧バージョン（v2, v3, v5など）
- `/archive/tests/` - 古いテストファイル
- `/archive/place_id_old/` - 古いPlace ID取得スクリプト
- `/archive/debug/` - デバッグファイル
- `/backup/` - バックアップファイル

## 使用方法

### Place ID更新
```bash
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/collect_place_ids.py
```

### ルート取得
```bash
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_scraper.py
```

## 注意事項
- 新しいバージョンを作る前に、既存ファイルの修正を検討
- テストファイルは作業後にアーカイブへ移動
- バックアップは`/backup/`フォルダへ