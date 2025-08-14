<?php
// PDF処理用API
error_reporting(E_ALL);
ini_set('display_errors', 0);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

// 最大アップロードサイズを50MBに設定
ini_set('upload_max_filesize', '50M');
ini_set('post_max_size', '50M');
ini_set('memory_limit', '512M');

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
    
    if (empty($GEMINI_API_KEY)) {
        die(json_encode(['error' => 'API key not configured']));
    }
    
    // アクション確認
    $action = $_POST['action'] ?? '';
    if ($action !== 'parseProperties') {
        die(json_encode(['error' => 'Invalid action']));
    }
    
    // PDFファイル確認
    if (!isset($_FILES['pdf']) || $_FILES['pdf']['error'] !== UPLOAD_ERR_OK) {
        die(json_encode(['error' => 'PDF upload failed: ' . ($_FILES['pdf']['error'] ?? 'unknown error')]));
    }
    
    // ファイルサイズチェック（50MB以下に制限）
    if ($_FILES['pdf']['size'] > 50 * 1024 * 1024) {
        die(json_encode(['error' => 'PDFファイルが大きすぎます（最大50MB）']));
    }
    
    // PDFをBase64に変換
    $pdfContent = file_get_contents($_FILES['pdf']['tmp_name']);
    if ($pdfContent === false) {
        die(json_encode(['error' => 'Failed to read PDF file']));
    }
    
    $base64Pdf = base64_encode($pdfContent);
    
    // Gemini APIへのリクエスト
    $prompt = "あなたは、多様なフォーマットの不動産広告PDFから、構造化されたデータを正確に抽出することを専門とするAIアシスタントです。

添付されたPDFファイルの内容を解析し、含まれている全不動産物件の情報をJSON配列形式で返してください。

【抽出ルール】

1. name (物件名):
   - 物件の正式名称を抽出します。
   - 部屋番号（例: \"801\"）が含まれている場合は、それも必ず名称に含めてください。（例: \"テラス月島 801\"）

2. address (住所):
   - 都道府県から番地、建物名などを省略せず、記載されている完全な住所を抽出してください。
   - 物件所在地と建物名が別の場所に記載されている場合でも、それらを論理的に結合して完全な住所を生成してください。

3. rent (家賃):
   - 「賃料」と「管理費・共益費」を必ず合計し、月額の総支払額を算出してください。
   - 「礼金・敷金」は家賃に含めないでください。
   - 最終的な出力は、カンマ区切りの円表記（例: \"194,000円\"）にフォーマットしてください。

4. area (面積):
   - 「専有面積」「専有」「使用部分面積」「床面積」などの表記から面積を抽出してください。
   - 平米（㎡）表記で数値のみを抽出してください（例: \"50.5\"）。
   - 畳数しか記載がない場合は、1畳=1.62㎡として概算変換してください。
   - 単位は含めず、数値のみを文字列として返してください。

【出力に関する厳格な注意事項】
- フォーマット: 必ずJSON配列[...]形式で、説明文やマークダウン（```json```など）を一切含めず、JSONデータのみを返してください。
- 網羅性: PDF内に存在する物件は、例外なくすべて配列に含めてください（20物件以上でも必ず全件抽出）。
- 空の場合: 物件が見つからない場合は、空の配列[]を返してください。
- 制限回避: トークン制限に達しそうな場合でも、可能な限り多くの物件を含めてください。

