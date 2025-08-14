<?php
/**
 * Google Maps Route API for JSON Generator
 * json-generator.htmlから呼び出されるAPI
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// エラーログ設定
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);

function logError($message) {
    error_log("[Google Maps Route API] " . $message);
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
    // リクエストデータの取得
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
    
    // Python scriptを呼び出し
    $result = callGoogleMapsScript($origin, $destination);
    
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
    $totalRoutes = count($properties) * count($destinations);
    $currentRoute = 0;
    
    foreach ($properties as $propertyIndex => $property) {
        $propertyResults = [];
        
        foreach ($destinations as $destination) {
            $currentRoute++;
            
            // 進捗を送信（Server-Sent Eventsの代替）
            if ($currentRoute % 5 === 0) {
                // 定期的に進捗をログに記録
                logError("Processing route {$currentRoute}/{$totalRoutes}");
            }
            
            $origin = $property['address'] ?? '';
            $destinationAddr = $destination['address'] ?? $destination['name'];
            
            if ($origin && $destinationAddr) {
                $result = callGoogleMapsScript($origin, $destinationAddr);
                
                if ($result['success']) {
                    $convertedResult = convertToPropertiesFormat(
                        $result['data'],
                        $destination['id'] ?? generateDestinationId($destination['name']),
                        $destination['name']
                    );
                    
                    $propertyResults[] = $convertedResult;
                } else {
                    // エラーの場合はダミーデータを作成
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
                
                // API負荷軽減のため待機
                usleep(2000000); // 2秒
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
        'results' => $results,
        'total_processed' => $currentRoute
    ], JSON_UNESCAPED_UNICODE);
}

/**
 * Google Maps Pythonスクリプトを呼び出し
 */
function callGoogleMapsScript($origin, $destination) {
    // 既にApacheコンテナ内なので、直接Pythonを呼び出し
    $scriptPath = '/var/www/japandatascience.com/timeline-mapping/api/google_maps_combined.py';
    
    // 直接Pythonスクリプトを実行（要：python3がインストール済み）
    $command = sprintf(
        'python3 %s %s %s 2>&1',
        escapeshellarg($scriptPath),
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
    
    // JSONの解析を試行
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
            
            // 徒歩の場合の特別処理
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

/**
 * 路線名の正規化
 */
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
    
    $cleanedName = str_replace('駅', '', $stationName);
    return $cleanedName . '(東京都)';
}

/**
 * 目的地IDの生成
 */
function generateDestinationId($name) {
    return strtolower(str_replace([' ', '　', '(', ')', '（', '）'], '_', $name));
}

?>