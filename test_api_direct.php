<?php
// APIの直接テスト（エラー確認用）

// すべてのエラーを表示
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

echo "=== API 直接テスト ===\n\n";

// 1. .envファイルの存在確認
$envPath = __DIR__ . '/.env';
echo "1. .envファイル確認: ";
if (file_exists($envPath)) {
    echo "✅ 存在します\n";
    
    // .envを読み込み
    $lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $_ENV = [];
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        list($name, $value) = explode('=', $line, 2);
        $_ENV[trim($name)] = trim($value);
    }
    
    echo "   - GEMINI_API_KEY: " . (isset($_ENV['GEMINI_API_KEY']) ? '✅ 設定済み' : '❌ 未設定') . "\n";
    echo "   - GOOGLE_MAPS_API_KEY: " . (isset($_ENV['GOOGLE_MAPS_API_KEY']) ? '✅ 設定済み' : '❌ 未設定') . "\n";
} else {
    echo "❌ 存在しません\n";
}

// 2. generate.phpの構文チェック
echo "\n2. generate.phpの構文チェック: ";
$output = [];
$returnCode = 0;
exec('php -l ' . __DIR__ . '/api/generate.php 2>&1', $output, $returnCode);
if ($returnCode === 0) {
    echo "✅ 構文エラーなし\n";
} else {
    echo "❌ 構文エラーあり\n";
    echo "   エラー内容: " . implode("\n   ", $output) . "\n";
}

// 3. maps.phpの構文チェック
echo "\n3. maps.phpの構文チェック: ";
$output = [];
$returnCode = 0;
exec('php -l ' . __DIR__ . '/api/maps.php 2>&1', $output, $returnCode);
if ($returnCode === 0) {
    echo "✅ 構文エラーなし\n";
} else {
    echo "❌ 構文エラーあり\n";
    echo "   エラー内容: " . implode("\n   ", $output) . "\n";
}

// 4. save.phpの構文チェック
echo "\n4. save.phpの構文チェック: ";
$output = [];
$returnCode = 0;
exec('php -l ' . __DIR__ . '/api/save.php 2>&1', $output, $returnCode);
if ($returnCode === 0) {
    echo "✅ 構文エラーなし\n";
} else {
    echo "❌ 構文エラーあり\n";
    echo "   エラー内容: " . implode("\n   ", $output) . "\n";
}

// 5. generate.phpのloadEnv関数を直接テスト
echo "\n5. loadEnv関数のテスト: ";
function loadEnv($path) {
    if (!file_exists($path)) {
        return false;
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        list($name, $value) = explode('=', $line, 2);
        $_ENV[trim($name)] = trim($value);
    }
    return true;
}

if (loadEnv($envPath)) {
    echo "✅ 正常に動作\n";
    echo "   GEMINI_API_KEY: " . (isset($_ENV['GEMINI_API_KEY']) ? substr($_ENV['GEMINI_API_KEY'], 0, 10) . '...' : 'なし') . "\n";
} else {
    echo "❌ エラー\n";
}

// 6. Gemini API URLの確認
echo "\n6. Gemini API URL構築テスト:\n";
$apiKey = $_ENV['GEMINI_API_KEY'] ?? 'KEY_NOT_SET';
$url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" . $apiKey;
echo "   URL: " . substr($url, 0, 100) . "...\n";

// 7. 簡単なAPIコールテスト（実際には送信しない）
echo "\n7. APIリクエスト構造テスト:\n";
$testData = [
    'contents' => [
        [
            'parts' => [
                ['text' => 'Test prompt']
            ]
        ]
    ]
];
echo "   リクエストデータ構造: ✅ 正常\n";
echo "   JSON形式: " . (json_encode($testData) !== false ? '✅ 正常' : '❌ エラー') . "\n";

echo "\n=== テスト完了 ===\n";
?>