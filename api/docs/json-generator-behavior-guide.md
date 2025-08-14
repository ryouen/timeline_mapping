# json-generator.html 動作仕様書

## 概要

json-generator.htmlは、Timeline Mappingプロジェクトのデータ生成ツールです。目的地と物件情報を入力し、Google Maps APIを使用してルート情報を自動生成し、JSONファイルとして保存します。

## ワークフロー

### 4ステップの処理フロー

1. **目的地設定** → 2. **物件情報** → 3. **ルート検索** → 4. **完了**

## 入力データ

### 1. 目的地情報（可変数）
- **入力方法**:
  - 手動入力（フォーム）
  - 自然言語解析（AI）
- **必須項目**:
  - 目的地名
  - 住所
  - カテゴリー（school/office/gym/station/airport）
  - 利用者（you/partner/both）
  - 訪問頻度（週/月/年単位）
- **データ数**: 制限なし（ユーザーが必要なだけ追加可能）

### 2. 物件情報（可変数）
- **入力方法**:
  - 手動入力（現在の住所）
  - PDF解析（物件リスト）
- **必須項目**:
  - 物件名
  - 住所
  - 家賃（オプション）
- **データ数**: 
  - 最低1件（現在の住所）
  - 上限なし（PDFから複数物件を一括登録可能）

## 処理タイミング

### Step 1: 目的地設定
- **即時処理**:
  - フォーム入力時: 即座にメモリ（destinations配列）に追加
  - 自然言語解析時: `/timeline-mapping/api/generate_test.php`へPOST
- **LocalStorage保存**: 追加/削除のたびに自動保存

### Step 2: 物件情報
- **即時処理**:
  - 手動入力時: 次のステップ移行時にproperties配列に追加
  - PDF解析時: `/timeline-mapping/api/generate_pdf.php`へPOST
- **自動ルート生成**: PDF解析直後に`generate_routes.php`でルート情報生成
- **LocalStorage保存**: 追加/削除のたびに自動保存

### Step 3: ルート検索
- **バッチ処理**:
  - 総ルート数 = 物件数 × 目的地数
  - 各ルートを順次検索（3秒間隔）
  - 進捗をリアルタイム表示
- **API呼び出し**:
  - `/timeline-mapping/api/google_maps_integration.php`経由
  - 内部でポート8000のAPIサーバーを使用

### Step 4: 完了
- **ファイル保存**:
  - `/timeline-mapping/api/save.php`へPOST
  - destinations.jsonとproperties.jsonを同時保存
  - バックアップファイルも自動生成

## 保存ファイル

### 1. destinations.json
```json
{
  "destinations": [
    {
      "id": "waseda_university",
      "name": "早稲田大学",
      "category": "school",
      "address": "東京都新宿区西早稲田1-6-1",
      "owner": "partner",
      "monthly_frequency": 4.4,
      "time_preference": "morning"
    }
  ]
}
```

### 2. properties.json
```json
{
  "properties": [
    {
      "name": "ルフォンプログレ神田プレミア",
      "address": "千代田区神田須田町1-20-1",
      "rent": "280,000",
      "routes": [
        {
          "destination": "waseda_university",
          "destination_name": "早稲田大学",
          "total_time": 25,
          "details": {
            "total_time": 25,
            "walk_to_station": 5,
            "station_used": "神田(東京都)",
            "trains": [...],
            "walk_from_station": 3,
            "wait_time_minutes": 3
          }
        }
      ],
      "total_monthly_travel_time": 220,
      "total_monthly_walk_time": 70.4,
      "stations": [
        {
          "name": "神田(東京都)",
          "lines": ["JR山手線", "東京メトロ銀座線"],
          "walk_times": {
            "JR": 5,
            "メトロ": 5
          }
        }
      ]
    }
  ]
}
```

### 保存場所
- **メインファイル**: `/var/www/japandatascience.com/timeline-mapping/data/`
  - destinations.json
  - properties.json
- **バックアップ**: `/var/www/japandatascience.com/timeline-mapping/data/backup/`
  - destinations_YYYYMMDD_HHMMSS.json
  - properties_YYYYMMDD_HHMMSS.json

## データの可変性

### 目的地数
- **最小**: 1件（少なくとも1つの目的地が必要）
- **最大**: 制限なし
- **実用的な範囲**: 5-20件程度

### 物件数
- **最小**: 1件（現在の住所）
- **最大**: 制限なし
- **実用的な範囲**: 10-30件程度
- **PDFからの一括登録**: 物件リストPDFから自動抽出

### ルート数
- **計算式**: 物件数 × 目的地数
- **例**: 18物件 × 8目的地 = 144ルート
- **処理時間**: 1ルートあたり約15秒（API制限含む）

## 特殊な処理

### 1. 頻度の自動計算
- 「週3回」→ 月13.2回に自動変換
- 「月2回」→ そのまま月2回
- 「年6回」→ 月0.5回に変換

### 2. 駅情報の自動集約
- 複数ルートから最寄り駅を自動抽出
- 路線ごとの徒歩時間を記録
- 重複を除いた駅リストを生成

### 3. 月間移動時間の計算
- 往復を考慮（×2）
- 訪問頻度を乗算
- 全目的地の合計を算出

## エラーハンドリング

### API障害時
- 個別ルートの失敗は記録して続行
- 最終的な成功/失敗数を表示
- 部分的な結果でもJSON生成可能

### ネットワークエラー
- LocalStorageにデータを保持
- 再実行時に途中から再開可能
- タイムアウト設定: 30秒

## 注意事項

1. **API使用量**
   - Google Maps APIは従量課金
   - 大量のルート検索はコストに注意
   - 3秒間隔で負荷分散

2. **処理時間**
   - 100ルート以上は10分以上かかる可能性
   - ブラウザを閉じないよう注意
   - バックグラウンドタブでも処理継続

3. **データ整合性**
   - 既存のTimeline Mappingと完全互換
   - 18物件は2025年8月12日時点の数値
   - ユーザーの入力により増減可能

## 関連ファイル

- `/timeline-mapping/json-generator.html` - メインツール
- `/timeline-mapping/api/generate_test.php` - 自然言語解析API
- `/timeline-mapping/api/generate_pdf.php` - PDF解析API  
- `/timeline-mapping/api/generate_routes.php` - ルート生成API
- `/timeline-mapping/api/google_maps_integration.php` - Google Maps統合API
- `/timeline-mapping/api/save.php` - ファイル保存API
- `/timeline-mapping/data/destinations.json` - 目的地データ
- `/timeline-mapping/data/properties.json` - 物件データ