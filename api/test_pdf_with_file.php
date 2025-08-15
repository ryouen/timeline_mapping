<?php
// PDFファイルのテストスクリプト
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "=== PDF File Test ===\n\n";

// .env読み込み
$envPath = __DIR__ . '/../.env';
if (!file_exists($envPath)) {
    die("ERROR: .env file not found at: $envPath\n");
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
    die("ERROR: API key not configured\n");
}

echo "API Key found: " . substr($GEMINI_API_KEY, 0, 10) . "...\n\n";

// PDFファイルを読み込み
$pdfPath = __DIR__ . '/../data/archive/pdf_files/0801_bukken.pdf';
if (!file_exists($pdfPath)) {
    die("ERROR: PDF file not found at: $pdfPath\n");
}

$pdfContent = file_get_contents($pdfPath);
$base64Pdf = base64_encode($pdfContent);

echo "PDF loaded: " . number_format(strlen($pdfContent)) . " bytes\n";
echo "Base64 size: " . number_format(strlen($base64Pdf)) . " bytes\n\n";

// Gemini APIに送信
$url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . $GEMINI_API_KEY;

$prompt = "Extract property information from this PDF and return as JSON array with: name, address, rent (including management fee), area. Return ONLY the JSON array, no markdown or explanation.";

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

echo "Sending request to Gemini API...\n";

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

echo "HTTP Code: $httpCode\n\n";

if ($error) {
    echo "CURL Error: $error\n";
    exit(1);
}

if ($httpCode !== 200) {
    echo "API Error Response:\n";
    $errorData = json_decode($response, true);
    print_r($errorData);
    exit(1);
}

$result = json_decode($response, true);

if ($result === null) {
    echo "Failed to decode JSON response\n";
    echo "JSON Error: " . json_last_error_msg() . "\n";
    exit(1);
}

if (isset($result['candidates'][0]['content']['parts'][0]['text'])) {
    $responseText = $result['candidates'][0]['content']['parts'][0]['text'];
    
    echo "Raw response text:\n";
    echo substr($responseText, 0, 1000) . "\n\n";
    
    // JSONの抽出
    if (preg_match('/```json\s*(.*?)\s*```/s', $responseText, $matches)) {
        $jsonText = $matches[1];
    } elseif (preg_match('/```\s*(.*?)\s*```/s', $responseText, $matches)) {
        $jsonText = $matches[1];
    } else {
        $jsonText = $responseText;
    }
    
    $jsonText = trim($jsonText);
    
    echo "Extracted JSON:\n";
    echo substr($jsonText, 0, 1000) . "\n\n";
    
    $properties = json_decode($jsonText, true);
    
    if ($properties === null) {
        echo "Failed to parse properties JSON\n";
        echo "JSON Error: " . json_last_error_msg() . "\n";
    } else {
        echo "Successfully parsed " . count($properties) . " properties:\n\n";
        foreach ($properties as $i => $prop) {
            echo "Property " . ($i + 1) . ":\n";
            echo "  Name: " . ($prop['name'] ?? 'N/A') . "\n";
            echo "  Address: " . ($prop['address'] ?? 'N/A') . "\n";
            echo "  Rent: " . ($prop['rent'] ?? 'N/A') . "\n";
            echo "  Area: " . ($prop['area'] ?? 'N/A') . "\n\n";
        }
    }
} else {
    echo "Unexpected response structure:\n";
    print_r(array_keys($result));
}