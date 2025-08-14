# JSONデータ構造の説明

このディレクトリには、時間距離マップアプリケーションで使用される2つのJSONファイルが含まれています。

## 1. `destinations.json` - 目的地リスト

このファイルは、生活の拠点となるすべての目的地を定義しています。各物件からこれらの目的地への移動時間を計算する際の基礎情報となります。

### 構造
```json
{
  "destinations": [
    {
      "id": "shizenkan_univ",
      "name": "Shizenkan University", 
      "category": "school",
      "address": "東京都中央区日本橋2-5-1 髙島屋三井ビルディング 17階",
      "owner": "you",
      "monthly_frequency": 13.2,
      "time_preference": "morning"
    }
  ]
}
```

### フィールド説明
- `id` (String): システム内での一意識別子
- `name` (String): **重要** - properties.jsonのdestinationフィールドとの完全一致が必要
- `category` (String): 目的地の種類（`school`, `gym`, `office`, `station`, `airport`など）
- `address` (String): 住所
- `owner` (String): 利用者（`you`, `partner`, `both`）
- `monthly_frequency` (Number): 月間訪問回数（重要度の算出に使用）
- `time_preference` (String): 利用時間帯（`morning`, `evening`）

## 2. `properties.json` - 物件リスト

このファイルは、検討対象の不動産物件とその詳細な移動情報を定義しています。

### 構造
```json
{
  "properties": [
    {
      "name": "ルフォンプログレ神田プレミア",
      "address": "東京都千代田区神田須田町1丁目20-1", 
      "rent": "280,000円",
      "total_monthly_travel_time": 644,
      "total_monthly_walk_time": 360,
      "stations": [...],
      "routes": [
        {
          "destination": "Shizenkan University",
          "total_time": 13,
          "details": {...}
        }
      ]
    }
  ]
}
```

### フィールド説明
- `name` (String): 物件名
- `address` (String): 物件住所
- `rent` (String): 家賃（表示用文字列）
- `total_monthly_travel_time` (Number): 月間総移動時間（分）
- `total_monthly_walk_time` (Number): 月間総徒歩時間（分）
- `stations` (Array): 最寄り駅情報
  - `name` (String): 駅名
  - `lines` (Array): 利用可能路線
  - `walk_time` (Number): 徒歩時間（分）
- `routes` (Array): 各目的地への経路情報
  - `destination` (String): **重要** - destinations.jsonのnameと完全一致が必要
  - `total_time` (Number): 総移動時間（分）
  - `details` (Object): 詳細な経路情報

### 経路詳細（details）の構造

#### 徒歩のみの場合
```json
{
  "walk_only": true,
  "walk_time": 13
}
```

#### 電車利用の場合
```json
{
  "walk_to_station": 4,
  "station_used": "神田駅",
  "trains": [
    {
      "line": "銀座線",
      "time": 2,
      "from": "神田",
      "to": "日本橋",
      "transfer_after": {
        "time": 4,
        "to_line": "副都心線"
      }
    }
  ],
  "walk_from_station": 7
}
```

## データ整合性の重要なルール

1. **名前の完全一致**: `properties.json`の`routes[].destination`は、`destinations.json`の`name`と**完全一致**する必要があります
2. **重複排除**: 同一物件の重複データは自動的に除去されます
3. **エラーハンドリング**: 不一致の目的地がある場合、コンソールに警告が表示されます

## 新しいデータの追加方法

1. **目的地を追加**: `destinations.json`に新しい目的地オブジェクトを追加
2. **物件を追加**: `properties.json`に新しい物件オブジェクトを追加
3. **経路情報**: 各物件から新目的地への`routes`エントリを追加
4. **名前の確認**: `destination`フィールドが`destinations.json`の`name`と完全一致することを確認

この構造に従うことで、ユーザーが自由にデータを追加・変更できる柔軟なシステムとなっています。