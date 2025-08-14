# json-generator.html 現住所に関する問題と改善案

## 現状の問題点

### 1. 現住所の重複入力問題

#### 問題の詳細
- **発生条件**：
  - LocalStorageにデータが保存されている状態でページを再読み込み
  - Step 2で「次へ」ボタンを押すたび
  
- **原因**：
  ```javascript
  // validateCurrentStep関数（667-681行）
  if (currentStep === 2) {
      const currentName = document.getElementById('currentName').value || '現在の住所';
      if (!properties.find(p => p.name === currentName)) {
          properties.unshift({
              name: currentName,
              address: currentAddress,
              rent: document.getElementById('currentRent').value || '0'
          });
      }
  }
  ```
  - フォームの値と既存データの名前が一致しない場合、新規追加と判断
  - LocalStorageから読み込んだ現住所があっても、フォームが空なら別物として扱われる

### 2. 現住所の削除ボタン非表示問題

#### 問題の詳細
- **現在の実装**：
  ```javascript
  // updatePropertiesList関数（1007行）
  ${index > 0 ? `<button class="btn-danger remove-btn" onclick="removeProperty(${index})">削除</button>` : ''}
  ```
  - インデックス0（配列の最初）の物件は常に削除ボタンが表示されない
  - 現住所は常に`properties.unshift`で先頭に追加されるため、削除不可

## 改善案

### 案1: 現住所を特別扱いしない（推奨）

#### 実装方針
1. 現住所も通常の物件として扱う
2. すべての物件に削除ボタンを表示
3. 物件が0件になることを許可

#### メリット
- シンプルで直感的
- ユーザーが自由に編集可能
- 特殊ケースが減る

#### 変更内容
```javascript
// validateCurrentStep関数の修正
if (currentStep === 2) {
    // 物件が0件の場合のみチェック
    if (properties.length === 0) {
        const currentAddress = document.getElementById('currentAddress').value;
        if (!currentAddress) {
            alert('少なくとも1つの物件を登録してください');
            return false;
        }
        // 新規追加
        properties.push({
            name: document.getElementById('currentName').value || '物件1',
            address: currentAddress,
            rent: document.getElementById('currentRent').value || '0'
        });
    }
}

// updatePropertiesList関数の修正
properties.map((prop, index) => `
    <div class="property-item">
        <button class="btn-danger remove-btn" onclick="removeProperty(${index})">削除</button>
        <strong>${prop.name}</strong>
        <div class="item-details">
            ${prop.address} | ${prop.rent}
        </div>
    </div>
`).join('')

// removeProperty関数の修正
function removeProperty(index) {
    properties.splice(index, 1);
    updatePropertiesList();
    saveToLocalStorage();
}
```

### 案2: 現住所フォームと物件リストを分離

#### 実装方針
1. 現住所入力フォームを独立させる
2. 「現住所として登録」ボタンを追加
3. 既存の現住所があれば上書き確認

#### メリット
- 現住所の特別な位置づけを維持
- 誤操作を防ぐ

#### デメリット
- UIが複雑になる
- 実装コストが高い

### 案3: 現住所の識別方法を改善

#### 実装方針
1. 物件に`isCurrent`フラグを追加
2. 現住所は1つのみ許可
3. 現住所の切り替え機能を提供

#### 変更内容
```javascript
// 物件データ構造の拡張
{
    name: "現在の自宅",
    address: "東京都千代田区...",
    rent: "150000",
    isCurrent: true  // 追加
}

// validateCurrentStep関数の修正
if (currentStep === 2) {
    const currentProperty = properties.find(p => p.isCurrent);
    const currentAddress = document.getElementById('currentAddress').value;
    
    if (currentAddress && !currentProperty) {
        // 現住所が未登録の場合のみ追加
        properties.unshift({
            name: document.getElementById('currentName').value || '現在の住所',
            address: currentAddress,
            rent: document.getElementById('currentRent').value || '0',
            isCurrent: true
        });
    }
}
```

## 推奨する解決策

**案1（現住所を特別扱いしない）**を推奨します。

### 理由
1. **シンプル**: 特殊ケースが減り、コードが理解しやすい
2. **柔軟性**: ユーザーが自由に物件を管理できる
3. **一貫性**: すべての物件が同じ扱いになる
4. **実装コスト**: 最小限の変更で実現可能

### 実装手順
1. `validateCurrentStep`関数を修正
2. `updatePropertiesList`関数から条件分岐を削除
3. `removeProperty`関数から条件を削除
4. Step 2のUIテキストを調整（「現在の住所」→「物件を追加」）

## 追加の改善提案

### 1. フォームのクリア機能
- 物件追加後、フォームを自動クリア
- 連続して物件を追加しやすくする

### 2. 編集機能の追加
- 登録済み物件の編集ボタン
- インライン編集またはモーダルダイアログ

### 3. 物件の並び替え
- ドラッグ&ドロップで順序変更
- 現住所を任意の位置に配置可能