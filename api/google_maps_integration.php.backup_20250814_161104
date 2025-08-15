<?php
/**
 * Google Maps Integration API
 * 既存のAPIサーバーを活用した安全な実装
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

function logMessage($message) {
    error_log("[Google Maps Integration] " . $message);
}

function sendError($message, $details = null) {
    $response = ['error' => $message];
    if ($details) {
        $response['details'] = $details;
    }
    echo json_encode($response, JSON_UNESCAPED_UNICODE);
    exit;
}

try {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (!$data) {
        sendError('Invalid JSON data');
    }
    
    $action = $data['action'] ?? '';
    
    switch ($action) {
        case 'getSingleRoute':
            getSingleRoute($data);
            break;
            
        case 'testConnection':
            testConnection();
            break;
            
        default:
            sendError('Invalid action: ' . $action);
    }
    
} catch (Exception $e) {
    logMessage("Exception: " . $e->getMessage());
    sendError('Internal server error', $e->getMessage());
}

/**
 * 単一ルートの検索
 */
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
        
        // ISO形式からDateTime形式に変換
        try {
            $dt = new DateTime($arrivalTime);
            $formattedArrivalTime = $dt->format('Y-m-d H:i:s');
            logMessage("Formatted arrival time: {$formattedArrivalTime}");
        } catch (Exception $e) {
            logMessage("Invalid arrival time format: {$arrivalTime}");
            $formattedArrivalTime = null;
        }
    } else {
        $formattedArrivalTime = null;
    }
    
    // 既存のAPIサーバーを呼び出し（到着時刻付き）
    $result = callExistingAPIServer($origin, $destination, $formattedArrivalTime);
    
    if ($result['success']) {
        // 形式を変換
        $convertedResult = convertToPropertiesFormat(
            $result['data'],
            $destinationId,
            $destinationName
        );
        
        echo json_encode([
            'success' => true,
            'route' => $convertedResult,
            'execution_time' => $result['execution_time'] ?? 0,
            'api_version' => 'google_maps_integration_v1'
        ], JSON_UNESCAPED_UNICODE);
    } else {
        sendError('Route search failed', $result['error']);
    }
}

/**
 * 接続テスト
 */
function testConnection() {
    $startTime = microtime(true);
    
    // ヘルスチェック
    $healthResult = callAPIEndpoint('http://vps_project-scraper-1:8000/health', 'GET');
    
    if (!$healthResult['success']) {
        echo json_encode([
            'success' => false,
            'error' => 'API server not accessible',
            'details' => $healthResult['error']
        ], JSON_UNESCAPED_UNICODE);
        return;
    }
    
    // サンプルルート検索
    $testResult = callExistingAPIServer('東京駅', '渋谷駅');
    
    $executionTime = microtime(true) - $startTime;
    
    echo json_encode([
        'success' => true,
        'health_check' => $healthResult['data'],
        'test_route' => $testResult,
        'execution_time' => $executionTime
    ], JSON_UNESCAPED_UNICODE);
}

/**
 * 既存のAPIサーバーを呼び出し
 */
function callExistingAPIServer($origin, $destination, $arrivalTime = null) {
    $data = [
        'origin' => $origin,
        'destination' => $destination
    ];
    
    if ($arrivalTime) {
        $data['arrival_time'] = $arrivalTime;
    }
    
    return callAPIEndpoint('http://vps_project-scraper-1:8000/api/transit', 'POST', $data);
}

/**
 * APIエンドポイントを呼び出し
 */
function callAPIEndpoint($url, $method = 'GET', $data = null) {
    $startTime = microtime(true);
    
    $context_options = [
        'http' => [
            'method' => $method,
            'timeout' => 30,
            'header' => [
                'Content-Type: application/json',
                'User-Agent: timeline-mapping-integration/1.0'
            ]
        ]
    ];
    
    if ($data && $method === 'POST') {
        $context_options['http']['content'] = json_encode($data);
    }
    
    $context = stream_context_create($context_options);
    $response = @file_get_contents($url, false, $context);
    
    $executionTime = microtime(true) - $startTime;
    
    if ($response === false) {
        return [
            'success' => false,
            'error' => 'HTTP request failed',
            'execution_time' => $executionTime
        ];
    }
    
    $decoded = json_decode($response, true);
    
    if ($decoded === null) {
        return [
            'success' => false,
            'error' => 'Invalid JSON response',
            'raw_response' => substr($response, 0, 200),
            'execution_time' => $executionTime
        ];
    }
    
    return [
        'success' => true,
        'data' => $decoded,
        'execution_time' => $executionTime
    ];
}

