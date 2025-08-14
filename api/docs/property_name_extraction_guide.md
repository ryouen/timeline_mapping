# 物件名の正しい抽出方法ガイド

## 問題の概要

properties.jsonファイルでは、物件名と駅名の両方が「name」というキーを使用しているため、単純に「name」キーを検索すると誤った数がカウントされてしまいます。

### 実際の数値
- **物件数**: 18件
- **駅名の数**: 45件  
- **合計nameキー数**: 63件

## JSONの構造

```json
{
  "properties": [
    {
      "name": "ルフォンプログレ神田プレミア",  // ← これが物件名
      "address": "千代田区神田須田町1-20-1",
      "rent": "280,000",
      "stations": [
        {
          "name": "神田(東京都)",  // ← これは駅名
          "distance": "100m"
        }
      ],
      "routes": [...]
    }
  ]
}
```

## 正しい物件名の抽出方法

### 1. Pythonでの抽出方法

```python
import json

# ファイルの読み込み
with open('properties.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 物件名のみを抽出
property_names = [prop['name'] for prop in data['properties']]
print(f"物件数: {len(property_names)}")
```

### 2. bashでjqを使用する場合

```bash
# 物件数をカウント
jq '.properties | length' properties.json

# 物件名のリストを取得
jq '.properties[].name' properties.json
```

### 3. JavaScriptでの抽出方法

```javascript
// JSONデータを読み込んだ後
const propertyNames = data.properties.map(prop => prop.name);
console.log(`物件数: ${propertyNames.length}`);
```

## 間違った抽出方法の例

### ❌ 悪い例: すべてのnameキーを検索

```python
# これは駅名も含んでしまう
def count_all_names(data):
    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "name":
                count += 1
            count += count_all_names(value)
    elif isinstance(data, list):
        for item in data:
            count += count_all_names(item)
    return count
```

## 物件一覧（2025年8月12日現在）

1. ルフォンプログレ神田プレミア
2. テラス月島 801
3. J-FIRST CHIYODA 702
4. ザ・パークハビオ日本橋箱崎町 204
5. DaiDo ANNEX 402
6. アーバンレジデンス神田富山町 302
7. グレイスリヴィエール東京八丁堀 702
8. クレスト五番町 801
9. ゼンパレス日本橋 702
10. コルティーレ日本橋人形町 501
11. シティインデックス千代田秋葉原 701
12. アーバンレジデンス神田富山町 701
13. レジディア月島III 1201
14. セレサ日本橋堀留町 605
15. La Belle 三越前 0702
16. アイル秋葉原EAST 307
17. リベルテ月島 604
18. シティハウス東京八重洲通り 1502

## 注意事項

- 物件を追加・削除する際は、必ず`properties`配列の直下に追加してください
- 駅情報は`stations`配列内に格納してください
- 新しい物件を追加する際は、既存の構造を厳密に守ってください

## 関連ファイル

- `/var/www/japandatascience.com/timeline-mapping/data/properties.json` - 物件データの実体
- `/home/ubuntu/count_properties.py` - 物件数カウント用スクリプト
- `/home/ubuntu/analyze_name_keys.py` - nameキー分析用スクリプト