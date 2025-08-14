# システムアーキテクチャ分析 - 2025年8月13日

## 現在のシステム構成

### 1. 実際に使用されているファイル

#### フロントエンド
- `json-generator.html` - メインのUI
- `index.html` - 表示用UI

#### APIレイヤー
- `google_maps_integration.php` - APIゲートウェイ（json-generator.htmlから呼ばれる）
- `generate_pdf.php` - PDF処理
- `generate_routes.php` - ダミールート生成（ステップ2で使用）
- `save-simple.php` - JSONファイル保存

#### APIサーバー（port 8000）
**コンテナ内で実行**:
- `/app/src/google_maps_api_server.py` - FastAPIサーバー
- `/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py` - 実際のスクレイピング実装

### 2. 使用されていないファイル

#### 問題のあるファイル
- `google_maps_unified.py` - 3e0パラメータ問題あり
- `google_maps_unified_backup_20250811.py` - バックアップ
- `google_maps_unified_fixed.py` - 未適用の修正版
- `google_maps_unified_safe.py` - 未適用の修正版

#### 古いバージョン・実験的ファイル
- `google_maps_combined.py`
- `google_maps_transit.py`
- `google_maps_transit_v2.py`
- `google_maps_transit_v3.py`
- `google_maps_transit_final.py`
- `google_maps_transit_improved.py`
- `google_maps_transit_ultrathink.py`
- `google_maps_walking_analyzer.py`
- `google_maps_walking_final.py`

#### 代替APIサーバー実装
- `scraper_http_server.py` - 別のHTTPサーバー実装
- `google_maps_api_server_improved.py` - 改良版（未使用）

#### テスト・デバッグファイル
- `test_google_maps.php`
- `test_google_maps_debug.py`
- `test_google_maps_direct.php`
- `test_google_maps_html_capture.py`
- `google_maps_transfer_debug.py`

#### その他の未使用ファイル
- `google_maps_proxy.php`
- `google_maps_route_api.php`
- `google_maps_transit_http.php`
- `google_transit_search.php`
- `maps_test_google_maps.php`
- `here_transit.php`

### 3. システムフロー

```
json-generator.html
    ↓ (Step 3: startRouteSearch)
    ↓ POST /timeline-mapping/api/google_maps_integration.php
    ↓   action: 'getSingleRoute'
    ↓
google_maps_integration.php
    ↓ callExistingAPIServer()
    ↓ POST http://vps_project-scraper-1:8000/api/transit
    ↓
APIサーバー (port 8000)
    ↓ google_maps_api_server.py (FastAPI)
    ↓ import google_maps_transit_docker
    ↓
google_maps_transit_docker.py
    ↓ Selenium + Chrome
    ↓
Google Maps
```

### 4. 重要な発見

1. **arrival_timeパラメータはサポートされているが使用されていない**
   - APIサーバーは arrival_time を受け取れる
   - しかし、json-generator.html は arrival_time を送信していない

2. **URLパラメータ**
   - 現在使用中の google_maps_transit_docker.py は正しく `3e3`（公共交通機関）を使用
   - google_maps_unified.py は誤って `3e0`（車）を使用

3. **時刻指定の実装状況**
   - 現在は「平日午前9時出発」がデフォルト（コード内で明示的な設定なし）
   - 「平日午前10時到着」への変更には arrival_time パラメータの追加が必要

### 5. アーカイブ化の推奨

使用されていないファイルを `/api/archive/2025-08-13-cleanup/` に移動することを推奨します。
これにより、コードベースがクリーンになり、メンテナンスが容易になります。