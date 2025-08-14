<?php
/**
 * エラーハンドリングテスト
 * 無効な入力での動作確認
 */

header('Content-Type: text/plain; charset=utf-8');

function runErrorHandlingTest() {
    echo "🧪 エラーハンドリングテスト開始\n\n";
    
    $errorTestCases = [
        [
            'name' => '無効な住所',
            'origin' => '存在しない住所12345',
            'destination' => '東京駅',
            'destinationId' => 'tokyo_station',
            'destinationName' => '東京駅',
            'expected' => 'graceful_error'
        ],
        [
            'name' => '空の住所',
            'origin' => '',
            'destination' => '東京駅',
            'destinationId' => 'tokyo_station', 
            'destinationName' => '東京駅',
            'expected' => 'validation_error'
        ],
        [
            'name' => '海外住所',
            'origin' => 'New York, USA',
            'destination' => '東京駅',
            'destinationId' => 'tokyo_station',
            'destinationName' => '東京駅',
            'expected' => 'no_route_or_error'
        ],
        [
            'name' => '非常に遠い場所',
            'origin' => '北海道札幌市',
            'destination' => '沖縄県那覇市',
            'destinationId' => 'naha',
            'destinationName' => '那覇市',
            'expected' => 'long_route_or_error'
        ]
    ];
    
    $testResults = [];
    
    foreach ($errorTestCases as $index => $testCase) {
        $testNumber = $index + 1;
        echo "🧪 エラーテスト {$testNumber}: {$testCase['name']}\n";
        echo "   入力: '{$testCase['origin']}' → '{$testCase['destination']}'\n";
        
        $startTime = microtime(true);
        $result = callRouteAPI(
            $testCase['origin'],
            $testCase['destination'],
            $testCase['destinationId'],
            $testCase['destinationName']
        );
        $executionTime = microtime(true) - $startTime;
        
        $testResults[] = analyzeErrorResult($testCase, $result, $executionTime);
        
        echo "   実行時間: " . number_format($executionTime, 2) . "秒\n";
        echo "\n";
        
        sleep(2); // 負荷軽減
    }
    
    // テスト結果サマリー
    echo "📊 エラーハンドリング結果サマリー\n";
    echo "=" . str_repeat("=", 50) . "\n";
    
    $gracefulErrors = 0;
    $hardErrors = 0;
    $unexpectedSuccess = 0;
    
    foreach ($testResults as $result) {
        echo "テスト: {$result['test_name']}\n";
        echo "  結果: {$result['result_type']}\n";
        echo "  評価: {$result['evaluation']}\n\n";
        
        switch ($result['evaluation']) {
            case 'PASS':
                $gracefulErrors++;
                break;
            case 'UNEXPECTED_SUCCESS':
                $unexpectedSuccess++;
                break;
            case 'HARD_ERROR':
                $hardErrors++;
                break;
        }
    }
    
    echo "総合評価:\n";
    echo "  適切なエラー処理: {$gracefulErrors}件\n";
    echo "  予期しない成功: {$unexpectedSuccess}件\n";
    echo "  ハードエラー: {$hardErrors}件\n";
    
    $totalTests = count($testResults);
    $healthScore = round(($gracefulErrors + $unexpectedSuccess) / $totalTests * 100, 1);
    echo "  システム健全性: {$healthScore}%\n";
    
    if ($hardErrors === 0) {
        echo "✅ エラーハンドリング: 良好\n";
    } else {
        echo "⚠️  エラーハンドリング: 改善必要\n";
    }
    
    return $testResults;
}

function analyzeErrorResult($testCase, $result, $executionTime) {
    $testName = $testCase['name'];
    $expected = $testCase['expected'];
    
    if ($result['success']) {
        // 成功した場合
        if (in_array($expected, ['graceful_error', 'validation_error'])) {
            // エラーを期待していたが成功
            return [
                'test_name' => $testName,
                'result_type' => 'Unexpected Success',
                'evaluation' => 'UNEXPECTED_SUCCESS',
                'details' => '期待されたエラーが発生せず成功した',
                'execution_time' => $executionTime
            ];
        } else {
            // 成功を期待していて成功
            return [
                'test_name' => $testName,
                'result_type' => 'Success',
                'evaluation' => 'PASS',
                'details' => '正常に処理された',
                'execution_time' => $executionTime
            ];
        }
    } else {
        // エラーが発生した場合
        $errorMessage = $result['error'] ?? 'Unknown error';
        
        // エラーメッセージの品質を評価
        if (empty($errorMessage) || $errorMessage === 'Internal server error') {
            return [
                'test_name' => $testName,
                'result_type' => 'Hard Error',
                'evaluation' => 'HARD_ERROR',
                'details' => '不適切なエラーメッセージ: ' . $errorMessage,
                'execution_time' => $executionTime
            ];
        } else {
            return [
                'test_name' => $testName,
                'result_type' => 'Graceful Error',
                'evaluation' => 'PASS',
                'details' => '適切なエラーメッセージ: ' . $errorMessage,
                'execution_time' => $executionTime
            ];
        }
    }
}

function callRouteAPI($origin, $destination, $destinationId, $destinationName) {
    $url = 'https://japandatascience.com/timeline-mapping/api/google_maps_integration.php';
    
    $postData = json_encode([
        'action' => 'getSingleRoute',
        'origin' => $origin,
        'destination' => $destination,
        'destinationId' => $destinationId,
        'destinationName' => $destinationName
    ]);
    
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => [
                'Content-Type: application/json',
                'User-Agent: error-handling-test/1.0'
            ],
            'content' => $postData,
            'timeout' => 60
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ]);
    
    $response = @file_get_contents($url, false, $context);
    
    if ($response === false) {
        return [
            'success' => false,
            'error' => 'HTTP request failed'
        ];
    }
    
    $decoded = json_decode($response, true);
    
    if ($decoded === null) {
        return [
            'success' => false,
            'error' => 'Invalid JSON response'
        ];
    }
    
    return $decoded;
}

// テスト実行
runErrorHandlingTest();

?>