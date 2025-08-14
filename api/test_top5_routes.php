<?php
header('Content-Type: application/json; charset=utf-8');
$origin = "東京都千代田区神田須田町1-20-1";
$destinations = [
    ["id" => "shizenkan_university", "name" => "Shizenkan University", "address" => "東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階"],
    ["id" => "tokyo_american_club", "name" => "東京アメリカンクラブ", "address" => "東京都中央区日本橋室町３丁目２−１"],
    ["id" => "kamiyacho_ee_office", "name" => "神谷町(EE)", "address" => "東京都港区虎ノ門４丁目２−６ 第二扇屋ビル 1F"]
];
$results = ["origin" => $origin, "routes" => []];
foreach ($destinations as $dest) {
    $results["routes"][] = ["destination" => $dest["name"], "test" => "実行してください"];
}
echo json_encode($results, JSON_UNESCAPED_UNICODE);
