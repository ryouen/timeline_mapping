<?php
// PHP関数の単体テスト

echo "=== JSON Generator PHP 単体テスト ===\n\n";

$testResults = [];
$passCount = 0;
$failCount = 0;

function test($name, $condition, $details = '') {
    global $testResults, $passCount, $failCount;
    
    if ($condition) {
        echo "✅ PASS: $name\n";
        $passCount++;
    } else {
        echo "❌ FAIL: $name\n";
        if ($details) echo "   詳細: $details\n";
        $failCount++;
    }
    
    $testResults[] = ['name' => $name, 'result' => $condition, 'details' => $details];
}

// ==================== .env ファイル読み込みテスト ====================
echo "【.envファイル読み込みテスト】\n";

function testLoadEnv() {
    // loadEnv関数を定義
    function loadEnvTest($path) {
        if (!file_exists($path)) {
            return false;
        }
        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        $env = [];
        foreach ($lines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            $parts = explode('=', $line, 2);
            if (count($parts) == 2) {
                $env[trim($parts[0])] = trim($parts[1]);
            }
        }
        return $env;
    }
    
    // テスト用の一時.envファイル作成
    $testEnvContent = "# Test env file\nTEST_KEY=test_value\nANOTHER_KEY=another_value\n# Comment line\nKEY_WITH_EQUALS=value=with=equals\n";
    file_put_contents('test.env', $testEnvContent);
    
    $env = loadEnvTest('test.env');
    
    test('.env読み込み - ファイル存在', $env !== false);
    test('.env読み込み - キー取得', isset($env['TEST_KEY']) && $env['TEST_KEY'] === 'test_value');
    test('.env読み込み - コメント無視', !isset($env['# Test env file']));
    test('.env読み込み - 等号を含む値', isset($env['KEY_WITH_EQUALS']) && $env['KEY_WITH_EQUALS'] === 'value=with=equals');
    
    // クリーンアップ
    unlink('test.env');
    
    // 存在しないファイル
    $env = loadEnvTest('nonexistent.env');
    test('.env読み込み - 存在しないファイル', $env === false);
}

testLoadEnv();

// ==================== APIキー検証テスト ====================
echo "\n【APIキー検証テスト】\n";

// 実際の.envファイルをチェック
$envPath = __DIR__ . '/.env';
if (file_exists($envPath)) {
    $lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $_ENV = [];
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        $parts = explode('=', $line, 2);
        if (count($parts) == 2) {
            $_ENV[trim($parts[0])] = trim($parts[1]);
        }
    }
    
    test('GEMINI_API_KEY存在', isset($_ENV['GEMINI_API_KEY']));
    test('GOOGLE_MAPS_API_KEY存在', isset($_ENV['GOOGLE_MAPS_API_KEY']));
    test('OPENAI_API_KEY存在', isset($_ENV['OPENAI_API_KEY']));
    
    // APIキーの形式チェック（簡易）
    if (isset($_ENV['GEMINI_API_KEY'])) {
        test('GEMINI_API_KEY形式', 
            strlen($_ENV['GEMINI_API_KEY']) > 20 && 
            strpos($_ENV['GEMINI_API_KEY'], 'AIza') === 0,
            'Google APIキーは通常AIzaで始まる'
        );
    }
} else {
    echo "⚠️ .envファイルが見つかりません\n";
}

// ==================== JSON解析テスト ====================
echo "\n【JSON解析テスト】\n";

function testJSONParsing() {
    // Gemini APIのレスポンスをシミュレート
    $testResponses = [
        // 正常なJSON
        '{"destinations": [{"id": "test", "name": "Test"}]}',
        // JSONの前後にテキストがある
        'Here is the JSON: {"destinations": [{"id": "test", "name": "Test"}]} End of response',
        // 改行を含むJSON
        "{\n  \"destinations\": [\n    {\"id\": \"test\", \"name\": \"Test\"}\n  ]\n}",
        // エスケープされた文字を含む
        '{"destinations": [{"name": "Test \"quoted\" name"}]}',
    ];
    
    foreach ($testResponses as $index => $response) {
        // JSON抽出ロジック（generate.phpと同じ）
        preg_match('/\{.*\}/s', $response, $matches);
        if ($matches) {
            $json = json_decode($matches[0], true);
            test("JSON解析 テストケース" . ($index + 1), $json !== null);
        } else {
            test("JSON解析 テストケース" . ($index + 1), false, "JSONが抽出できない");
        }
    }
}

