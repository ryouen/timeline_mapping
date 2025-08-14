<?php
/**
 * Yahoo!乗換案内APIラッパー（改良版 - エラーハンドリング強化）
 * 
 * Yahoo!乗換案内の検索結果ページから__NEXT_DATA__を抽出し、
 * ルート情報を構造化されたJSONとして返す
 * 
 * エラー時にはより詳細な情報を返すように改良
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
error_log("Yahoo Transit API v2: Searching route from '$origin' to '$destination'");

try {
    $result = getYahooTransitRoute($origin, $destination);
    
    if ($result === null || (isset($result['status']) && $result['status'] === 'error')) {
        // エラーレスポンス
        http_response_code(500);
        echo json_encode($result ?? ['status' => 'error', 'message' => 'Unknown error occurred']);
    } else {
        // 成功レスポンス
        echo json_encode($result);
    }
} catch (Exception $e) {
    error_log("Yahoo Transit API v2: Exception - " . $e->getMessage());
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
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36');
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    $html = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);
    
    if ($curl_error) {
        error_log("Yahoo Transit API: cURL error for $origin -> $destination: $curl_error");
        return ['status' => 'error', 'message' => 'Network error: ' . $curl_error, 'origin' => $origin, 'destination' => $destination];
    }

    if ($http_code !== 200 || !$html) {
        error_log("Yahoo Transit API: HTTP $http_code for $origin -> $destination");
        return ['status' => 'error', 'message' => 'Yahoo API returned status ' . $http_code, 'origin' => $origin, 'destination' => $destination];
    }

    // 埋め込みJSON(__NEXT_DATA__)を抽出
    preg_match('/<script id="__NEXT_DATA__" type="application\/json">(.*?)<\/script>/s', $html, $matches);

    if (!isset($matches[1])) {
        // デバッグ用：HTMLの一部をログに記録
        $html_sample = substr($html, 0, 1000);
        error_log("Yahoo Transit API: No __NEXT_DATA__ found for $origin -> $destination. HTML sample: $html_sample");
        
        // エラー用HTMLをファイルに保存（デバッグ用）
        $debug_file = '/tmp/yahoo_error_' . date('YmdHis') . '_' . md5($origin . $destination) . '.html';
        file_put_contents($debug_file, $html);
        
        return ['status' => 'error', 'message' => 'Could not find route data in Yahoo response', 'debug_file' => $debug_file, 'origin' => $origin, 'destination' => $destination];
    }

    $data = json_decode($matches[1], true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log("Yahoo Transit API: JSON decode error for $origin -> $destination: " . json_last_error_msg());
        return ['status' => 'error', 'message' => 'Failed to parse JSON data: ' . json_last_error_msg(), 'origin' => $origin, 'destination' => $destination];
    }

    // ルート情報を抽出
    $raw_routes = $data['props']['pageProps']['naviSearchParam']['featureInfoList'] ?? [];
    if (empty($raw_routes)) {
        error_log("Yahoo Transit API: No routes found for $origin -> $destination");
        return ['status' => 'no_routes', 'message' => 'No transit routes found between locations', 'origin' => $origin, 'destination' => $destination];
    }

    // ルートデータを整形
    $formatted_routes = [];
    foreach ($raw_routes as $i => $route) {
        $summary = $route['summaryInfo'];
        $sections = [];
        $walk_time_total = 0;
        
        $edge_list = $route['edgeInfoList'] ?? [];
        $edge_count = count($edge_list);
        
        // セクションを構築
        for ($j = 0; $j < $edge_count; $j++) {
            $edge = $edge_list[$j];
            $access_type = $edge['accessInfo']['type'] ?? -1;
            
            // 最後のedgeは到着地点なので、セクションとしては処理しない
            if ($j === $edge_count - 1) {
                break;
            }
            
            if ($access_type === 1) {
                // 徒歩区間
                preg_match('/(\d+)分/', $edge['railName'] ?? '', $walk_matches);
                $walk_minutes = (int)($walk_matches[1] ?? 0);
                $walk_time_total += $walk_minutes;
                
                $sections[] = [
                    'type' => 'walk',
                    'duration_minutes' => $walk_minutes,
                    'departure_station' => $edge['pointName'] ?? $edge['stationName'] ?? '',
                    'arrival_station' => isset($edge_list[$j + 1]) ? 
                        ($edge_list[$j + 1]['pointName'] ?? $edge_list[$j + 1]['stationName'] ?? '') : ''
                ];
            } else {
                // 電車・バス区間
                $sections[] = [
                    'type' => 'train',
                    'line_name' => $edge['railNameExcludingDestination'] ?? $edge['railName'] ?? '',
                    'destination' => $edge['destination'] ?? null,
                    'departure_station' => $edge['pointName'] ?? $edge['stationName'] ?? '',
                    'departure_time' => $edge['timeInfo'][0]['time'] ?? null,
                    'arrival_station' => isset($edge_list[$j + 1]) ? 
                        ($edge_list[$j + 1]['pointName'] ?? $edge_list[$j + 1]['stationName'] ?? '') : '',
                    'arrival_time' => isset($edge_list[$j + 1]['timeInfo'][0]['time']) ? 
                        $edge_list[$j + 1]['timeInfo'][0]['time'] : 
                        ($edge['timeInfo'][1]['time'] ?? null)
                ];
            }
        }
        
        // 最後の地点情報をチェック（到着地点への徒歩）
        if ($edge_count > 0) {
            $last_edge = $edge_list[$edge_count - 1];
            // 最後の区間に徒歩時間が含まれているかチェック
            if (isset($last_edge['railName']) && preg_match('/徒歩(\d+)分/', $last_edge['railName'], $walk_matches)) {
                $walk_minutes = (int)($walk_matches[1] ?? 0);
                $walk_time_total += $walk_minutes;
                
                // 最後の徒歩セクションを追加
                $sections[] = [
                    'type' => 'walk',
                    'duration_minutes' => $walk_minutes,
                    'departure_station' => $edge_count > 1 ? 
                        ($edge_list[$edge_count - 2]['stationName'] ?? '') : '',
                    'arrival_station' => $last_edge['stationName'] ?? $last_edge['pointName'] ?? ''
                ];
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
                'walk_time_minutes' => $walk_time_total
            ],
            'sections' => $sections
        ];
    }

    // 最終的な出力データ
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