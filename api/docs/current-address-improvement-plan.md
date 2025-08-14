# 現住所問題の改善計画と影響分析

## 初期計画

### 計画A: 現住所を特別扱いしない完全フラット化

#### 実装内容
1. すべての物件に削除ボタンを表示
2. 現住所という概念を廃止
3. validateCurrentStepで自動追加を削除

#### 予想される悪影響
- ❌ **データ整合性の問題**: 既存ユーザーの現住所（index 0）が特別な意味を持たなくなる
- ❌ **UXの混乱**: 「現在の住所（比較基準）」というUIと実装が矛盾
- ❌ **比較機能の破壊**: Timeline Mappingが現住所を基準に比較する機能が動作しなくなる可能性

### 計画B: 現住所フラグによる管理

#### 実装内容
1. isCurrentフラグを追加
2. 現住所は1つのみ許可
3. 現住所の切り替え機能

#### 予想される悪影響
- ❌ **データ構造の変更**: properties.jsonの構造変更により既存データとの互換性問題
- ❌ **実装複雑度**: 多くの箇所で条件分岐が必要
- ❌ **マイグレーション**: 既存データの変換が必要

## 悪影響の詳細分析

### 1. 既存システムへの影響

#### Timeline Mapping (index.html) の動作確認が必要
- 現住所を特別扱いしているコードの有無
- 物件の順序に依存する処理
- 比較機能の実装方法

#### 既存データとの互換性
- 18件の既存物件データ
- ユーザーが作成した過去のデータ
- バックアップファイルの扱い

### 2. ユーザー体験への影響

#### 期待される動作の変更
- 現在：現住所は常に最初で削除不可
- 変更後：どの物件も削除可能

#### 学習コストの発生
- 既存ユーザーの混乱
- ドキュメントの更新必要性

## 改訂版計画（悪影響を最小化）

### 最終計画: スマートな現住所管理

#### 基本方針
1. **データ構造は変更しない**（互換性維持）
2. **UIは現状維持**（ユーザー体験の継続性）
3. **内部ロジックのみ改善**（問題の根本解決）

#### 具体的な実装

```javascript
// 1. LocalStorage読み込み時の状態管理
let currentAddressFromStorage = null;

function loadFromLocalStorage() {
    const saved = localStorage.getItem('timeline_data');
    if (saved) {
        try {
            const data = JSON.parse(saved);
            destinations = data.destinations || [];
            properties = data.properties || [];
            
            // 現住所（最初の物件）を記録
            if (properties.length > 0) {
                currentAddressFromStorage = properties[0];
                // フォームに反映
                document.getElementById('currentName').value = currentAddressFromStorage.name || '';
                document.getElementById('currentAddress').value = currentAddressFromStorage.address || '';
                document.getElementById('currentRent').value = currentAddressFromStorage.rent || '';
            }
            
            updateDestinationsList();
            updatePropertiesList();
        } catch (error) {
            console.error('Load error:', error);
        }
    }
}

// 2. validateCurrentStepの改善
function validateCurrentStep() {
    if (currentStep === 1) {
        if (destinations.length === 0) {
            alert('少なくとも1つの目的地を登録してください');
            return false;
        }
    } else if (currentStep === 2) {
        const currentAddress = document.getElementById('currentAddress').value;
        const currentName = document.getElementById('currentName').value || '現在の住所';
        const currentRent = document.getElementById('currentRent').value || '0';
        
        if (!currentAddress && properties.length === 0) {
            alert('現在の住所を入力してください');
            return false;
        }
        
        // 現住所の更新または新規追加
        if (currentAddress) {
            const newCurrentProperty = {
                name: currentName,
                address: currentAddress,
                rent: currentRent
            };
            
            // 既存の現住所と比較
            if (properties.length > 0) {
                const existingCurrent = properties[0];
                // 内容が変更されている場合のみ更新
                if (existingCurrent.name !== currentName || 
                    existingCurrent.address !== currentAddress || 
                    existingCurrent.rent !== currentRent) {
                    properties[0] = newCurrentProperty;
                    saveToLocalStorage();
                }
            } else {
                // 新規追加
                properties.unshift(newCurrentProperty);
                saveToLocalStorage();
            }
        }
    }
    return true;
}

// 3. 削除機能の改善（現住所も削除可能に）
function updatePropertiesList() {
    const list = document.getElementById('propertiesList');
    if (properties.length === 0) {
        list.innerHTML = '';
        return;
    }

    list.innerHTML = '<h3 style="margin-top: 20px;">物件リスト</h3>' +
        properties.map((prop, index) => `
            <div class="property-item">
                <button class="btn-danger remove-btn" onclick="removeProperty(${index})">削除</button>
                <strong>${prop.name} ${index === 0 ? '（現住所）' : ''}</strong>
                <div class="item-details">
                    ${prop.address} | ${prop.rent}
                    ${prop.total_monthly_travel_time ? 
                        `<br><span style="color: #666;">月間移動時間: ${prop.total_monthly_travel_time}分 
                        (${Math.round(prop.total_monthly_travel_time/60*10)/10}時間)</span>` : ''}
                </div>
            </div>
        `).join('');
}

function removeProperty(index) {
    if (index === 0) {
        // 現住所を削除する場合の確認
        if (!confirm('現在の住所を削除しますか？\n比較基準がなくなりますが、よろしいですか？')) {
            return;
        }
        // フォームもクリア
        document.getElementById('currentName').value = '';
        document.getElementById('currentAddress').value = '';
        document.getElementById('currentRent').value = '';
    }
    
    properties.splice(index, 1);
    updatePropertiesList();
    saveToLocalStorage();
}

// 4. Step 2に入った時の処理を追加
function updateStepDisplay() {
    // 既存のコード...
    
    if (currentStep === 2) {
        // LocalStorageから読み込んだ現住所をフォームに反映
        if (properties.length > 0 && !document.getElementById('currentAddress').value) {
            const current = properties[0];
            document.getElementById('currentName').value = current.name || '';
            document.getElementById('currentAddress').value = current.address || '';
            document.getElementById('currentRent').value = current.rent || '';
        }
    }
}
```

## 最終計画の利点

### 1. 問題の解決
- ✅ 現住所の重複追加を防ぐ
- ✅ 現住所も削除可能（確認付き）
- ✅ フォームとデータの同期

### 2. 悪影響の最小化
- ✅ データ構造の変更なし
- ✅ 既存データとの完全互換
- ✅ UIの大幅な変更なし
- ✅ Timeline Mappingへの影響なし

### 3. ユーザー体験の向上
- ✅ 直感的な動作
- ✅ 誤操作の防止（確認ダイアログ）
- ✅ フォームの自動入力

## 実装手順

1. **バックアップ作成**
   ```bash
   cp json-generator.html json-generator.html.backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **段階的実装**
   - Phase 1: loadFromLocalStorageの改善
   - Phase 2: validateCurrentStepの修正
   - Phase 3: 削除機能の改善
   - Phase 4: テストと微調整

3. **テスト項目**
   - 新規利用時の動作
   - 既存データ読み込み時の動作
   - 現住所の編集・削除
   - Timeline Mappingとの連携

## リスク管理

### 潜在的リスク
1. 現住所を誤って削除する可能性
   - 対策：確認ダイアログ

2. フォームとデータの不整合
   - 対策：Step 2進入時の自動同期

3. 既存ユーザーの混乱
   - 対策：最小限の変更、直感的な動作

### ロールバック計画
- バックアップファイルから即座に復元可能
- 変更は内部ロジックのみなので影響範囲が限定的