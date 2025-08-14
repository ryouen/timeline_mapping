<?php
// generate.phpのエラー確認用テスト
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

// POSTデータ受信
$input = json_decode(file_get_contents('php://input'), true);

// デバッグ情報
echo json_encode([
    'debug' => true,
    'received_input' => $input,
    'request_method' => $_SERVER['REQUEST_METHOD'],
    'content_type' => $_SERVER['CONTENT_TYPE'] ?? 'not set',
    'post_data_length' => strlen(file_get_contents('php://input'))
]);
?>