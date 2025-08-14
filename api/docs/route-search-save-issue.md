# ルート検索結果が保存されない問題の分析

## 問題の原因

### 1. 重複したstartRouteSearch関数

json-generator.htmlに**2つのstartRouteSearch関数**が定義されています：

- **1026行目**: 古い実装（saveJSONFiles()を呼ぶ）
- **1390行目**: 新しい実装（saveJSONFiles()を呼ばない）

JavaScriptの仕様により、後で定義された関数（1390行目）が実際に使用されます。

### 2. 新しい実装の問題点

```javascript
// 1390行目以降のstartRouteSearch関数
async function startRouteSearch() {
    // ... ルート検索処理 ...
    
    // ルート検索完了
    updatePropertiesList();
    saveToLocalStorage();        // LocalStorageには保存
    updateStats();
    
    // saveJSONFiles()が呼ばれていない！ ← これが原因
    
    hideProcessing();
    
    const message = `ルート検索が完了しました！\n成功: ${successfulRoutes}件\n失敗: ${failedRoutes}件...`;
    alert(message);
    
    if (successfulRoutes > 0) {
        nextStep();
    }
}
```

### 3. 保存タイミングの違い

#### 古い実装（1026行目）
- ルート検索完了後、即座にsaveJSONFiles()を実行
- Step 4に自動遷移

#### 新しい実装（1390行目）
- ルート検索完了後、LocalStorageのみ更新
- ユーザーがnextStep()でStep 4に進む必要がある
- **Step 4に到達しないとサーバー保存されない**

## 調査結果

### 実際のファイル状況
```bash
# 最新のproperties.json: 2025年8月10日（古い）
-rwxr-xr-x 1 www-data www-data 200349 Aug 10 00:39 properties.json

# バックアップも古い
-rwxr-xr-x 1 root root 200349 Aug 11 04:23 properties_backup_20250811_192328.json
```

### LocalStorageの確認方法
ブラウザの開発者ツールで以下を確認：
- `timeline_data`
- `timeline_destinations` 
- `timeline_properties`

これらに23物件のデータが保存されている可能性が高いです。

## 解決策

### 即座の対処法

1. **ブラウザからデータを回収**
   ```javascript
   // 開発者ツールのコンソールで実行
   const data = JSON.parse(localStorage.getItem('timeline_data'));
   console.log(JSON.stringify(data, null, 2));
   ```

2. **手動でsaveJSONFiles()を実行**
   ```javascript
   // 開発者ツールのコンソールで実行
   saveJSONFiles();
   ```

### 根本的な修正

#### オプション1: 新しい実装を修正（推奨）
```javascript
// 1452行目付近に追加
// ルート検索完了
updatePropertiesList();
saveToLocalStorage();
await saveJSONFiles();  // ← この行を追加
updateStats();
```

#### オプション2: 古い実装に戻す
1390行目以降のstartRouteSearch関数を削除し、1026行目の実装を使用

#### オプション3: Step 4での保存を確実にする
nextStep()関数でStep 4に遷移した際に自動的にsaveJSONFiles()を呼ぶ

## エラーの影響

### 質問：エラーが1件でもあれば保存しないのか？

**答え：いいえ**

- エラーがあっても保存処理は実行される
- 1444行目：「エラーの場合でも処理を継続」とコメント
- failedRoutesの数に関わらず、successfulRoutes > 0なら次のステップへ進む

問題は単純に**saveJSONFiles()が呼ばれていない**ことです。

## 23物件について

現在のproperties.jsonは18物件ですが、ユーザーが言及している23物件は：
1. PDFから追加で5物件を読み込んだ
2. 手動で5物件を追加した
3. LocalStorageには保存されているがサーバーには未保存

## 推奨アクション

1. **即座の対応**
   - ブラウザのLocalStorageからデータを回収
   - 手動でsaveJSONFiles()を実行

2. **コード修正**
   - 1454行目の後にawait saveJSONFiles();を追加
   - 重複した関数定義を整理

3. **テスト**
   - 修正後、小規模なデータでテスト
   - 保存が正しく行われることを確認