<?php
// Yahoo Transit API デバッグ版
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$json_input = file_get_contents('php://input');
$input_data = json_decode($json_input, true);

$origin = $input_data['origin'] ?? 'EMPTY';
$destination = $input_data['destination'] ?? 'EMPTY';

// URLパラメータを生成
$dt = new DateTime();
$params = [
    'from' => $origin,
    'to' => $destination,
    'y' => $dt->format('Y'),
    'm' => $dt->format('m'),
    'd' => $dt->format('d'),
    'hh' => $dt->format('H'),
    'm1' => floor($dt->format('i') / 10),
    'm2' => $dt->format('i') % 10,
    'type' => 1,
    'ticket' => 'ic',
];

$url = 'https://transit.yahoo.co.jp/search/result?' . http_build_query($params);

// デバッグ情報を返す
$debug_info = [
    'raw_input' => $json_input,
    'parsed_input' => $input_data,
    'origin_used' => $origin,
    'destination_used' => $destination,
    'generated_url' => $url,
    'url_params' => $params,
    'timestamp' => date('Y-m-d H:i:s')
];

echo json_encode($debug_info, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
?>