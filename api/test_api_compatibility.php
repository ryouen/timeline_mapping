<?php
/**
 * Test compatibility between Yahoo Transit API and Google Maps scraping
 */

// Test parameters
$test_routes = [
    [
        'origin' => '東京駅',
        'destination' => '渋谷駅',
        'name' => 'Simple station to station'
    ],
    [
        'origin' => '東京都中央区日本橋本町4-14-2',
        'destination' => '東京都中央区日本橋2-5-1',
        'name' => 'Address to address'
    ]
];

function callAPI($url, $data) {
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => json_encode($data),
            'timeout' => 60
        ]
    ];
    
    $context = stream_context_create($options);
    $response = @file_get_contents($url, false, $context);
    
    if ($response === FALSE) {
        return null;
    }
    
    return json_decode($response, true);
}

function compareStructures($yahoo, $google, $path = '') {
    $differences = [];
    
    // Check if both have the same keys
    if (is_array($yahoo) && is_array($google)) {
        $yahooKeys = array_keys($yahoo);
        $googleKeys = array_keys($google);
        
        $missingInGoogle = array_diff($yahooKeys, $googleKeys);
        $extraInGoogle = array_diff($googleKeys, $yahooKeys);
        
        foreach ($missingInGoogle as $key) {
            $differences[] = "$path.$key exists in Yahoo but not in Google";
        }
        
        foreach ($extraInGoogle as $key) {
            $differences[] = "$path.$key exists in Google but not in Yahoo";
        }
        
        // Compare common keys
        $commonKeys = array_intersect($yahooKeys, $googleKeys);
        foreach ($commonKeys as $key) {
            if (is_array($yahoo[$key]) && is_array($google[$key])) {
                $subDiffs = compareStructures($yahoo[$key], $google[$key], "$path.$key");
                $differences = array_merge($differences, $subDiffs);
            }
        }
    }
    
    return $differences;
}

// Run tests
foreach ($test_routes as $test) {
    echo "\n=== Testing: " . $test['name'] . " ===\n";
    echo "Route: " . $test['origin'] . " → " . $test['destination'] . "\n\n";
    
    // Call Yahoo Transit API
    echo "1. Calling Yahoo Transit API...\n";
    $yahooData = [
        'origin' => $test['origin'],
        'destination' => $test['destination'],
        'arrival_time' => null
    ];
    
    $yahooResult = callAPI('http://localhost/timeline-mapping/api/yahoo_transit_api_v5.php', $yahooData);
    
    if ($yahooResult && $yahooResult['status'] === 'success') {
        echo "✅ Yahoo API returned success\n";
        echo "  Total time: " . $yahooResult['route']['total_time'] . " minutes\n";
        echo "  Trains: " . count($yahooResult['route']['details']['trains']) . "\n";
    } else {
        echo "❌ Yahoo API failed\n";
        if ($yahooResult) {
            echo "  Error: " . ($yahooResult['message'] ?? 'Unknown error') . "\n";
        }
    }
    
    // Call Google Maps scraping
    echo "\n2. Calling Google Maps scraping...\n";
    $googleData = [
        'origin' => $test['origin'],
        'destination' => $test['destination'],
        'arrival_time' => null
    ];
    
    $googleResult = callAPI('http://localhost/timeline-mapping/api/google_maps_transit.php', $googleData);
    
    if ($googleResult && $googleResult['status'] === 'success') {
        echo "✅ Google Maps scraping returned success\n";
        echo "  Total time: " . $googleResult['route']['total_time'] . " minutes\n";
        echo "  Trains: " . count($googleResult['route']['details']['trains']) . "\n";
    } else {
        echo "❌ Google Maps scraping failed\n";
        if ($googleResult) {
            echo "  Error: " . ($googleResult['message'] ?? 'Unknown error') . "\n";
        }
    }
    
    // Compare structures
    if ($yahooResult && $googleResult && 
        $yahooResult['status'] === 'success' && 
        $googleResult['status'] === 'success') {
        
        echo "\n3. Comparing API structures...\n";
        $differences = compareStructures($yahooResult, $googleResult);
        
        if (empty($differences)) {
            echo "✅ API structures are identical!\n";
        } else {
            echo "⚠️  Found structure differences:\n";
            foreach ($differences as $diff) {
                echo "   - $diff\n";
            }
        }
        
        // Compare specific values
        echo "\n4. Comparing key values:\n";
        
        // Compare search_info
        $yahooType = $yahooResult['search_info']['type'] ?? '';
        $googleType = $googleResult['search_info']['type'] ?? '';
        echo "  Search type: Yahoo='{$yahooType}', Google='{$googleType}' ";
        echo ($yahooType === $googleType ? "✅" : "❌") . "\n";
        
        // Compare route details structure
        $yahooDetails = $yahooResult['route']['details'];
        $googleDetails = $googleResult['route']['details'];
        
        $detailFields = ['wait_time_minutes', 'walk_to_station', 'station_used', 'walk_from_station'];
        foreach ($detailFields as $field) {
            $yahooVal = $yahooDetails[$field] ?? 'N/A';
            $googleVal = $googleDetails[$field] ?? 'N/A';
            echo "  $field: Yahoo='$yahooVal', Google='$googleVal' ";
            echo (gettype($yahooVal) === gettype($googleVal) ? "✅" : "❌ (type mismatch)") . "\n";
        }
        
        // Compare train structure
        if (isset($yahooDetails['trains'][0]) && isset($googleDetails['trains'][0])) {
            echo "\n  First train comparison:\n";
            $yahooTrain = $yahooDetails['trains'][0];
            $googleTrain = $googleDetails['trains'][0];
            
            $trainFields = ['line', 'time', 'from', 'to'];
            foreach ($trainFields as $field) {
                $yahooVal = $yahooTrain[$field] ?? 'N/A';
                $googleVal = $googleTrain[$field] ?? 'N/A';
                echo "    $field: Yahoo='$yahooVal', Google='$googleVal' ";
                echo (isset($yahooTrain[$field]) === isset($googleTrain[$field]) ? "✅" : "❌") . "\n";
            }
        }
    }
    
    echo "\n" . str_repeat("-", 60) . "\n";
}

echo "\n=== Test Complete ===\n";
?>