<?php
// OpenAI APIテスト
header('Content-Type: application/json');

// .envファイル読み込み
$envPath = __DIR__ . '/../.env';
$lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$env = [];
foreach ($lines as $line) {
    if (strpos(trim($line), '#') === 0) continue;
    $parts = explode('=', $line, 2);
    if (count($parts) == 2) {
        $env[trim($parts[0])] = trim($parts[1]);
    }
}

$openaiKey = $env['OPENAI_API_KEY'] ?? '';

// OpenAI APIテスト
$url = 'https://api.openai.com/v1/chat/completions';

$data = [
    'model' => 'gpt-3.5-turbo',
    'messages' => [
        ['role' => 'user', 'content' => 'Reply with just "OK" if you are working']
    ],
    'max_tokens' => 10
];

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Authorization: Bearer ' . $openaiKey
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($response === false) {
    die(json_encode(['error' => 'Request failed']));
}

echo json_encode([
    'status' => 'success',
    'http_code' => $httpCode,
    'response' => json_decode($response, true)
]);
?>