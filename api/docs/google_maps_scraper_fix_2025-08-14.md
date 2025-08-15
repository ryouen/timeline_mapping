# Google Maps スクレイパー修正記録

作成日：2025-08-14
作成者：Claude

## 修正の背景

Google Mapsスクレイピングシステムに重大な問題があり、正しいルート情報を取得できない場合に、偽のデータを捏造して返していました。

### 主要な問題点

1. **府中オフィスルートの異常**
   - 実際：神田→府中（約45-50分）
   - 誤って返されていた結果：神田→日本橋（8分）

2. **有害なフォールバック処理**
   - ルート情報が取得できない場合、ハードコーディングされた「神田→日本橋」を返していた
   - エラーを隠蔽し、デバッグを困難にしていた

## 実施した修正

### 1. ハードコーディングされたデフォルト値の削除

#### 修正前（576-585行目）
```python
# 最小限の情報を保証
if not route_info['trains']:
    route_info['trains'] = [{
        'line': '銀座線',
        'time': 3,
        'from': '神田',
        'to': '日本橋'
    }]
    route_info['station_used'] = '神田'
```

#### 修正後
```python
# ルート情報が取得できなかった場合はNoneを返す
if not route_info['trains']:
    logger.warning("No train information could be extracted from page source")
    return None
```

### 2. デフォルト値の削除

#### 修正前（428-434行目）
```python
route_info = {
    'total_time': 8,  # デフォルト
    'trains': [],
    'walk_to_station': 4,
    'walk_from_station': 1,
    'station_used': None
}
```

#### 修正後
```python
route_info = {
    'total_time': None,  # デフォルト値を使わない
    'trains': [],
    'walk_to_station': None,
    'walk_from_station': None,
    'station_used': None
}
```

### 3. エラー時の適切な処理

ルート情報が全く取得できない場合、明確にエラーを返すように修正：

```python
if not route_info or not route_info.get('trains'):
    logger.warning(f"[{request_id}] Component extraction failed, using fallback")
    fallback_info = extract_route_fallback(driver)
    if fallback_info:
        route_info = fallback_info
    else:
        # ルート情報が全く取得できない場合
        logger.error(f"[{request_id}] Failed to extract any route information")
        return {
            'status': 'error',
            'message': 'No route information could be extracted',
            'extraction_info': {
                'method': 'failed',
                'details_expanded': details_expanded,
                'request_id': request_id
            }
        }
```

### 4. 妥当性チェックの追加

府中へのルートは最低でも30分はかかるはずなので、それより短い場合はエラーを返す：

```python
# 妥当性チェック
total_minutes = route_info.get('total_time')
if origin.lower().find('府中') >= 0 or destination.lower().find('府中') >= 0:
    # 府中へのルートは最低でも30分はかかるはず
    if total_minutes < 30:
        logger.error(f"[{request_id}] Suspicious route time to/from Fuchu: {total_minutes} minutes")
        return {
            'status': 'error',
            'message': f'Route time seems incorrect: {total_minutes} minutes to/from Fuchu',
            'extraction_info': {
                'method': 'validation_failed',
                'details_expanded': details_expanded,
                'request_id': request_id,
                'extracted_time': total_minutes
            }
        }
```

## 修正の効果

### 修正前
- エラーが発生しても偽のデータを返す
- デバッグが困難
- ユーザーに誤った情報を提供

### 修正後
- エラーが発生したら明確にエラーを返す
- 問題の特定が容易
- データの信頼性が向上

## テスト結果

府中オフィスルートのテスト：
```bash
docker exec vps_project-scraper-1 python3 /app/output/japandatascience.com/timeline-mapping/api/google_maps_scraper.py \
  "東京都千代田区神田須田町1-20-1" "東京都府中市住吉町5-22-5" departure 9AM
```

結果：
```json
{
  "status": "error",
  "message": "No route information could be extracted",
  "extraction_info": {
    "method": "failed",
    "details_expanded": false,
    "request_id": "東京都千代田区神田須-東京都府中市住吉町5-1755182762.553136"
  }
}
```

これは正しい動作です。偽のデータを返すよりも、エラーを返す方が適切です。

## 今後の課題

1. **スクレイピングロジックの改善**
   - Google Mapsの新しいHTML構造に対応
   - より堅牢な要素選択方法の実装

2. **エラーハンドリングの強化**
   - より詳細なエラー情報の提供
   - リトライメカニズムの実装

3. **Google Maps APIへの移行検討**
   - スクレイピングの代わりに公式APIを使用
   - より安定した結果を得られる可能性

## 学習事項

1. **「常に何か返す」設計の危険性**
   - エラーを隠蔽し、問題の発見を遅らせる
   - ユーザーに誤った情報を提供するリスク

2. **明確なエラーハンドリングの重要性**
   - エラーは明確にエラーとして返す
   - デバッグとメンテナンスが容易になる

3. **データの妥当性チェック**
   - 常識的に考えて異常な値は検出する
   - ビジネスロジックに基づいた検証を実装