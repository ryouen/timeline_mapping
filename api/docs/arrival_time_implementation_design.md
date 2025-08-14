# 到着時刻設定変更 - 実装設計書

**作成日**: 2025年8月13日  
**設計目的**: 「平日午前10時到着」機能の安全かつ確実な実装

## 1. 実装方針

### 1.1 段階的実装アプローチ
**Phase 1**: URL形式の変更（ハイフン問題の解決）  
**Phase 2**: 到着時刻機能の追加  
**Phase 3**: エラーハンドリングとロギングの強化

### 1.2 設計原則
- **後方互換性**: 既存の動作を破壊しない
- **フォールバック**: エラー時は従来の方式に切り替え
- **透明性**: 詳細なログで問題を追跡可能に

## 2. Phase 1: URL形式の変更

### 2.1 google_maps_transit_docker.py の修正

```python
def extract_route_details(driver, origin, destination, arrival_time=None):
    """Extract transit route details from Google Maps"""
    
    # 住所の自動調整（丁目の後のスペースを削除）
    import re
    adjusted_origin = re.sub(r'(\d+丁目)\s+(\d+)', r'\1\2', origin)
    if adjusted_origin != origin:
        print(f"Adjusted origin address: {origin} -> {adjusted_origin}")
        origin = adjusted_origin
    
    # Build URL for transit directions
    base_url = "https://www.google.com/maps/dir/"
    
    # URL encode the locations
    from urllib.parse import quote
    encoded_origin = quote(origin)
    encoded_destination = quote(destination)
    
    # 新しい安全なURL形式を使用
    url = f"{base_url}{encoded_origin}/{encoded_destination}/?travelmode=transit"
    
    # 到着時刻が指定されている場合
    if arrival_time:
        if isinstance(arrival_time, datetime):
            timestamp = int(arrival_time.timestamp())
            url += f"&arrival_time={timestamp}"
            print(f"[DEBUG] Using arrival time: {arrival_time} (timestamp: {timestamp})")
    
    print(f"[DEBUG] Accessing URL: {url}")
    
    # 以下、既存のスクレイピングロジックを維持
```

### 2.2 フォールバック機能の実装

```python
def try_multiple_url_formats(driver, origin, destination, arrival_time=None):
    """複数のURL形式を試行"""
    url_formats = []
    
    # 優先順位1: 新しい安全な形式
    safe_url = build_safe_url(origin, destination, arrival_time)
    url_formats.append(('safe', safe_url))
    
    # 優先順位2: 従来の形式（フォールバック）
    if not arrival_time:  # 到着時刻なしの場合のみ
        legacy_url = build_legacy_url(origin, destination)
        url_formats.append(('legacy', legacy_url))
    
    for format_name, url in url_formats:
        try:
            print(f"[INFO] Trying {format_name} format...")
            driver.get(url)
            # ページロードの確認
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-trip-index]')))
            print(f"[SUCCESS] {format_name} format worked")
            return True
        except TimeoutException:
            print(f"[WARNING] {format_name} format timed out")
            continue
    
    return False
```

## 3. Phase 2: 到着時刻機能の実装

### 3.1 json-generator.html の修正

```javascript
// 平日午前10時到着の時刻を計算
function getNextWeekday10AM() {
    const now = new Date();
    let targetDate = new Date(now);
    
    // 今日が平日で10時前なら今日
    if (now.getDay() >= 1 && now.getDay() <= 5 && now.getHours() < 10) {
        targetDate.setHours(10, 0, 0, 0);
    } else {
        // 次の平日を探す
        targetDate.setDate(targetDate.getDate() + 1);
        while (targetDate.getDay() === 0 || targetDate.getDay() === 6) {
            targetDate.setDate(targetDate.getDate() + 1);
        }
        targetDate.setHours(10, 0, 0, 0);
    }
    
    return targetDate;
}

// searchSingleRoute の修正
async function searchSingleRoute(origin, destination, destinationId, destinationName) {
    try {
        const arrivalTime = getNextWeekday10AM();
        
        const response = await fetch('/timeline-mapping/api/google_maps_integration.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'getSingleRoute',
                origin: origin,
                destination: destination,
                destinationId: destinationId,
                destinationName: destinationName,
                arrivalTime: arrivalTime.toISOString()  // ISO形式で送信
            })
        });
        
        // 以下、既存のロジック
```

### 3.2 google_maps_integration.php の修正

