<?php
// PDFアップロードのデバッグ
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: text/plain; charset=utf-8');

echo "=== PDF API Debug Test ===\n\n";

// generate_pdf.phpに直接アクセスした時のレスポンスを確認
$url = 'https://japandatascience.com/timeline-mapping/api/generate_pdf.php';

// テストリクエスト（PDFなし）
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, ['action' => 'parseProperties']);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "HTTP Status: $httpCode\n";
echo "Response (first 500 chars):\n";
echo substr($response, 0, 500) . "\n\n";

// HTMLが返されているかチェック
if (strpos($response, '<') === 0) {
    echo "ERROR: HTML response detected instead of JSON!\n";
    echo "This usually means there's a PHP error or warning being output.\n\n";
    
    // エラーメッセージを抽出
    if (preg_match('/<b>(Warning|Error|Notice):<\/b>(.+?)<br/i', $response, $matches)) {
        echo "PHP Error found: " . strip_tags($matches[0]) . "\n";
    }
} else {
    // JSONとしてパース
    $data = json_decode($response, true);
    if ($data === null) {
        echo "ERROR: Invalid JSON response\n";
        echo "JSON Error: " . json_last_error_msg() . "\n";
    } else {
        echo "Valid JSON response:\n";
        print_r($data);
    }
}