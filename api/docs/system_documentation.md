# Timeline Mapping システムドキュメント

最終更新: 2025-08-14 08:00 JST
更新者: Claude

## 🚨 重要：作業ディレクトリ

**本番環境での作業は必ずDockerコンテナ経由で行うこと**
- 本番ディレクトリ: `/var/www/japandatascience.com/timeline-mapping/`
- Dockerコンテナ内: `/usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/`
- ❌ 使用禁止: `/home/ubuntu/timeline_mapping/` （古い開発環境）

## 📊 システム構成

### 1. データ生成フロー（json-generator.html）

```
URL: https://japandatascience.com/timeline-mapping/json-generator.html

ステップ1: 目的地設定
    ↓ [次へ] クリック時
    → destinations.json 保存（上書き）

ステップ2: 物件情報
    ↓ PDFアップロード時
    → properties_base.json 保存（バックアップ付き）

ステップ3: ルート検索
    ↓ 検索完了時
    → destinations.json + properties.json 同時保存（上書き）

ステップ4: 完了
```

### 2. 保存されるJSONファイル

| ファイル | 内容 | 保存場所 | バックアップ |
|---------|------|---------|-------------|
| destinations.json | 目的地情報 | `/data/destinations.json` | なし（手動推奨） |
| properties.json | 物件＋ルート情報 | `/data/properties.json` | なし（手動推奨） |
| properties_base.json | 物件基本情報 | `/data/properties_base.json` | 自動（タイムスタンプ付き） |

### 3. APIエンドポイント

#### ルート検索API
```
POST /timeline-mapping/api/google_maps_integration.php
{
    "action": "getSingleRoute",
    "origin": "出発地",
    "destination": "目的地",
    "destinationId": "ID",
    "destinationName": "名前",
    "arrivalTime": "ISO8601形式（オプション）"
}
```

#### 内部構成
```
google_maps_integration.php
    ↓ HTTP通信
scraper:8000/api/transit (FastAPI)
    ↓
google_maps_scraper.py (旧 ultimate)
    ↓
高品質なスクレイピング結果
```

### 4. データ表示（index.html）

```
URL: https://japandatascience.com/timeline-mapping/

読み込みファイル:
- ./data/destinations.json
- ./data/properties.json

表示内容:
- 時間距離マップ
- 物件ランキング
- ルート詳細
```

## 🔧 メンテナンス手順

### データ更新の流れ

1. **バックアップ（重要！）**
```bash
docker exec vps_project-web-1 cp /usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/data/destinations.json /usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/data/backup/destinations_$(date +%Y%m%d_%H%M%S).json

docker exec vps_project-web-1 cp /usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/data/properties.json /usr/local/apache2/htdocs/japandatascience.com/timeline-mapping/data/backup/properties_$(date +%Y%m%d_%H%M%S).json
```

2. **json-generator.htmlでデータ生成**
   - https://japandatascience.com/timeline-mapping/json-generator.html
   - 既存データの復元機能あり
   - ルート検索実行

3. **結果確認**
   - https://japandatascience.com/timeline-mapping/
   - 路線名が具体的か（銀座線、山手線など）
   - 駅名が正確か（神田、日本橋など）

### トラブルシューティング

#### 問題: 路線名が「電車」、駅名が住所の断片
原因: 古いスクレイピングシステムが使用されている
解決: google_maps_integration.phpが正しくgoogle_maps_scraper.pyを呼び出しているか確認

#### 問題: ID表記揺れ（ハイフン vs アンダースコア）
原因: 手動編集または異なる生成ロジック
解決: generateId()関数の統一、LLMプロンプトの明確化

## 📁 ファイル構造

```
timeline-mapping/
├── api/
│   ├── google_maps_scraper.py         # メインスクレイピング
│   ├── google_maps_integration.php    # APIブリッジ
│   ├── save-simple.php               # JSON保存
│   ├── generate_test.php             # Gemini API（目的地解析）
│   └── tests/                        # テストファイル
├── data/
│   ├── destinations.json             # 目的地データ
│   ├── properties.json               # 物件＋ルートデータ
│   ├── properties_base.json          # 物件基本データ
│   └── backup/                       # バックアップ
├── index.html                        # メイン表示
└── json-generator.html               # データ生成ツール
```

## ⚠️ 注意事項

1. **データは上書きされる** - 必ず事前バックアップ
2. **本番作業はDockerコンテナ経由** - 直接ファイル編集禁止
3. **API制限** - スクレイピング間隔は3秒以上空ける
4. **権限** - www-data:www-data で保存される

## 🔍 デバッグ

### ログ確認
```bash
# PHPエラーログ
docker exec vps_project-web-1 tail -f /var/log/apache2/error.log

# スクレイピングログ
docker exec vps_project-scraper-1 tail -f /app/logs/scraper.log
```

### テストツール
- https://japandatascience.com/timeline-mapping/test_integration.html

## 📝 更新履歴

- 2025-08-14: Google Maps高品質スクレイピング実装
- 2025-08-14: ドキュメント作成

---
*このドキュメントは定期的に更新してください*