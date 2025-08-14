<?php
// /timeline-mapping/api/maps.php
// Google Maps API プロキシ (walking/driving) + HERE Transit API (transit)

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// .envファイルから環境変数を読み込む
function loadEnv($path) {
    if (!file_exists($path)) {
        return false;
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        $parts = explode('=', $line, 2);
        if (count($parts) == 2) {
            $_ENV[trim($parts[0])] = trim($parts[1]);
        }
    }
    return true;
}

// .envを読み込み
loadEnv(__DIR__ . '/../.env');

$GOOGLE_MAPS_API_KEY = $_ENV['GOOGLE_MAPS_API_KEY'] ?? '';
$HERE_API_KEY = $_ENV['HERE_API_KEY'] ?? '';

// リクエスト処理
$input = json_decode(file_get_contents('php://input'), true);

$origin = $input['origin'] ?? '';
$destination = $input['destination'] ?? '';
$mode = $input['mode'] ?? 'transit';
$departure_time = $input['departure_time'] ?? 'morning';

if (empty($origin) || empty($destination)) {
    echo json_encode(['error' => 'Origin and destination are required']);
    exit;
}

// Transit mode: Use Yahoo! Transit scraping for Japan transit support
if ($mode === 'transit') {
    // Forward request to Yahoo Transit API (improved version with __NEXT_DATA__)
    $yahooRequest = [
        'origin' => $origin,
        'destination' => $destination
    ];
    
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => json_encode($yahooRequest),
            'timeout' => 60
        ]
    ];
    
    $context = stream_context_create($options);
    $yahooResponse = @file_get_contents('https://japandatascience.com/timeline-mapping/api/yahoo_transit_api_v5.php', false, $context);
    
    if ($yahooResponse !== FALSE) {
        // Yahoo APIからのレスポンスをGoogle Maps形式に変換
        $yahooData = json_decode($yahooResponse, true);
        
        // Yahoo APIがエラーを返した場合
        if (isset($yahooData['status'])) {
            if ($yahooData['status'] === 'error' || $yahooData['status'] === 'no_routes') {
                error_log("Maps.php: Yahoo API error - " . ($yahooData['message'] ?? 'Unknown error'));
                echo json_encode(['status' => 'ZERO_RESULTS', 'error' => $yahooData['message'] ?? 'No route found']);
                exit;
            }
        }
        
        // v5 API形式に対応
        if (isset($yahooData['route']) && $yahooData['status'] === 'success') {
            $route = $yahooData['route'];
            $details = $route['details'];
            
            // Google Maps API互換形式に変換
            $steps = [];
            
            // 1. 最初の徒歩区間
            if ($details['walk_to_station'] > 0) {
                $steps[] = [
                    'travel_mode' => 'WALKING',
                    'duration' => [
                        'value' => $details['walk_to_station'] * 60,
                        'text' => $details['walk_to_station'] . '分'
                    ]
                ];
            }
            
            // 2. 電車区間と乗り換え
            foreach ($details['trains'] as $train) {
                $steps[] = [
                    'travel_mode' => 'TRANSIT',
                    'duration' => [
                        'value' => $train['time'] * 60,
                        'text' => $train['time'] . '分'
                    ],
                    'transit_details' => [
                        'line' => [
                            'name' => $train['line'] ?? '不明',
                            'vehicle' => [
                                'type' => 'RAIL'
                            ]
                        ],
                        'departure_stop' => ['name' => $train['from']],
                        'arrival_stop' => ['name' => $train['to']]
                    ]
                ];
                
                // 乗り換え徒歩がある場合
                if (isset($train['transfer_after']) && $train['transfer_after']['time'] > 0) {
                    $steps[] = [
                        'travel_mode' => 'WALKING',
                        'duration' => [
                            'value' => $train['transfer_after']['time'] * 60,
                            'text' => $train['transfer_after']['time'] . '分'
                        ]
                    ];
                }
            }
            
            // 3. 最後の徒歩区間
            if ($details['walk_from_station'] > 0) {
                $steps[] = [
                    'travel_mode' => 'WALKING',
                    'duration' => [
                        'value' => $details['walk_from_station'] * 60,
                        'text' => $details['walk_from_station'] . '分'
                    ]
                ];
            }
            
            // 総徒歩時間を計算
            $total_walk_time = $details['walk_to_station'] + $details['walk_from_station'];
            foreach ($details['trains'] as $train) {
                if (isset($train['transfer_after'])) {
                    $total_walk_time += $train['transfer_after']['time'];
                }
            }
            
            $googleFormatResponse = [
                'status' => 'OK',
                'routes' => [[
                    'legs' => [[
                        'duration' => [
                            'value' => $route['total_time'] * 60,
                            'text' => $route['total_time'] . '分'
                        ],
                        'steps' => $steps,
                        'walk_time' => [
                            'value' => $total_walk_time * 60,
                            'text' => $total_walk_time . '分'
                        ],
                        // v5 APIからの詳細データを含める
                        'route_details' => $details
                    ]]
                ]]
            ];
            
            echo json_encode($googleFormatResponse, JSON_UNESCAPED_UNICODE);
            exit;
        } else if (isset($yahooData['routes']) && !empty($yahooData['routes'])) {
            // v4 API互換性維持（fallback）
            $route = $yahooData['routes'][0];
            
            // Google Maps API互換形式に変換
            $steps = [];
            foreach ($route['sections'] as $section) {
                if ($section['type'] === 'walk') {
                    $steps[] = [
                        'travel_mode' => 'WALKING',
                        'duration' => [
                            'value' => 300, // デフォルト5分
                            'text' => '5分'
                        ]
                    ];
                } else {
                    // 電車の所要時間を計算（デフォルト10分）
                    $trainDuration = 600; // デフォルト10分（秒）
                    if (isset($section['departure_time']) && isset($section['arrival_time'])) {
                        // 時刻から計算を試みる
                        $dep = strtotime($section['departure_time']);
                        $arr = strtotime($section['arrival_time']);
                        if ($dep && $arr) {
                            $trainDuration = max(60, $arr - $dep); // 最小1分
                        }
                    }
                    
                    $steps[] = [
                        'travel_mode' => 'TRANSIT',
                        'duration' => [
                            'value' => $trainDuration,
                            'text' => round($trainDuration / 60) . '分'
                        ],
                        'transit_details' => [
                            'line' => [
                                'name' => $section['line_name'] ?? '不明',
                                'vehicle' => [
                                    'type' => 'RAIL'
                                ]
                            ],
                            'departure_stop' => ['name' => $section['departure_station']],
                            'arrival_stop' => ['name' => $section['arrival_station']]
                        ]
                    ];
                }
            }
            
            $googleFormatResponse = [
                'status' => 'OK',
                'routes' => [[
                    'legs' => [[
                        'duration' => [
                            'value' => $route['summary']['total_minutes'] * 60,
                            'text' => $route['summary']['total_minutes'] . '分'
                        ],
                        'steps' => $steps,
                        'walk_time' => [
                            'value' => $route['summary']['walk_time_minutes'] * 60,
                            'text' => $route['summary']['walk_time_minutes'] . '分'
                        ],
                        // v4 APIからの乗り換え情報を含む電車データを追加
                        'trains_with_transfer' => $route['trains_with_transfer'] ?? []
                    ]]
                ]]
            ];
            
            echo json_encode($googleFormatResponse, JSON_UNESCAPED_UNICODE);
            exit;
        } else if (isset($yahooData['error'])) {
            // エラーの場合
            echo json_encode(['status' => 'ZERO_RESULTS', 'error' => $yahooData['message']]);
            exit;
        }
    }
    
    // Fallback: Try Google Maps scraping via HTTP API
    error_log('Yahoo Transit scraping failed, falling back to Google Maps scraping');
    
    // Call Google Maps scraping API via HTTP
    $googleMapsData = [
        'origin' => $origin,
        'destination' => $destination,
        'arrival_time' => null  // Use default time
    ];
    
    // Scraperコンテナ内のAPIサーバーを呼び出す
    $api_url = 'http://scraper:8000/api/transit';
    
    $ch = curl_init($api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($googleMapsData));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Accept: application/json'
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60);
    
    $googleMapsResult = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($googleMapsResult && $http_code === 200) {
        $googleMapsResponse = json_decode($googleMapsResult, true);
        
        if ($googleMapsResponse && $googleMapsResponse['status'] === 'success') {
            // Convert Google Maps scraping response to Google Maps API format
            $route = $googleMapsResponse['route'];
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
                            'name' => $train['line'],
                            'vehicle' => [
                                'type' => 'RAIL'
                            ]
                        ],
                        'departure_stop' => ['name' => $train['from']],
                        'arrival_stop' => ['name' => $train['to']]
                    ]
                ];
                
                // Add transfer if exists
                if (isset($train['transfer_after'])) {
                    $steps[] = [
                        'travel_mode' => 'WALKING',
                        'duration' => [
                            'value' => $train['transfer_after']['time'] * 60,
                            'text' => $train['transfer_after']['time'] . '分'
                        ]
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
                        'steps' => $steps,
                        'walk_time' => [
                            'value' => ($details['walk_to_station'] + $details['walk_from_station']) * 60,
                            'text' => ($details['walk_to_station'] + $details['walk_from_station']) . '分'
                        ],
                        'source' => 'google_maps_scraping'
                    ]]
                ]]
            ];
            
            echo json_encode($googleFormatResponse, JSON_UNESCAPED_UNICODE);
            exit;
        }
    }
    
    // If Google Maps scraping also failed, return error
    echo json_encode(['status' => 'ZERO_RESULTS', 'error' => 'Both Yahoo Transit and Google Maps scraping failed']);
    exit;
}

