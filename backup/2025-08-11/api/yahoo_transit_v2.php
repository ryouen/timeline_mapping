<?php
// Yahoo!乗換案内スクレイピングAPI v2 - 正規表現ベース
// 日本の公共交通機関ルート検索

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET');
header('Access-Control-Allow-Headers: Content-Type');

// POSTリクエストの処理
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
} else {
    $input = $_GET;
}

$origin = $input['origin'] ?? '';
$destination = $input['destination'] ?? '';
$departure_time = $input['departure_time'] ?? 'morning';

if (empty($origin) || empty($destination)) {
    echo json_encode(['error' => 'Origin and destination are required'], JSON_UNESCAPED_UNICODE);
    exit;
}

/**
 * Yahoo!乗換案内からルート情報を取得
 */
function getYahooTransitRoute($origin, $destination, $departureTime = null) {
    if ($departureTime === null || $departureTime === 'morning') {
        $dt = new DateTime('tomorrow 09:00');
    } else {
        $dt = new DateTime($departureTime);
    }
    
    $baseUrl = "https://transit.yahoo.co.jp/search/result";
    
    // パラメータの準備
    $params = [
        'from' => $origin,
        'to' => $destination,
        'y' => $dt->format('Y'),
        'm' => $dt->format('m'),
        'd' => $dt->format('d'),
        'hh' => $dt->format('H'),
        'm1' => floor($dt->format('i') / 10),
        'm2' => $dt->format('i') % 10,
        'type' => 1,  // 出発時刻指定
        'ticket' => 'ic',  // IC運賃
        'expkind' => 1,  // 普通列車優先
        'ws' => 3  // 歩く速度：標準
    ];
    
    $url = $baseUrl . '?' . http_build_query($params);
    
    // cURLでHTMLを取得
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_ENCODING, 'gzip, deflate');
    
    $html = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode !== 200) {
        return [
            'error' => 'Failed to fetch route',
            'status' => 'HTTP_ERROR',
            'code' => $httpCode
        ];
    }
    
    // HTMLパース（正規表現ベース）
    return parseYahooTransitWithRegex($html);
}

/**
 * Yahoo!乗換案内のHTMLを正規表現でパース
 */
function parseYahooTransitWithRegex($html) {
    // ルートが見つからない場合
    if (strpos($html, 'elmNotFound') !== false || strpos($html, 'route01') === false) {
        return [
            'status' => 'ZERO_RESULTS',
            'routes' => []
        ];
    }
    
    // route01セクションを抽出
    preg_match('/<div[^>]*id="route01"[^>]*>(.*?)<div[^>]*id="route02"/s', $html, $routeMatch);
    if (empty($routeMatch)) {
        // route02がない場合はページ終端まで
        preg_match('/<div[^>]*id="route01"[^>]*>(.*?)<!-- \.routeList -->/s', $html, $routeMatch);
    }
    
    if (empty($routeMatch)) {
        return [
            'status' => 'ZERO_RESULTS',
            'routes' => []
        ];
    }
    
    $routeHtml = $routeMatch[1];
    
    // 所要時間の取得
    $totalMinutes = 0;
    if (preg_match('/<li[^>]*class="time"[^>]*>.*?<span[^>]*class="small"[^>]*>.*?<\/span>\s*([^<]+)/s', $routeHtml, $timeMatch)) {
        $timeText = trim($timeMatch[1]);
        if (preg_match('/(\d+)時間/', $timeText, $hours)) {
            $totalMinutes += intval($hours[1]) * 60;
        }
        if (preg_match('/(\d+)分/', $timeText, $minutes)) {
            $totalMinutes += intval($minutes[1]);
        }
    }
    
    // 運賃の取得
    $totalFare = 0;
    if (preg_match('/<li[^>]*class="fare"[^>]*>.*?<span[^>]*class="mark"[^>]*>([^<]+)/s', $routeHtml, $fareMatch)) {
        $fareText = $fareMatch[1];
        $totalFare = intval(preg_replace('/[^\d]/', '', $fareText));
    }
    
    // 乗換回数の取得
    $transferCount = 0;
    if (preg_match('/<li[^>]*class="transfer"[^>]*>.*?<span[^>]*class="mark"[^>]*>([^<]+)/s', $routeHtml, $transferMatch)) {
        $transferCount = intval($transferMatch[1]);
    }
    
    // 詳細ルート情報を取得
    $steps = [];
    $walkTimeTotal = 0;
    $stations = [];
    
    // 最初の徒歩区間を取得
    if (preg_match('/<p[^>]*class="walk"[^>]*>.*?(\d+)分/s', $routeHtml, $firstWalkMatch)) {
        $walkTime = intval($firstWalkMatch[1]);
        $walkTimeTotal += $walkTime;
        
        $steps[] = [
            'travel_mode' => 'WALKING',
            'duration' => [
                'value' => $walkTime * 60,
                'text' => $walkTime . '分'
            ]
        ];
    }
    
    // 交通機関区間を取得（簡易版）
    preg_match_all('/<div[^>]*class="transport"[^>]*>([^<]+)<\/div>/s', $routeHtml, $transportMatches);
    
    if (!empty($transportMatches[1])) {
        foreach ($transportMatches[1] as $transport) {
            $lineName = trim($transport);
            
            // 駅名を取得するため、より詳細なパースが必要
            // ここでは簡易的に路線名のみ記録
            $steps[] = [
                'travel_mode' => 'TRANSIT',
                'transit_details' => [
                    'line' => [
                        'name' => $lineName,
                        'vehicle' => [
                            'type' => (strpos($lineName, 'バス') !== false) ? 'BUS' : 'RAIL'
                        ]
                    ],
                    'departure_stop' => ['name' => ''],
                    'arrival_stop' => ['name' => '']
                ]
            ];
        }
        
        // 最初の利用駅を取得（簡易版）
        if (preg_match('/<dt>([^<]+駅[^<]*)<\/dt>/u', $routeHtml, $stationMatch)) {
            $stations[] = trim($stationMatch[1]);
        }
    }
    
    // 最後の徒歩区間がある場合
    if (preg_match_all('/<p[^>]*class="walk"[^>]*>.*?(\d+)分/s', $routeHtml, $allWalkMatches)) {
        // 最初の徒歩以外の徒歩時間も追加
        for ($i = 1; $i < count($allWalkMatches[1]); $i++) {
            $walkTime = intval($allWalkMatches[1][$i]);
            $walkTimeTotal += $walkTime;
        }
    }
    
    // 徒歩のみのルートかチェック
    $isWalkOnly = empty($transportMatches[1]);
    if ($isWalkOnly) {
        $walkTimeTotal = $totalMinutes;
    }
    
    return [
        'status' => 'OK',
        'routes' => [[
            'legs' => [[
                'duration' => [
                    'value' => $totalMinutes * 60,
                    'text' => $totalMinutes . '分'
                ],
                'steps' => $steps,
                'walk_time' => [
                    'value' => $walkTimeTotal * 60,
                    'text' => $walkTimeTotal . '分'
                ],
                'fare' => [
                    'value' => $totalFare,
                    'text' => '¥' . number_format($totalFare)
                ],
                'transfers' => $transferCount,
                'stations_used' => $stations
            ]]
        ]]
    ];
}

// メイン処理
$result = getYahooTransitRoute($origin, $destination, $departure_time);

// JSON出力
echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>