```php
function getSingleRoute($data) {
    $origin = $data['origin'] ?? '';
    $destination = $data['destination'] ?? '';
    $destinationId = $data['destinationId'] ?? '';
    $destinationName = $data['destinationName'] ?? '';
    $arrivalTime = $data['arrivalTime'] ?? null;  // 新規追加
    
    if (!$origin || !$destination) {
        sendError('Origin and destination are required');
    }
    
    logMessage("Route search: {$origin} -> {$destination}");
    if ($arrivalTime) {
        logMessage("Arrival time requested: {$arrivalTime}");
    }
    
    // 既存のAPIサーバーを呼び出し（到着時刻を含む）
    $apiData = [
        'origin' => $origin,
        'destination' => $destination
    ];
    
    if ($arrivalTime) {
        // ISO形式からdatetimeに変換
        $dt = new DateTime($arrivalTime);
        $apiData['arrival_time'] = $dt->format('Y-m-d H:i:s');
    }
    
    $result = callExistingAPIServer($apiData);
    
    // 以下、既存のロジック
```

## 4. Phase 3: エラーハンドリングの強化

### 4.1 詳細なログ記録

```python
# google_maps_transit_docker.py に追加
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/google_maps_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_route_details_with_logging(driver, origin, destination, arrival_time=None):
    """ログ記録付きのルート取得"""
    start_time = datetime.now()
    request_id = f"{start_time.timestamp()}"
    
    logger.info(f"[{request_id}] Starting route search: {origin} -> {destination}")
    if arrival_time:
        logger.info(f"[{request_id}] Arrival time: {arrival_time}")
    
    try:
        result = extract_route_details(driver, origin, destination, arrival_time)
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Success in {duration:.2f}s")
        return result
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{request_id}] Failed after {duration:.2f}s: {str(e)}")
        logger.exception(e)
        raise
```

### 4.2 エラー時の自動リトライ

```python
def extract_route_with_retry(driver, origin, destination, arrival_time=None, max_retries=3):
    """リトライ機能付きルート取得"""
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                time.sleep(2 * attempt)  # 指数バックオフ
            
            return extract_route_details_with_logging(driver, origin, destination, arrival_time)
            
        except TimeoutException:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts")
                raise
```

## 5. テスト計画

### 5.1 単体テスト

```python
# test_url_generation.py
def test_safe_url_generation():
    """安全なURL形式のテスト"""
    test_cases = [
        ("東京都中央区佃2丁目 22-3", "東京駅"),
        ("東京都千代田区神田須田町1-20-1", "渋谷駅"),
    ]
    
    for origin, destination in test_cases:
        url = build_safe_url(origin, destination)
        assert "!" not in url, f"URL contains '!' character: {url}"
        assert "travelmode=transit" in url
```

### 5.2 統合テスト

```bash
# test_integration.sh
#!/bin/bash

# テストケース1: ハイフンを含む住所
echo "Testing problematic address..."
curl -X POST http://localhost:8000/api/transit \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "東京都中央区佃2丁目 22-3",
    "destination": "東京駅",
    "arrival_time": "2025-08-14 10:00:00"
  }'

# 結果を確認
echo "Check if the route was found successfully"
```

## 6. デプロイ手順

### 6.1 事前準備
1. バックアップの確認
2. テスト環境での動作確認
3. ログディレクトリの作成

### 6.2 実装手順
```bash
# 1. コンテナ内のファイルを更新
docker cp google_maps_transit_docker.py vps_project-scraper-1:/app/output/japandatascience.com/timeline-mapping/api/

# 2. APIサーバーの再起動
docker restart vps_project-scraper-1

# 3. ヘルスチェック
curl http://localhost:8000/health

# 4. テスト実行
./test_integration.sh
```

## 7. ロールバック手順

問題が発生した場合：
```bash
# 1. バックアップから復元
cp /home/ubuntu/backup/timeline-mapping/2025-08-13-before-arrival-time-change/*.py .
cp /home/ubuntu/backup/timeline-mapping/2025-08-13-before-arrival-time-change/*.php .
cp /home/ubuntu/backup/timeline-mapping/2025-08-13-before-arrival-time-change/*.html .

# 2. コンテナ内のファイルを復元
docker cp google_maps_transit_docker.py vps_project-scraper-1:/app/output/japandatascience.com/timeline-mapping/api/

# 3. APIサーバーの再起動
docker restart vps_project-scraper-1
```

## 8. 監視項目

1. エラー率の推移
2. 処理時間の変化
3. 特定の物件でのエラー頻度
4. メモリ使用量

## 9. 成功基準

- [ ] テラス月島801のエラーが解消
- [ ] 平日午前10時到着で正しくルート検索
- [ ] エラー率1%未満
- [ ] 平均処理時間が30秒以内