<?php
/**
 * 最近のエラーチェック
 */

header('Content-Type: text/plain; charset=utf-8');

echo "🔍 json-generator.html エラー調査\n\n";

// APIサーバーの状態確認
echo "1. APIサーバー状態確認:\n";
$health = file_get_contents('http://vps_project-scraper-1:8000/health');
if ($health) {
    echo "  ✅ APIサーバーは正常に動作しています\n";
    echo "  " . $health . "\n";
} else {
    echo "  ❌ APIサーバーに接続できません\n";
}

echo "\n2. 問題のある可能性のあるルートのテスト:\n\n";

// よくエラーになりやすいパターンをテスト
$testCases = [
    [
        'name' => '長い住所',
        'origin' => '東京都千代田区神田佐久間町1-11 産報佐久間ビル',
        'destination' => '東京駅'
    ],
    [
        'name' => '曖昧な住所',
        'origin' => '千代田区',
        'destination' => '渋谷駅'
    ],
    [
        'name' => '特殊文字を含む住所',
        'origin' => '千代田区神田須田町１−２０−１',
        'destination' => '東京駅'
    ]
];

foreach ($testCases as $test) {
    echo "テスト: {$test['name']}\n";
    echo "  出発: {$test['origin']}\n";
    echo "  到着: {$test['destination']}\n";
    
    $postData = json_encode([
        'origin' => $test['origin'],
        'destination' => $test['destination']
    ]);
    
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => $postData,
            'timeout' => 20
        ]
    ]);
    
    $startTime = microtime(true);
    $result = @file_get_contents('http://vps_project-scraper-1:8000/api/transit', false, $context);
    $executionTime = microtime(true) - $startTime;
    
    if ($result === false) {
        echo "  ❌ エラー: リクエスト失敗\n";
        $error = error_get_last();
        if ($error) {
            echo "  詳細: " . $error['message'] . "\n";
        }
    } else {
        $data = json_decode($result, true);
        if ($data && isset($data['success'])) {
            if ($data['success']) {
                echo "  ✅ 成功 (実行時間: " . number_format($executionTime, 2) . "秒)\n";
            } else {
                echo "  ❌ エラー: " . ($data['error'] ?? 'Unknown error') . "\n";
            }
        } else {
            echo "  ❌ エラー: 無効なレスポンス\n";
        }
    }
    echo "\n";
    
    sleep(2); // APIへの負荷を軽減
}

echo "3. 推奨される対処法:\n";
echo "  - タイムアウトを延長する（現在30秒 → 60秒）\n";
echo "  - 住所を正規化する（全角・半角の統一など）\n";
echo "  - エラー時の再試行機能を追加\n";
echo "  - バッチ処理の間隔を延長（現在3秒 → 5秒）\n";
?>