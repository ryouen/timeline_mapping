<?php
// 最小限のテストAPI
header('Content-Type: application/json');

// .envファイルの確認
$envPath = __DIR__ . '/../.env';
if (!file_exists($envPath)) {
    die(json_encode(['error' => '.env file not found']));
}

// .env読み込み
$lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$env = [];
foreach ($lines as $line) {
    if (strpos(trim($line), '#') === 0) continue;
    $parts = explode('=', $line, 2);
    if (count($parts) == 2) {
        $env[trim($parts[0])] = trim($parts[1]);
    }
}

// APIキーの確認
$geminiKey = 'AIzaSyAoAcBgr0yOCzyQ_Z-7YuJJSdjaEP-IsVk'; // 直接新しいキーを使用
if (empty($geminiKey)) {
    die(json_encode(['error' => 'GEMINI_API_KEY not found']));
}

// 簡単なテストリクエスト
$url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' . $geminiKey;

$data = [
    'contents' => [
        [
            'parts' => [
                ['text' => 'Reply with just "OK" if you are working']
            ]
        ]
    ]
];

$options = [
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($data),
        'timeout' => 10
    ]
];

$context = stream_context_create($options);
$response = @file_get_contents($url, false, $context);

if ($response === false) {
    $error = error_get_last();
    die(json_encode([
        'error' => 'API request failed',
        'details' => $error['message'] ?? 'Unknown error',
        'url' => substr($url, 0, 50) . '...',
        'key_length' => strlen($geminiKey)
    ]));
}

$result = json_decode($response, true);
echo json_encode([
    'status' => 'success',
    'api_response' => $result
]);
?>