【出力例】
[
  {
    \"name\": \"テラス月島 801\",
    \"address\": \"東京都中央区佃2丁目22-3\",
    \"rent\": \"194,000円\",
    \"area\": \"50.5\"
  },
  {
    \"name\": \"J-FIRST CHIYODA 702\",
    \"address\": \"東京都千代田区外神田2丁目8-14\",
    \"rent\": \"200,000円\",
    \"area\": \"45.2\"
  }
]";
    
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
            'temperature' => 0.3,  // より確実な出力のため低めに設定
            'maxOutputTokens' => 16384,  // 20物件以上に対応（最大値）
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
        die(json_encode(['error' => 'API request failed: ' . $error]));
    }
    
    if ($httpCode !== 200) {
        $errorResponse = json_decode($response, true);
        die(json_encode([
            'error' => 'API returned HTTP ' . $httpCode,
            'api_error' => $errorResponse
        ]));
    }
    
    $result = json_decode($response, true);
    
    // JSONデコード失敗チェック
    if ($result === null) {
        die(json_encode([
            'error' => 'Failed to decode API response',
            'raw_response' => substr($response, 0, 1000),
            'json_error' => json_last_error_msg()
        ]));
    }
    
    // デバッグモード：全レスポンスを返す
    if (isset($_POST['debug']) && $_POST['debug'] === 'true') {
        die(json_encode([
            'debug' => true,
            'full_api_response' => $result,
            'http_code' => $httpCode
        ]));
    }
    
    if (!isset($result['candidates'][0]['content']['parts'][0]['text'])) {
        // デバッグ用に詳細な情報を返す
        die(json_encode([
            'error' => 'Unexpected API response',
            'api_response_structure' => array_keys($result ?? []),
            'candidates_count' => count($result['candidates'] ?? []),
            'first_candidate' => isset($result['candidates'][0]) ? array_keys($result['candidates'][0]) : null,
            'raw_response_sample' => substr(json_encode($result), 0, 500)
        ]));
    }
    
    $responseText = $result['candidates'][0]['content']['parts'][0]['text'];
    
    // JSONの抽出を試みる（マークダウンのコードブロックなどを除去）
    if (preg_match('/```json\s*(.*?)\s*```/s', $responseText, $matches)) {
        $jsonText = $matches[1];
    } elseif (preg_match('/```\s*(.*?)\s*```/s', $responseText, $matches)) {
        $jsonText = $matches[1];
    } else {
        $jsonText = $responseText;
    }
    
    // 改行や余分な空白を除去
    $jsonText = trim($jsonText);
    
    $properties = json_decode($jsonText, true);
    
    if ($properties === null) {
        // JSONが不完全な場合の修復を試行
        $fixedJson = $jsonText;
        
        // 不完全な最後のオブジェクトを削除
        if (substr($fixedJson, -1) === '{' || substr($fixedJson, -2) === ',\n{') {
            $lastBrace = strrpos($fixedJson, '{');
            $lastComma = strrpos($fixedJson, ',');
            
            if ($lastBrace > $lastComma) {
                // 最後の不完全なオブジェクトを削除
                $fixedJson = substr($fixedJson, 0, $lastBrace);
                // 末尾のカンマを削除
                $fixedJson = rtrim($fixedJson, ",\n ");
            }
        }
        
        // 配列を閉じる
        if (substr($fixedJson, -1) !== ']') {
            $fixedJson .= '\n]';
        }
        
        // 修復されたJSONを試行
        $properties = json_decode($fixedJson, true);
        
        if ($properties === null) {
            // 修復も失敗した場合はエラーを返す
            die(json_encode([
                'error' => 'Failed to parse properties JSON',
                'raw_response' => substr($responseText, 0, 500),
                'json_error' => json_last_error_msg(),
                'cleaned_json' => substr($jsonText, 0, 500),
                'fixed_attempt' => substr($fixedJson, 0, 500)
            ]));
        }
    }
    
    // propertiesが配列でない場合（オブジェクトの場合）、配列に変換
    if (!is_array($properties)) {
        $properties = [$properties];
    }
    
    // propertiesキーを持つオブジェクトの場合
    if (isset($properties['properties'])) {
        $properties = $properties['properties'];
    }
    
    // 成功レスポンス
    echo json_encode(['properties' => $properties]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Server error',
        'message' => $e->getMessage()
    ]);
}
?>