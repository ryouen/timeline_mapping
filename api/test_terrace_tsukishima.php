<?php
/**
 * テラス月島のルート検索テスト
 */

header('Content-Type: text/plain; charset=utf-8');

echo "🧪 テラス月島 801 ルート検索テスト\n\n";

$origin = "東京都中央区佃2丁目 22-3";
$destinations = [
    ['id' => 'tokyo_station', 'name' => '東京駅', 'address' => '東京駅'],
    ['id' => 'haneda_airport', 'name' => '羽田空港', 'address' => '羽田空港'],
    ['id' => 'kamiyacho', 'name' => '神谷町(EE)', 'address' => '神谷町駅']
];

echo "出発地: $origin\n\n";

foreach ($destinations as $dest) {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    echo "目的地: {$dest['name']} ({$dest['address']})\n";
    
    // 1. APIサーバーに直接リクエスト
    echo "\n1. APIサーバーへの直接リクエスト:\n";
    
    $postData = json_encode([
        'origin' => $origin,
        'destination' => $dest['address']
    ]);
    
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => $postData,
            'timeout' => 45
        ]
    ]);
    
    $startTime = microtime(true);
    $result = @file_get_contents('http://vps_project-scraper-1:8000/api/transit', false, $context);
    $executionTime = microtime(true) - $startTime;
    
    if ($result === false) {
        echo "  ❌ エラー: APIサーバーへの接続失敗\n";
        $error = error_get_last();
        if ($error) {
            echo "  詳細: " . $error['message'] . "\n";
        }
    } else {
        $data = json_decode($result, true);
        if ($data && isset($data['success'])) {
            if ($data['success']) {
                echo "  ✅ 成功 (実行時間: " . number_format($executionTime, 2) . "秒)\n";
                echo "  総所要時間: " . $data['data']['total_time'] . "分\n";
                if (isset($data['data']['route_details'])) {
                    echo "  ルート: " . $data['data']['route_details'] . "\n";
                }
            } else {
                echo "  ❌ エラー: " . ($data['error'] ?? 'Unknown error') . "\n";
                if (isset($data['details'])) {
                    echo "  詳細: " . json_encode($data['details'], JSON_UNESCAPED_UNICODE) . "\n";
                }
            }
        } else {
            echo "  ❌ エラー: 無効なレスポンス\n";
            echo "  レスポンス: " . substr($result, 0, 200) . "...\n";
        }
    }
    
    // 2. google_maps_integration.php経由のテスト
    echo "\n2. google_maps_integration.php経由:\n";
    
    $integrationData = json_encode([
        'action' => 'getSingleRoute',
        'origin' => $origin,
        'destination' => $dest['address'],
        'destinationId' => $dest['id'],
        'destinationName' => $dest['name']
    ]);
    
    $integrationContext = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => $integrationData,
            'timeout' => 45
        ]
    ]);
    
    $startTime2 = microtime(true);
    $result2 = @file_get_contents('https://japandatascience.com/timeline-mapping/api/google_maps_integration.php', false, $integrationContext);
    $executionTime2 = microtime(true) - $startTime2;
    
    if ($result2 === false) {
        echo "  ❌ エラー: 統合APIへの接続失敗\n";
        $error = error_get_last();
        if ($error) {
            echo "  詳細: " . $error['message'] . "\n";
        }
    } else {
        $data2 = json_decode($result2, true);
        if ($data2 && isset($data2['success'])) {
            if ($data2['success']) {
                echo "  ✅ 成功 (実行時間: " . number_format($executionTime2, 2) . "秒)\n";
                if (isset($data2['route']['total_time'])) {
                    echo "  総所要時間: " . $data2['route']['total_time'] . "分\n";
                }
            } else {
                echo "  ❌ エラー: " . ($data2['error'] ?? 'Unknown error') . "\n";
            }
        } else {
            echo "  ❌ エラー: 無効なレスポンス\n";
        }
    }
    
    echo "\n";
    sleep(3); // API負荷軽減
}

echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
echo "診断結果:\n\n";

echo "考えられる原因:\n";
echo "1. 住所形式の問題\n";
echo "   - 「佃2丁目 22-3」という形式がGoogle Mapsで認識されない可能性\n";
echo "   - 「佃2-22-3」または「佃二丁目22番3号」に変更する必要があるかも\n";
echo "\n";
echo "2. タイムアウトの問題\n";
echo "   - 月島から羽田空港は距離があるため、ルート計算に時間がかかる\n";
echo "   - 現在のタイムアウト設定では不十分な可能性\n";
echo "\n";
echo "3. Google Maps APIの制限\n";
echo "   - 短時間に多数のリクエストを送信したため一時的にブロックされた可能性\n";

?>