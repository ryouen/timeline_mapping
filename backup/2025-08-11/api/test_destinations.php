<?php
// 目的地解析の最小テスト
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: application/json; charset=utf-8');

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

$apiKey = $_ENV['GEMINI_API_KEY'] ?? '';

// テスト用の固定プロンプト
$prompt = "以下の文章から目的地を抽出してJSONで返してください：週3回ジムに通う、毎日オフィスに出社

JSONフォーマット:
[
  {
    \"id\": \"gym\",
    \"name\": \"ジム\",
    \"category\": \"gym\",
    \"address\": \"未定\",
    \"owner\": \"you\",
    \"monthly_frequency\": 13.2,
    \"time_preference\": \"morning\"
  }
]";

$url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . $apiKey;

$data = [
    'contents' => [
        [
            'parts' => [
                ['text' => $prompt]
            ]
        ]
    ],
    'generationConfig' => [
        'temperature' => 0.7,
        'maxOutputTokens' => 2048,
        'response_mime_type' => 'application/json'
    ]
];

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($error) {
    die(json_encode(['error' => 'CURL error', 'details' => $error]));
}

if ($httpCode !== 200) {
    die(json_encode(['error' => 'HTTP error', 'code' => $httpCode, 'response' => $response]));
}

$result = json_decode($response, true);

if (isset($result['candidates'][0]['content']['parts'][0]['text'])) {
    $destinations = json_decode($result['candidates'][0]['content']['parts'][0]['text'], true);
    echo json_encode(['success' => true, 'destinations' => $destinations]);
} else {
    echo json_encode(['error' => 'Unexpected response', 'raw' => $result]);
}
?>