<?php
// デバッグ版generate.php
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// OPTIONSリクエスト（CORS preflight）への対応
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// デバッグ: リクエスト情報
$debugInfo = [
    'method' => $_SERVER['REQUEST_METHOD'],
    'content_type' => $_SERVER['CONTENT_TYPE'] ?? 'not set',
    'raw_input' => file_get_contents('php://input')
];

// POSTデータを取得
$input = json_decode(file_get_contents('php://input'), true);

// .env読み込み
$envPath = __DIR__ . '/../.env';
if (!file_exists($envPath)) {
    die(json_encode(['error' => '.env file not found', 'debug' => $debugInfo]));
}

$lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
foreach ($lines as $line) {
    if (strpos(trim($line), '#') === 0) continue;
    $parts = explode('=', $line, 2);
    if (count($parts) == 2) {
        $_ENV[trim($parts[0])] = trim($parts[1]);
    }
}

$GEMINI_API_KEY = $_ENV['GEMINI_API_KEY'] ?? '';

if (empty($GEMINI_API_KEY)) {
    die(json_encode(['error' => 'GEMINI_API_KEY not found', 'debug' => $debugInfo]));
}

// action確認
$action = $input['action'] ?? '';

echo json_encode([
    'debug_mode' => true,
    'received_action' => $action,
    'received_input' => $input,
    'api_key_length' => strlen($GEMINI_API_KEY),
    'expected_action' => 'parseDestinations',
    'action_match' => ($action === 'parseDestinations')
]);
?>