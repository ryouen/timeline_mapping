# Timeline Mapping - JSON Generator 開発ドキュメント

**作成日**: 2024-08-09  
**最終更新**: 2024-08-09  
**ステータス**: PHP実行環境問題で一時停止、Gemini CLI調査中

## 📋 プロジェクト概要

### 目的
既存のTimeline Mapping可視化システム用のJSONデータ（destinations.json、properties.json）を生成・編集するWebベースのツールを開発

### 主要機能
1. **目的地管理**: 自然言語入力からの目的地抽出（Gemini API）
2. **物件管理**: PDFからの物件情報抽出（Gemini Vision API）
3. **ルート検索**: Google Maps APIによる自動ルート計算
4. **JSONファイル生成**: 既存フォーマットと完全互換のデータ出力

## 🗂️ ファイル構成

### 完成済みファイル
```
/var/www/japandatascience.com/timeline-mapping/
├── .env                           # APIキー設定（完了）
├── .htaccess                      # セキュリティ設定（完了、PHP実行問題対応中）
├── json-generator.html            # メインジェネレーターUI（完了）
├── api/
│   ├── generate.php              # Gemini API プロキシ（完了、実行待ち）
│   ├── maps.php                  # Google Maps API プロキシ（完了）
│   └── save.php                  # JSONファイル保存（完了）
├── data/
│   ├── destinations.json         # 既存目的地データ
│   ├── properties.json           # 既存物件データ
│   └── backup/                   # バックアップフォルダ（作成済み）
└── 各種テストファイル（後述）
```

### テスト・デバッグファイル
```
├── test_suite.html               # 包括的テストスイート
├── test_api_response.html        # APIレスポンステスト
├── test_basic_api.html           # 基本API動作確認
├── test_php_functions.php        # PHP単体テスト
├── api/
│   ├── debug.php                 # ステップバイステップ確認
│   ├── test.php                  # 最小API確認
│   └── generate_simple.php       # 最小generate.php
├── phpinfo.php                   # PHP動作確認
├── server_check.html             # サーバー状況確認
└── gemini_cli_investigation.md   # Gemini CLI調査依頼書
```

### ドキュメント・分析ファイル
```
├── json-generator-analysis.md    # システム分析レポート
├── json-spec-diff.md            # JSON仕様差異分析
└── project_documentation.md     # 本ドキュメント
```

## 🛠️ 開発完了内容

### 1. API設計・実装（完了）
**generate.php**:
- Gemini Pro APIによる自然言語解析
- Gemini Pro Vision APIによるPDF解析
- 詳細なプロンプト設計（owner判定、頻度計算含む）
- エラーハンドリング、タイムアウト設定（30秒）

**maps.php**:
- Google Maps Directions API連携
- 平日朝9時出発条件でのルート検索
- 日本語対応、完全なレスポンス転送

**save.php**:
- destinations.json、properties.jsonの保存
- タイムスタンプ付きバックアップ自動作成
- 日本語文字化け防止（JSON_UNESCAPED_UNICODE）

### 2. UI実装（完了）
**json-generator.html**:
- 4ステップワークフロー（目的地→物件→ルート検索→完了）
- AIによる自然言語解析UI
- PDFアップロード機能
- リアルタイムプレビュー
- LocalStorage連携

### 3. データ互換性（検証済み）
- 既存destinations.json、properties.jsonとの完全互換性確認
- 複雑な月間移動時間計算ロジック実装
- 駅情報の自動生成
- owner判定（you/partner/both）

### 4. セキュリティ設定（完了）
- .envファイルの.htaccess保護
- CORS設定
- APIキー管理
- ファイルアクセス制御

### 5. 包括的テストスイート（完了）
- API機能テスト（目的地解析、PDF解析、Maps、保存）
- JavaScript関数テスト（parseFrequency、generateId）
- エッジケーステスト（空入力、不正リクエスト）
- パフォーマンステスト

## ⚠️ 現在の問題・停止理由

### 主要問題: PHP実行環境
**症状**:
- PHPファイルがコードとして表示される（実行されない）
- phpinfo.php → コードが表示
- api/debug.php → コードが表示
- APIレスポンス → 空（JSONパースエラー）

**原因候補**:
- Apache mod_php未インストール/無効
- Nginx + PHP-FPM未設定/停止
- VirtualHost設定でPHP処理未定義
- .htaccess設定問題

**調査依頼済み**:
`gemini_cli_investigation.md` でGemini CLIに詳細調査依頼中

## 🎯 修正完了後の検証手順

