# JSON仕様差異分析レポート

## 主要な構造差異

### 1. stations配列の構造変更

#### 既存の構造 (現在のdata/properties.json)
```json
"stations": [
  {
    "name": "神田駅",
    "lines": ["JR山手線", "東京メトロ銀座線"],
    "walk_time": 5  // 単一の数値（分）
  }
]
```

#### 新システムが生成する構造
```json
"stations": [
  {
    "name": "神田駅",
    "lines": ["JR山手線", "東京メトロ銀座線"],
    "walk_times": {  // オブジェクト型（路線グループ別）
      "JR": 5,
      "メトロ": 3
    }
  }
]
```

### 2. destinations.jsonの構造

#### 既存の構造
```json
{
  "id": "shizenkan_univ",  // 必須
  "name": "Shizenkan University",
  "category": "school",
  "address": "東京都中央区日本橋2-5-1",
  "owner": "you",
  "monthly_frequency": 13.2,  // 数値型
  "time_preference": "morning"
}
```

#### 新システムが生成する構造
```json
{
  "id": "dest_1234567890",  // 自動生成ID
  "name": "Shizenkan University",
  "category": "school",
  "address": "東京都中央区日本橋2-5-1",
  "owner": "you",
  "monthly_frequency": 13.2,  // parseFrequency()で計算
  "time_preference": "morning"
}
```

## 影響範囲

### index.htmlへの影響

1. **stations情報の読み取り部分**
   - 現在: `station.walk_time`を直接参照
   - 変更後: `station.walk_time || station.walk_times[lineGroup]`のような条件分岐が必要

2. **表示に影響なし**
   - destinations.idは表示に使用されていない（内部参照のみ）
   - monthly_frequencyの計算ロジックは同じ

## 修正方針

### オプション1: 新システム側を修正（推奨）
json-generator-tool.htmlの`generateStationsArray`関数を修正して、既存フォーマットに合わせる：
- `walk_times`オブジェクトではなく、単一の`walk_time`数値を生成
- 最も短い徒歩時間を採用

### オプション2: index.html側を修正
既存と新規両方のフォーマットに対応：
```javascript
const walkTime = station.walk_time || 
                 (station.walk_times ? Math.min(...Object.values(station.walk_times)) : 0);
```

## 推奨アクション

1. **新システム側の修正を実施**
   - 既存システムとの完全互換性を保つ
   - 破壊的変更を避ける

2. **段階的移行**
   - まず互換性のある形で実装
   - 将来的により詳細な情報が必要になったら拡張

## テスト計画

1. 新システムでJSONを生成
2. 生成されたJSONでindex.htmlが正常動作することを確認
3. 特に以下をチェック：
   - 駅情報の表示
   - 徒歩時間の計算
   - ルート表示の正確性