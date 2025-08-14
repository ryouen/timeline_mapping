<?php
/**
 * Google Maps Route Test API
 * 段階的実装のためのテスト版
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

function logMessage($message) {
    error_log("[Test Route API] " . $message);
}

try {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (!$data) {
        echo json_encode(['error' => 'Invalid JSON data'], JSON_UNESCAPED_UNICODE);
        exit;
    }
    
    $origin = $data['origin'] ?? '';
    $destination = $data['destination'] ?? '';
    
    if (!$origin || !$destination) {
        echo json_encode(['error' => 'Origin and destination are required'], JSON_UNESCAPED_UNICODE);
        exit;
    }
    
    logMessage("Testing route: {$origin} -> {$destination}");
    
    // Docker通信テスト
    $dockerTest = testDockerCommunication();
    
    if (!$dockerTest['success']) {
        echo json_encode([
            'success' => false,
            'error' => 'Docker communication failed',
            'docker_test' => $dockerTest
        ], JSON_UNESCAPED_UNICODE);
        exit;
    }
    
    // 実際のルート検索テスト
    $routeResult = callGoogleMapsScript($origin, $destination);
    
    echo json_encode([
        'success' => $routeResult['success'],
        'docker_test' => $dockerTest,
        'route_result' => $routeResult,
        'timestamp' => date('Y-m-d H:i:s')
    ], JSON_UNESCAPED_UNICODE);
    
} catch (Exception $e) {
    logMessage("Exception: " . $e->getMessage());
    echo json_encode([
        'success' => false,
        'error' => 'Internal server error',
        'details' => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}

/**
 * Docker通信テスト
 */
function testDockerCommunication() {
    // Dockerコンテナリストを確認
    $output = shell_exec('docker ps --format "table {{.Names}}" 2>&1');
    
    if ($output === null) {
        return [
            'success' => false,
            'error' => 'Docker command not available',
            'output' => null
        ];
    }
    
    // scraperコンテナが動いているかチェック
    $scraperRunning = strpos($output, 'vps_project-scraper-1') !== false;
    
    if (!$scraperRunning) {
        return [
            'success' => false,
            'error' => 'Scraper container not running',
            'docker_ps' => $output
        ];
    }
    
    // シンプルなコマンドテスト
    $testOutput = shell_exec('docker exec vps_project-scraper-1 python --version 2>&1');
    
    return [
        'success' => true,
        'scraper_running' => true,
        'python_version' => trim($testOutput),
        'docker_ps_partial' => substr($output, 0, 200)
    ];
}

/**
 * Google Maps スクリプト呼び出し
 */
function callGoogleMapsScript($origin, $destination) {
    $scriptPath = '/app/output/japandatascience.com/timeline-mapping/api/google_maps_combined.py';
    
    // タイムアウト付きでコマンド実行
    $command = sprintf(
        'timeout 30 docker exec vps_project-scraper-1 python %s %s %s 2>&1',
        escapeshellarg($scriptPath),
        escapeshellarg($origin),
        escapeshellarg($destination)
    );
    
    $startTime = microtime(true);
    $output = shell_exec($command);
    $executionTime = microtime(true) - $startTime;
    
    if ($output === null) {
        return [
            'success' => false,
            'error' => 'Script execution failed',
            'execution_time' => $executionTime
        ];
    }
    
    // JSON解析を試行
    $decoded = json_decode($output, true);
    
    if ($decoded === null) {
        return [
            'success' => false,
            'error' => 'Invalid JSON output',
            'raw_output' => substr($output, 0, 500),
            'execution_time' => $executionTime
        ];
    }
    
    return [
        'success' => true,
        'data' => $decoded,
        'execution_time' => $executionTime,
        'output_length' => strlen($output)
    ];
}

?>