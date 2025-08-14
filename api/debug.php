<?php
// Debug API - Step by step check

// Step 1: Basic output
echo "Step 1: Basic output OK\n";

// Step 2: Headers
header('Content-Type: text/plain; charset=utf-8');
echo "Step 2: Headers set OK\n";

// Step 3: Check .env file
$envPath = __DIR__ . '/../.env';
if (file_exists($envPath)) {
    echo "Step 3: .env file exists\n";
} else {
    echo "Step 3: .env file NOT found at: $envPath\n";
}

// Step 4: Read .env test
$lines = @file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
if ($lines) {
    echo "Step 4: .env file read successfully (" . count($lines) . " lines)\n";
    
    // Check API key exists (show first 10 chars only)
    foreach ($lines as $line) {
        if (strpos($line, 'GEMINI_API_KEY') === 0) {
            $parts = explode('=', $line, 2);
            if (count($parts) == 2) {
                echo "Step 5: GEMINI_API_KEY found: " . substr($parts[1], 0, 10) . "...\n";
            }
        }
    }
} else {
    echo "Step 4: Failed to read .env file\n";
}

// Step 6: Check POST data
$input = file_get_contents('php://input');
echo "Step 6: POST data length: " . strlen($input) . "\n";

// Step 7: JSON output test
echo "Step 7: Testing JSON output...\n";
$testArray = ['test' => 'success', 'time' => date('Y-m-d H:i:s')];
echo json_encode($testArray) . "\n";

echo "\nAll steps completed!\n";
?>