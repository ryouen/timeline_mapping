# Google Maps時刻指定機能の技術調査結果

## 調査日時
2025年8月14日

## 概要
Google Maps APIでの時刻指定ルート検索について、技術仕様と実際の動作を調査しました。

## 主要な発見事項

### 1. URLパラメータの限界
- `departure_time`および`arrival_time`パラメータをURLに含めても、Google Mapsは初期状態では「すぐに出発」を選択
- パラメータは認識されるが、UIに反映されない

### 2. 時刻選択UIの存在
- 「すぐに出発」ボタンをクリックすると、時刻選択メニューが表示される
- メニューには「出発時刻」「到着時刻」の選択肢がある

### 3. 対話的な時刻設定の必要性
- 時刻を指定するには、ページロード後にUIとの対話が必要
- Seleniumなどの自動化ツールでの実装が可能

## テストしたURL形式

### 1. 現在の形式（data=）
```
https://www.google.com/maps/dir/{origin}/{destination}/data=!3m1!4b1!4m2!4m1!3e3
```
- 時刻指定なし、公共交通機関モードのみ

### 2. アプローチA（departure_time）
```
https://www.google.com/maps/dir/{origin}/{destination}/?travelmode=transit&departure_time={timestamp}
```
- タイムスタンプは秒単位（ミリ秒ではない）
- UIには反映されない

### 3. アプローチA（API版）
```
https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=transit&departure_time={timestamp}
```
- 最も標準的なAPI形式
- パラメータは認識されるがUIには反映されない

### 4. アプローチB（data=時刻付き）
```
https://www.google.com/maps/dir/{origin}/{destination}/data=!3e3!6e1!8j{timestamp}
```
- 従来の形式、現在は機能しない可能性

## 実装の改善点

### google_maps_transit_docker_v2.py の新機能

1. **時刻指定UIとの対話**
   - ページロード後に「すぐに出発」ボタンをクリック
   - 時刻選択メニューから「出発時刻」を選択
   - 指定時刻を入力または選択

2. **改善されたコマンドライン引数**
   ```bash
   # 出発時刻指定
   python script.py "東京駅" "渋谷駅" "departure:2024-12-25 08:00:00"
   
   # 到着時刻指定
   python script.py "東京駅" "渋谷駅" "arrival:2024-12-25 09:00:00"
   
   # 現在時刻（デフォルト）
   python script.py "東京駅" "渋谷駅" "now"
   ```

3. **レスポンスの改善**
   - 実際の出発・到着時刻を含む
   - リクエストされた時刻との比較が可能

## 技術的な制約事項

1. **動的なページ読み込み**
   - Google MapsはJavaScriptで動的にコンテンツを生成
   - 十分な待機時間が必要（5秒程度）

2. **UI要素の変動性**
   - Google MapsのUI要素は頻繁に変更される
   - 複数のセレクターを試す必要がある

3. **ヘッドレスモードでの制限**
   - 一部のUI要素がヘッドレスモードで異なる動作をする可能性
   - デバッグ時はスクリーンショットが重要

## 今後の改善提案

1. **エラーハンドリングの強化**
   - 時刻設定が失敗した場合のフォールバック
   - より詳細なエラーメッセージ

2. **時刻プリセットの活用**
   - 正確な時刻入力ができない場合、最も近いプリセット時刻を選択

3. **結果の検証**
   - 設定した時刻が正しく反映されたかの確認
   - 期待される時刻と実際の時刻の差分チェック

## 参考資料

- テストスクリプト: `/var/www/japandatascience.com/timeline-mapping/api/test_google_maps_time*.py`
- テスト結果: `/var/www/japandatascience.com/timeline-mapping/api/test_results_time_format*.json`
- スクリーンショット: `/var/www/japandatascience.com/timeline-mapping/api/test_screenshots/`