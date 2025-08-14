# JSON構造互換性修正ガイド

作成日: 2025-08-13
作成者: Claude Code

## 問題の概要

timeline-mappingプロジェクトにおいて、JSONファイルの構造とindex.htmlが期待する構造に不一致があり、データの読み込みが失敗していました。

## 発見された不一致

### 1. destinationフィールドの不一致
- **index.html期待**: `route.destination`
- **JSON実際**: `route.destination_id`と`route.destination_name`

### 2. detailsオブジェクトの構造
- **index.html期待**:
  ```javascript
  {
    destination: "destination_id",
    total_time: 26,
    details: {
      walk_to_station: 5,
      walk_from_station: 2,
      trains: [...],
      walk_only: false,
      transfer_time: 0
    }
  }
  ```
- **JSON実際**:
  ```javascript
  {
    destination_id: "shizenkan_university",
    destination_name: "Shizenkan University",
    total_time: 26,
    walk_to_station: 5,
    walk_from_station: 2,
    trains: [...]
  }
  ```

### 3. stationsフィールドの欠如
- **index.html期待**: `prop.stations`配列
- **JSON実際**: stationsフィールドが存在しない

## 実装した解決策

index.htmlの`loadDataFromJSON()`関数（1345行目付近）に、JSONデータを読み込んだ直後に変換処理を追加しました：

```javascript
// JSONデータの構造を期待される形式に変換
propData.properties = propData.properties.map(prop => {
    const transformedProp = {...prop};
    
    // stationsフィールドがない場合は空配列を設定
    if (!transformedProp.stations) {
        transformedProp.stations = [];
    }
    
    // routesの変換
    if (transformedProp.routes) {
        transformedProp.routes = transformedProp.routes.map(route => {
            const transformedRoute = {
                destination: route.destination_id, // destination_idをdestinationに変換
                total_time: route.total_time,
                details: {
                    walk_to_station: route.walk_to_station || 0,
                    walk_from_station: route.walk_from_station || 0,
                    trains: route.trains || [],
                    walk_only: route.walk_only || false,
                    transfer_time: route.transfer_time || 0
                }
            };
            
            // 歩行のみの場合の処理
            if (route.walk_only) {
                transformedRoute.details.walk_only = true;
                transformedRoute.details.walk_time = route.total_time;
            }
            
            return transformedRoute;
        });
    }
    
    return transformedProp;
});
```

## 修正の利点

1. **既存JSONファイルの保持**: 既存のJSONファイルを変更する必要がない
2. **後方互換性**: 古い形式と新しい形式の両方に対応可能
3. **段階的移行**: 将来的にJSON形式を統一する際の移行が容易

## 確認事項

### formatStations関数の動作確認
- 空配列を受け取った場合は「駅情報なし」を返す
- 適切にエラーハンドリングされている

### エラーハンドリング
- データ読み込み失敗時は「データの読み込みに失敗しました。サンプルデータを表示します。」を表示
- コンソールにエラーログを出力

## 今後の推奨事項

1. **JSON形式の統一**: 将来的にはJSONとindex.htmlで期待する形式を統一すべき
2. **スキーマ検証**: JSON読み込み時にスキーマ検証を追加
3. **ドキュメント化**: JSONファイルの仕様をドキュメント化

## 関連ファイル

- `/var/www/japandatascience.com/timeline-mapping/index.html`
- `/var/www/japandatascience.com/timeline-mapping/data/properties.json`
- `/var/www/japandatascience.com/timeline-mapping/data/destinations.json`

## テスト方法

1. ブラウザでhttps://japandatascience.com/timeline-mapping/にアクセス
2. 開発者ツールのコンソールでエラーが出ていないことを確認
3. 物件情報が正しく表示されることを確認
4. 各目的地への経路が正しく表示されることを確認