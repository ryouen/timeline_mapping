<?php
/**
 * Yahoo!乗換案内スクレイピングAPI
 * * 機能:
 * - POSTリクエストで出発地(origin)と目的地(destination)のJSONを受け取る
 * - Yahoo!乗換案内の検索結果ページから埋め込みJSON(__NEXT_DATA__)を抽出
 * - データを整形し、ルート情報をJSON形式で返す
 * * 使い方:
 * このファイルをWebサーバーに配置し、POSTリクエストを送信する。
 * 例: curl -X POST -H "Content-Type: application/json" -d '{"origin":"東京駅", "destination":"大阪駅"}' https://your-server.com/yahoo_transit_api.php
 */

// --- ヘッダー設定 (APIとして機能させるため) ---
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *'); // 必要に応じて特定のドメインに制限
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// プリフライトリクエストへの対応
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// --- メイン処理 ---

// POSTリクエストのボディからJSONデータを取得
$json_input = file_get_contents('php://input');
$input_data = json_decode($json_input, true);

// 入力バリデーション
if (empty($input_data['origin']) || empty($input_data['destination'])) {
    http_response_code(400); // Bad Request
    echo json_encode([
        'error' => 'Bad Request',
        'message' => 'origin and destination are required.'
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// ルート検索の実行
$origin = $input_data['origin'];
$destination = $input_data['destination'];

$route_info = getYahooTransitRoute($origin, $destination);

if ($route_info === null) {
    http_response_code(404); // Not Found
    echo json_encode([
        'error' => 'Not Found',
        'message' => "No routes found from {$origin} to {$destination}."
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// 成功レスポンス
http_response_code(200);
echo json_encode($route_info, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);


/**
 * Yahoo!乗換案内の検索を実行し、結果を整形して返すメイン関数
 * @param string $origin 出発地
 * @param string $destination 目的地
 * @return array|null 整形されたルート情報、または失敗時にnull
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
    curl_close($ch);

    if ($http_code !== 200 || !$html) {
        return null;
    }

    // 埋め込みJSON(__NEXT_DATA__)を抽出
    preg_match('/<script id="__NEXT_DATA__" type="application\/json">(.*?)<\/script>/s', $html, $matches);

    if (!isset($matches[1])) {
        return null;
    }

    $data = json_decode($matches[1], true);

    // JSONデータからルート情報を抽出
    $raw_routes = $data['props']['pageProps']['naviSearchParam']['featureInfoList'] ?? [];
    if (empty($raw_routes)) {
        return null;
    }
    
    // 必要な情報だけを整形して新しい配列に格納
    $formatted_routes = [];
    foreach ($raw_routes as $i => $route) {
        $summary = $route['summaryInfo'];
        $sections = [];
        $walk_time_total = 0;
        
        foreach ($route['edgeInfoList'] as $edge) {
            $type = ($edge['accessInfo']['type'] ?? -1) === 1 ? 'walk' : 'train';
            
            // 徒歩時間の合計を計算
            if ($type === 'walk') {
                preg_match('/(\d+)分/', $edge['railName'], $walk_matches);
                $walk_time_total += (int)($walk_matches[1] ?? 0);
            }

            $sections[] = [
                'type' => $type,
                'line_name' => $edge['railNameExcludingDestination'] ?? null,
                'destination' => $edge['destination'] ?? null,
                'departure_station' => $edge['pointName'],
                'departure_time' => $edge['timeInfo'][0]['time'] ?? null,
                'arrival_station' => null, // 次のedgeのpointNameが到着駅となる
                'arrival_time' => $edge['timeInfo'][1]['time'] ?? ($edge['timeInfo'][0]['time'] ?? null),
            ];
        }

        // 各区間の到着駅を次の区間の出発駅から補完
        for ($j = 0; $j < count($sections) - 1; $j++) {
            $sections[$j]['arrival_station'] = $sections[$j + 1]['departure_station'];
        }
        // 最後の区間の到着駅
        $last_edge = end($route['edgeInfoList']);
        $sections[count($sections) - 1]['arrival_station'] = $last_edge['stationName'];
        

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
        'search_query' => [
            'from' => $origin,
            'to' => $destination,
            'datetime' => $dt->format(DateTime::ATOM)
        ],
        'routes' => $formatted_routes
    ];
}