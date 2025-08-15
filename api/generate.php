<?php
// /timeline-mapping/api/generate.php
// Gemini API プロキシ

// タイムゾーンを日本標準時に設定
date_default_timezone_set('Asia/Tokyo');

// エラー表示を無効化（本番環境）
ini_set('display_errors', 0);
ini_set('display_startup_errors', 0);
error_reporting(E_ALL);

// エラーハンドラを設定
set_error_handler(function($severity, $message, $file, $line) {
    throw new ErrorException($message, 0, $severity, $file, $line);
});

// UTF-8エンコーディングを設定
mb_internal_encoding('UTF-8');
mb_http_output('UTF-8');

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// OPTIONSリクエスト（CORS preflight）への対応
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// .envファイルから環境変数を読み込む
function loadEnv($path) {
    if (!file_exists($path)) {
        return false;
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        $parts = explode('=', $line, 2);
        if (count($parts) == 2) {
            $_ENV[trim($parts[0])] = trim($parts[1]);
        }
    }
    return true;
}

try {
    // .envを読み込み
    loadEnv(__DIR__ . '/../.env');

    $GEMINI_API_KEY = $_ENV['GEMINI_API_KEY'] ?? '';

    if (empty($GEMINI_API_KEY)) {
        http_response_code(500);
        echo json_encode(['error' => 'Gemini API key not configured']);
        exit;
    }

    // リクエスト処理
    $input = json_decode(file_get_contents('php://input'), true);
    $action = $input['action'] ?? '';

if ($action === 'parseDestinations') {
    // 自然言語から目的地を抽出
    $text = $input['text'] ?? '';
    
    $prompt = "あなたは、データを構造化する専門家です。

以下の##インプット情報 に記載された目的地リストを、##出力形式 に従ってJSON形式に変換してください。

【処理ルール】
1. id: 各目的地に英語の小文字とアンダースコアで構成される一意のIDを割り振る
   - 例: shizenkan_univ, axle_ochanomizu, haneda_airport
   - 日本語名は適切にローマ字化する

2. name: インプット情報にある名称をそのまま使用
   - 「ShizenkanUniv.」→「ShizenkanUniv.」
   - 「日本橋(ジム)」→「日本橋(ジム)」
   - 括弧や記号もそのまま保持

3. category: 以下のルールで分類
   - 大学・学校 → school
   - ジム・スポーツ施設 → gym
   - オフィス・会社 → office
   - 駅 → station
   - 空港 → airport
   - その他施設 → office

4. address: 住所の処理
   - 〒から始まる住所をそのまま使用（〒は削除）
   - ビル名まで含める
   - 住所がない場合（東京駅、羽田空港など）は場所の説明を使用
   - 例: \"東京駅新幹線乗り場\"、\"羽田空港第1・第2ターミナル\"

5. owner: 所有者の判定
   - デフォルトは\"you\"
   - 「パートナーは」「パートナーの」以降に記載 → \"partner\"
   - 同じ場所が両方にある場合 → \"both\"
   - 判定方法：
     * まず全体をスキャンして同じ場所を特定
     * 同じ場所（住所または名前が一致）→ \"both\"
     * パートナーセクションのみ → \"partner\"
     * それ以外 → \"you\"

6. monthly_frequency: 訪問頻度の計算
   - 「週N回」「週N回程度」 → N * 4.4
   - 「週N～M回」 → ((N+M)/2) * 4.4
   - 「月N回」「月N回程度」 → N
   - 「月N～M回」 → (N+M) / 2
   - 「月０～１回」 → 0.5

7. time_preference: すべて\"morning\"

【重要な注意事項】
- 「また、パートナーは」以降はパートナーの目的地として処理
- 同じ場所が重複する場合は1つにまとめてowner=\"both\"とする
- 住所が全角数字の場合は半角に変換

## インプット情報
$text

## 出力形式
{
  \"destinations\": [
    {
      \"id\": \"shizenkan_univ\",
      \"name\": \"ShizenkanUniv.\",
      \"category\": \"school\",
      \"address\": \"東京都中央区日本橋2丁目5-1 髙島屋三井ビルディング 17階\",
      \"owner\": \"you\",
      \"monthly_frequency\": 13.2,
      \"time_preference\": \"morning\"
    },
    {
      \"id\": \"nihonbashi_gym\",
      \"name\": \"日本橋(ジム)\",
      \"category\": \"gym\",
      \"address\": \"東京都中央区日本橋室町3丁目2-1\",
      \"owner\": \"both\",
      \"monthly_frequency\": 4.4,
      \"time_preference\": \"morning\"
    }
  ]
}

JSONのみを返してください。コメントや説明は不要です。";

    $response = callGeminiAPI($prompt, $GEMINI_API_KEY);
    echo $response;
    
} elseif ($action === 'parseProperties') {
    // PDFから物件情報を抽出
    if (!isset($_FILES['pdf'])) {
        echo json_encode(['error' => 'No PDF file uploaded']);
        exit;
    }
    
    $pdfPath = $_FILES['pdf']['tmp_name'];
    $pdfContent = file_get_contents($pdfPath);
    $base64Pdf = base64_encode($pdfContent);
    
    // Gemini Vision APIでPDFを解析
    $prompt = "あなたは不動産物件情報を正確に抽出する専門家です。

このPDFから賃貸物件の情報を抽出し、構造化されたJSONデータを生成してください。

【抽出ルール】
1. name: 物件名・マンション名を正確に抽出
   - 「ルフォンプログレ神田プレミア」のような正式名称を使用
   - 部屋番号は含めない

2. address: Google Maps APIで検索可能な完全な住所
   - 都道府県から番地まで含む完全な形式
   - 例: \"東京都千代田区神田須田町1丁目20-1\"
   - マンション名は含めない（番地まで）
   - 「ー」は半角ハイフン「-」に統一

3. rent: 月額総費用（カンマ区切り、円記号付き）
   - 家賃と管理費を合計した金額
   - 3桁ごとにカンマを入れ、最後に「円」を付ける
   - 例: 家賃28万円+管理費1.5万円の場合 → \"295,000円\"
   - 共益費、管理費も全て含めた総額

【出力形式】
{
    \"properties\": [
        {
            \"name\": \"ルフォンプログレ神田プレミア\",
            \"address\": \"東京都千代田区神田須田町1丁目20-1\",
            \"rent\": \"295,000円\"
        }
    ]
}

