<?php
// /timeline-mapping/api/save.php
// JSONファイルを/data/フォルダに保存

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// データディレクトリのパス
$dataDir = __DIR__ . '/../data/';

// ディレクトリが存在しない場合は作成
if (!file_exists($dataDir)) {
    mkdir($dataDir, 0755, true);
}

// POSTデータを取得
$input = json_decode(file_get_contents('php://input'), true);

if (!$input || !isset($input['destinations']) || !isset($input['properties'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid data']);
    exit;
}

try {
    // destinations.jsonを保存
    $destinationsFile = $dataDir . 'destinations.json';
    file_put_contents($destinationsFile, json_encode($input['destinations'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    // properties.jsonを保存
    $propertiesFile = $dataDir . 'properties.json';
    file_put_contents($propertiesFile, json_encode($input['properties'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    // タイムスタンプ付きバックアップも作成
    $timestamp = date('Y-m-d_H-i-s');
    $backupDir = $dataDir . 'backup/';
    
    if (!file_exists($backupDir)) {
        mkdir($backupDir, 0755, true);
    }
    
    file_put_contents($backupDir . "destinations_{$timestamp}.json", 
        json_encode($input['destinations'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    file_put_contents($backupDir . "properties_{$timestamp}.json", 
        json_encode($input['properties'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    echo json_encode([
        'success' => true,
        'message' => 'Files saved successfully',
        'files' => [
            'destinations' => $destinationsFile,
            'properties' => $propertiesFile
        ]
    ]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save files: ' . $e->getMessage()]);
}
?>