# ゴールデンファイル作成ガイド

このディレクトリには、Google Mapsスクレイピングの検証用ゴールデンファイル（正解データ）を保存します。

## ゴールデンファイルの作成手順

1. 提供されたGoogle Maps URLをブラウザで開く
2. 表示されたルート情報を確認
3. 以下の情報を対応するJSONファイルに記入：

### 必要な情報

- **total_time**: 総所要時間（分）
- **walk_to_station**: 出発地から最初の駅までの徒歩時間（分）
- **station_used**: 最初に使用する駅名（「駅」を除いた名前）
- **trains**: 電車情報の配列
  - **line**: 路線名（例：「地下鉄銀座線」）
  - **time**: 乗車時間（分）
  - **from**: 出発駅名（「駅」を除く）
  - **to**: 到着駅名（「駅」を除く）
- **walk_from_station**: 最後の駅から目的地までの徒歩時間（分）

### 実例

Google Mapsの表示：
```
11:23 - 11:31 （8 分）
徒歩  地下鉄銀座線
神田駅から 11:27

11:23 ルフォンプログレ神田プレミア
徒歩 約 4 分、230 m
11:27 神田駅
地下鉄銀座線各停渋谷行 3 分（2 駅乗車）
11:30 日本橋駅
徒歩 約 1 分、230 m
11:31 日本橋髙島屋三井ビルディング
```

JSONファイルへの記入：
```json
{
  "route": {
    "total_time": 8,
    "details": {
      "wait_time_minutes": 3,
      "walk_to_station": 4,
      "station_used": "神田",
      "trains": [
        {
          "line": "地下鉄銀座線",
          "time": 3,
          "from": "神田",
          "to": "日本橋"
        }
      ],
      "walk_from_station": 1
    }
  }
}
```

## 注意事項

1. **verified_manually**を必ず`true`に変更する
2. 駅名から「駅」を除去する（例：「神田駅」→「神田」）
3. 路線名は正確に記入（例：「地下鉄銀座線」）
4. 時間は分単位で記入
5. 複数の電車を使う場合は、trains配列に順番に追加

## ファイル命名規則

- `{test_id}_{mode}.json`
- test_id: simple_route, complex_route, long_walk_route
- mode: departure, arrival