# ゴールデンファイル構造仕様書

## 概要
Google Mapsスクレイピングの検証用ゴールデンファイル（正解データ）の構造と作成方法を定義します。

## ファイル構造

### 基本構造
```json
{
  "test_info": {
    "test_id": "simple_route",
    "test_name": "シンプルルート（乗り換えなし）",
    "mode": "departure",  // または "arrival"
    "origin": "東京都千代田区神田須田町1-20-1 ルフォンプログレ神田プレミア",
    "destination": "東京都中央区日本橋2-5-1 髙島屋三井ビルディング",
    "created_at": "2025-08-14T11:30:00",
    "verified_manually": true  // 手動確認済みフラグ
  },
  "expected_result": {
    "status": "success",
    "search_info": {
      "type": "departure",  // または "arrival"
      "day_of_week": "Thursday",
      "arrival_time": null  // arrival時のみ "2025-08-14 10:00:00"
    },
    "route": {
      "total_time": 29,  // 総所要時間（分）
      "details": {
        "walk_to_station": 4,  // 出発地から最初の駅までの徒歩時間
        "station_used": "神田",  // 最初に使用する駅名
        "trains": [],  // 電車情報の配列（詳細は下記）
        "walk_from_station": 3  // 最後の駅から目的地までの徒歩時間
      }
    }
  }
}
```

### trains配列の構造

#### 基本的な電車情報
```json
{
  "line": "地下鉄銀座線",  // 路線名
  "time": 7,  // 乗車時間（分）
  "from": "神田",  // 出発駅（「駅」を除いた名前）
  "to": "銀座",  // 到着駅（「駅」を除いた名前）
  "departure": "9:05",  // 出発時刻（オプション）
  "arrival": "9:12"  // 到着時刻（オプション）
}
```

#### 乗り換えがある場合
最後の電車以外には`transfer_after`を追加：
```json
{
  "line": "地下鉄銀座線",
  "time": 7,
  "from": "神田",
  "to": "銀座",
  "departure": "9:05",
  "arrival": "9:12",
  "transfer_after": {
    "walk_time": 1,  // 乗り換え徒歩時間（分）
    "wait_time": 3,  // 次の電車までの待ち時間（分）
    "to_station": "銀座"  // 乗り換え先の駅名（同じ駅でも記載）
  }
}
```

## 時間計算のルール

### 1. 総所要時間の検証
```
総所要時間 = 徒歩時間の合計 + 電車乗車時間の合計 + 待ち時間の合計
```

具体的には：
```
total_time = walk_to_station + Σ(train.time) + Σ(transfer.walk_time) + Σ(transfer.wait_time) + walk_from_station
```

### 2. 乗り換え時間の計算
Google Mapsのデータから以下のように計算：
```
待ち時間 = 次の電車の出発時刻 - 前の電車の到着時刻 - 乗り換え徒歩時間
```

例：
- 9:12 銀座駅着
- 徒歩1分
- 9:16 銀座駅発
- 待ち時間 = 9:16 - 9:12 - 1分 = 3分

### 3. 最初の待ち時間（wait_time_minutes）の廃止
以前は出発から最初の駅での電車待ち時間を`wait_time_minutes`として記録していましたが、
この情報は`walk_to_station`に含まれるため、別途記録する必要はありません。

## テストケース

### 1. simple_route - シンプルルート（乗り換えなし）
- 特徴：単一路線での移動
- 例：神田→日本橋（銀座線）

### 2. complex_route - 複数乗り換えルート
- 特徴：複数の路線を乗り継ぐ
- 例：神田→六本木（銀座線→日比谷線）

### 3. long_walk_route - 徒歩が長いルート
- 特徴：駅までの徒歩や乗り換え徒歩が長い
- 例：神田→ダイバーシティ東京（山手線/京浜東北線→ゆりかもめ）

## 作成手順

1. Google Mapsで該当ルートを検索
2. 時刻設定（9時出発または10時到着）を確認
3. 表示された詳細情報から以下を抽出：
   - 総所要時間
   - 各区間の徒歩時間
   - 各電車の路線名、乗車時間、駅名
   - 出発・到着時刻（乗り換え計算用）
4. JSONファイルに記入
5. `verified_manually: true`に変更
6. 時間の合計が正しいか検証（±2分程度の誤差は許容）

## 注意事項

1. **駅名の処理**
   - 「駅」を除去（例：「神田駅」→「神田」）
   - 一貫性を保つ

2. **路線名の正確性**
   - Google Maps表示のまま記載
   - 例：「地下鉄銀座線」「JR山手線」「ゆりかもめ」

3. **時間の単位**
   - すべて分単位（秒は切り捨て）

4. **データの完全性**
   - Google Mapsに表示されたすべての情報を記録
   - 推測や固定値の使用は禁止

## ファイル保存場所
```
/var/www/japandatascience.com/timeline-mapping/api/test_golden/
├── simple_route_departure.json
├── simple_route_arrival.json
├── complex_route_departure.json
├── complex_route_arrival.json
├── long_walk_route_departure.json
└── long_walk_route_arrival.json
```

## 更新履歴
- 2025-08-14: 初版作成
- 2025-08-14: `wait_time_minutes`を廃止し、`transfer_after`構造を追加
- 2025-08-14: 時間計算の詳細ルールを明文化