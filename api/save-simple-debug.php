<?php
// デバッグ版 save-simple.php
// エラー表示を有効化
error_reporting(E_ALL);
ini_set('display_errors', 1);

// ログファイルのパス
$logFile = __DIR__ . '/save-simple-debug.log';

// デバッグログ関数
function debugLog($message) {
    global $logFile;
    $timestamp = date('Y-m-d H:i:s');
    $logMessage = "[{$timestamp}] {$message}\n";
    file_put_contents($logFile, $logMessage, FILE_APPEND);
}

// JSONヘッダー
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

debugLog("=== Save request received ===");

try {
    // データディレクトリのパス
    $dataDir = __DIR__ . '/../data/';
    debugLog("Data directory: {$dataDir}");
    
    // ディレクトリが存在しない場合は作成
    if (!file_exists($dataDir)) {
        debugLog("Creating data directory...");
        if (!mkdir($dataDir, 0755, true)) {
            throw new Exception('Failed to create data directory');
        }
    }
    
    // POSTデータを取得
    $rawInput = file_get_contents('php://input');
    debugLog("Raw input length: " . strlen($rawInput));
    
    $input = json_decode($rawInput, true);
    
    if (!$input) {
        debugLog("JSON decode failed. Raw input (first 500 chars): " . substr($rawInput, 0, 500));
        throw new Exception('Invalid JSON data');
    }
    
    debugLog("Received data keys: " . implode(', ', array_keys($input)));
    
    // 通常の保存モード（両方のファイルを保存）
    if (isset($input['destinations']) && isset($input['properties'])) {
        debugLog("Normal save mode detected");
        
        // destinationsのデータ構造を確認
        if (isset($input['destinations']['destinations'])) {
            debugLog("Destinations count: " . count($input['destinations']['destinations']));
        } else {
            debugLog("Warning: destinations.destinations not found");
        }
        
        // propertiesのデータ構造を確認
        if (isset($input['properties']['properties'])) {
            debugLog("Properties count: " . count($input['properties']['properties']));
        } else {
            debugLog("Warning: properties.properties not found");
        }
        
        // destinations.jsonを保存
        $destinationsFile = $dataDir . 'destinations.json';
        $destContent = json_encode($input['destinations'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        debugLog("Saving destinations.json, size: " . strlen($destContent) . " bytes");
        
        $destResult = file_put_contents($destinationsFile, $destContent);
        
        if ($destResult === false) {
            debugLog("Failed to save destinations.json");
            throw new Exception('Failed to save destinations.json');
        }
        debugLog("Destinations saved successfully: {$destResult} bytes written");
        
        // properties.jsonを保存
        $propertiesFile = $dataDir . 'properties.json';
        $propContent = json_encode($input['properties'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        debugLog("Saving properties.json, size: " . strlen($propContent) . " bytes");
        
        $propResult = file_put_contents($propertiesFile, $propContent);
        
        if ($propResult === false) {
            debugLog("Failed to save properties.json");
            throw new Exception('Failed to save properties.json');
        }
        debugLog("Properties saved successfully: {$propResult} bytes written");
        
        // タイムスタンプ付きバックアップも作成
        $timestamp = date('Y-m-d_H-i-s');
        $backupDir = $dataDir . 'backup/';
        
        if (!file_exists($backupDir)) {
            @mkdir($backupDir, 0755, true);
        }
        
        // バックアップ
        $backupDest = $backupDir . "destinations_{$timestamp}.json";
        $backupProp = $backupDir . "properties_{$timestamp}.json";
        
        @file_put_contents($backupDest, $destContent);
        @file_put_contents($backupProp, $propContent);
        
        debugLog("Backups created: {$backupDest}, {$backupProp}");
        
        // 成功レスポンス
        $response = [
            'success' => true,
            'message' => 'Files saved successfully',
            'files' => [
                'destinations' => $destinationsFile,
                'properties' => $propertiesFile
            ],
            'timestamp' => $timestamp
        ];
        
        debugLog("Success response: " . json_encode($response));
        echo json_encode($response);
    } else {
        debugLog("Invalid data format - missing destinations or properties");
        throw new Exception('Invalid data format');
    }
    
} catch (Exception $e) {
    debugLog("Exception caught: " . $e->getMessage());
    
    // エラーレスポンス
    http_response_code(500);
    $errorResponse = [
        'success' => false,
        'error' => $e->getMessage()
    ];
    
    debugLog("Error response: " . json_encode($errorResponse));
    echo json_encode($errorResponse);
}

debugLog("=== Request processing completed ===\n");
?>