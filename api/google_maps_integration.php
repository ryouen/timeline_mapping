<?php
/**
 * Google Maps Integration API
 * HTTPエンドポイント経由でスクレイピングサービスを呼び出す
 * Updated: 2025-08-14
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

function logMessage($message) {
    error_log("[Google Maps Integration] " . date('Y-m-d H:i:s') . " - " . $message);
}

function sendError($message, $details = null) {
    $response = ['success' => false, 'error' => $message];
    if ($details) {
        $response['details'] = $details;
    }
    echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function sendSuccess($data) {
    $response = ['success' => true];
    foreach ($data as $key => $value) {
        $response[$key] = $value;
    }
    echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
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
    sendError('Server error', $e->getMessage());
}

function getSingleRoute($data) {
    $origin = $data['origin'] ?? '';
    $destination = $data['destination'] ?? '';
    $destinationId = $data['destinationId'] ?? '';
    $destinationName = $data['destinationName'] ?? '';
    $arrivalTime = $data['arrivalTime'] ?? null;
    
    if (!$origin || !$destination) {
        sendError('Origin and destination are required');
    }
    
    logMessage("Route search: {$origin} -> {$destination}");
    if ($arrivalTime) {
        logMessage("Arrival time requested: {$arrivalTime}");
    }
    
    // スクレイピングサービスを呼び出し
    $result = callScrapingService($origin, $destination, $arrivalTime);
    
    if ($result && $result['status'] === 'success' && isset($result['route'])) {
        $route = $result['route'];
        
        // properties.json形式に変換
        $formattedRoute = [
            'destination' => $destinationId,
            'destination_name' => $destinationName,
            'total_time' => $route['total_time'] ?? 0,
            'details' => $route['details'] ?? []
        ];
        
        // 総徒歩時間の計算
        if (isset($route['details'])) {
            $details = $route['details'];
            $total_walk = ($details['walk_to_station'] ?? 0) + ($details['walk_from_station'] ?? 0);
            $formattedRoute['total_walk_time'] = $total_walk;
        }
        
        sendSuccess(['route' => $formattedRoute]);
    } else {
        $errorMessage = isset($result['message']) ? $result['message'] : 'No route found';
        sendError($errorMessage, $result);
    }
}

function callScrapingService($origin, $destination, $arrivalTime = null) {
    // スクレイピングサービスのエンドポイント
    $url = 'http://scraper:8000/api/transit';
    
    // リクエストデータ
    $requestData = [
        'origin' => $origin,
        'destination' => $destination
    ];
    
    if ($arrivalTime) {
        try {
            $dt = new DateTime($arrivalTime);
            $requestData['arrival_time'] = $dt->format('Y-m-d H:i:s');
        } catch (Exception $e) {
            logMessage("Invalid arrival time format: {$arrivalTime}");
        }
    }
    
    // HTTPリクエストの設定
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => [
                'Content-Type: application/json',
                'Accept: application/json'
            ],
            'content' => json_encode($requestData),
            'timeout' => 60,
            'ignore_errors' => true
        ]
    ];
    
    $context = stream_context_create($options);
    
    logMessage("Calling scraping service: {$url}");
    logMessage("Request data: " . json_encode($requestData));
    
    // リクエスト実行
    $response = @file_get_contents($url, false, $context);
    
    if ($response === false) {
        logMessage("Failed to call scraping service");
        return [
            'status' => 'error',
            'message' => 'Failed to connect to scraping service'
        ];
    }
    
    logMessage("Raw response length: " . strlen($response));
    
    // レスポンスをパース
    $result = json_decode($response, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        logMessage("JSON parse error: " . json_last_error_msg());
        return [
            'status' => 'error',
            'message' => 'Invalid response from scraping service'
        ];
    }
    
    return $result;
}

function testConnection() {
    // HTTPエンドポイントの接続テスト
    $url = 'http://scraper:8000/api/health';
    
    $options = [
        'http' => [
            'method' => 'GET',
            'timeout' => 10,
            'ignore_errors' => true
        ]
    ];
    
    $context = stream_context_create($options);
    $response = @file_get_contents($url, false, $context);
    
    if ($response !== false) {
        $data = json_decode($response, true);
        if ($data && isset($data['status']) && $data['status'] === 'ok') {
            sendSuccess(['message' => 'Connection test successful']);
        } else {
            sendSuccess(['message' => 'Scraping service is accessible']);
        }
    } else {
        sendError('Cannot connect to scraping service');
    }
}