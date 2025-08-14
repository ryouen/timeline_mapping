# 📋 テストファイル一覧 - 2025年8月13日

## 🧪 テストスクリプト（/home/ubuntu/）

### Python テストスクリプト

1. **test_arrival_time.py**
   - 目的: 到着時刻機能のテスト
   - 機能: 平日午前10時到着でのルート検索
   - 実行方法: `python3 /home/ubuntu/test_arrival_time.py`

2. **test_google_maps_url_formats.py**
   - 目的: Google Maps URLフォーマットのテスト
   - 機能: 様々なURLパラメータの組み合わせテスト
   - 実行方法: `python3 /home/ubuntu/test_google_maps_url_formats.py`

3. **test_safe_url_format.py**
   - 目的: 安全なURL形式のテスト
   - 機能: 問題のあるパラメータを除外したURL生成
   - 実行方法: `python3 /home/ubuntu/test_safe_url_format.py`

4. **test_here_direct.py**
   - 目的: HERE Maps API直接テスト
   - 機能: HERE Maps APIとの接続確認
   - 実行方法: `python3 /home/ubuntu/test_here_direct.py`

5. **test_here_v8.py**
   - 目的: HERE Maps API v8のテスト
   - 機能: 最新バージョンのAPIテスト
   - 実行方法: `python3 /home/ubuntu/test_here_v8.py`

6. **test_here_other_cities.py**
   - 目的: 他都市でのHERE Maps APIテスト
   - 機能: 東京以外の都市での動作確認
   - 実行方法: `python3 /home/ubuntu/test_here_other_cities.py`

7. **test_here_routing_v8.py**
   - 目的: HERE Maps ルーティングAPI v8テスト
   - 機能: ルート検索機能の詳細テスト
   - 実行方法: `python3 /home/ubuntu/test_here_routing_v8.py`

8. **test_corrected_here.py**
   - 目的: HERE Maps API修正版テスト
   - 機能: バグ修正後の動作確認
   - 実行方法: `python3 /home/ubuntu/test_corrected_here.py`

9. **test_yahoo_direct.py**
   - 目的: Yahoo乗換案内直接テスト
   - 機能: 旧システムとの比較用
   - 実行方法: `python3 /home/ubuntu/test_yahoo_direct.py`

### Shell テストスクリプト

1. **test_arrival_time.sh**
   - 目的: APIエンドポイント経由での到着時刻テスト
   - 機能: curlを使用したAPI統合テスト
   - 実行方法: `bash /home/ubuntu/test_arrival_time.sh`

2. **test_realistic_case.sh**
   - 目的: 実際の使用ケースのテスト
   - 機能: 本番環境想定のシナリオテスト
   - 実行方法: `bash /home/ubuntu/test_realistic_case.sh`

3. **test_api_with_safe_url.sh**
   - 目的: 安全なURL形式でのAPIテスト
   - 機能: 修正版URLパラメータの検証
   - 実行方法: `bash /home/ubuntu/test_api_with_safe_url.sh`

4. **test_phase1_terrace_tsukishima.sh**
   - 目的: テラス月島問題の第1段階テスト
   - 機能: 問題のある物件の個別テスト
   - 実行方法: `bash /home/ubuntu/test_phase1_terrace_tsukishima.sh`

5. **test_integration_phase2.sh**
   - 目的: 統合テストの第2段階
   - 機能: システム全体の統合動作確認
   - 実行方法: `bash /home/ubuntu/test_integration_phase2.sh`

## 📁 バックアップファイル（/home/ubuntu/backup/timeline-mapping/2025-08-13-before-arrival-time-change/）

### 重要なバックアップファイル

1. **json-generator.html**
   - 内容: フロントエンドのメインファイル
   - 重要度: 高（ユーザーインターフェース）

2. **google_maps_integration.php**
   - 内容: APIゲートウェイ
   - 重要度: 高（フロントエンドとバックエンドの橋渡し）

3. **google_maps_api_server.py**
   - 内容: Python APIサーバー
   - 重要度: 高（バックエンドのメインロジック）

4. **google_maps_transit_docker.py**
   - 内容: Dockerコンテナ内で動作するスクレイピングエンジン
   - 重要度: 高（Google Maps連携の核心部分）

5. **generate_routes.php**
   - 内容: ルート生成ロジック
   - 重要度: 中

6. **generate_pdf.php**
   - 内容: PDF生成機能
   - 重要度: 中

7. **save-simple.php**
   - 内容: データ保存機能
   - 重要度: 中

## 🔧 実行時の注意事項

### Pythonスクリプトの実行
- **ローカル実行**: 一部のテストスクリプトはローカルで実行可能
- **コンテナ実行**: Google Maps関連はDockerコンテナ内での実行が必要
  ```bash
  docker exec vps_project-scraper-1 python /app/src/スクリプト名.py
  ```

### Shellスクリプトの実行
- すべてローカルで実行可能
- APIサーバーが起動していることが前提
- 実行前に `chmod +x スクリプト名.sh` で実行権限を付与

## 📝 メモ

- すべてのテストスクリプトは開発・デバッグ用
- 本番環境への影響はない
- テスト実行時はAPIサーバーのログも確認することを推奨
  ```bash
  docker logs -f vps_project-scraper-1
  ```

---
作成日時: 2025年8月13日
用途: テストファイルの一覧と実行方法の記録