/**
 * Google Maps出力をproperties.json形式に変換
 */
function convertToPropertiesFormat($apiResult, $destinationId, $destinationName) {
    if ($apiResult['status'] !== 'success') {
        return null;
    }
    
    $route = $apiResult['route'] ?? [];
    $details = $route['details'] ?? [];
    
    // 待ち時間の集計
    $totalWaitTime = $details['wait_time_minutes'] ?? 0;
    
    // 路線情報の正規化
    $normalizedTrains = [];
    foreach ($details['trains'] ?? [] as $train) {
        $normalizedTrain = [
            'line' => normalizeLineName($train['line'] ?? ''),
            'time' => $train['time'] ?? 0,
            'from' => normalizeStationName($train['from'] ?? ''),
            'to' => normalizeStationName($train['to'] ?? '')
        ];
        
        if (isset($train['transfer_after'])) {
            $transfer = $train['transfer_after'];
            $normalizedTrain['transfer_after'] = [
                'time' => $transfer['time'] ?? 0,
                'to_line' => normalizeLineName($transfer['to_line'] ?? '')
            ];
        }
        
        $normalizedTrains[] = $normalizedTrain;
    }
    
    // 徒歩のみかどうかの判定
    $isWalkingOnly = empty($normalizedTrains) || 
                     ($details['walk_to_station'] ?? 0) + ($details['walk_from_station'] ?? 0) === ($route['total_time'] ?? 0);
    
    if ($isWalkingOnly) {
        return [
            'destination' => $destinationId,
            'destination_name' => $destinationName,
            'total_time' => $route['total_time'] ?? 0,
            'details' => [
                'walk_only' => true,
                'walk_time' => $route['total_time'] ?? 0,
                'walk_to_station' => $route['total_time'] ?? 0,
                'station_used' => '',
                'trains' => [],
                'walk_from_station' => 0,
                'wait_time_minutes' => 0
            ]
        ];
    }
    
    // 電車ルートの場合
    return [
        'destination' => $destinationId,
        'destination_name' => $destinationName,
        'total_time' => $route['total_time'] ?? 0,
        'details' => [
            'walk_to_station' => $details['walk_to_station'] ?? 0,
            'station_used' => normalizeStationName($details['station_used'] ?? ''),
            'trains' => $normalizedTrains,
            'walk_from_station' => $details['walk_from_station'] ?? 0,
            'wait_time_minutes' => $totalWaitTime
        ]
    ];
}

/**
 * 路線名の正規化
 */
function normalizeLineName($lineName) {
    $lineMap = [
        '電車' => '電車', // 既存APIからの汎用的な出力
        '銀座線' => '東京メトロ銀座線',
        '丸ノ内線' => '東京メトロ丸ノ内線',
        '日比谷線' => '東京メトロ日比谷線',
        '東西線' => '東京メトロ東西線',
        '千代田線' => '東京メトロ千代田線',
        '有楽町線' => '東京メトロ有楽町線',
        '半蔵門線' => '東京メトロ半蔵門線',
        '南北線' => '東京メトロ南北線',
        '副都心線' => '東京メトロ副都心線',
        '山手線' => 'JR山手線',
        '中央線' => 'JR中央線',
        '京浜東北線' => 'JR京浜東北線'
    ];
    
    foreach ($lineMap as $pattern => $replacement) {
        if (strpos($lineName, $pattern) !== false) {
            return $replacement;
        }
    }
    
    return $lineName;
}

/**
 * 駅名の正規化
 */
function normalizeStationName($stationName) {
    if (!$stationName) {
        return $stationName;
    }
    
    if (strpos($stationName, '(東京都)') !== false) {
        return $stationName;
    }
    
    // 住所が含まれている場合は簡略化
    if (strpos($stationName, '区') !== false) {
        $parts = explode('区', $stationName);
        $cleanedName = trim($parts[0]) . '区';
        return $cleanedName;
    }
    
    $cleanedName = str_replace('駅', '', $stationName);
    return $cleanedName . '(東京都)';
}

?>