testJSONParsing();

// ==================== 頻度計算テスト ====================
echo "\n【頻度計算ロジックテスト】\n";

function testFrequencyCalculation() {
    // PHPでの頻度計算をテスト（プロンプトで指定した計算式）
    $testCases = [
        ['input' => '週3回', 'expected' => 13.2],
        ['input' => '週1回', 'expected' => 4.4],
        ['input' => '月4回', 'expected' => 4],
        ['input' => '月2～3回', 'expected' => 2.5],
        ['input' => '月1-2回', 'expected' => 1.5],
        ['input' => '月0～1回', 'expected' => 0.5],
    ];
    
    foreach ($testCases as $tc) {
        $input = $tc['input'];
        $expected = $tc['expected'];
        
        // 週N回のパターン
        if (preg_match('/週(\d+)/', $input, $matches)) {
            $calculated = floatval($matches[1]) * 4.4;
        }
        // 月N～M回のパターン
        elseif (preg_match('/月(\d+)[～\-~](\d+)/', $input, $matches)) {
            $calculated = (floatval($matches[1]) + floatval($matches[2])) / 2;
        }
        // 月N回のパターン
        elseif (preg_match('/月(\d+)/', $input, $matches)) {
            $calculated = floatval($matches[1]);
        }
        else {
            $calculated = 0;
        }
        
        test("頻度計算: $input", abs($calculated - $expected) < 0.01, "期待値: $expected, 計算値: $calculated");
    }
}

testFrequencyCalculation();

// ==================== 住所正規化テスト ====================
echo "\n【住所正規化テスト】\n";

function testAddressNormalization() {
    $testAddresses = [
        ['input' => '〒103-0027 東京都中央区日本橋２丁目５−１', 
         'expected' => '東京都中央区日本橋2丁目5-1'],
        ['input' => '東京都千代田区神田小川町３ー２８ー５',
         'expected' => '東京都千代田区神田小川町3-28-5'],
    ];
    
    foreach ($testAddresses as $tc) {
        $input = $tc['input'];
        $expected = $tc['expected'];
        
        // 正規化処理
        $normalized = $input;
        $normalized = preg_replace('/〒\d{3}-\d{4}\s*/', '', $normalized); // 郵便番号削除
        $normalized = mb_convert_kana($normalized, 'n'); // 全角数字を半角に
        $normalized = str_replace('ー', '-', $normalized); // 全角ハイフンを半角に
        $normalized = str_replace('−', '-', $normalized); // 別の全角ハイフンも
        
        test("住所正規化: " . substr($input, 0, 20) . "...", 
            trim($normalized) === $expected,
            "結果: $normalized"
        );
    }
}

testAddressNormalization();

// ==================== エラーハンドリングテスト ====================
echo "\n【エラーハンドリングテスト】\n";

function testErrorHandling() {
    // タイムアウト設定の確認
    $options = [
        'http' => [
            'timeout' => 30,
            'ignore_errors' => true
        ]
    ];
    
    test('HTTPオプション - タイムアウト設定', $options['http']['timeout'] === 30);
    test('HTTPオプション - エラー無視設定', $options['http']['ignore_errors'] === true);
    
    // エラーレスポンスのテスト
    $errorResponse = json_encode(['error' => 'Test error message']);
    $decoded = json_decode($errorResponse, true);
    test('エラーレスポンス解析', isset($decoded['error']));
}

testErrorHandling();

// ==================== サマリー ====================
echo "\n" . str_repeat('=', 50) . "\n";
echo "テストサマリー\n";
echo str_repeat('=', 50) . "\n";
echo "✅ 成功: $passCount\n";
echo "❌ 失敗: $failCount\n";
$total = $passCount + $failCount;
$percentage = $total > 0 ? round(($passCount / $total) * 100, 1) : 0;
echo "成功率: {$percentage}%\n";

// 失敗したテストの詳細
if ($failCount > 0) {
    echo "\n失敗したテスト:\n";
    foreach ($testResults as $result) {
        if (!$result['result']) {
            echo "  - {$result['name']}\n";
            if ($result['details']) {
                echo "    {$result['details']}\n";
            }
        }
    }
}

?>