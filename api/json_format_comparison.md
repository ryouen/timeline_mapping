# JSON形式の比較分析

## 理想形式（properties.json）vs 現在の出力

### 1. 理想的なJSON形式（properties.json）

```json
{
  "destination": "kamiyacho_ee_office",
  "destination_name": "神谷町(EE)",
  "total_time": 29,
  "details": {
    "total_time": 29,
    "walk_to_station": 3,
    "station_used": "神田(東京都)",
    "trains": [
      {
        "line": "東京メトロ銀座線",
        "time": 6,
        "from": "神田(東京都)",
        "to": "銀座",
        "transfer_after": {
          "time": 1,
          "to_line": "東京メトロ日比谷線"
        }
      },
      {
        "line": "東京メトロ日比谷線",
        "time": 6,
        "from": "銀座",
        "to": "神谷町"
      }
    ],
    "walk_from_station": 1,
    "wait_time_minutes": 12
  }
}
```

### 2. 現在のGoogle Maps出力

```json
{
  "status": "success",
  "search_info": {
    "type": "departure",
    "time": "2025-08-12 03:13:10"
  },
  "route": {
    "total_time": 22,
    "details": {
      "walk_to_station": 3,
      "station_used": "神田駅",
      "trains": [
        {
          "line": "銀座線",
          "time": 6,
          "from": "神田",
          "to": "銀座",
          "transfer_after": {
            "time": 4,
            "to_line": "日比谷線"
          }
        },
        {
          "line": "日比谷線",
          "time": 6,
          "from": "銀座",
          "to": "神谷町",
          "wait_time": 6
        }
      ],
      "walk_from_station": 3
    }
  }
}
```

### 3. 差異分析

| 項目 | 理想形式 | 現在の出力 | 対応必要性 |
|------|---------|-----------|------------|
| ルート構造 | 直接的 | route内にネスト | ✅ 要変換 |
| destination | ✅ あり | ❌ なし | ✅ 追加必要 |
| destination_name | ✅ あり | ❌ なし | ✅ 追加必要 |
| total_time（トップレベル） | ✅ あり | ❌ なし | ✅ 追加必要 |
| details.total_time | ✅ あり | ❌ なし | ✅ 追加必要 |
| station_used | "神田(東京都)" | "神田駅" | ✅ 形式統一 |
| trains[].line | "東京メトロ銀座線" | "銀座線" | ✅ 正式名称に |
| trains[].from/to | "(東京都)"付き | シンプル | ✅ 形式統一 |
| wait_time_minutes | ✅ 統合値 | ❌ 個別のwait_time | ✅ 集計必要 |
| transfer_after.to_line | 正式名称 | 略称 | ✅ 形式統一 |

### 4. 必要な変換処理

1. **構造の平坦化**
   - `route.total_time` → `total_time`
   - `route.details` → `details`

2. **メタ情報の追加**
   - `destination`: 目的地ID（別途マッピング必要）
   - `destination_name`: 目的地名

3. **駅名・路線名の正規化**
   - "神田駅" → "神田(東京都)"
   - "銀座線" → "東京メトロ銀座線"
   - "日比谷線" → "東京メトロ日比谷線"

4. **待ち時間の集計**
   - 各trains要素のwait_timeを合計
   - `wait_time_minutes`として統合

5. **不要な情報の削除**
   - `status`
   - `search_info`

### 5. 変換関数の実装案

```python
def convert_to_ideal_format(google_result, destination_id, destination_name):
    """Google Maps出力を理想的な形式に変換"""
    
    if google_result.get("status") != "success":
        return None
    
    route = google_result.get("route", {})
    details = route.get("details", {})
    
    # 待ち時間の集計
    total_wait_time = sum(
        train.get("wait_time", 0) 
        for train in details.get("trains", [])
    )
    
    # 路線名の正規化
    normalized_trains = []
    for train in details.get("trains", []):
        normalized_train = {
            "line": normalize_line_name(train.get("line", "")),
            "time": train.get("time", 0),
            "from": normalize_station_name(train.get("from", "")),
            "to": normalize_station_name(train.get("to", ""))
        }
        
        if "transfer_after" in train:
            normalized_train["transfer_after"] = {
                "time": train["transfer_after"].get("time", 0),
                "to_line": normalize_line_name(
                    train["transfer_after"].get("to_line", "")
                )
            }
        
        normalized_trains.append(normalized_train)
    
    return {
        "destination": destination_id,
        "destination_name": destination_name,
        "total_time": route.get("total_time", 0),
        "details": {
            "total_time": route.get("total_time", 0),
            "walk_to_station": details.get("walk_to_station", 0),
            "station_used": normalize_station_name(
                details.get("station_used", "")
            ),
            "trains": normalized_trains,
            "walk_from_station": details.get("walk_from_station", 0),
            "wait_time_minutes": total_wait_time
        }
    }
```

### 6. 使用状況の最終確認結果

index.htmlとdata-loader.jsを確認した結果：
- **`route.total_time`**: ✅ 使用中（表示に必要）
- **`details.total_time`**: ❌ 未使用（削除可能）
- **その他のdetails内フィールド**: ✅ すべて使用中

### 7. 実装方針

1. **削除するフィールド**
   - `details.total_time`（重複かつ未使用）

2. **必須フィールド**
   - トップレベルの`total_time`
   - `details`内の各種時間情報（walk_to_station、trains、wait_time_minutes等）

3. **変換実装**
   - `google_maps_json_converter.py`を作成
   - details.total_timeは出力しない
   - 駅名・路線名の正規化を実施