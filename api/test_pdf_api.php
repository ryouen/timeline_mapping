<?php
// PDF API テストスクリプト
error_reporting(E_ALL);
ini_set('display_errors', 1);

// .env読み込み
$envPath = __DIR__ . '/../.env';
$lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
foreach ($lines as $line) {
    if (strpos(trim($line), '#') === 0) continue;
    $parts = explode('=', $line, 2);
    if (count($parts) == 2) {
        $_ENV[trim($parts[0])] = trim($parts[1]);
    }
}

$GEMINI_API_KEY = $_ENV['GEMINI_API_KEY'] ?? '';

if (empty($GEMINI_API_KEY)) {
    die("ERROR: API key not configured\n");
}

echo "Testing Gemini API connection...\n";
echo "API Key: " . substr($GEMINI_API_KEY, 0, 10) . "...\n\n";

// シンプルなテスト
$url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=" . $GEMINI_API_KEY;

$data = [
    'contents' => [
        [
            'parts' => [
                ['text' => 'Return a simple JSON array with 2 test properties in this exact format: [{"name": "Test Property 1", "address": "Tokyo", "rent": "100,000円", "area": "50"}, {"name": "Test Property 2", "address": "Osaka", "rent": "80,000円", "area": "40"}]']
            ]
        ]
    ],
    'generationConfig' => [
        'temperature' => 0.1,
        'maxOutputTokens' => 1024,
        'response_mime_type' => 'application/json'
    ]
];

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_VERBOSE, true);

echo "Sending request to Gemini API...\n";

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

echo "HTTP Code: $httpCode\n";

if ($error) {
    echo "CURL Error: $error\n";
    exit(1);
}

if ($httpCode !== 200) {
    echo "API Error Response:\n";
    echo $response . "\n";
    exit(1);
}

echo "Raw Response:\n";
echo substr($response, 0, 500) . "\n\n";

$result = json_decode($response, true);

if ($result === null) {
    echo "Failed to decode JSON response\n";
    echo "JSON Error: " . json_last_error_msg() . "\n";
    exit(1);
}

if (isset($result['candidates'][0]['content']['parts'][0]['text'])) {
    $text = $result['candidates'][0]['content']['parts'][0]['text'];
    echo "Extracted text:\n$text\n\n";
    
    // JSONとしてパース
    $properties = json_decode($text, true);
    if ($properties) {
        echo "Successfully parsed properties:\n";
        print_r($properties);
    } else {
        echo "Failed to parse properties JSON\n";
    }
} else {
    echo "Unexpected response structure:\n";
    print_r($result);
}