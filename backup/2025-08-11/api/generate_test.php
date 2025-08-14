<?php
// 完全に作り直したシンプル版
error_reporting(E_ALL);
ini_set('display_errors', 0);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

try {
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
    
    // リクエスト取得
    $input = json_decode(file_get_contents('php://input'), true);
    $action = $input['action'] ?? '';
    
    if ($action !== 'parseDestinations') {
        die(json_encode(['error' => 'Invalid action: ' . $action]));
    }
    
    $text = $input['text'] ?? '';
    if (empty($text)) {
        die(json_encode(['error' => 'No text provided']));
    }
    
    // シンプルなプロンプト
    $prompt = "次のテキストから目的地を抽出し、JSON配列で返してください。週N回は月N*4.4回に変換してください。\n\nテキスト: " . $text . "\n\n必須フィールド:\n- id: 英語の識別子\n- name: 目的地名\n- category: gym/office/school/station/airport\n- address: 住所（不明なら空文字）\n- owner: you/partner/both\n- monthly_frequency: 月の訪問回数\n- time_preference: morning\n\n形式:\n[{\"id\":\"string\",\"name\":\"string\",\"category\":\"gym/office/school\",\"address\":\"string\",\"owner\":\"you\",\"monthly_frequency\":number,\"time_preference\":\"morning\"}]";
    
    $url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . $GEMINI_API_KEY;
    
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
        die(json_encode(['error' => 'CURL error: ' . $error]));
    }
    
    if ($httpCode !== 200) {
        die(json_encode(['error' => 'HTTP ' . $httpCode, 'response' => json_decode($response, true)]));
    }
    
    $result = json_decode($response, true);
    
    if (!isset($result['candidates'][0]['content']['parts'][0]['text'])) {
        die(json_encode(['error' => 'Unexpected API response structure', 'raw' => $result]));
    }
    
    $destinations = json_decode($result['candidates'][0]['content']['parts'][0]['text'], true);
    
    if ($destinations === null) {
        die(json_encode(['error' => 'Failed to parse destinations JSON']));
    }
    
    // 成功レスポンス
    echo json_encode(['destinations' => $destinations]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Exception occurred',
        'message' => $e->getMessage()
    ]);
}
?>