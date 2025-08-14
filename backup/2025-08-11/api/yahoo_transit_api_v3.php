<?php
/**
 * Yahoo!乗換案内APIラッパー v3（改良版 - より堅牢なデータ構造処理）
 * 
 * 最後が徒歩にならない場合（駅直結など）にも対応
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// POSTデータを取得
$input = json_decode(file_get_contents('php://input'), true);

if (!$input || !isset($input['origin']) || !isset($input['destination'])) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Origin and destination are required']);
    exit;
}

$origin = $input['origin'];
$destination = $input['destination'];

// デバッグログ
error_log("Yahoo Transit API v3: Searching route from '$origin' to '$destination'");

try {
    $result = getYahooTransitRoute($origin, $destination);
    
    if ($result === null || (isset($result['status']) && $result['status'] === 'error')) {
        http_response_code(500);
        echo json_encode($result ?? ['status' => 'error', 'message' => 'Unknown error occurred']);
    } else {
        echo json_encode($result);
    }
} catch (Exception $e) {
    error_log("Yahoo Transit API v3: Exception - " . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Internal server error: ' . $e->getMessage(),
        'origin' => $origin,
        'destination' => $destination
    ]);
}

/**
 * Yahoo!乗換案内の検索を実行し、結果を整形して返すメイン関数
 */
