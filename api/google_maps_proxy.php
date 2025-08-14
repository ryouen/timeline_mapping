<?php
/**
 * Google Maps Route Proxy API
 * Dockerコンテナ間通信用のプロキシ
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

function logError($message) {
    error_log("[Google Maps Proxy] " . $message);
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
            
        case 'getBulkRoutes':
            getBulkRoutes($data);
            break;
            
        default:
            sendError('Invalid action: ' . $action);
    }
    
} catch (Exception $e) {
    logError("Exception: " . $e->getMessage());
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
    
    if (!$origin || !$destination) {
        sendError('Origin and destination are required');
    }
    
    // Scraperコンテナ内のHTTPサーバーに接続
    $result = callScraperHTTPAPI($origin, $destination);
    
    if ($result['success']) {
        // JSON形式を変換
        $convertedResult = convertToPropertiesFormat(
            $result['data'], 
            $destinationId, 
            $destinationName
        );
        
        echo json_encode([
            'success' => true,
            'route' => $convertedResult
        ], JSON_UNESCAPED_UNICODE);
    } else {
        sendError('Route search failed', $result['error']);
    }
}

/**
 * 複数ルートの一括検索
 */
function getBulkRoutes($data) {
    $properties = $data['properties'] ?? [];
    $destinations = $data['destinations'] ?? [];
    
    if (empty($properties) || empty($destinations)) {
        sendError('Properties and destinations are required');
    }
    
    $results = [];
    
    foreach ($properties as $propertyIndex => $property) {
        $propertyResults = [];
        
        foreach ($destinations as $destination) {
            $origin = $property['address'] ?? '';
            $destinationAddr = $destination['address'] ?? $destination['name'];
            
            if ($origin && $destinationAddr) {
                $result = callScraperHTTPAPI($origin, $destinationAddr);
                
                if ($result['success']) {
                    $convertedResult = convertToPropertiesFormat(
                        $result['data'],
                        $destination['id'] ?? generateDestinationId($destination['name']),
                        $destination['name']
                    );
                    
                    $propertyResults[] = $convertedResult;
                } else {
                    // エラー用ダミーデータ
                    $propertyResults[] = [
                        'destination' => $destination['id'] ?? generateDestinationId($destination['name']),
                        'destination_name' => $destination['name'],
                        'total_time' => 999,
                        'details' => [
                            'walk_to_station' => 0,
                            'station_used' => 'エラー',
                            'trains' => [],
                            'walk_from_station' => 0,
                            'wait_time_minutes' => 0,
                            'error' => $result['error']
                        ]
                    ];
                }
                
                // 負荷軽減
                sleep(2);
            }
        }
        
        $results[] = [
            'property_index' => $propertyIndex,
            'property_name' => $property['name'] ?? "物件{$propertyIndex}",
            'routes' => $propertyResults
        ];
    }
    
    echo json_encode([
        'success' => true,
        'results' => $results
    ], JSON_UNESCAPED_UNICODE);
}

/**
 * Scraperコンテナ内のHTTPサーバーを呼び出し
 */
function callScraperHTTPAPI($origin, $destination) {
    // Scraperコンテナ内で簡易HTTPサーバーを立ち上げているものとする
    $url = 'http://vps_project-scraper-1:8000/route';
    
    $postData = json_encode([
        'origin' => $origin,
        'destination' => $destination
    ]);
    
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => $postData,
            'timeout' => 60
        ]
    ]);
    
    $response = @file_get_contents($url, false, $context);
    
    if ($response === false) {
        // HTTPサーバーが動いていない場合、直接Pythonスクリプトを呼び出し
        return callGoogleMapsScriptDirect($origin, $destination);
    }
    
    $decoded = json_decode($response, true);
    
    if ($decoded === null) {
        return [
            'success' => false,
            'error' => 'Invalid JSON response from scraper'
        ];
    }
    
    if ($decoded['status'] === 'success') {
        return [
            'success' => true,
            'data' => $decoded
        ];
    } else {
        return [
            'success' => false,
            'error' => $decoded['message'] ?? 'Unknown error'
        ];
    }
}

/**
 * 直接Pythonスクリプトを呼び出し（フォールバック）
 */
function callGoogleMapsScriptDirect($origin, $destination) {
    // Scraperコンテナに直接コマンドを送信（docker execの代替）
    $command = sprintf(
        'echo \'{"origin": %s, "destination": %s}\' | docker exec -i vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_combined.py %s %s 2>&1',
        json_encode($origin),
        json_encode($destination),
        escapeshellarg($origin),
        escapeshellarg($destination)
    );
    
    $output = shell_exec($command);
    
    if ($output === null) {
        return [
            'success' => false,
            'error' => 'Failed to execute script'
        ];
    }
    
    $decoded = json_decode($output, true);
    
    if ($decoded === null) {
        return [
            'success' => false,
            'error' => 'Invalid JSON output: ' . substr($output, 0, 200)
        ];
    }
    
    if ($decoded['status'] === 'success') {
        return [
            'success' => true,
            'data' => $decoded
        ];
    } else {
        return [
            'success' => false,
            'error' => $decoded['message'] ?? 'Unknown error'
        ];
    }
}

/**
 * Google Maps出力をproperties.json形式に変換
 */
function convertToPropertiesFormat($googleResult, $destinationId, $destinationName) {
    if ($googleResult['status'] !== 'success') {
        return null;
    }
    
    $route = $googleResult['route'] ?? [];
    $details = $route['details'] ?? [];
    
    // 待ち時間の集計
    $totalWaitTime = 0;
    foreach ($details['trains'] ?? [] as $train) {
        $totalWaitTime += $train['wait_time'] ?? 0;
    }
    
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
            
            if (strpos($transfer['to_line'] ?? '', '徒歩') !== false) {
                $normalizedTrain['transfer_after']['to_line'] = '徒歩' . ($transfer['time'] ?? 0) . '分';
            }
        }
        
        $normalizedTrains[] = $normalizedTrain;
    }
    
    // 徒歩のみの場合
    if ($details['route_type'] ?? '' === 'walking_only') {
        return [
            'destination' => $destinationId,
            'destination_name' => $destinationName,
            'total_time' => $route['total_time'] ?? 0,
            'details' => [
                'walk_only' => true,
                'walk_time' => $route['total_time'] ?? 0,
                'walk_to_station' => $route['total_time'] ?? 0,
                'distance_meters' => $details['distance_meters'] ?? 0,
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

function normalizeLineName($lineName) {
    $lineMap = [
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
        '京浜東北線' => 'JR京浜東北線',
        '浅草線' => '都営浅草線',
        '三田線' => '都営三田線',
        '新宿線' => '都営新宿線',
        '大江戸線' => '都営大江戸線'
    ];
    
    foreach ($lineMap as $short => $full) {
        if (strpos($lineName, $short) !== false) {
            return $full;
        }
    }
    
    return $lineName;
}

function normalizeStationName($stationName) {
    if (!$stationName) {
        return $stationName;
    }
    
    if (strpos($stationName, '(東京都)') !== false) {
        return $stationName;
    }
    
    $cleanedName = str_replace('駅', '', $stationName);
    return $cleanedName . '(東京都)';
}

function generateDestinationId($name) {
    return strtolower(str_replace([' ', '　', '(', ')', '（', '）'], '_', $name));
}

?>