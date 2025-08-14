<?php
// エラー表示を抑制
error_reporting(0);
ini_set('display_errors', 0);

// デバッグログを追加
$debugLog = __DIR__ . '/save-debug-' . date('Y-m-d') . '.log';
file_put_contents($debugLog, "\n[" . date('Y-m-d H:i:s') . "] Request received\n", FILE_APPEND);

// JSONヘッダーを最初に送信
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

try {
    // データディレクトリのパス
    $dataDir = __DIR__ . '/../data/';
    
    // ディレクトリが存在しない場合は作成
    if (!file_exists($dataDir)) {
        if (!mkdir($dataDir, 0755, true)) {
            throw new Exception('Failed to create data directory');
        }
    }
    
    // POSTデータを取得
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input) {
        throw new Exception('Invalid JSON data');
    }
    
    // 目的地のみ保存モード
    if (isset($input['saveDestinationsOnly']) && $input['saveDestinationsOnly'] === true) {
        if (!isset($input['destinations'])) {
            throw new Exception('Destinations data is required');
        }
        
        // destinations.jsonを保存
        $destinationsFile = $dataDir . 'destinations.json';
        $destResult = file_put_contents($destinationsFile, json_encode($input['destinations'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        
        if ($destResult === false) {
            throw new Exception('Failed to save destinations.json');
        }
        
        // 成功レスポンス
        echo json_encode([
            'success' => true,
            'message' => 'Destinations saved successfully',
            'file' => $destinationsFile
        ]);
        exit;
    }
    
    // 物件基本情報のみ保存モード
    if (isset($input['savePropertiesBaseOnly']) && $input['savePropertiesBaseOnly'] === true) {
        if (!isset($input['propertiesBase'])) {
            throw new Exception('Properties base data is required');
        }
        
        // properties_base.jsonを保存
        $propertiesBaseFile = $dataDir . 'properties_base.json';
        $baseResult = file_put_contents($propertiesBaseFile, json_encode($input['propertiesBase'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        
        if ($baseResult === false) {
            throw new Exception('Failed to save properties_base.json');
        }
        
        // タイムスタンプ付きバックアップも作成
        $timestamp = date('Y-m-d_H-i-s');
        $backupDir = $dataDir . 'backup/';
        
        if (!file_exists($backupDir)) {
            @mkdir($backupDir, 0755, true);
        }
        
        @file_put_contents($backupDir . "properties_base_{$timestamp}.json", 
            json_encode($input['propertiesBase'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        
        // 成功レスポンス
        echo json_encode([
            'success' => true,
            'message' => 'Properties base saved successfully',
            'file' => $propertiesBaseFile
        ]);
        exit;
    }
    
    // 通常の保存モード（両方のファイルを保存）
    if (!isset($input['destinations']) || !isset($input['properties'])) {
        file_put_contents($debugLog, "[" . date('Y-m-d H:i:s') . "] ERROR: Missing destinations or properties\n", FILE_APPEND);
        throw new Exception('Invalid data format');
    }
    
    file_put_contents($debugLog, "[" . date('Y-m-d H:i:s') . "] Normal save mode: " . count($input['properties']['properties'] ?? []) . " properties\n", FILE_APPEND);
    
    // destinations.jsonを保存
    $destinationsFile = $dataDir . 'destinations.json';
    $destResult = file_put_contents($destinationsFile, json_encode($input['destinations'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    if ($destResult === false) {
        throw new Exception('Failed to save destinations.json');
    }
    
    // properties.jsonを保存
    $propertiesFile = $dataDir . 'properties.json';
    $propResult = file_put_contents($propertiesFile, json_encode($input['properties'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    if ($propResult === false) {
        throw new Exception('Failed to save properties.json');
    }
    
    // タイムスタンプ付きバックアップも作成
    $timestamp = date('Y-m-d_H-i-s');
    $backupDir = $dataDir . 'backup/';
    
    if (!file_exists($backupDir)) {
        if (!mkdir($backupDir, 0755, true)) {
            // バックアップ失敗は警告のみ
        }
    }
    
    // バックアップ（エラーは無視）
    @file_put_contents($backupDir . "destinations_{$timestamp}.json", 
        json_encode($input['destinations'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    @file_put_contents($backupDir . "properties_{$timestamp}.json", 
        json_encode($input['properties'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    // 成功レスポンス
    $response = [
        'success' => true,
        'message' => 'Files saved successfully',
        'files' => [
            'destinations' => $destinationsFile,
            'properties' => $propertiesFile
        ],
        'timestamp' => date('Y-m-d H:i:s')
    ];
    
    file_put_contents($debugLog, "[" . date('Y-m-d H:i:s') . "] SUCCESS: Files saved\n", FILE_APPEND);
    echo json_encode($response);
    
} catch (Exception $e) {
    // エラーレスポンス
    file_put_contents($debugLog, "[" . date('Y-m-d H:i:s') . "] EXCEPTION: " . $e->getMessage() . "\n", FILE_APPEND);
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>