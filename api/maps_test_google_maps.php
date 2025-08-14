<?php
/**
 * Google Maps スクレイピング専用テストエンドポイント
 * フォールバックなし、Google Mapsスクレイピングのみを使用
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// リクエスト処理
$input = json_decode(file_get_contents('php://input'), true);

$origin = $input['origin'] ?? '';
$destination = $input['destination'] ?? '';
$mode = $input['mode'] ?? 'transit';

if (empty($origin) || empty($destination)) {
    http_response_code(400);
    echo json_encode(['error' => 'Origin and destination are required']);
    exit;
}

// Transit mode only for this test
if ($mode !== 'transit') {
    http_response_code(400);
    echo json_encode(['error' => 'This test endpoint only supports transit mode']);
    exit;
}

// Google Maps スクレイピングAPIを直接呼び出す
$api_data = [
    'origin' => $origin,
    'destination' => $destination,
    'arrival_time' => $input['arrival_time'] ?? null
];

// デフォルトの到着時刻設定（Yahoo Transit APIと同じロジック）
if ($api_data['arrival_time'] === null) {
    $dt = new DateTime();
    $days_until_tuesday = (2 - $dt->format('w') + 7) % 7;
    if ($days_until_tuesday == 0) {
        $days_until_tuesday = 7;
    }
    $dt->modify("+{$days_until_tuesday} days");
    $dt->setTime(10, 0, 0);
    $api_data['arrival_time'] = $dt->format('Y-m-d H:i:s');
}

// Scraperコンテナ内のAPIサーバーを呼び出す
$api_url = 'http://scraper:8000/api/transit';

$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($api_data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Accept: application/json'
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 60);

$start_time = microtime(true);
$response = curl_exec($ch);
$end_time = microtime(true);
$execution_time = round(($end_time - $start_time) * 1000); // ミリ秒

$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

// エラーハンドリング
if ($response === false) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Failed to connect to Google Maps scraping service',
        'error_detail' => $curl_error,
        'test_info' => [
            'service' => 'google_maps_scraping',
            'execution_time_ms' => $execution_time
        ]
    ]);
    exit;
}

// レスポンスの処理
$result = json_decode($response, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Invalid JSON response from scraping service',
        'json_error' => json_last_error_msg(),
        'test_info' => [
            'service' => 'google_maps_scraping',
            'execution_time_ms' => $execution_time
        ]
    ]);
    exit;
}

// Google Maps形式に変換（maps.phpと同じロジック）
if ($result && $result['status'] === 'success') {
    $route = $result['route'];
    $details = $route['details'];
    
    // Build steps array
    $steps = [];
    
    // Walk to station
    if ($details['walk_to_station'] > 0) {
        $steps[] = [
            'travel_mode' => 'WALKING',
            'duration' => [
                'value' => $details['walk_to_station'] * 60,
                'text' => $details['walk_to_station'] . '分'
            ]
        ];
    }
    
    // Train segments
    foreach ($details['trains'] as $train) {
        $steps[] = [
            'travel_mode' => 'TRANSIT',
            'duration' => [
                'value' => $train['time'] * 60,
                'text' => $train['time'] . '分'
            ],
            'transit_details' => [
                'line' => [
                    'name' => $train['line'] ?? '電車',
                    'vehicle' => [
                        'type' => 'RAIL'
                    ]
                ],
                'departure_stop' => ['name' => $train['from']],
                'arrival_stop' => ['name' => $train['to']]
            ]
        ];
        
        // Add transfer walking if exists
        if (isset($train['transfer_after']) && $train['transfer_after']['time'] > 0) {
            $steps[] = [
                'travel_mode' => 'WALKING',
                'duration' => [
                    'value' => $train['transfer_after']['time'] * 60,
                    'text' => $train['transfer_after']['time'] . '分'
                ],
                'html_instructions' => $train['transfer_after']['to_line'] . 'へ乗り換え'
            ];
        }
    }
    
    // Walk from station
    if ($details['walk_from_station'] > 0) {
        $steps[] = [
            'travel_mode' => 'WALKING',
            'duration' => [
                'value' => $details['walk_from_station'] * 60,
                'text' => $details['walk_from_station'] . '分'
            ]
        ];
    }
    
    $googleFormatResponse = [
        'status' => 'OK',
        'routes' => [[
            'legs' => [[
                'duration' => [
                    'value' => $route['total_time'] * 60,
                    'text' => $route['total_time'] . '分'
                ],
                'steps' => $steps
            ]]
        ]],
        // テスト情報を追加
        'test_info' => [
            'service' => 'google_maps_scraping',
            'execution_time_ms' => $execution_time,
            'search_info' => $result['search_info'] ?? null,
            'original_total_time' => $route['original_total_time'] ?? null
        ]
    ];
    
    echo json_encode($googleFormatResponse, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} else {
    // エラーレスポンス
    http_response_code($http_code !== 200 ? $http_code : 500);
    echo json_encode([
        'status' => 'ZERO_RESULTS',
        'error' => $result['message'] ?? 'Unknown error',
        'test_info' => [
            'service' => 'google_maps_scraping',
            'execution_time_ms' => $execution_time
        ]
    ], JSON_UNESCAPED_UNICODE);
}
?>