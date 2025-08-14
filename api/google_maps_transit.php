<?php
/**
 * Google Maps Transit Scraping API
 * PHP wrapper for Python scraping script
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

$origin = $input_data['origin'];
$destination = $input_data['destination'];
$arrival_time = $input_data['arrival_time'] ?? null;

// Docker経由でPythonスクリプトを実行
$cmd_parts = [
    'docker',
    'exec',
    'vps_project-scraper-1',
    'python',
    '/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py',
    escapeshellarg($origin),
    escapeshellarg($destination)
];

// 到着時刻の処理（Yahoo Transit APIと同じロジック）
if ($arrival_time === null) {
    // デフォルトは翌火曜日の朝10時に到着
    $dt = new DateTime();
    $days_until_tuesday = (2 - $dt->format('w') + 7) % 7;
    if ($days_until_tuesday == 0) {
        $days_until_tuesday = 7; // 今日が火曜日なら翌週の火曜日
    }
    $dt->modify("+{$days_until_tuesday} days");
    $dt->setTime(10, 0, 0); // 朝10時に設定
    $cmd_parts[] = escapeshellarg($dt->format('Y-m-d H:i:s'));
} else if ($arrival_time === 'now') {
    $cmd_parts[] = escapeshellarg('now');
} else {
    // カスタム到着時刻
    try {
        $dt = new DateTime($arrival_time);
        $cmd_parts[] = escapeshellarg($dt->format('Y-m-d H:i:s'));
    } catch (Exception $e) {
        http_response_code(400);
        echo json_encode([
            'status' => 'error',
            'message' => 'Invalid arrival_time format'
        ]);
        exit;
    }
}

// コマンドを実行（エラー出力は別途処理）
$command = implode(' ', $cmd_parts);
$descriptorspec = array(
    0 => array("pipe", "r"),  // stdin
    1 => array("pipe", "w"),  // stdout
    2 => array("pipe", "w")   // stderr
);

$process = proc_open($command, $descriptorspec, $pipes);

if (!is_resource($process)) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Failed to execute Python script'
    ]);
    exit;
}

// 標準出力と標準エラー出力を取得
$output = stream_get_contents($pipes[1]);
$error_output = stream_get_contents($pipes[2]);

// パイプを閉じる
fclose($pipes[0]);
fclose($pipes[1]);
fclose($pipes[2]);

// プロセスを閉じる
$return_value = proc_close($process);

// エラー出力がある場合はログに記録
if (!empty($error_output)) {
    error_log('Google Maps Transit API stderr: ' . $error_output);
}

// 出力が空の場合
if (empty($output)) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'No output from scraping service',
        'debug' => !empty($error_output) ? 'Check server logs for details' : null
    ]);
    exit;
}

// JSONデコードを試みる
$result = json_decode($output, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    // JSONパースエラーの場合、デバッグ情報は最小限に
    http_response_code(500);
    
    // ログファイルにエラー詳細を記録
    error_log('Google Maps Transit API JSON parse error: ' . substr($output, 0, 500));
    
    echo json_encode([
        'status' => 'error',
        'message' => 'Invalid response from scraping service',
        'json_error' => json_last_error_msg()
    ]);
    exit;
}

// 正常なレスポンスを返す
if ($result['status'] === 'success') {
    http_response_code(200);
} else {
    http_response_code(500);
}

echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>