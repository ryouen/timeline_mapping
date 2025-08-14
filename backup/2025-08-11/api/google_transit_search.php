<?php
/**
 * Google Maps Transit Search API
 * 独立したGoogle Maps経路検索サービス
 */

// --- ヘッダー設定 ---
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// --- 入力処理 ---
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $origin = $_GET['origin'] ?? '';
    $destination = $_GET['destination'] ?? '';
    $arrival_time = $_GET['arrival_time'] ?? null;
} else {
    $json_input = file_get_contents('php://input');
    $input_data = json_decode($json_input, true);
    
    $origin = $input_data['origin'] ?? '';
    $destination = $input_data['destination'] ?? '';
    $arrival_time = $input_data['arrival_time'] ?? null;
}

// 必須パラメータチェック
if (empty($origin) || empty($destination)) {
    http_response_code(400);
    echo json_encode([
        'status' => 'error',
        'message' => 'origin と destination は必須です'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Docker経由でGoogle Mapsスクレイピングを実行
function searchGoogleMapsTransit($origin, $destination, $arrival_time = null) {
    // コマンド構築
    $cmd_parts = [
        'docker',
        'exec',
        'vps_project-scraper-1',
        'python',
        '/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py',
        escapeshellarg($origin),
        escapeshellarg($destination)
    ];
    
    // 到着時刻の処理
    if ($arrival_time === null) {
        // デフォルトは翌火曜日の朝10時に到着
        $dt = new DateTime();
        $days_until_tuesday = (2 - $dt->format('w') + 7) % 7;
        if ($days_until_tuesday == 0) {
            $days_until_tuesday = 7;
        }
        $dt->modify("+{$days_until_tuesday} days");
        $dt->setTime(10, 0, 0);
        $cmd_parts[] = escapeshellarg($dt->format('Y-m-d H:i:s'));
    } else if ($arrival_time === 'now') {
        $cmd_parts[] = escapeshellarg('now');
    } else {
        try {
            $dt = new DateTime($arrival_time);
            $cmd_parts[] = escapeshellarg($dt->format('Y-m-d H:i:s'));
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => '到着時刻の形式が正しくありません'
            ];
        }
    }
    
    // コマンド実行
    $command = implode(' ', $cmd_parts) . ' 2>&1';
    $output = shell_exec($command);
    
    if ($output === null) {
        return [
            'status' => 'error',
            'message' => 'スクレイピングサービスの実行に失敗しました'
        ];
    }
    
    // 結果をパース
    $result = json_decode($output, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log('Google Maps Transit search JSON parse error: ' . substr($output, 0, 500));
        return [
            'status' => 'error',
            'message' => 'スクレイピング結果の解析に失敗しました'
        ];
    }
    
    return $result;
}

// メイン処理
$result = searchGoogleMapsTransit($origin, $destination, $arrival_time);

// 結果を整形して返す
if ($result['status'] === 'success') {
    // 成功時は追加情報を付与
    $result['service'] = 'google_maps_scraping';
    $result['search_params'] = [
        'origin' => $origin,
        'destination' => $destination,
        'arrival_time' => $arrival_time
    ];
    
    http_response_code(200);
} else {
    http_response_code(500);
}

echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>