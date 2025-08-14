<?php
// テキストベースの物件解析テスト
error_reporting(E_ALL);
ini_set('display_errors', 0);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

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
    $text = $input['text'] ?? '';
    
    if (empty($text)) {
        die(json_encode(['error' => 'No text provided']));
    }
    
    // プロンプト
    $prompt = "以下のテキストから物件情報を抽出してJSON配列で返してください。

テキスト:
" . $text . "

出力形式（JSON配列のみ返す）:
[
  {
    \"name\": \"物件名\",
    \"address\": \"住所（Google Maps検索可能な形式）\",
    \"rent\": \"家賃（例: 200,000円）\"
  }
]

注意:
- 物件が複数ある場合は配列に複数要素を含める
- 物件情報が見つからない場合は空配列[]を返す
- JSONのみ返す（説明文不要）";
    
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
            'temperature' => 0.3,
            'maxOutputTokens' => 1024,
            'response_mime_type' => 'application/json'
        ]
    ];
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_TIMEOUT, 15);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode !== 200) {
        die(json_encode(['error' => 'API returned HTTP ' . $httpCode]));
    }
    
    $result = json_decode($response, true);
    
    if (!isset($result['candidates'][0]['content']['parts'][0]['text'])) {
        die(json_encode(['error' => 'Unexpected API response structure']));
    }
    
    $responseText = $result['candidates'][0]['content']['parts'][0]['text'];
    $properties = json_decode($responseText, true);
    
    if ($properties === null) {
        die(json_encode([
            'error' => 'Failed to parse JSON',
            'raw_response' => substr($responseText, 0, 500),
            'json_error' => json_last_error_msg()
        ]));
    }
    
    // 成功
    echo json_encode(['properties' => $properties]);
    
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
}
?>