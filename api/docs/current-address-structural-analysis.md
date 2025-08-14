# 現住所問題の構造的分析と解決策

## 🔍 Ultrathink: 問題の根本原因

### 1. データフローの断絶

```
LocalStorage → properties配列 ✓
properties配列 → 表示リスト ✓
properties配列 → フォーム ✗ （ここが欠落）
```

### 2. 状態管理の不整合

現在の実装では3つの状態が同期されていない：
- **フォームの値**（currentName, currentAddress, currentRent）
- **properties配列**（実際のデータ）
- **LocalStorage**（永続化されたデータ）

### 3. ロジックの重複と矛盾

```javascript
// validateCurrentStep（667行目）
if (!properties.find(p => p.name === currentName)) {
    properties.unshift({...});  // 名前が一致しない場合に新規追加
}
```

問題点：
- フォームが空 → currentName = "現在の住所"
- 既存物件名が "ルフォンプログレ神田プレミア" 
- 名前が一致しない → 重複追加

## 🏗️ 構造的な解決策

### 基本設計思想

1. **現住所 = properties[0]**（不変）
2. **フォーム = 現住所の編集インターフェース**
3. **最低1件保証**（index.html互換性）

### 実装方針

#### A. 状態の単一方向フロー

```
LocalStorage
    ↓ (load)
properties[0]
    ↓ (sync)
フォーム
    ↓ (edit)
properties[0]更新
    ↓ (save)
LocalStorage
```

#### B. 明確な責任分離

1. **フォーム**: 現住所（properties[0]）の編集専用
2. **物件リスト**: すべての物件を表示・管理
3. **validateCurrentStep**: 物件0件の場合のみ新規作成

## 📝 具体的な実装

### 1. loadFromLocalStorageの改善

```javascript
function loadFromLocalStorage() {
    const saved = localStorage.getItem('timeline_data');
    if (saved) {
        try {
            const data = JSON.parse(saved);
            destinations = data.destinations || [];
            properties = data.properties || [];
            
            // 現住所（最初の物件）をフォームに反映
            if (properties.length > 0) {
                syncCurrentAddressToForm();
            }
            
            updateDestinationsList();
            updatePropertiesList();
        } catch (error) {
            console.error('Load error:', error);
        }
    }
}

// 新規関数：現住所をフォームに同期
function syncCurrentAddressToForm() {
    if (properties.length > 0) {
        const current = properties[0];
        document.getElementById('currentName').value = current.name || '';
        document.getElementById('currentAddress').value = current.address || '';
        document.getElementById('currentRent').value = current.rent || '';
    }
}
```

### 2. validateCurrentStepの簡潔化

```javascript
function validateCurrentStep() {
    if (currentStep === 1) {
        if (destinations.length === 0) {
            alert('少なくとも1つの目的地を登録してください');
            return false;
        }
    } else if (currentStep === 2) {
        const currentAddress = document.getElementById('currentAddress').value.trim();
        const currentName = document.getElementById('currentName').value.trim() || '現在の住所';
        const currentRent = document.getElementById('currentRent').value.trim() || '0';
        
        if (properties.length === 0) {
            // 物件が0件の場合
            if (!currentAddress) {
                alert('現在の住所を入力してください');
                return false;
            }
            // 新規作成
            properties.push({
                name: currentName,
                address: currentAddress,
                rent: currentRent
            });
        } else {
            // 既存の現住所を更新（フォームに値がある場合のみ）
            if (currentAddress) {
                properties[0] = {
                    ...properties[0],  // 既存のルート情報等を保持
                    name: currentName,
                    address: currentAddress,
                    rent: currentRent
                };
            }
        }
        saveToLocalStorage();
    }
    return true;
}
```

### 3. updatePropertiesListの改善

```javascript
function updatePropertiesList() {
    const list = document.getElementById('propertiesList');
    if (properties.length === 0) {
        list.innerHTML = '<p style="color: #999;">物件を登録してください</p>';
        return;
    }

    list.innerHTML = '<h3 style="margin-top: 20px;">物件リスト</h3>' +
        properties.map((prop, index) => `
            <div class="property-item">
                <div class="property-actions" style="float: right;">
                    ${properties.length > 1 ? 
                        `<button class="btn-danger btn-small" onclick="removeProperty(${index})">削除</button>` : 
                        '<span style="color: #999; font-size: 12px;">削除不可</span>'}
                    ${index > 0 ? 
                        `<button class="btn-secondary btn-small" onclick="makeCurrentAddress(${index})" style="margin-left: 5px;">現住所に設定</button>` : 
                        ''}
                </div>
                <strong>${prop.name} ${index === 0 ? '<span style="color: #4CAF50;">（現住所）</span>' : ''}</strong>
                <div class="item-details">
                    ${prop.address} | ${prop.rent ? prop.rent + '円' : '家賃未設定'}
                    ${prop.total_monthly_travel_time ? 
                        `<br><span style="color: #666;">月間移動時間: ${prop.total_monthly_travel_time}分 
                        (${Math.round(prop.total_monthly_travel_time/60*10)/10}時間)</span>` : ''}
                </div>
            </div>
        `).join('');
}
```

### 4. removePropertyの安全性向上

```javascript
function removeProperty(index) {
    if (properties.length === 1) {
        alert('最低1件の物件が必要です。\n内容を変更する場合は、上のフォームで編集してください。');
        return;
    }
    
    const confirmMessage = index === 0 ? 
        `現住所「${properties[0].name}」を削除しますか？\n「${properties[1].name}」が新しい現住所になります。` :
        `「${properties[index].name}」を削除しますか？`;
    
    if (confirm(confirmMessage)) {
        properties.splice(index, 1);
        
        // 現住所を削除した場合、新しい現住所をフォームに反映
        if (index === 0) {
            syncCurrentAddressToForm();
        }
        
        updatePropertiesList();
        saveToLocalStorage();
    }
}
```

### 5. 現住所切り替え機能

```javascript
function makeCurrentAddress(index) {
    if (index === 0) return;
    
    const property = properties[index];
    if (confirm(`「${property.name}」を現在の住所に設定しますか？`)) {
        // 配列の順序を入れ替え
        properties.splice(index, 1);
        properties.unshift(property);
        
        // フォームを更新
        syncCurrentAddressToForm();
        
        updatePropertiesList();
        saveToLocalStorage();
    }
}
```

### 6. Step切り替え時の同期

```javascript
function updateStepDisplay() {
    // 既存のコード...
    
    if (currentStep === 2) {
        // Step 2に入った時、現住所をフォームに反映
        syncCurrentAddressToForm();
    }
}
```

## 🎯 この設計の利点

1. **データの一貫性**: フォームとproperties[0]が常に同期
2. **index.html互換**: 最低1件保証、properties[0]は現住所
3. **直感的なUI**: フォームは編集、リストは管理
4. **柔軟性**: 現住所の削除・切り替えが可能

## ⚠️ エッジケース対策

1. **空のフォーム送信**: 既存物件がある場合は更新しない
2. **最後の1件**: 削除不可の明示
3. **現住所切り替え**: ルート情報等を保持

## 📊 状態遷移図

```
初期状態
    ↓
LocalStorage読み込み
    ↓
properties[0]あり? → Yes → フォームに反映
    ↓ No
フォーム空欄
    ↓
ユーザー入力
    ↓
次へボタン
    ↓
properties[0]あり? → Yes → 更新
    ↓ No
新規作成
```

この構造により、現住所の管理が明確になり、ユーザーの混乱を防げます。