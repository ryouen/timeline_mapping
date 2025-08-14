<?php
/**
 * Direct test for Google Maps Transit API
 */

// Test by directly calling the PHP script
$test_data = [
    'origin' => '東京都中央区日本橋本町4-14-2',  // ルフォンプログレ日本橋
    'destination' => '東京都中央区日本橋2-5-1',    // 至善館
    'arrival_time' => null  // Use default (next Tuesday 10:00)
];

echo "=== Direct Test: Simple Route ===\n";
echo "Origin: " . $test_data['origin'] . "\n";
echo "Destination: " . $test_data['destination'] . "\n\n";

// Simulate POST data
$_SERVER['REQUEST_METHOD'] = 'POST';
$json_input = json_encode($test_data);

// Include the script directly
ob_start();
$old_input = file_get_contents('php://input');
stream_wrapper_unregister("php");
stream_wrapper_register("php", "MockPhpStream");
MockPhpStream::$data = $json_input;

include __DIR__ . '/google_maps_transit.php';

$output = ob_get_clean();

// Restore original stream
stream_wrapper_restore("php");

// Parse the output
$result = json_decode($output, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    echo "Error: Invalid JSON response\n";
    echo "Raw output: " . $output . "\n";
    exit(1);
}

// Pretty print the result
echo "Result:\n";
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n\n";

// Verify structure matches Yahoo API format
if ($result['status'] === 'success') {
    echo "✅ Status: Success\n";
    echo "Total time: " . $result['route']['total_time'] . " minutes\n";
    echo "Route breakdown:\n";
    $details = $result['route']['details'];
    echo "  - Wait time: " . $details['wait_time_minutes'] . " min\n";
    echo "  - Walk to station: " . $details['walk_to_station'] . " min\n";
    echo "  - Station: " . $details['station_used'] . "\n";
    
    foreach ($details['trains'] as $i => $train) {
        echo "  - Train " . ($i + 1) . ": " . $train['line'] . " (" . $train['time'] . " min)\n";
        echo "    From: " . $train['from'] . " → To: " . $train['to'] . "\n";
        if (isset($train['transfer_after'])) {
            echo "    Transfer: " . $train['transfer_after']['time'] . " min to " . $train['transfer_after']['to_line'] . "\n";
        }
    }
    
    echo "  - Walk from station: " . $details['walk_from_station'] . " min\n";
} else {
    echo "❌ Status: Error\n";
    echo "Error message: " . ($result['message'] ?? 'Unknown error') . "\n";
    if (isset($result['traceback'])) {
        echo "Traceback:\n" . $result['traceback'] . "\n";
    }
}

// Mock stream wrapper class
class MockPhpStream {
    public static $data = '';
    private $position = 0;
    
    public function stream_open($path, $mode, $options, &$opened_path) {
        return true;
    }
    
    public function stream_read($count) {
        $ret = substr(self::$data, $this->position, $count);
        $this->position += strlen($ret);
        return $ret;
    }
    
    public function stream_eof() {
        return $this->position >= strlen(self::$data);
    }
    
    public function stream_stat() {
        return [];
    }
}
?>