<?php
// APIテスト用デバッグスクリプト

header('Content-Type: application/json');

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

// .envを読み込み
loadEnv(__DIR__ . '/../.env');

$GOOGLE_MAPS_API_KEY = $_ENV['GOOGLE_MAPS_API_KEY'] ?? '';

if (empty($GOOGLE_MAPS_API_KEY)) {
    echo json_encode(['error' => 'API key not found']);
    exit;
}

// テストデータ
$origin = '東京駅';
$destination = '新宿駅';
$mode = 'transit';

// 現在時刻を使用
$departureTimestamp = time();

// APIリクエストURL生成
$params = [
    'origin' => $origin,
    'destination' => $destination,
    'mode' => $mode,
    'departure_time' => $departureTimestamp,
    'language' => 'ja',
    'region' => 'jp',
    'key' => $GOOGLE_MAPS_API_KEY
];

$url = 'https://maps.googleapis.com/maps/api/directions/json?' . http_build_query($params);

// デバッグ情報
$debug = [
    'request_url' => $url,
    'departure_time' => date('Y-m-d H:i:s', $departureTimestamp),
    'params' => $params
];

// API呼び出し
$response = file_get_contents($url);
$data = json_decode($response, true);

// 結果出力
echo json_encode([
    'debug' => $debug,
    'response' => $data
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
?>