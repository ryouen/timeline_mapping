# Google Maps 到着時刻指定URL調査報告書

**調査日**: 2025年8月13日  
**調査者**: Claude  
**調査背景**: 「平日午前9時出発」から「平日午前10時到着」への変更

**更新履歴**:
- 2025-08-14: ハイフン問題が実は半角スペース問題であったことを明記

## 1. 現在の問題点

### ~~ハイフンを含む番地とURLパラメータの干渉~~ → 半角スペース問題（2025-08-14更新）

**当初の仮説（誤り）**:
- ハイフン（-）を含む番地がURLパラメータと干渉
- `data=!3m1!4b1!4m2!4m1!3e3` の「!」記号が問題

**真の原因（確定）**:
- **問題の本質**: 丁目と番地の間の半角スペース
- **例**: `佃2丁目 22-3` のスペースがURLエンコードで`%20`に変換
- **解決策**: `re.sub(r'(\d+丁目)\s+(\d+)', r'\1\2', address)`でスペースを削除

## 2. URL形式の比較

### 現在の形式（data=!記法）
```
# 出発時刻指定なし
https://www.google.com/maps/dir/{origin}/{destination}/data=!3m1!4b1!4m2!4m1!3e3

# 到着時刻指定あり（推測）
https://www.google.com/maps/dir/{origin}/{destination}/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{timestamp}!3e3
```

パラメータの意味（推測）:
- `3e3`: 公共交通機関（transit）
- `6e1`: 到着時刻指定
- `7e2`: 平日
- `8j{timestamp}`: Unix timestamp

### 推奨される安全な形式
```
# 出発時刻指定なし
https://www.google.com/maps/dir/{origin}/{destination}/?travelmode=transit

# 到着時刻指定あり
https://www.google.com/maps/dir/{origin}/{destination}/?travelmode=transit&arrival_time={timestamp}
```

## 3. テスト結果

### テストケース
1. テラス月島801: 東京都中央区佃2丁目 22-3
2. 通常の住所: 東京都中央区佃2丁目 12-1  
3. ハイフンが多い住所: 東京都千代田区神田須田町1-20-1

### 結果
- **data=!記法**: すべてのケースで「!」記号を5〜9個含む
- **?travelmode形式**: 「!」記号を一切含まない（安全）

## 4. 実装への影響

### 変更が必要なファイル
1. **google_maps_transit_docker.py** (コンテナ内)
   - URL生成ロジックの変更
   - 到着時刻パラメータの追加

2. **google_maps_integration.php**
   - arrival_timeパラメータの受け渡し

3. **json-generator.html**
   - 到着時刻（平日午前10時）の計算
   - APIへのarrival_timeパラメータ送信

## 5. 推奨される実装方法

### Step 1: URL形式の変更（安全性向上）
```python
# 変更前
url = f"{base_url}{encoded_origin}/{encoded_destination}/data=!3m1!4b1!4m2!4m1!3e3"

# 変更後
url = f"{base_url}{encoded_origin}/{encoded_destination}/?travelmode=transit"
```

### Step 2: 到着時刻指定の追加
```python
if arrival_time:
    timestamp = int(arrival_time.timestamp())
    url += f"&arrival_time={timestamp}"
```

### Step 3: 平日午前10時の計算ロジック
```javascript
function getNextWeekday10AM() {
    const now = new Date();
    let targetDate = new Date(now);
    
    // 今日が平日で10時前なら今日、それ以外は次の平日
    if (now.getDay() >= 1 && now.getDay() <= 5 && now.getHours() < 10) {
        // 今日の10時
    } else {
        // 次の平日を探す
        targetDate.setDate(targetDate.getDate() + 1);
        while (targetDate.getDay() === 0 || targetDate.getDay() === 6) {
            targetDate.setDate(targetDate.getDate() + 1);
        }
    }
    
    targetDate.setHours(10, 0, 0, 0);
    return targetDate;
}
```

## 6. リスクと対策

### リスク
1. Google Maps URLパラメータの非公式性
2. パラメータ形式の将来的な変更可能性
3. Seleniumスクレイピングの安定性

### 対策
1. 両方のURL形式をサポート（フォールバック機能）
2. エラー時の詳細ログ記録
3. 定期的な動作確認テスト

## 7. テスト計画

1. **単体テスト**: URL生成ロジックのテスト
2. **統合テスト**: 実際のGoogle Mapsでの動作確認
3. **回帰テスト**: 既存の184物件すべてで動作確認

## 8. 結論

### 当初の結論（一部誤り）
- ハイフンを含む番地の問題を解決するため、`?travelmode=transit`形式への移行を推奨

### 更新後の結論（2025-08-14）
- **真の問題は半角スペース**であり、住所正規化処理で解決
- `?travelmode=transit`形式はシンプルで保守性が高いため採用
- 到着時刻指定には`arrival_time`パラメータを使用
- 段階的な実装とテストにより、リスクを最小化