# 到着時刻実装の重要な学び

作成日: 2025-08-13
作成者: Claude

## 概要

Timeline Mappingプロジェクトで「平日午前9時出発」から「平日午前10時到着」への変更を実装した際の重要な学びを記録します。

## 1. ハイフン付き住所の問題と解決

### 問題の本質
- 「東京都中央区佃2丁目 22-3」のようなハイフン付き住所でルート検索が失敗
- 184物件中3物件（テラス月島801関連）で発生
- ユーザーは最初「22-3」を例として挙げたが、本質は**ハイフン全般**の問題

### 根本原因
```python
# 問題のあったURL形式
url = f"{base_url}{encoded_origin}/{encoded_destination}/data=!3m1!4b1!4m2!4m1!3e3"
```
- `data=!`パラメータ内の「!」記号がハイフンと干渉
- URL解析時にハイフンが特殊文字として誤解釈される

### 解決策
```python
# 安全なURL形式に変更
url = f"{base_url}{encoded_origin}/{encoded_destination}/?travelmode=transit"
```
- シンプルなクエリパラメータ形式を採用
- 特殊文字の干渉を回避

## 2. システムアーキテクチャの理解

### 処理フロー
```
json-generator.html 
    ↓ (JavaScript: searchSingleRoute)
google_maps_integration.php
    ↓ (HTTP POST)
APIサーバー (port 8000)
    ↓ (Python: FastAPI)
google_maps_transit_docker.py
    ↓ (Selenium WebDriver)
Google Maps
```

### 重要な発見
1. **APIサーバーは既に到着時刻に対応済み**
   - `arrival_time`パラメータを受け取る実装が存在
   - フロントエンドとPHPゲートウェイの修正のみで対応可能

2. **Dockerコンテナ内での実行が必須**
   ```bash
   # 正しい実行方法
   docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/スクリプト名.py
   ```

## 3. 実装の段階的アプローチ

### Phase 1: URL形式の修正とテスト
1. 問題の特定と根本原因の分析
2. 最小限の変更でURL形式を修正
3. テラス月島を含む全物件でテスト実施
4. 成功確認後に次フェーズへ

### Phase 2: 到着時刻機能の実装
1. フロントエンド（json-generator.html）
   - `getNextWeekday10AM()`関数の追加
   - ISO 8601形式での時刻送信

2. PHPゲートウェイ（google_maps_integration.php）
   - 到着時刻パラメータの受け取りと転送
   - DateTime形式への変換処理

3. 表示の更新
   - ステップ3の説明文を「平日午前10時到着」に変更

## 4. テスト戦略

### 単体テスト
- 各コンポーネントを個別にテスト
- curlコマンドで直接APIを呼び出し

### 統合テスト
- エンドツーエンドのフロー確認
- 実際のブラウザ動作を想定したテスト

### 重要なテストケース
1. ハイフン付き住所（テラス月島）
2. 通常の住所
3. 到着時刻ありとなしの比較

## 5. 得られた教訓

### 1. 問題の本質を見極める
- ユーザーの最初の報告（「22-3」）は例示
- 本質的な問題（ハイフン全般）を理解することが重要

### 2. 既存実装の活用
- 新機能追加前に既存コードを十分に調査
- APIサーバーが既に対応していたことで工数削減

### 3. 段階的な実装
- Phase 1で基本問題を解決
- Phase 2で新機能を追加
- 各段階でテストを実施

### 4. バックアップの重要性
```bash
/home/ubuntu/backup/timeline-mapping/2025-08-13-before-arrival-time-change/
```
- 変更前の動作するコードを必ず保存
- ロールバック可能な状態を維持

### 5. ドキュメント化
- 実装中の発見や決定事項を即座に記録
- 将来の保守や拡張のための情報を残す

## 今後の推奨事項

1. **監視の実装**
   - ハイフン付き住所の成功率を定期的に確認
   - 新規物件追加時の動作確認

2. **エラーハンドリングの強化**
   - URL形式のフォールバック機構
   - より詳細なエラーログ

3. **パフォーマンス最適化**
   - 並列処理の活用
   - キャッシュ機構の検討

## 関連ドキュメント
- `/var/www/japandatascience.com/timeline-mapping/api/docs/google_maps_migration_progress.md`
- `/var/www/japandatascience.com/timeline-mapping/api/docs/python_execution_guide.md`
- `/var/www/japandatascience.com/timeline-mapping/api/docs/handover_document_20250813.md`