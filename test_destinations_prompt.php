<?php
// 目的地解析プロンプトのテスト

$testInput = "ShizenkanUniv.　〒103-0027 東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階　週３回程度

日本橋(ジム)　〒103-0022 東京都中央区日本橋室町３丁目２−１　週１回程度

axle御茶ノ水　〒101-0052 東京都千代田区神田小川町３丁目２８−５　月１～２回

Yawara　〒150-0001 東京都渋谷区神宮前１丁目８−１０ Ｔｈｅ Ｉｃｅ Ｃｕｂｅｓ　月４回程度

東京駅　東京駅新幹線乗り場　月２～３回

羽田空港　第1・第2ターミナル　月０～１回



また、パートナーは

神谷町オフィス　〒105-0001 東京都港区虎ノ門４丁目２−６ 第二扇屋ビル 1F　週１～２回程度

早稲田大学　〒169-0051 東京都新宿区西早稲田１丁目６　週１～２回程度

日本橋　ジム　〒103-0022 東京都中央区日本橋室町３丁目２−１　週１回程度

東京駅　新幹線出張　月０～１回";

// 現在のプロンプトをテスト
$prompt = "あなたは、データを構造化する専門家です。

以下の##インプット情報 に記載された目的地リストを、##出力形式 に従ってJSON形式に変換してください。

【処理ルール】
- id: 各目的地に、英語の小文字とアンダースコアで構成される一意のIDを割り振ってください。
- name: インプット情報にある名称を正式名称として使用してください。
- category: 目的地の種類を、school, gym, office, station, airport のいずれかに分類してください。
- address: インプット情報にある住所を正確に抽出してください。
- owner: 目的地が誰のものかを示します。「私の」「私とパートナーの」といった文脈からyou, partner, bothのいずれかを判断してください。
- monthly_frequency: 1ヶ月あたりの平均訪問回数を計算してください。計算式は以下の通りです。
  - 「週N回」の場合: N * 4.4
  - 「月N～M回」の場合: (N+M) / 2
- time_preference: 現時点では、すべての目的地に\"morning\"を割り当ててください。

## インプット情報
$testInput

## 出力形式（例）
{
  \"destinations\": [
    {
      \"id\": \"shizenkan_univ\",
      \"name\": \"Shizenkan University\",
      \"category\": \"school\",
      \"address\": \"東京都中央区日本橋2-5-1 髙島屋三井ビルディング 17階\",
      \"owner\": \"you\",
      \"monthly_frequency\": 13.2,
      \"time_preference\": \"morning\"
    }
  ]
}

JSONのみを返してください。コメントや説明は不要です。";

echo "=== テストインプット ===\n";
echo $testInput;
echo "\n\n=== 期待される出力 ===\n";
echo "- ShizenkanUniv: owner=you, frequency=13.2 (週3*4.4)\n";
echo "- 日本橋(ジム): owner=both, frequency=4.4 (週1*4.4) ※パートナーも利用\n";
echo "- axle御茶ノ水: owner=you, frequency=1.5 (月1-2の平均)\n";
echo "- Yawara: owner=you, frequency=4\n";
echo "- 東京駅: owner=both, frequency=2.5 (月2-3の平均) ※パートナーも利用\n";
echo "- 羽田空港: owner=you, frequency=0.5 (月0-1の平均)\n";
echo "- 神谷町オフィス: owner=partner, frequency=6.6 (週1.5*4.4)\n";
echo "- 早稲田大学: owner=partner, frequency=6.6\n";
echo "\n\n=== プロンプトの問題点 ===\n";
echo "1. 「パートナーは」という文脈の理解が不明確\n";
echo "2. 同じ場所(日本橋ジム、東京駅)が両方にある場合の処理\n";
echo "3. 住所がない場合(東京駅、羽田空港)の処理\n";
echo "4. 月0-1回のような低頻度の処理\n";
?>