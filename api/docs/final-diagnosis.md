# 最終診断：データ保存問題の完全分析

## 1. 確認した事実

### ✅ 動作している部分
- PHPは正常に動作（Dockerコンテナ内でroot権限）
- ファイルパスは正しい
- 書き込み権限あり
- save.phpへのアクセス可能

### ❌ 問題の証拠
- properties.jsonが空のデータで上書きされた（8月13日11:11）
- 送信されたデータ：
  ```json
  {
    "destinations": {"destinations": []},
    "properties": {"properties": []}
  }
  ```

## 2. 根本原因

### 🚨 最も可能性が高い原因：タイミングの問題

#### シナリオ
1. ユーザーがjson-generator.htmlを開く
2. **loadFromLocalStorage()が実行される**
3. LocalStorageから23物件のデータが読み込まれる
4. Step 3で「以前の検索結果を復元」ボタンが表示される
5. ユーザーがボタンをクリック
6. **しかし、この時点でグローバル変数が空になっている**

#### なぜ空になるのか？

可能性1: **resetAll()が呼ばれた**
```javascript
function resetAll() {
    if (confirm('すべてのデータをリセットしてよろしいですか？')) {
        destinations = [];  // ← ここで空になる
        properties = [];    // ← ここで空になる
        // ...
    }
}
```

可能性2: **ページの再読み込み**
- 部分的な再読み込みでグローバル変数がリセット
- しかしLocalStorageは残っている

可能性3: **validateCurrentStepのバグ**
- Step間の移動でデータが消える可能性

## 3. デバッグ手順

### Step 1: ブラウザコンソールで確認
```javascript
// 現在のグローバル変数を確認
console.log('destinations:', destinations);
console.log('properties:', properties);

// LocalStorageを確認
const saved = JSON.parse(localStorage.getItem('timeline_data'));
console.log('LocalStorage data:', saved);
```

### Step 2: 手動でデータを復元
```javascript
// LocalStorageから手動で復元
const saved = JSON.parse(localStorage.getItem('timeline_data'));
destinations = saved.destinations;
properties = saved.properties;
console.log('Restored:', destinations.length, properties.length);
```

### Step 3: 手動で保存を実行
```javascript
// 手動でsaveJSONFiles()を実行
await saveJSONFiles();
```

## 4. 推奨される修正

### 修正1: restorePreviousSearchの改善
```javascript
async function restorePreviousSearch() {
    const saved = localStorage.getItem('timeline_data');
    if (!saved) {
        alert('保存されたデータが見つかりません');
        return;
    }
    
    try {
        const data = JSON.parse(saved);
        
        // データの検証
        if (!data || !data.destinations || !data.properties ||
            data.destinations.length === 0 || data.properties.length === 0) {
            throw new Error('データが不正または空です');
        }
        
        // 明示的にグローバル変数に設定
        window.destinations = data.destinations;
        window.properties = data.properties;
        
        // 確認
        if (destinations.length === 0 || properties.length === 0) {
            throw new Error('データの設定に失敗しました');
        }
        
        // 続行...
    } catch (error) {
        alert(`エラー: ${error.message}`);
    }
}
```

### 修正2: loadFromLocalStorageの問題
現在のloadFromLocalStorage()は単にデータを読み込むだけで、
restorePreviousSearch()とは独立して動作しています。
これが混乱の原因かもしれません。

## 5. テストログファイル

以下のファイルを確認してください：
```bash
ls -la /var/www/japandatascience.com/timeline-mapping/data/save-test-*.txt
```

これらのファイルに、実際に送信されたデータが記録されています。

## 6. 結論

問題は**save.phpの動作**ではなく、**JavaScriptのデータ管理**にあります。
特に、グローバル変数の`destinations`と`properties`が、
復元ボタンをクリックする時点で空になっている可能性が高いです。

## 7. 次のアクション

1. ブラウザの開発者ツールでコンソールログを確認
2. 上記のデバッグ手順を実行
3. 必要に応じてJavaScriptの修正を適用