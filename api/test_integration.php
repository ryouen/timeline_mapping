<?php
header('Content-Type: application/json; charset=utf-8');

// タイムアウトを5分に設定
set_time_limit(300);

// エラーレポート
error_reporting(E_ALL);
ini_set('display_errors', 1);

// タイムアウト箇所を特定するための詳細ログ
$debug_log = [];
$start_time = microtime(true);

function log_progress($message) {
    global $debug_log, $start_time;
    $elapsed = round(microtime(true) - $start_time, 2);
    $debug_log[] = [
        'time' => $elapsed,
        'message' => $message
    ];
    error_log("[{$elapsed}s] {$message}");
}

try {
    log_progress("リクエスト受信");
    
    // POSTデータを取得
    $input = json_decode(file_get_contents('php://input'), true);
    
    $origin = $input['origin'] ?? '東京都千代田区神田須田町1-20-1';
    $destination = $input['destination'] ?? '東京駅';
    $arrival_time = $input['arrival_time'] ?? null;
    
    log_progress("パラメータ解析完了: {$origin} → {$destination}");
    
    // Pythonスクリプトを実行（タイムアウト付き）
    $command = sprintf(
        'timeout 120 docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/test_timeout_debug.py %s %s 2>&1',
        escapeshellarg($origin),
        escapeshellarg($destination)
    );
    
    log_progress("コマンド実行開始");
    
    $output = [];
    $return_var = 0;
    exec($command, $output, $return_var);
    
    $elapsed = round(microtime(true) - $start_time, 2);
    log_progress("コマンド実行完了 (終了コード: {$return_var})");
    
    // タイムアウトチェック
    if ($return_var === 124) {
        // timeout コマンドによるタイムアウト
        echo json_encode([
            'success' => false,
            'error' => 'タイムアウト: 処理が2分以内に完了しませんでした',
            'timeout_info' => [
                'elapsed_seconds' => $elapsed,
                'debug_log' => $debug_log,
                'last_output' => array_slice($output, -10), // 最後の10行
                'timeout_location' => 'Pythonスクリプト実行中'
            ]
        ]);
        exit;
    }
    
    // 出力を結合
    $result_text = implode("\n", $output);
    
    // JSON部分を抽出
    if (preg_match('/\{.*\}/s', $result_text, $matches)) {
        $json_result = json_decode($matches[0], true);
        if ($json_result) {
            $json_result['debug_log'] = $debug_log;
            $json_result['total_time'] = $elapsed;
            echo json_encode($json_result);
        } else {
            echo json_encode([
                'success' => false,
                'error' => 'JSONパースエラー',
                'raw_output' => $result_text,
                'debug_log' => $debug_log
            ]);
        }
    } else {
        echo json_encode([
            'success' => false,
            'error' => 'JSON出力が見つかりません',
            'raw_output' => $result_text,
            'debug_log' => $debug_log,
            'return_code' => $return_var
        ]);
    }
    
} catch (Exception $e) {
    $elapsed = round(microtime(true) - $start_time, 2);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage(),
        'debug_log' => $debug_log,
        'elapsed' => $elapsed,
        'exception_location' => $e->getFile() . ':' . $e->getLine()
    ]);
}
?>