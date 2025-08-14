# 根本原因分析：データが保存されない問題

## 発見した事実

### 1. 権限とファイルパス ✅
- PHPはDockerコンテナ内でrootとして実行
- ファイルパスは正しい（/usr/local/apache2/htdocs/...）
- 書き込み権限あり（テストファイル作成成功）

### 2. save.phpの動作 ✅
- save-debug.phpは正常に動作
- POSTリクエストを受信
- ファイルへの書き込み成功

### 3. 🚨 問題の核心：空のデータ
```json
{
    "destinations": {
        "destinations": []
    },
    "properties": {
        "properties": []
    }
}
```

## 原因の推測

### 可能性1: グローバル変数の問題
restorePreviousSearch()で：
```javascript
destinations = data.destinations || [];
properties = data.properties || [];
```

しかし、saveJSONFiles()を呼ぶ時点で空になっている？

### 可能性2: スコープの問題
関数内でグローバル変数が正しく更新されていない？

### 可能性3: 非同期処理のタイミング
データの設定とsaveJSONFiles()の間で何かが起きている？

## 確認すべきこと

### 1. restorePreviousSearch内でのデータ確認
```javascript
console.log('Before save - destinations:', destinations);
console.log('Before save - properties:', properties);
```

### 2. saveJSONFiles内でのデータ確認
```javascript
console.log('In saveJSONFiles - destinations:', destinations);
console.log('In saveJSONFiles - properties:', properties);
```

### 3. ブラウザコンソールでの直接確認
```javascript
// グローバル変数を確認
console.log('Global destinations:', destinations);
console.log('Global properties:', properties);
```

## 修正案

### 案1: データの明示的な確認
```javascript
async function restorePreviousSearch() {
    const saved = localStorage.getItem('timeline_data');
    if (!saved) {
        alert('保存されたデータが見つかりません');
        return;
    }
    
    showProcessing('データを復元中...');
    
    try {
        const data = JSON.parse(saved);
        
        // データの存在を確認
        if (!data.destinations || !data.properties) {
            throw new Error('データ形式が不正です');
        }
        
        // グローバル変数に設定
        destinations = data.destinations;
        properties = data.properties;
        
        // 設定後の確認
        console.log('Restored destinations:', destinations.length);
        console.log('Restored properties:', properties.length);
        
        if (destinations.length === 0 || properties.length === 0) {
            throw new Error('データが空です');
        }
        
        // 以下続く...
    }
}
```

### 案2: saveJSONFiles()の修正
```javascript
async function saveJSONFiles() {
    // データの存在を確認
    if (!destinations || destinations.length === 0) {
        throw new Error('目的地データがありません');
    }
    if (!properties || properties.length === 0) {
        throw new Error('物件データがありません');
    }
    
    // 以下続く...
}
```

## 結論

save.phpは正常に動作していますが、**空のデータが送信されている**ことが問題です。
グローバル変数の管理に問題がある可能性が高いです。