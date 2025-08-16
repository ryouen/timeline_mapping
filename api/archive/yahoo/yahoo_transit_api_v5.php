<?php
/**
 * Yahoo!乗換案内スクレイピングAPI 最終版
 * * 機能:
 * - __NEXT_DATA__ JSONを解析し、より正確な時間計算を行う
 * - 「最初の駅での待ち時間」を新たに抽出し、JSONに含める
 */

// --- ヘッダー設定 ---
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// --- メイン処理 ---
$json_input = file_get_contents('php://input');
$input_data = json_decode($json_input, true);

if (empty($input_data['origin']) || empty($input_data['destination'])) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'origin and destination are required.']);
    exit;
}

$origin = $input_data['origin'];
$destination = $input_data['destination'];
$arrival_time = $input_data['arrival_time'] ?? null;  // 到着時刻を受け取る（オプション）

try {
    $result = getYahooTransitRoute($origin, $destination, $arrival_time);
    if ($result['status'] === 'success') {
        http_response_code(200);
        echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    } else {
        http_response_code(500);
        echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Internal Server Error: ' . $e->getMessage()]);
}

/**
 * Yahoo!乗換案内の検索を実行し、結果を整形して返すメイン関数
 */
function getYahooTransitRoute($origin, $destination, $arrival_time = null) {
    // デフォルトは翌火曜日の朝10時に到着
    if ($arrival_time === null) {
        // 翌火曜日を計算
        $dt = new DateTime();
        $days_until_tuesday = (2 - $dt->format('w') + 7) % 7;
        if ($days_until_tuesday == 0) {
            $days_until_tuesday = 7; // 今日が火曜日なら翌週の火曜日
        }
        $dt->modify("+{$days_until_tuesday} days");
        $dt->setTime(10, 0, 0); // 朝10時に設定
        $search_type = 4;  // 到着時刻指定
    } else if ($arrival_time === 'now') {
        // 特別な値 'now' が指定された場合は現在時刻で出発
        $dt = new DateTime();
        $search_type = 1;  // 出発時刻指定
    } else {
        // カスタム到着時刻が指定された場合
        $dt = new DateTime($arrival_time);
        $search_type = 4;  // 到着時刻指定
    }
    
    // 検索情報を保存（後で返却用）
    $search_datetime = $dt->format('Y-m-d H:i:s');
    $search_day_of_week = $dt->format('l');
    
    $params = [
        'from' => $origin, 'to' => $destination,
        'y' => $dt->format('Y'), 'm' => $dt->format('m'), 'd' => $dt->format('d'),
        'hh' => $dt->format('H'), 'm1' => floor($dt->format('i') / 10), 'm2' => $dt->format('i') % 10,
        'type' => $search_type, 'ticket' => 'ic',
    ];
    $url = 'https://transit.yahoo.co.jp/search/result?' . http_build_query($params);

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_TIMEOUT => 30,
    ]);
    $html = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);

    if ($curl_error) {
        error_log("Yahoo Transit API v5: cURL error - $curl_error");
        return ['status' => 'error', 'message' => 'Network error: ' . $curl_error];
    }

    if ($http_code !== 200 || !$html) {
        error_log("Yahoo Transit API v5: HTTP $http_code");
        return ['status' => 'error', 'message' => 'Failed to fetch data from Yahoo. HTTP: ' . $http_code];
    }

    preg_match('/<script id="__NEXT_DATA__" type="application\/json">(.*?)<\/script>/s', $html, $matches);
    if (!isset($matches[1])) {
        return ['status' => 'error', 'message' => 'Could not find __NEXT_DATA__ in HTML.'];
    }

    $data = json_decode($matches[1], true);
    $raw_routes = $data['props']['pageProps']['naviSearchParam']['featureInfoList'] ?? [];
    if (empty($raw_routes)) {
        return ['status' => 'error', 'message' => 'No routes found in __NEXT_DATA__.'];
    }
    
    // 最初の（最も効率的な）ルートのみを解析
    $best_raw_route = $raw_routes[0];
    
    // --- 新しいデータ整形ロジック ---
    $details = parseRouteDetails($best_raw_route['edgeInfoList']);

    // --- total_timeを内訳の合計値で再計算して上書き ---
    $recalculated_total_time = 
        $details['wait_time_minutes'] +
        $details['walk_to_station'] +
        $details['walk_from_station'];

    foreach ($details['trains'] as $train) {
        $recalculated_total_time += $train['time'];
        if (isset($train['transfer_after'])) {
            $recalculated_total_time += $train['transfer_after']['time'];
        }
    }

    return [
        'status' => 'success',
        'search_info' => [
            'type' => $search_type === 4 ? 'arrival' : 'departure',
            'datetime' => $search_datetime,
            'day_of_week' => $search_day_of_week  // 曜日
        ],
        'route' => [
            // Yahoo!の総時間ではなく、再計算した値を採用する
            'total_time' => $recalculated_total_time,
            'original_total_time' => (int) filter_var($best_raw_route['summaryInfo']['totalTime'], FILTER_SANITIZE_NUMBER_INT),  // 元の値も保存（デバッグ用）
            'details' => $details
        ]
    ];
}

