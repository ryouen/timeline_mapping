# JSONファイル命名規則

作成日: 2025-08-13
作成者: Claude Code

## ファイル命名規則

### 1. 基本ファイル

#### destinations.json
- **内容**: 目的地情報（完全版）
- **作成タイミング**: ステップ1（目的地設定）完了時
- **保存場所**: `/timeline-mapping/data/`
- **フォーマット**:
```json
{
    "destinations": [
        {
            "id": "string",
            "name": "string",
            "category": "string",
            "address": "string",
            "owner": "string",
            "monthly_frequency": number,
            "time_preference": "string"
        }
    ]
}
```

#### properties_base.json
- **内容**: 物件基本情報（ルート情報なし）
- **作成タイミング**: PDFアップロード・解析完了時
- **保存場所**: `/timeline-mapping/data/`
- **フォーマット**:
```json
{
    "properties": [
        {
            "name": "string",
            "address": "string",
            "rent": "string",
            "area": "string"  // オプション
        }
    ]
}
```

#### properties.json
- **内容**: 物件情報（ルート情報含む完全版）
- **作成タイミング**: ルート検索完了後、最終保存時
- **保存場所**: `/timeline-mapping/data/`
- **フォーマット**: properties_base.json + routes情報

### 2. バックアップファイル

#### タイムスタンプ付きバックアップ
- **命名規則**: `{ファイル名}_{YYYY-MM-DD_HH-mm-ss}.json`
- **例**: 
  - `destinations_2025-08-13_14-30-45.json`
  - `properties_base_2025-08-13_14-35-20.json`
  - `properties_2025-08-13_15-00-00.json`
- **保存場所**: `/timeline-mapping/data/backup/`

### 3. 実行フロー

1. **ステップ1完了時**
   - `destinations.json` を生成・保存

2. **PDFアップロード時**
   - `properties_base.json` を生成・保存
   - タイムスタンプ付きバックアップも作成

3. **ルート検索完了時**
   - `properties.json` を生成・保存（ルート情報含む）
   - タイムスタンプ付きバックアップも作成

## 利点

1. **段階的保存**: 各ステップで進捗が保存される
2. **データ復旧**: properties_base.jsonがあれば、ルート検索のみやり直し可能
3. **履歴管理**: タイムスタンプ付きバックアップで変更履歴を追跡
4. **明確な命名**: ファイル名から内容が推測可能

## 注意事項

- properties_base.jsonは物件の基本情報のみを含み、ルート情報は含まない
- properties.jsonは最終的な完全データ
- バックアップファイルは定期的に整理することを推奨