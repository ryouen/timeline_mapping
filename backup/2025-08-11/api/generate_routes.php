<?php
// Timeline Mapping用 properties.json 生成API
error_reporting(E_ALL);
ini_set('display_errors', 0);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

try {
    $input = json_decode(file_get_contents('php://input'), true);
    $properties = $input['properties'] ?? [];
    $destinations = $input['destinations'] ?? [];
    
    if (empty($properties) || empty($destinations)) {
        die(json_encode(['error' => 'Properties and destinations data required']));
    }
    
    // 各物件に対してルート情報を生成
    $propertiesWithRoutes = [];
    
    foreach ($properties as $property) {
        $propertyWithRoutes = [
            'name' => $property['name'] ?? '',
            'address' => $property['address'] ?? '',
            'rent' => $property['rent'] ?? '',
            'routes' => [],
            'stations' => [],
            'total_monthly_travel_time' => 0
        ];
        
        $totalTime = 0;
        $stationsUsed = [];
        
        // 各目的地へのルート生成
        foreach ($destinations as $destination) {
            $route = generateRouteForDestination($property['address'], $destination);
            $propertyWithRoutes['routes'][] = $route;
            
            // 月間移動時間計算
            $totalTime += $route['total_time'] * $destination['monthly_frequency'];
            
            // 使用駅の収集
            foreach ($route['trains'] as $train) {
                if (!in_array($train['from'], $stationsUsed)) {
                    $stationsUsed[] = $train['from'];
                }
                if (!in_array($train['to'], $stationsUsed)) {
                    $stationsUsed[] = $train['to'];
                }
            }
        }
        
        $propertyWithRoutes['total_monthly_travel_time'] = round($totalTime);
        
        // 駅情報の生成
        foreach ($stationsUsed as $stationName) {
            $propertyWithRoutes['stations'][] = [
                'name' => $stationName,
                'lines' => getStationLines($stationName),
                'walk_time' => rand(3, 8) // 仮の徒歩時間
            ];
        }
        
        $propertiesWithRoutes[] = $propertyWithRoutes;
    }
    
    echo json_encode([
        'properties' => $propertiesWithRoutes
    ]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Server error',
        'message' => $e->getMessage()
    ]);
}

// サンプルルート生成（実際はGoogle Maps APIを使用）
function generateRouteForDestination($propertyAddress, $destination) {
    $routeTemplates = [
        [
            'destination_id' => $destination['id'],
            'destination_name' => $destination['name'],
            'total_time' => rand(25, 45),
            'walk_to_station' => rand(3, 8),
            'trains' => [
                [
                    'line' => '東京メトロ有楽町線',
                    'time' => rand(8, 12),
                    'from' => '月島',
                    'to' => '有楽町'
                ],
                [
                    'line' => 'JR山手線',
                    'time' => rand(6, 10),
                    'from' => '有楽町',
                    'to' => '表参道'
                ]
            ],
            'walk_from_station' => rand(2, 6)
        ]
    ];
    
    // 目的地に応じたルートカスタマイズ
    $template = $routeTemplates[0];
    $template['destination_id'] = $destination['id'];
    $template['destination_name'] = $destination['name'];
    
    // 目的地別のルート調整
    switch ($destination['id']) {
        case 'shizenkan_univ':
            $template['trains'] = [
                [
                    'line' => '東京メトロ有楽町線',
                    'time' => 10,
                    'from' => '月島',
                    'to' => '銀座一丁目'
                ],
                [
                    'line' => '東京メトロ銀座線',
                    'time' => 8,
                    'from' => '銀座',
                    'to' => '日本橋'
                ]
            ];
            $template['total_time'] = 25;
            break;
            
        case 'yawara_jingumae':
            $template['trains'] = [
                [
                    'line' => '東京メトロ有楽町線',
                    'time' => 12,
                    'from' => '月島',
                    'to' => '有楽町'
                ],
                [
                    'line' => 'JR山手線',
                    'time' => 8,
                    'from' => '有楽町',
                    'to' => '新橋'
                ],
                [
                    'line' => '東京メトロ銀座線',
                    'time' => 10,
                    'from' => '新橋',
                    'to' => '表参道'
                ]
            ];
            $template['total_time'] = 38;
            break;
    }
    
    return $template;
}

// 駅の路線情報
function getStationLines($stationName) {
    $stationLines = [
        '月島' => ['東京メトロ有楽町線', '都営大江戸線'],
        '有楽町' => ['東京メトロ有楽町線', 'JR山手線', 'JR京浜東北線'],
        '銀座' => ['東京メトロ銀座線', '東京メトロ丸ノ内線', '東京メトロ日比谷線'],
        '日本橋' => ['東京メトロ銀座線', '東京メトロ東西線', '東京メトロ半蔵門線'],
        '表参道' => ['東京メトロ銀座線', '東京メトロ半蔵門線', '東京メトロ千代田線'],
        '新橋' => ['JR山手線', 'JR京浜東北線', '東京メトロ銀座線']
    ];
    
    return $stationLines[$stationName] ?? [$stationName . '線'];
}
?>