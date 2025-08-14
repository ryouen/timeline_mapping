# Step by Step データフロー分析

## 1. LocalStorageのデータ構造

### 保存されているキー
- `timeline_data` - destinations と properties を含むオブジェクト
- `timeline_destinations` - destinations のみ（未使用？）
- `timeline_properties` - properties のみ（未使用？）

### データ形式
```javascript
{
  destinations: [
    {
      id: "waseda_university",
      name: "早稲田大学",
      category: "school",
      address: "東京都新宿区西早稲田1-6-1",
      owner: "partner",
      monthly_frequency: 4.4,
      time_preference: "morning"
    }
  ],
  properties: [
    {
      name: "ルフォンプログレ神田プレミア",
      address: "千代田区神田須田町1-20-1",
      rent: "280,000",
      routes: [...],
      total_monthly_travel_time: 220,
      total_monthly_walk_time: 70.4,
      stations: [...]
    }
  ]
}
```

## 2. 復元時のデータフロー

### Step 1: LocalStorage読み込み（restorePreviousSearch関数）
```javascript
const saved = localStorage.getItem('timeline_data');
const data = JSON.parse(saved);
destinations = data.destinations || [];
properties = data.properties || [];
```

### Step 2: saveJSONFiles()の呼び出し
```javascript
const destinationsData = { destinations: destinations };
const propertiesData = { properties: properties };

await fetch('/timeline-mapping/api/save.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        destinations: destinationsData,
        properties: propertiesData
    })
});
```

### Step 3: save.php の処理

## 3. 確認すべきポイント

### ❓ 疑問点1: データ形式の不一致？
saveJSONFiles()で送信されるデータ：
```json
{
  destinations: { destinations: [...] },  // 二重構造
  properties: { properties: [...] }       // 二重構造
}
```

save.phpが期待するデータ：
```json
{
  destinations: { destinations: [...] },
  properties: { properties: [...] }
}
```

### ❓ 疑問点2: ファイルの実際の内容
- 現在のproperties.jsonは18物件
- 復元しようとしているのは23物件
- ファイルが実際に更新されているか？

### ❓ 疑問点3: 権限の問題
```
-rwxr-xr-x 1 www-data www-data properties.json
```
- www-dataが所有
- PHPはどのユーザーで実行される？
- 書き込み権限はある？