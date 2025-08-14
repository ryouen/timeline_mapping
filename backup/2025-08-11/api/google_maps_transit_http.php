<?php
/**
 * Google Maps Transit API - HTTP版
 * Scraperコンテナで動作するHTTP APIサービスを呼び出す
 */

// --- ヘッダー設定 ---
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// --- メイン処理 ---
$json_input = file_get_contents('php://input');
$input_data = json_decode($json_input, true);

if (empty($input_data['origin']) || empty($input_data['destination'])) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'origin and destination are required.']);
    exit;
}

// 到着時刻の処理（Yahoo Transit APIと同じロジック）
$arrival_time = $input_data['arrival_time'] ?? null;
if ($arrival_time === null) {
    // デフォルトは翌火曜日の朝10時に到着
    $dt = new DateTime();
    $days_until_tuesday = (2 - $dt->format('w') + 7) % 7;
    if ($days_until_tuesday == 0) {
        $days_until_tuesday = 7;
    }
    $dt->modify("+{$days_until_tuesday} days");
    $dt->setTime(10, 0, 0);
    $arrival_time = $dt->format('Y-m-d H:i:s');
}

// HTTP APIリクエストデータ
$api_data = [
    'origin' => $input_data['origin'],
    'destination' => $input_data['destination'],
    'arrival_time' => $arrival_time
];

// Scraperコンテナ内のAPIサーバーを呼び出す
$api_url = 'http://scraper:8000/api/transit';

// cURLでAPIを呼び出す
$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($api_data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Accept: application/json'
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 60); // 60秒タイムアウト

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

// エラーハンドリング
if ($response === false) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Failed to connect to scraping service',
        'error_detail' => $curl_error
    ]);
    exit;
}

// APIレスポンスの処理
$result = json_decode($response, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Invalid response from scraping service'
    ]);
    exit;
}

// HTTPステータスコードに基づいてレスポンスを返す
if ($http_code === 200) {
    http_response_code(200);
} else {
    http_response_code($http_code);
}

echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>