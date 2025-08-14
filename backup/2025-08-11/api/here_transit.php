<?php
// HERE Public Transit API integration for Japanese transit routing
// This replaces Google Maps API for transit mode which doesn't work in Japan

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

// Load .env
loadEnv(__DIR__ . '/../.env');

// HERE API credentials
$HERE_API_KEY = $_ENV['HERE_API_KEY'] ?? '';

if (empty($HERE_API_KEY)) {
    // Return fallback response if HERE API key not configured
    echo json_encode([
        'error' => 'HERE API key not configured',
        'status' => 'API_KEY_MISSING'
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

// Function to geocode address using HERE Geocoding API
function geocodeLocation($address, $apiKey) {
    $url = 'https://geocode.search.hereapi.com/v1/geocode';
    $params = [
        'q' => $address,
        'apiKey' => $apiKey,
        'in' => 'countryCode:JPN',  // Restrict to Japan
        'limit' => 1
    ];
    
    $geocodeUrl = $url . '?' . http_build_query($params);
    $response = @file_get_contents($geocodeUrl);
    
    if ($response === FALSE) {
        return null;
    }
    
    $data = json_decode($response, true);
    if (isset($data['items'][0]['position'])) {
        return [
            'lat' => $data['items'][0]['position']['lat'],
            'lng' => $data['items'][0]['position']['lng']
        ];
    }
    
    return null;
}

// Function to get transit route using HERE Public Transit API
function getTransitRoute($origin, $destination, $apiKey, $departureTime) {
    // First geocode the addresses
    $originCoords = geocodeLocation($origin, $apiKey);
    $destCoords = geocodeLocation($destination, $apiKey);
    
    if (!$originCoords || !$destCoords) {
        return [
            'error' => 'Failed to geocode locations',
            'status' => 'GEOCODING_ERROR'
        ];
    }
    
    // HERE Public Transit API endpoint
    $url = 'https://transit.router.hereapi.com/v8/routes';
    
    // Format departure time for HERE API (ISO 8601)
    $departureTimeISO = date('Y-m-d\TH:i:s', $departureTime);
    
    $params = [
        'apiKey' => $apiKey,
        'origin' => $originCoords['lat'] . ',' . $originCoords['lng'],
        'destination' => $destCoords['lat'] . ',' . $destCoords['lng'],
        'departureTime' => $departureTimeISO,
        'return' => 'travelSummary,routes',
        'alternatives' => 3,  // Get up to 3 alternative routes
        'modes' => 'pedestrian,publicTransport'  // Walking + Public Transit
    ];
    
    $routeUrl = $url . '?' . http_build_query($params);
    $response = @file_get_contents($routeUrl);
    
    if ($response === FALSE) {
        return [
            'error' => 'Failed to get transit route',
            'status' => 'ROUTE_ERROR'
        ];
    }
    
    $data = json_decode($response, true);
    
    // Convert HERE response to Google Maps compatible format
    if (isset($data['routes']) && count($data['routes']) > 0) {
        $routes = [];
        
        foreach ($data['routes'] as $hereRoute) {
            if (!isset($hereRoute['sections'])) continue;
            
            $totalDuration = 0;
            $totalWalkTime = 0;
            $steps = [];
            
            foreach ($hereRoute['sections'] as $section) {
                $duration = $section['travelSummary']['duration'] ?? 0;
                $totalDuration += $duration;
                
                // Check if this is a walking section
                if ($section['type'] === 'pedestrian') {
                    $totalWalkTime += $duration;
                }
                
                // Build step information
                $step = [
                    'duration' => [
                        'value' => $duration,
                        'text' => formatDuration($duration)
                    ],
                    'travel_mode' => $section['type'] === 'pedestrian' ? 'WALKING' : 'TRANSIT'
                ];
                
                // Add transit details if available
                if ($section['type'] === 'transit' && isset($section['transport'])) {
                    $step['transit_details'] = [
                        'line' => [
                            'name' => $section['transport']['name'] ?? '',
                            'short_name' => $section['transport']['shortName'] ?? '',
                            'vehicle' => [
                                'type' => mapTransportMode($section['transport']['mode'] ?? '')
                            ]
                        ],
                        'departure_stop' => [
                            'name' => $section['departure']['place']['name'] ?? ''
                        ],
                        'arrival_stop' => [
                            'name' => $section['arrival']['place']['name'] ?? ''
                        ]
                    ];
                }
                
                $steps[] = $step;
            }
            
            $route = [
                'legs' => [[
                    'duration' => [
                        'value' => $totalDuration,
                        'text' => formatDuration($totalDuration)
                    ],
                    'steps' => $steps,
                    'walk_time' => [
                        'value' => $totalWalkTime,
                        'text' => formatDuration($totalWalkTime)
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
    
    return [
        'status' => 'ZERO_RESULTS',
        'routes' => []
    ];
}

// Helper function to format duration in seconds to human readable
function formatDuration($seconds) {
    $hours = floor($seconds / 3600);
    $minutes = floor(($seconds % 3600) / 60);
    
    if ($hours > 0) {
        return $hours . '時間' . $minutes . '分';
    } else {
        return $minutes . '分';
    }
}

// Helper function to map HERE transport modes to Google Maps types
function mapTransportMode($hereMode) {
    $modeMap = [
        'highSpeedTrain' => 'RAIL',
        'intercityTrain' => 'RAIL',
        'interRegionalTrain' => 'RAIL',
        'regionalTrain' => 'RAIL',
        'cityTrain' => 'RAIL',
        'subway' => 'SUBWAY',
        'lightRail' => 'TRAM',
        'monorail' => 'RAIL',
        'bus' => 'BUS',
        'rapidBus' => 'BUS',
        'expressBus' => 'BUS',
        'localBus' => 'BUS',
        'ferry' => 'FERRY'
    ];
    
    return $modeMap[$hereMode] ?? 'OTHER';
}

// Set departure time (morning 9:00)
$today9am = strtotime('today 9:00');
if (time() > $today9am) {
    $departureTimestamp = strtotime('tomorrow 9:00');
} else {
    $departureTimestamp = $today9am;
}

// Get transit route using HERE API
$result = getTransitRoute($origin, $destination, $HERE_API_KEY, $departureTimestamp);

// Return the result
echo json_encode($result, JSON_UNESCAPED_UNICODE);
?>