【注意事項】
- 複数物件がある場合は配列に全て含める
- 物件情報が明確に区別できない場合は1つの物件として扱う
- 価格が不明な場合は\"0\"を設定
- JSONのみを返す（説明文は不要）";
    
    $response = callGeminiVisionAPI($prompt, $base64Pdf, $GEMINI_API_KEY);
    echo $response;
    
} else {
    echo json_encode(['error' => 'Invalid action']);
}

// Gemini API呼び出し関数
function callGeminiAPI($prompt, $apiKey) {
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
    
    $options = [
        'http' => [
            'header' => "Content-Type: application/json\r\n",
            'method' => 'POST',
            'content' => json_encode($data),
            'timeout' => 30,  // 30秒のタイムアウト
            'ignore_errors' => true  // エラー時もレスポンスを取得
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    
    if ($result === FALSE) {
        error_log('Gemini API call failed: ' . error_get_last()['message']);
        return json_encode(['error' => 'Failed to call Gemini API - timeout or network error']);
    }
    
    $response = json_decode($result, true);
    
    // エラーレスポンスのチェック
    if (isset($response['error'])) {
        error_log('Gemini API error: ' . json_encode($response['error']));
        return json_encode(['error' => 'Gemini API error: ' . ($response['error']['message'] ?? 'Unknown error')]);
    }
    
    $text = $response['candidates'][0]['content']['parts'][0]['text'] ?? '';
    
    if (empty($text)) {
        error_log('Gemini API response empty: ' . $result);
        return json_encode(['error' => 'Empty response from Gemini API']);
    }
    
    // response_mime_type: 'application/json'を使用しているので、textは既にJSONフォーマット
    // JSONとして検証
    $jsonData = json_decode($text, true);
    if ($jsonData === null) {
        error_log('Failed to parse Gemini response as JSON: ' . $text);
        return json_encode(['error' => 'Invalid JSON response from API']);
    }
    
    // destinations配列をラップして返す
    if (isset($jsonData['destinations'])) {
        return json_encode($jsonData);
    } else if (is_array($jsonData)) {
        // 配列の場合はdestinationsとしてラップ
        return json_encode(['destinations' => $jsonData]);
    } else {
        return json_encode($jsonData);
    }
}

// Gemini Vision API呼び出し関数（PDF対応）
function callGeminiVisionAPI($prompt, $base64Content, $apiKey) {
    $url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . $apiKey;
    
    $data = [
        'contents' => [
            [
                'parts' => [
                    ['text' => $prompt],
                    [
                        'inline_data' => [
                            'mime_type' => 'application/pdf',
                            'data' => $base64Content
                        ]
                    ]
                ]
            ]
        ]
    ];
    
    $options = [
        'http' => [
            'header' => "Content-Type: application/json\r\n",
            'method' => 'POST',
            'content' => json_encode($data),
            'timeout' => 30,  // 30秒のタイムアウト
            'ignore_errors' => true  // エラー時もレスポンスを取得
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    
    if ($result === FALSE) {
        error_log('Gemini Vision API call failed: ' . error_get_last()['message']);
        return json_encode(['error' => 'Failed to call Gemini Vision API - timeout or network error']);
    }
    
    $response = json_decode($result, true);
    
    // エラーレスポンスのチェック
    if (isset($response['error'])) {
        error_log('Gemini Vision API error: ' . json_encode($response['error']));
        return json_encode(['error' => 'Gemini Vision API error: ' . ($response['error']['message'] ?? 'Unknown error')]);
    }
    
    $text = $response['candidates'][0]['content']['parts'][0]['text'] ?? '';
    
    if (empty($text)) {
        error_log('Gemini Vision API response empty: ' . $result);
        return json_encode(['error' => 'Empty response from Gemini Vision API']);
    }
    
    // JSONテキストを抽出
    preg_match('/\{.*\}/s', $text, $matches);
    if ($matches) {
        return $matches[0];
    }
    
    // JSON抽出失敗時はテキスト全体を返す（LLMがJSONのみ返している場合）
    $jsonTest = json_decode($text, true);
    if ($jsonTest !== null) {
        return $text;
    }
    
    error_log('Failed to parse Gemini Vision response: ' . $text);
    return json_encode(['error' => 'Failed to parse response']);
}

} catch (Exception $e) {
    // エラーをJSONで返す
    http_response_code(500);
    echo json_encode([
        'error' => 'Server error occurred',
        'message' => $e->getMessage(),
        'file' => basename($e->getFile()),
        'line' => $e->getLine()
    ]);
    exit;
}
?>