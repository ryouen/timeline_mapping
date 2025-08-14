<?php
/**
 * 統合機能実用テスト
 * 小規模データでエンドツーエンドテスト
 */

header('Content-Type: application/json; charset=utf-8');

function runIntegrationTest() {
    echo "🧪 統合機能実用テスト開始\n\n";
    
    // テスト用小規模データ
    $testProperties = [
        [
            'name' => 'テスト物件A',
            'address' => '千代田区神田須田町1-20-1',
            'rent' => '250000'
        ]
    ];
    
    $testDestinations = [
        [
            'id' => 'tokyo_station',
            'name' => '東京駅',
            'address' => '東京駅'
        ],
        [
            'id' => 'shibuya_station', 
            'name' => '渋谷駅',
            'address' => '渋谷駅'
        ]
    ];
    
    $results = [];
    $totalTests = count($testProperties) * count($testDestinations);
    $currentTest = 0;
    
    echo "📊 テスト計画: {$totalTests}ルート\n";
    echo "物件: " . $testProperties[0]['name'] . " (" . $testProperties[0]['address'] . ")\n";
    echo "目的地: " . implode(', ', array_column($testDestinations, 'name')) . "\n\n";
    
    foreach ($testProperties as $property) {
        $propertyResults = [
            'property' => $property,
            'routes' => [],
            'success_count' => 0,
            'error_count' => 0
        ];
        
        foreach ($testDestinations as $destination) {
            $currentTest++;
            echo "🔍 テスト {$currentTest}/{$totalTests}: {$property['name']} → {$destination['name']}\n";
            
            $startTime = microtime(true);
            $result = callRouteAPI(
                $property['address'], 
                $destination['address'],
                $destination['id'],
                $destination['name']
            );
            $executionTime = microtime(true) - $startTime;
            
            if ($result['success']) {
                $propertyResults['routes'][] = $result['route'];
                $propertyResults['success_count']++;
                echo "✅ 成功 (" . number_format($executionTime, 2) . "秒) - 総時間: " . $result['route']['total_time'] . "分\n";
                
                // 詳細表示
                $details = $result['route']['details'];
                echo "   詳細: 徒歩{$details['walk_to_station']}分 + 電車 + 徒歩{$details['walk_from_station']}分\n";
                
            } else {
                $propertyResults['error_count']++;
                echo "❌ 失敗 (" . number_format($executionTime, 2) . "秒): " . $result['error'] . "\n";
            }
            
            echo "\n";
            sleep(2); // 負荷軽減
        }
        
        $results[] = $propertyResults;
    }
    
    // テスト結果サマリー
    echo "📊 テスト結果サマリー\n";
    echo "=" . str_repeat("=", 50) . "\n";
    
    $totalSuccess = 0;
    $totalErrors = 0;
    
    foreach ($results as $result) {
        $totalSuccess += $result['success_count'];
        $totalErrors += $result['error_count'];
        
        echo "物件: " . $result['property']['name'] . "\n";
        echo "  成功: {$result['success_count']}, 失敗: {$result['error_count']}\n";
    }
    
    echo "\n全体結果:\n";
    echo "  成功率: " . round($totalSuccess / $totalTests * 100, 1) . "% ({$totalSuccess}/{$totalTests})\n";
    echo "  失敗: {$totalErrors}件\n";
    
    // JSON出力テスト
    if ($totalSuccess > 0) {
        echo "\n📄 properties.json形式出力テスト\n";
        $propertiesJson = generatePropertiesJson($results);
        
        // ファイル保存
        $testFile = '/tmp/integration_test_properties.json';
        file_put_contents($testFile, json_encode($propertiesJson, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        echo "✅ JSONファイル生成成功: {$testFile}\n";
        
        // 構造検証
        $validation = validatePropertiesJson($propertiesJson);
        if ($validation['valid']) {
            echo "✅ JSON構造検証: 正常\n";
        } else {
            echo "❌ JSON構造検証: エラー - " . $validation['error'] . "\n";
        }
    }
    
    return [
        'test_summary' => [
            'total_tests' => $totalTests,
            'success_count' => $totalSuccess,
            'error_count' => $totalErrors,
            'success_rate' => round($totalSuccess / $totalTests * 100, 1)
        ],
        'results' => $results
    ];
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
                'User-Agent: integration-test/1.0'
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

function generatePropertiesJson($results) {
    $properties = [];
    
    foreach ($results as $result) {
        $property = [
            'name' => $result['property']['name'],
            'address' => $result['property']['address'],
            'rent' => $result['property']['rent'],
            'routes' => $result['routes']
        ];
        
        $properties[] = $property;
    }
    
    return ['properties' => $properties];
}

function validatePropertiesJson($json) {
    if (!isset($json['properties']) || !is_array($json['properties'])) {
        return ['valid' => false, 'error' => 'properties配列が存在しません'];
    }
    
    foreach ($json['properties'] as $property) {
        if (!isset($property['name']) || !isset($property['address']) || !isset($property['routes'])) {
            return ['valid' => false, 'error' => '必須フィールドが不足しています'];
        }
        
        foreach ($property['routes'] as $route) {
            if (!isset($route['destination']) || !isset($route['total_time']) || !isset($route['details'])) {
                return ['valid' => false, 'error' => 'ルート構造が不正です'];
            }
        }
    }
    
    return ['valid' => true];
}

// テスト実行
$result = runIntegrationTest();

?>