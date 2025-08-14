<?php
// 最小限のgenerate.php - 問題の切り分け用

header('Content-Type: application/json');

// 最初のテスト - 単純なレスポンス
echo json_encode(['status' => 'test', 'message' => 'Simple generate.php is working']);
exit;

// ここから下は実行されない（上でexitしているため）
// 段階的にコメントアウトを外してテスト可能
?>