function getYahooTransitRoute($origin, $destination) {
    $dt = new DateTime();
    $params = [
        'from' => $origin,
        'to' => $destination,
        'y' => $dt->format('Y'),
        'm' => $dt->format('m'),
        'd' => $dt->format('d'),
        'hh' => $dt->format('H'),
        'm1' => floor($dt->format('i') / 10),
        'm2' => $dt->format('i') % 10,
        'type' => 1,
        'ticket' => 'ic',
    ];
    $url = 'https://transit.yahoo.co.jp/search/result?' . http_build_query($params);

    // cURLでHTMLを取得
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    $html = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);
    
    if ($curl_error) {
        error_log("Yahoo Transit API: cURL error for $origin -> $destination: $curl_error");
        return ['status' => 'error', 'message' => 'Network error: ' . $curl_error];
    }

    if ($http_code !== 200 || !$html) {
        error_log("Yahoo Transit API: HTTP $http_code for $origin -> $destination");
        return ['status' => 'error', 'message' => 'Yahoo API returned status ' . $http_code];
    }

    // 埋め込みJSON(__NEXT_DATA__)を抽出
    preg_match('/<script id="__NEXT_DATA__" type="application\/json">(.*?)<\/script>/s', $html, $matches);

    if (!isset($matches[1])) {
        $debug_file = '/tmp/yahoo_error_' . date('YmdHis') . '_' . md5($origin . $destination) . '.html';
        file_put_contents($debug_file, $html);
        error_log("Yahoo Transit API: No __NEXT_DATA__ found. Debug file: $debug_file");
        return ['status' => 'error', 'message' => 'Could not find route data in Yahoo response'];
    }

    $data = json_decode($matches[1], true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log("Yahoo Transit API: JSON decode error: " . json_last_error_msg());
        return ['status' => 'error', 'message' => 'Failed to parse JSON data'];
    }

    // ルート情報を抽出
    $raw_routes = $data['props']['pageProps']['naviSearchParam']['featureInfoList'] ?? [];
    if (empty($raw_routes)) {
        error_log("Yahoo Transit API: No routes found for $origin -> $destination");
        return ['status' => 'no_routes', 'message' => 'No transit routes found'];
    }

    // ルートデータを整形（改善版）
    $formatted_routes = [];
    foreach ($raw_routes as $i => $route) {
        $summary = $route['summaryInfo'];
        $sections = [];
        $walk_time_total = 0;
        
        $edge_list = $route['edgeInfoList'] ?? [];
        $edge_count = count($edge_list);
        
        // Phase 1: 最初の徒歩区間を確認
        $first_walk_minutes = 0;
        if ($edge_count > 0 && ($edge_list[0]['accessInfo']['type'] ?? -1) === 1) {
            preg_match('/(\d+)分/', $edge_list[0]['railName'] ?? '', $matches);
            $first_walk_minutes = (int)($matches[1] ?? 0);
            $walk_time_total += $first_walk_minutes;
            
            $sections[] = [
                'type' => 'walk',
                'duration_minutes' => $first_walk_minutes,
                'departure_station' => $edge_list[0]['pointName'] ?? $edge_list[0]['stationName'] ?? $origin,
                'arrival_station' => isset($edge_list[1]) ? 
                    ($edge_list[1]['pointName'] ?? $edge_list[1]['stationName'] ?? '') : ''
            ];
        }
        
        // Phase 2: 電車・バス区間と乗り換えを処理
        for ($j = 0; $j < $edge_count; $j++) {
            $edge = $edge_list[$j];
            $access_type = $edge['accessInfo']['type'] ?? -1;
            
            // 電車・バス区間（type = 0）
            if ($access_type === 0) {
                // 到着駅を安全に取得
                $arrival_station = '';
                $arrival_time = null;
                
                // 次のedgeを探して到着駅を特定
                for ($k = $j + 1; $k < $edge_count; $k++) {
                    if (isset($edge_list[$k]['stationName']) || isset($edge_list[$k]['pointName'])) {
                        $arrival_station = $edge_list[$k]['pointName'] ?? $edge_list[$k]['stationName'] ?? '';
                        $arrival_time = $edge_list[$k]['timeInfo'][0]['time'] ?? null;
                        break;
                    }
                }
                
                // 到着駅が見つからない場合は目的地を使用
                if (empty($arrival_station)) {
                    $arrival_station = $destination;
                }
                
                $sections[] = [
                    'type' => 'train',
                    'line_name' => $edge['railNameExcludingDestination'] ?? $edge['railName'] ?? '',
                    'destination' => $edge['destination'] ?? null,
                    'departure_station' => $edge['pointName'] ?? $edge['stationName'] ?? '',
                    'departure_time' => $edge['timeInfo'][0]['time'] ?? null,
                    'arrival_station' => $arrival_station,
                    'arrival_time' => $arrival_time ?? ($edge['timeInfo'][1]['time'] ?? null)
                ];
                
                // 次が乗り換え徒歩の場合
                if (isset($edge_list[$j + 1]) && ($edge_list[$j + 1]['accessInfo']['type'] ?? -1) === 1 && $j + 1 < $edge_count - 1) {
                    preg_match('/(\d+)分/', $edge_list[$j + 1]['railName'] ?? '', $matches);
                    $transfer_walk = (int)($matches[1] ?? 0);
                    $walk_time_total += $transfer_walk;
                    
                    $sections[] = [
                        'type' => 'walk',
                        'duration_minutes' => $transfer_walk,
                        'departure_station' => $arrival_station,
                        'arrival_station' => isset($edge_list[$j + 2]) ? 
                            ($edge_list[$j + 2]['pointName'] ?? $edge_list[$j + 2]['stationName'] ?? '') : ''
                    ];
                    
                    $j++; // 乗り換え徒歩をスキップ
                }
            }
        }
        
        // Phase 3: 最後の徒歩区間を確認（駅直結でない場合のみ）
        $last_walk_minutes = 0;
        if ($edge_count > 1) {
            $last_edge = $edge_list[$edge_count - 1];
            $last_access_type = $last_edge['accessInfo']['type'] ?? -1;
            
            // 最後が徒歩区間の場合のみ処理
            if ($last_access_type === 1) {
                if (preg_match('/徒歩(\d+)分/', $last_edge['railName'] ?? '', $matches)) {
                    $last_walk_minutes = (int)($matches[1] ?? 0);
                    $walk_time_total += $last_walk_minutes;
                    
                    // 出発駅を特定
                    $from_station = '';
                    for ($k = $edge_count - 2; $k >= 0; $k--) {
                        if (isset($edge_list[$k]['stationName']) || isset($edge_list[$k]['pointName'])) {
                            $from_station = $edge_list[$k]['stationName'] ?? $edge_list[$k]['pointName'] ?? '';
                            break;
                        }
                    }
                    
                    $sections[] = [
                        'type' => 'walk',
                        'duration_minutes' => $last_walk_minutes,
                        'departure_station' => $from_station,
                        'arrival_station' => $last_edge['stationName'] ?? $last_edge['pointName'] ?? $destination
                    ];
                }
            }
        }

        $formatted_routes[] = [
            'route_id' => $i + 1,
            'summary' => [
                'departure_time' => $summary['departureTime'],
                'arrival_time' => $summary['arrivalTime'],
                'total_minutes' => (int) filter_var($summary['totalTime'], FILTER_SANITIZE_NUMBER_INT),
                'total_fare_yen' => (int) $summary['totalPrice'],
                'transfer_count' => (int) $summary['transferCount'],
                'walk_time_minutes' => $walk_time_total,
                'walk_to_station' => $first_walk_minutes,
                'walk_from_station' => $last_walk_minutes
            ],
            'sections' => $sections
        ];
    }

    return [
        'status' => 'success',
        'search_query' => [
            'from' => $origin,
            'to' => $destination,
            'datetime' => $dt->format(DateTime::ATOM)
        ],
        'routes' => $formatted_routes
    ];
}

?>