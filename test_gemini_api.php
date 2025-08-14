<?php
// Gemini API テストスクリプト

// テストデータ
$testInput = "私の会社は東京都千代田区神田須田町1-20にあります。週3回通っています。
パートナーと一緒に通っているジムは東京都中央区日本橋室町3-2-1にあります。月8回程度です。";

// cURLでAPIをテスト
$ch = curl_init('http://localhost/timeline-mapping/api/generate.php');

$data = json_encode([
    'action' => 'parseDestinations',
    'text' => $testInput
]);

curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "HTTP Status Code: $httpCode\n";
echo "Response:\n";
echo $response;
echo "\n\nDecoded JSON:\n";
print_r(json_decode($response, true));
?>