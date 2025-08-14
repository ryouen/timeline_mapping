<?php
// Ekispert API integration for Japanese transit routing
// Official API for Japanese public transportation

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// Load environment variables
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

loadEnv(__DIR__ . '/../.env');

$EKISPERT_API_KEY = $_ENV['EKISPERT_API_KEY'] ?? '';

if (empty($EKISPERT_API_KEY)) {
    echo json_encode([
        'error' => 'Ekispert API key not configured',
        'status' => 'API_KEY_MISSING',
        'message' => 'Please apply for free API key at: https://ekiworld.net/service/sexp/webservice/free_provision.html'
    ]);
    exit;
}

// Get request data
$input = json_decode(file_get_contents('php://input'), true);

$origin = $input['origin'] ?? '';
$destination = $input['destination'] ?? '';
$mode = $input['mode'] ?? 'transit';
$departure_time = $input['departure_time'] ?? 'morning';

if (empty($origin) || empty($destination)) {
    echo json_encode(['error' => 'Origin and destination are required']);
    exit;
}

// Function to search route using Ekispert API
function getEkispertRoute($origin, $destination, $apiKey) {
    // Ekispert Search API endpoint
    $baseUrl = 'https://api.ekispert.jp/v1/json/search/course/extreme';
    
    // Set departure time (morning 9:00)
    $today9am = strtotime('today 9:00');
    if (time() > $today9am) {
        $departureTime = strtotime('tomorrow 9:00');
    } else {
        $departureTime = $today9am;
    }
    
    // Format time for Ekispert (HHMM format)
    $timeFormatted = date('Hi', $departureTime);
    $dateFormatted = date('Ymd', $departureTime);
    
    $params = [
        'key' => $apiKey,
        'viaList' => $origin . ':' . $destination,
        'date' => $dateFormatted,
        'time' => $timeFormatted,
        'searchType' => 'departure',  // 出発時刻指定
        'sort' => 'time',  // 所要時間順でソート
        'plane' => 'false',  // 飛行機を使わない
        'shinkansen' => 'true',  // 新幹線OK
        'limitedExpress' => 'true',  // 特急OK
        'ship' => 'false',  // 船を使わない
        'bus' => 'true',  // バスOK
        'walk' => 'true',  // 徒歩区間OK
        'answer' => '3',  // 3つの候補を返す
        'corporationBind' => 'false'
    ];
    
    $url = $baseUrl . '?' . http_build_query($params);
    
    $context = stream_context_create([
        'http' => [
            'timeout' => 30,
            'user_agent' => 'Mozilla/5.0 (compatible; TimelineMapping/1.0)'
        ]
    ]);
    
    $response = @file_get_contents($url, false, $context);
    
    if ($response === FALSE) {
        return [
            'error' => 'Failed to call Ekispert API',
            'status' => 'API_ERROR'
        ];
    }
    
    $data = json_decode($response, true);
    
    // Convert Ekispert response to Google Maps compatible format
    if (isset($data['ResultSet']['Course']) && is_array($data['ResultSet']['Course'])) {
        $routes = [];
        
        foreach ($data['ResultSet']['Course'] as $course) {
            $totalTime = (int)($course['timeTotal'] ?? 0);
            $walkTime = (int)($course['walkTime'] ?? 0);
            $fare = (int)($course['fareTotal'] ?? 0);
            
            $steps = [];
            
            // Process route sections
            if (isset($course['Route']['Point']) && is_array($course['Route']['Point'])) {
                $points = $course['Route']['Point'];
                
                for ($i = 0; $i < count($points) - 1; $i++) {
                    $fromPoint = $points[$i];
                    $toPoint = $points[$i + 1];
                    
                    // Check if there's a Line between points (transit)
                    if (isset($course['Route']['Line'])) {
                        $lines = is_array($course['Route']['Line'][0]) ? $course['Route']['Line'] : [$course['Route']['Line']];
                        
                        foreach ($lines as $line) {
                            if (isset($line['Name'])) {
                                $step = [
                                    'travel_mode' => 'TRANSIT',
                                    'duration' => [
                                        'value' => $line['timeTotal'] ?? 0,
                                        'text' => formatMinutes($line['timeTotal'] ?? 0)
                                    ],
                                    'transit_details' => [
                                        'line' => [
                                            'name' => $line['Name'],
                                            'short_name' => $line['Name'],
                                            'vehicle' => [
                                                'type' => mapEkispertTransportType($line['Type'] ?? '')
                                            ]
                                        ],
                                        'departure_stop' => [
                                            'name' => $fromPoint['Name'] ?? ''
                                        ],
                                        'arrival_stop' => [
                                            'name' => $toPoint['Name'] ?? ''
                                        ]
                                    ]
                                ];
                                $steps[] = $step;
                            }
                        }
                    }
                    
                    // Add walking segments
                    if (isset($fromPoint['walkTime']) && $fromPoint['walkTime'] > 0) {
                        $steps[] = [
                            'travel_mode' => 'WALKING',
                            'duration' => [
                                'value' => (int)$fromPoint['walkTime'] * 60,
                                'text' => formatMinutes($fromPoint['walkTime'])
                            ]
                        ];
                    }
                }
            }
            
            $route = [
                'legs' => [[
                    'duration' => [
                        'value' => $totalTime * 60,  // Convert to seconds
                        'text' => formatMinutes($totalTime)
                    ],
                    'steps' => $steps,
                    'walk_time' => [
                        'value' => $walkTime * 60,
                        'text' => formatMinutes($walkTime)
                    ],
                    'fare' => [
                        'value' => $fare,
                        'text' => '¥' . number_format($fare)
                    ]
                ]]
            ];
            
            $routes[] = $route;
        }
        
        return [
            'status' => 'OK',
            'routes' => $routes,
            'geocoded_waypoints' => [
                ['geocoder_status' => 'OK'],
                ['geocoder_status' => 'OK']
            ]
        ];
    }
    
    // Check for specific error messages
    if (isset($data['ResultSet']['Error'])) {
        $errorCode = $data['ResultSet']['Error']['code'] ?? '';
        $errorMessage = $data['ResultSet']['Error']['Message'] ?? 'Unknown error';
        
        return [
            'status' => 'ZERO_RESULTS',
            'error' => "Ekispert API Error: {$errorMessage} (Code: {$errorCode})",
            'routes' => []
        ];
    }
    
    return [
        'status' => 'ZERO_RESULTS',
        'routes' => [],
        'debug_response' => $data  // For debugging
    ];
}

// Helper function to format minutes
function formatMinutes($minutes) {
    $hours = floor($minutes / 60);
    $mins = $minutes % 60;
    
    if ($hours > 0) {
        return $hours . '時間' . $mins . '分';
    } else {
        return $mins . '分';
    }
}

// Helper function to map Ekispert transport types to Google Maps types
function mapEkispertTransportType($ekispertType) {
    $typeMap = [
        'train' => 'RAIL',
        'subway' => 'SUBWAY',
        'bus' => 'BUS',
        'walk' => 'WALKING',
        'ship' => 'FERRY'
    ];
    
    return $typeMap[strtolower($ekispertType)] ?? 'RAIL';
}

// Get route using Ekispert API
$result = getEkispertRoute($origin, $destination, $EKISPERT_API_KEY);

// Return the result
echo json_encode($result, JSON_UNESCAPED_UNICODE);
?>