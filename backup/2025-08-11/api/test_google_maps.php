<?php
/**
 * Test script for Google Maps Transit API
 */

// Test case 1: Simple route
$test_data = [
    'origin' => '東京都中央区日本橋本町4-14-2',  // ルフォンプログレ日本橋
    'destination' => '東京都中央区日本橋2-5-1',    // 至善館
    'arrival_time' => null  // Use default (next Tuesday 10:00)
];

echo "=== Test Case 1: Simple Route ===\n";
echo "Origin: " . $test_data['origin'] . "\n";
echo "Destination: " . $test_data['destination'] . "\n\n";

// Call the API
$url = 'http://localhost/timeline-mapping/api/google_maps_transit.php';

$options = [
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($test_data),
        'timeout' => 120  // 2 minutes timeout
    ]
];

$context = stream_context_create($options);
$response = @file_get_contents($url, false, $context);

if ($response === FALSE) {
    echo "Error: Failed to call API\n";
    exit(1);
}

$result = json_decode($response, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    echo "Error: Invalid JSON response\n";
    echo "Raw response: " . $response . "\n";
    exit(1);
}

// Pretty print the result
echo "Result:\n";
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n\n";

// Verify structure matches Yahoo API format
if ($result['status'] === 'success') {
    echo "✅ Status: Success\n";
    
    // Check required fields
    $required_fields = [
        'search_info' => ['type', 'datetime', 'day_of_week'],
        'route' => ['total_time', 'details']
    ];
    
    $details_fields = [
        'wait_time_minutes',
        'walk_to_station',
        'station_used',
        'trains',
        'walk_from_station'
    ];
    
    $all_good = true;
    
    // Check main structure
    foreach ($required_fields as $section => $fields) {
        if (!isset($result[$section])) {
            echo "❌ Missing section: $section\n";
            $all_good = false;
            continue;
        }
        
        foreach ($fields as $field) {
            if (!isset($result[$section][$field])) {
                echo "❌ Missing field: $section.$field\n";
                $all_good = false;
            } else {
                echo "✅ Found: $section.$field\n";
            }
        }
    }
    
    // Check details structure
    if (isset($result['route']['details'])) {
        foreach ($details_fields as $field) {
            if (!isset($result['route']['details'][$field])) {
                echo "❌ Missing detail field: $field\n";
                $all_good = false;
            } else {
                echo "✅ Found detail: $field\n";
            }
        }
        
        // Check trains structure
        if (isset($result['route']['details']['trains']) && is_array($result['route']['details']['trains'])) {
            echo "✅ Trains array found with " . count($result['route']['details']['trains']) . " train(s)\n";
            
            foreach ($result['route']['details']['trains'] as $i => $train) {
                $train_fields = ['line', 'time', 'from', 'to'];
                foreach ($train_fields as $field) {
                    if (!isset($train[$field])) {
                        echo "❌ Train $i missing field: $field\n";
                        $all_good = false;
                    }
                }
            }
        }
    }
    
    if ($all_good) {
        echo "\n✅ All structure checks passed! Format is compatible with Yahoo Transit API.\n";
    } else {
        echo "\n⚠️  Some structure checks failed. Please review the output.\n";
    }
    
} else {
    echo "❌ Status: Error\n";
    echo "Error message: " . ($result['message'] ?? 'Unknown error') . "\n";
    if (isset($result['traceback'])) {
        echo "Traceback:\n" . $result['traceback'] . "\n";
    }
}

// Test case 2: With specific arrival time
echo "\n\n=== Test Case 2: With Arrival Time ===\n";

$test_data2 = [
    'origin' => '東京駅',
    'destination' => '渋谷駅',
    'arrival_time' => 'now'  // Current time
];

echo "Origin: " . $test_data2['origin'] . "\n";
echo "Destination: " . $test_data2['destination'] . "\n";
echo "Arrival time: now\n\n";

$options2 = [
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($test_data2),
        'timeout' => 120
    ]
];

$context2 = stream_context_create($options2);
$response2 = @file_get_contents($url, false, $context2);

if ($response2 !== FALSE) {
    $result2 = json_decode($response2, true);
    if ($result2 && $result2['status'] === 'success') {
        echo "✅ Test case 2 passed\n";
        echo "Total time: " . $result2['route']['total_time'] . " minutes\n";
        echo "Route: ";
        if (isset($result2['route']['details']['station_used'])) {
            echo $result2['route']['details']['station_used'];
        }
        if (isset($result2['route']['details']['trains'][0])) {
            echo " → " . $result2['route']['details']['trains'][0]['line'];
        }
        echo "\n";
    } else {
        echo "❌ Test case 2 failed\n";
        if (isset($result2['message'])) {
            echo "Error: " . $result2['message'] . "\n";
        }
    }
} else {
    echo "❌ Test case 2 failed to execute\n";
}

echo "\n=== Test Complete ===\n";
?>