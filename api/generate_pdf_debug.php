<?php
// PDF処理用API - デバッグ版
error_reporting(E_ALL);
ini_set('display_errors', 1);

// エラーハンドラを設定してJSONで返す
function error_handler($errno, $errstr, $errfile, $errline) {
    header('Content-Type: application/json; charset=utf-8');
    die(json_encode([
        'error' => 'PHP Error',
        'details' => [
            'message' => $errstr,
            'file' => basename($errfile),
            'line' => $errline
        ]
    ]));
}
set_error_handler('error_handler');

// 致命的エラーもキャッチ
register_shutdown_function(function() {
    $error = error_get_last();
    if ($error && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR])) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode([
            'error' => 'Fatal Error',
            'details' => [
                'message' => $error['message'],
                'file' => basename($error['file']),
                'line' => $error['line']
            ]
        ]);
    }
});

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

try {
    // .env読み込み
    $envPath = __DIR__ . '/../.env';
    if (!file_exists($envPath)) {
        throw new Exception('.env file not found');
    }
    
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
        die(json_encode(['error' => 'API key not configured']));
    }
    
    // アクション確認
    $action = $_POST['action'] ?? '';
    if ($action !== 'parseProperties') {
        die(json_encode(['error' => 'Invalid action', 'received' => $action]));
    }
    
    // PDFファイル確認
    if (!isset($_FILES['pdf']) || $_FILES['pdf']['error'] !== UPLOAD_ERR_OK) {
        $uploadError = $_FILES['pdf']['error'] ?? 'no file';
        $errorMessages = [
            UPLOAD_ERR_INI_SIZE => 'File exceeds upload_max_filesize',
            UPLOAD_ERR_FORM_SIZE => 'File exceeds MAX_FILE_SIZE',
            UPLOAD_ERR_PARTIAL => 'File was only partially uploaded',
            UPLOAD_ERR_NO_FILE => 'No file was uploaded',
            UPLOAD_ERR_NO_TMP_DIR => 'Missing temporary folder',
            UPLOAD_ERR_CANT_WRITE => 'Failed to write file to disk',
            UPLOAD_ERR_EXTENSION => 'File upload stopped by extension'
        ];
        $errorMsg = $errorMessages[$uploadError] ?? "Unknown error: $uploadError";
        die(json_encode(['error' => 'PDF upload failed', 'details' => $errorMsg]));
    }
    
    // ファイルサイズチェック
    if ($_FILES['pdf']['size'] > 50 * 1024 * 1024) {
        die(json_encode(['error' => 'PDFファイルが大きすぎます（最大50MB）']));
    }
    
    // PDFをBase64に変換
    $pdfContent = file_get_contents($_FILES['pdf']['tmp_name']);
    if ($pdfContent === false) {
        die(json_encode(['error' => 'Failed to read PDF file']));
    }
    
    $base64Pdf = base64_encode($pdfContent);
    
    // プロンプト（シンプル版）
    $prompt = "Extract property information from this PDF and return as JSON array with: name, address, rent (including management fee), area. Return ONLY the JSON array, no markdown or explanation.";
    
    $url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . $GEMINI_API_KEY;
    
    $data = [
        'contents' => [
            [
                'parts' => [
                    ['text' => $prompt],
                    [
                        'inline_data' => [
                            'mime_type' => 'application/pdf',
                            'data' => $base64Pdf
                        ]
                    ]
                ]
            ]
        ],
        'generationConfig' => [
            'temperature' => 0.3,
            'maxOutputTokens' => 16384
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
        die(json_encode(['error' => 'API request failed', 'details' => $error]));
    }
    
    if ($httpCode !== 200) {
        $errorResponse = json_decode($response, true);
        die(json_encode([
            'error' => 'API returned HTTP ' . $httpCode,
            'api_error' => $errorResponse
        ]));
    }
    
    $result = json_decode($response, true);
    
    if ($result === null) {
        die(json_encode([
            'error' => 'Failed to decode API response',
            'raw_response' => substr($response, 0, 1000),
            'json_error' => json_last_error_msg()
        ]));
    }
    
    if (!isset($result['candidates'][0]['content']['parts'][0]['text'])) {
        die(json_encode([
            'error' => 'Unexpected API response structure',
            'response_keys' => array_keys($result)
        ]));
    }
    
    $responseText = $result['candidates'][0]['content']['parts'][0]['text'];
    
    // JSONの抽出
    if (preg_match('/```json\s*(.*?)\s*```/s', $responseText, $matches)) {
        $jsonText = $matches[1];
    } elseif (preg_match('/```\s*(.*?)\s*```/s', $responseText, $matches)) {
        $jsonText = $matches[1];
    } else {
        $jsonText = $responseText;
    }
    
    $jsonText = trim($jsonText);
    
    // JSONパース
    $properties = json_decode($jsonText, true);
    
    if ($properties === null) {
        die(json_encode([
            'error' => 'Failed to parse properties JSON',
            'raw_text' => substr($jsonText, 0, 500),
            'json_error' => json_last_error_msg()
        ]));
    }
    
    // 成功レスポンス
    echo json_encode([
        'success' => true,
        'properties' => $properties,
        'count' => count($properties)
    ]);
    
} catch (Exception $e) {
    echo json_encode([
        'error' => 'Exception',
        'message' => $e->getMessage(),
        'line' => $e->getLine()
    ]);
}