/**
 * YahooのedgeInfoListから詳細なルート情報を抽出・整形する関数
 */
function parseRouteDetails($edge_list) {
    $walk_to_station = 0;
    $station_used = null;
    $trains = [];
    $walk_from_station = 0;
    $wait_time_minutes = 0;

    if (empty($edge_list)) return [];

    // 1. 家から最初の駅までの徒歩
    $first_edge = $edge_list[0];
    if (($first_edge['accessInfo']['type'] ?? -1) === 1) { // 1: walk
        preg_match('/(\d+)分/', $first_edge['railName'] ?? '', $matches);
        $walk_to_station = (int)($matches[1] ?? 0);
    }
    
    // 2. 電車区間と乗り換えの処理
    $train_section = null;
    for ($i = 0; $i < count($edge_list); $i++) {
        $edge = $edge_list[$i];
        
        // 電車区間の開始
        if (($edge['accessInfo']['type'] ?? -1) === 0) { // 0: train
            if ($station_used === null) {
                $station_used = $edge['pointName'];
                // 最初の駅での待ち時間を計算
                $arrival_at_station_str = $edge['timeInfo'][0]['time'] ?? null;
                $departure_on_train_str = $edge['timeInfo'][1]['time'] ?? null;
                if($arrival_at_station_str && $departure_on_train_str) {
                    $arrival_dt = new DateTime($arrival_at_station_str);
                    $departure_dt = new DateTime($departure_on_train_str);
                    $wait_time_minutes = round(($departure_dt->getTimestamp() - $arrival_dt->getTimestamp()) / 60);
                }
            }
            
            $departure_time_str = $edge['timeInfo'][1]['time'] ?? ($edge['timeInfo'][0]['time'] ?? null);
            $arrival_time_str = isset($edge_list[$i + 1]) ? ($edge_list[$i + 1]['timeInfo'][0]['time'] ?? null) : null;
            
            $train_duration = 0;
            if ($departure_time_str && $arrival_time_str) {
                $dep = new DateTime($departure_time_str);
                $arr = new DateTime($arrival_time_str);
                $train_duration = round(($arr->getTimestamp() - $dep->getTimestamp()) / 60);
            }

            $train_section = [
                'line' => $edge['railNameExcludingDestination'],
                'time' => $train_duration,
                'from' => $edge['pointName'],
                'to' => isset($edge_list[$i + 1]) ? $edge_list[$i + 1]['pointName'] : '最終目的地',
            ];
            
            // 乗り換えチェック
            $next_i = $i + 1;
            if (isset($edge_list[$next_i])) {
                $next_edge = $edge_list[$next_i];
                // 次が乗り換え（徒歩）
                if (($next_edge['accessInfo']['type'] ?? -1) === 1) {
                    preg_match('/(\d+)分/', $next_edge['railName'] ?? '', $matches);
                    $transfer_walk_time = (int)($matches[1] ?? 0);
                    $train_section['to'] = $next_edge['pointName'];

                    // さらにその次が電車
                    $after_transfer_i = $i + 2;
                    if(isset($edge_list[$after_transfer_i])) {
                         $train_section['transfer_after'] = [
                            'time' => $transfer_walk_time,
                            'to_line' => $edge_list[$after_transfer_i]['railNameExcludingDestination']
                        ];
                    }
                    $i++; // 徒歩区間をスキップ
                }
            }
            $trains[] = $train_section;
        }
    }
    
    // 3. 最後の徒歩区間
    $last_edge = end($edge_list);
    if (($last_edge['accessInfo']['type'] ?? -1) === 1 && count($edge_list) > 1) {
        preg_match('/(\d+)分/', $last_edge['railName'] ?? '', $matches);
        $walk_from_station = (int)($matches[1] ?? 0);
    }
    
    return [
        'wait_time_minutes' => $wait_time_minutes,
        'walk_to_station' => $walk_to_station,
        'station_used' => $station_used,
        'trains' => $trains,
        'walk_from_station' => $walk_from_station
    ];
}