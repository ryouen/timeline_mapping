<?php
/**
 * 府中オフィスルートの修正スクリプト
 * Golden Fileのデータで間違ったルートを上書きする
 */

// JSONファイルを読み込み
$propertiesPath = __DIR__ . '/../data/properties.json';
$goldenPath = __DIR__ . '/../data/golden_routes.json';

if (!file_exists($propertiesPath) || !file_exists($goldenPath)) {
    die("必要なファイルが見つかりません\n");
}

$properties = json_decode(file_get_contents($propertiesPath), true);
$golden = json_decode(file_get_contents($goldenPath), true);

if (!$properties || !$golden) {
    die("JSONの読み込みに失敗しました\n");
}

// バックアップを作成
$backupPath = __DIR__ . '/../data/backup/properties_' . date('Ymd_His') . '_before_fix.json';
if (!is_dir(dirname($backupPath))) {
    mkdir(dirname($backupPath), 0755, true);
}
file_put_contents($backupPath, json_encode($properties, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
echo "バックアップを作成しました: $backupPath\n";

// 府中オフィスのルートを修正
$fixCount = 0;
$correctRoute = $golden['routes']['fuchu_office']['correct_route'];

foreach ($properties['properties'] as &$property) {
    if (isset($property['routes']) && is_array($property['routes'])) {
        foreach ($property['routes'] as &$route) {
            if ($route['destination'] === 'fuchu_office') {
                // 現在の間違ったルートを記録
                $oldRoute = $route;
                
                // 正しいルートで上書き
                $route['total_time'] = $correctRoute['total_time'];
                $route['details'] = $correctRoute['details'];
                $route['total_walk_time'] = $correctRoute['total_walk_time'];
                
                $fixCount++;
                echo "修正: {$property['name']} → 府中オフィス\n";
                echo "  旧: {$oldRoute['total_time']}分 ({$oldRoute['details']['trains'][0]['from']} → {$oldRoute['details']['trains'][0]['to']})\n";
                echo "  新: {$route['total_time']}分 ({$route['details']['trains'][0]['from']} → {$route['details']['trains'][0]['to']})\n\n";
            }
        }
    }
}

// 修正したデータを保存
if ($fixCount > 0) {
    file_put_contents($propertiesPath, json_encode($properties, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    echo "\n合計 {$fixCount} 件のルートを修正しました。\n";
    echo "properties.json を更新しました。\n";
} else {
    echo "\n修正対象のルートが見つかりませんでした。\n";
}