// For walking and driving modes, use Google Maps API
if (empty($GOOGLE_MAPS_API_KEY)) {
    http_response_code(500);
    echo json_encode(['error' => 'Google Maps API key not configured']);
    exit;
}

// 平日朝9時の出発時間を設定（今日または明日の朝9時）
$today9am = strtotime('today 9:00');
if (time() > $today9am) {
    // 既に9時を過ぎている場合は明日の朝9時
    $departureTimestamp = strtotime('tomorrow 9:00');
} else {
    // まだ9時前なら今日の朝9時
    $departureTimestamp = $today9am;
}

// Google Maps Directions API呼び出し（制限なしキーを使用）
$params = [
    'origin' => $origin,
    'destination' => $destination,
    'mode' => $mode,
    'language' => 'ja',
    'region' => 'jp',  // 日本地域を明示
    'key' => $GOOGLE_MAPS_API_KEY
];

// transitモードの場合のみdeparture_timeを追加
if ($mode === 'transit') {
    // transitの場合は現在時刻を使用
    $params['departure_time'] = time();
}

$url = 'https://maps.googleapis.com/maps/api/directions/json?' . http_build_query($params);

$response = file_get_contents($url);

if ($response === FALSE) {
    echo json_encode(['error' => 'Failed to call Google Maps API']);
    exit;
}

// レスポンスをそのまま返す（JavaScriptで解析）
echo $response;
?>