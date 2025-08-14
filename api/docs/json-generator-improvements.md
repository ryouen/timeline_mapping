# json-generator.html 改善内容

## 実装した機能

### 1. ルート検索結果の自動保存

**問題**: 23物件×8目的地のルート検索が完了してもサーバーに保存されていなかった

**原因**: `startRouteSearch`関数が重複しており、新しい方（1390行目）で`saveJSONFiles()`が呼ばれていなかった

**修正内容**:
```javascript
// 1457行目に追加
// サーバーにも保存
await saveJSONFiles();
```

これにより、ルート検索完了時に自動的にサーバーへ保存されます。

### 2. 以前の検索結果を復元する機能

**追加した機能**:
- Step 3（ルート検索画面）で、LocalStorageに保存された検索結果を検出
- 検出した場合、情報を表示して復元オプションを提供
- 復元ボタンをクリックで直接Step 4（完了画面）へ遷移

**実装詳細**:

#### UI追加（563-571行目）
```html
<div id="previousSearchAlert" style="display: none; margin-top: 20px;">
    <div class="alert alert-info">
        <strong>以前のルート検索結果が見つかりました</strong><br>
        <span id="previousSearchInfo"></span><br>
        <button onclick="restorePreviousSearch()" style="margin-top: 10px;">
            以前の検索結果を復元
        </button>
    </div>
</div>
```

#### 検出機能（1560-1588行目）
```javascript
function checkPreviousSearchResults() {
    const saved = localStorage.getItem('timeline_data');
    if (!saved) return;
    
    try {
        const data = JSON.parse(saved);
        // ルート検索が完了しているかチェック
        let hasRoutes = false;
        let routeCount = 0;
        
        data.properties.forEach(prop => {
            if (prop.routes && prop.routes.length > 0) {
                hasRoutes = true;
                routeCount += prop.routes.length;
            }
        });
        
        if (hasRoutes) {
            const info = `物件数: ${data.properties.length}, 目的地数: ${data.destinations.length}, ルート数: ${routeCount}`;
            document.getElementById('previousSearchInfo').textContent = info;
            document.getElementById('previousSearchAlert').style.display = 'block';
        }
    } catch (error) {
        console.error('Error checking previous search:', error);
    }
}
```

#### 復元機能（1590-1616行目）
```javascript
function restorePreviousSearch() {
    const saved = localStorage.getItem('timeline_data');
    if (!saved) {
        alert('保存されたデータが見つかりません');
        return;
    }
    
    try {
        const data = JSON.parse(saved);
        destinations = data.destinations || [];
        properties = data.properties || [];
        
        updateDestinationsList();
        updatePropertiesList();
        updateStats();
        
        // 直接完了画面へ
        currentStep = 4;
        updateStepDisplay();
        
        alert('以前の検索結果を復元しました');
    } catch (error) {
        console.error('Restore error:', error);
        alert('データの復元に失敗しました');
    }
}
```

## 使用方法

### 1. 新規でルート検索を行う場合
- 通常通りStep 1から順番に進む
- Step 3でルート検索を実行
- 完了時に自動的にサーバーとLocalStorageに保存

### 2. 以前の検索結果がある場合
- Step 3に到達すると自動的に検出
- 「以前のルート検索結果が見つかりました」と表示
- 物件数、目的地数、ルート数が表示される
- 「以前の検索結果を復元」ボタンをクリック
- 直接Step 4（完了画面）へ移動
- JSONファイルのダウンロードや確認が可能

### 3. 23物件のデータを回収する場合
1. json-generator.htmlを開く
2. Step 3まで進む（データは入力不要）
3. 「以前の検索結果を復元」ボタンをクリック
4. Step 4で「properties.jsonをダウンロード」をクリック

## 注意事項

- LocalStorageのデータは`timeline_data`キーで保存
- ブラウザのキャッシュをクリアするとデータが失われる
- 復元機能はルート情報が含まれている場合のみ表示される
- 空の物件リストや目的地リストは復元対象外

## バックアップ

変更前のファイルは以下に保存：
- `~/json-generator.html.backup_20250813_011735`