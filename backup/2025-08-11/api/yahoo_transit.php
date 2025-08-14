<?php
// Yahoo!乗換案内スクレイピングAPI
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
    
    // HTMLパース
    return parseYahooTransitHTML($html);
}

/**
 * Yahoo!乗換案内のHTMLをパース
 */
function parseYahooTransitHTML($html) {
    // DOMDocumentでパース
    libxml_use_internal_errors(true);
    $doc = new DOMDocument();
    $doc->loadHTML('<?xml encoding="UTF-8">' . $html);
    libxml_clear_errors();
    $xpath = new DOMXPath($doc);
    
    // ルートが見つからない場合のチェック
    $noRoute = $xpath->query("//div[@class='elmNotFound']");
    if ($noRoute->length > 0) {
        return [
            'status' => 'ZERO_RESULTS',
            'routes' => []
        ];
    }
    
    // 最初のルート（route01）を取得
    $route = $xpath->query("//div[@id='route01']")->item(0);
    if (!$route) {
        return [
            'status' => 'ZERO_RESULTS',
            'routes' => []
        ];
    }
    
    // 概要情報の取得
    $summaryInfo = [];
    
    // 所要時間
    $timeNode = $xpath->query(".//div[@class='routeSummary']//li[@class='time']//span[last()]", $route)->item(0);
    $totalMinutes = 0;
    if ($timeNode) {
        $timeText = $timeNode->textContent;
        if (preg_match('/(\d+)時間/', $timeText, $hours)) {
            $totalMinutes += intval($hours[1]) * 60;
        }
        if (preg_match('/(\d+)分/', $timeText, $minutes)) {
            $totalMinutes += intval($minutes[1]);
        }
    }
    
    // 運賃
    $fareNode = $xpath->query(".//div[@class='routeSummary']//li[@class='fare']//span[@class='mark']", $route)->item(0);
    $totalFare = 0;
    if ($fareNode) {
        $fareText = $fareNode->textContent;
        $totalFare = intval(preg_replace('/[^\d]/', '', $fareText));
    }
    
    // 乗換回数
    $transferNode = $xpath->query(".//div[@class='routeSummary']//li[@class='transfer']//span[@class='mark']", $route)->item(0);
    $transferCount = 0;
    if ($transferNode) {
        $transferCount = intval($transferNode->textContent);
    }
    
    // 詳細な区間情報の取得
    $sections = [];
    $walkTimeTotal = 0;
    $stations = [];
    
    // 駅と交通機関のセクションを取得
    $stationNodes = $xpath->query(".//div[@class='routeDetail']//div[@class='station']", $route);
    $fareNodes = $xpath->query(".//div[@class='routeDetail']//div[@class='fareSection']", $route);
    
    // 最初の駅（出発地点）
    if ($stationNodes->length > 0) {
        $firstStation = $stationNodes->item(0);
        $departurePoint = $xpath->query(".//dl/dt", $firstStation)->item(0);
        if ($departurePoint) {
            $departurePointName = trim($departurePoint->textContent);
            
            // 最初の駅までの徒歩
            $walkNode = $xpath->query(".//following-sibling::div[@class='access'][1]//span[@class='icnWalk']/parent::*", $firstStation)->item(0);
            if ($walkNode) {
                $walkText = $walkNode->textContent;
                if (preg_match('/(\d+)分/', $walkText, $walkMinutes)) {
                    $walkTime = intval($walkMinutes[1]);
                    $walkTimeTotal += $walkTime;
                    
                    // 次の駅名を取得
                    $nextStation = $stationNodes->item(1);
                    if ($nextStation) {
                        $stationName = trim($xpath->query(".//dl/dt", $nextStation)->item(0)->textContent);
                        $stations[] = $stationName;
                        
                        $sections[] = [
                            'type' => 'walk',
                            'duration_minutes' => $walkTime,
                            'from' => $departurePointName,
                            'to' => $stationName
                        ];
                    }
                }
            }
        }
    }
    
    // 交通機関の区間
    foreach ($fareNodes as $index => $fareSection) {
        $transportNode = $xpath->query(".//div[@class='transport']", $fareSection)->item(0);
        if (!$transportNode) continue;
        
        $lineName = trim($transportNode->textContent);
        
        // この区間の駅を特定
        $prevStationNode = $xpath->query("./preceding-sibling::div[@class='station'][1]", $fareSection)->item(0);
        $nextStationNode = $xpath->query("./following-sibling::div[@class='station'][1]", $fareSection)->item(0);
        
        if ($prevStationNode && $nextStationNode) {
            $fromStation = trim($xpath->query(".//dl/dt", $prevStationNode)->item(0)->textContent);
            $toStation = trim($xpath->query(".//dl/dt", $nextStationNode)->item(0)->textContent);
            
            // 交通機関タイプの判定
            $transportType = 'train';
            if (strpos($lineName, 'バス') !== false) {
                $transportType = 'bus';
            }
            
            $sections[] = [
                'type' => $transportType,
                'line_name' => $lineName,
                'from' => $fromStation,
                'to' => $toStation
            ];
            
            // 最初の乗車駅を記録
            if ($index === 0 && !in_array($fromStation, $stations)) {
                $stations[] = $fromStation;
            }
        }
    }
    
    // 最後の駅から目的地までの徒歩
    if ($stationNodes->length > 1) {
        $lastStation = $stationNodes->item($stationNodes->length - 1);
        $walkNode = $xpath->query(".//p[@class='walk']", $lastStation)->item(0);
        if ($walkNode) {
            $walkText = $walkNode->textContent;
            if (preg_match('/(\d+)分/', $walkText, $walkMinutes)) {
                $walkTime = intval($walkMinutes[1]);
                $walkTimeTotal += $walkTime;
            }
        }
    }
    
    // 徒歩のみのルートかチェック
    $isWalkOnly = count(array_filter($sections, function($s) { return $s['type'] !== 'walk'; })) === 0;
    if ($isWalkOnly && count($sections) === 1) {
        $walkTimeTotal = $totalMinutes;
    }
    
    // Google Maps API互換形式に変換
    $steps = [];
    foreach ($sections as $section) {
        if ($section['type'] === 'walk') {
            $steps[] = [
                'travel_mode' => 'WALKING',
                'duration' => [
                    'value' => $section['duration_minutes'] * 60,
                    'text' => $section['duration_minutes'] . '分'
                ],
                'html_instructions' => $section['from'] . 'から' . $section['to'] . 'まで歩く'
            ];
        } else {
            $steps[] = [
                'travel_mode' => 'TRANSIT',
                'transit_details' => [
                    'line' => [
                        'name' => $section['line_name'],
                        'vehicle' => [
                            'type' => strtoupper($section['type'])
                        ]
                    ],
                    'departure_stop' => ['name' => $section['from']],
                    'arrival_stop' => ['name' => $section['to']]
                ]
            ];
        }
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