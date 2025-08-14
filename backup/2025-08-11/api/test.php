<?php
// 最小限のテストAPI

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// 基本的な動作確認
echo json_encode([
    'status' => 'ok',
    'message' => 'API is working',
    'php_version' => phpversion(),
    'timestamp' => date('Y-m-d H:i:s'),
    'request_method' => $_SERVER['REQUEST_METHOD'],
    'post_data' => file_get_contents('php://input')
]);
?>