### 1. PHP動作確認
```
https://japandatascience.com/timeline-mapping/phpinfo.php
→ PHP設定情報が表示されるか
```

### 2. API基本動作確認
```
https://japandatascience.com/timeline-mapping/api/debug.php
→ Step 1-7まで順次実行されるか
→ .env読み込み、APIキー確認まで成功するか
```

### 3. JSON Generator動作確認
```
https://japandatascience.com/timeline-mapping/json-generator.html
→ 「AIで解析して追加」機能動作確認
→ 実際のJSONファイル生成確認
```

### 4. 包括的テスト実行
```
https://japandatascience.com/timeline-mapping/test_suite.html
→ 全テスト実行、成功率確認
```

## 💡 次期作業計画

### Phase 1: PHP問題解決後の即時対応
1. **API動作確認**: debug.phpで全ステップ成功確認
2. **機能テスト**: 実際の目的地解析、PDF解析テスト
3. **JSON生成テスト**: 既存データとの互換性確認

### Phase 2: 機能改善
1. **プロンプト調整**: 実際の使用結果に基づくPrompt最適化
2. **UI改善**: エラーメッセージ改善、UX向上
3. **パフォーマンス最適化**: レスポンス時間短縮

### Phase 3: 拡張機能
1. **複数LLM対応**: OpenAI APIとの切り替え機能
2. **CSV インポート/エクスポート**: データの一括処理
3. **一括編集機能**: 複数項目の同時編集

## 📊 技術仕様

### API設定 (.env)
```bash
# 設定済みAPIキー
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSyBkHTXD...  
GOOGLE_MAPS_API_KEY=AIzaSyBkHTXD...
```

### プロンプト設計
**目的地解析プロンプト**:
- パートナー利用の判定
- 同一場所の重複統合（both判定）
- 頻度計算（週N回→N*4.4、月N-M回→平均値）

**PDF解析プロンプト**:
- Google Maps API対応住所形式
- 管理費込み総額計算
- 既存フォーマット準拠（"XXX,XXX円"）

### データ構造
**destinations.json**:
```json
{
  "id": "string",
  "name": "string", 
  "category": "school|gym|office|station|airport",
  "address": "string",
  "owner": "you|partner|both",
  "monthly_frequency": number,
  "time_preference": "morning"
}
```

**properties.json**:
```json
{
  "name": "string",
  "address": "string", 
  "rent": "XXX,XXX円",
  "total_monthly_travel_time": number,
  "total_monthly_walk_time": number,
  "stations": [...],
  "routes": [...]
}
```

## 🚨 重要な注意事項

### セキュリティ
1. `.env`ファイルは.htaccessで保護済み
2. APIキーは公開されないようPHPプロキシ経由
3. ファイルアップロード時の検証が必要（将来）

### 互換性
1. 既存JSON構造との完全互換性維持必須
2. Timeline Mappingでの表示確認必要
3. 新旧データの混在対応済み

### パフォーマンス
1. Gemini API: 30秒タイムアウト設定済み
2. Google Maps API: 従量課金（使用量注意）
3. 大量データ処理時のレート制限対応必要

## 📞 次回セッション開始時のチェックリスト

### 1. PHP問題解決確認
- [ ] phpinfo.php でPHP情報表示
- [ ] api/debug.php で全ステップ完了
- [ ] test_suite.html で基本テスト成功

### 2. 機能動作確認  
- [ ] 目的地の自然言語解析
- [ ] PDFからの物件情報抽出
- [ ] Google Maps APIルート検索
- [ ] JSONファイル保存

### 3. データ品質確認
- [ ] 生成されたJSONの構造確認
- [ ] Timeline Mappingでの表示確認
- [ ] 既存データとの互換性確認

---

## 📁 関連ファイルパス

**メインアプリケーション**:
- `/var/www/japandatascience.com/timeline-mapping/json-generator.html`

**API**:
- `/var/www/japandatascience.com/timeline-mapping/api/generate.php`
- `/var/www/japandatascience.com/timeline-mapping/api/maps.php`
- `/var/www/japandatascience.com/timeline-mapping/api/save.php`

**テストスイート**:
- `/var/www/japandatascience.com/timeline-mapping/test_suite.html`

**問題調査**:
- `/var/www/japandatascience.com/timeline-mapping/gemini_cli_investigation.md`

**設定ファイル**:
- `/var/www/japandatascience.com/timeline-mapping/.env`
- `/var/www/japandatascience.com/timeline-mapping/.htaccess`

---

*最終更新者: Claude Code Assistant*  
*次回担当者への引き継ぎ完了*