# json-generator.html ステップ分離修正 - 2025年8月13日 20:20

## 問題の概要

ユーザーからの報告：
1. ステップ2（物件情報）で物件の面積（平米数）が表示されない
2. ステップ2で本来表示されるべきでない月間移動時間が表示される
3. 全て削除ボタンがない

## 根本原因の分析

### 1. 面積が表示されない原因
- PDFから面積は正しく抽出されていた（generate_pdf.php）
- しかし、`generateRoutes`実行時に`generate_routes.php`が物件データを再構築する際、areaフィールドを含めていなかった
- 結果として面積データが失われていた

### 2. 月間移動時間が誤表示される原因
- PDFアップロード後、即座に`generateRoutes`関数が呼ばれていた（json-generator.html: 995行目）
- ステップ2で本来ステップ3の処理（ルート検索）が実行されていた
- ステップ間の責任範囲が不明確な設計上の欠陥

### 3. データフローの問題
- 各ステップの役割：
  - ステップ1: 目的地設定
  - ステップ2: 物件情報入力（基本情報のみ）
  - ステップ3: ルート検索（移動時間計算）
  - ステップ4: 確認・保存
- PDFアップロード時にステップ3の処理まで実行されていた

## 実施した修正

### 1. PDFアップロード時のルート生成を無効化
```javascript
// 修正前
await generateRoutes(data.properties);

// 修正後
// ステップ2ではルート情報を生成しない（ステップ3で実行）
// await generateRoutes(data.properties);
```

### 2. 物件リスト表示の改善
- `getCurrentStep()`関数を追加して現在のステップを判定
- ステップ2では月間移動時間を非表示に
- ステップ3以降でのみルート情報を表示

### 3. 全て削除ボタンの追加
- `removeAllProperties()`関数を実装
- 物件リストの下部に「全て削除」ボタンを配置
- 確認ダイアログ付きで安全に削除

### 4. generate_routes.phpの改善
- areaフィールドを保持するように修正
```php
'area' => $property['area'] ?? '',
```

### 5. フォーム同期の改善
- `syncCurrentAddressToForm()`にareaフィールドの同期を追加

## 影響範囲と確認事項

### 正常に動作する機能
- ✅ PDFからの物件情報抽出（面積含む）
- ✅ 手動での物件追加・編集
- ✅ ステップ3でのルート検索
- ✅ 段階的なJSON保存（destinations.json, properties_base.json, properties.json）

### ユーザーへの影響
- ステップ2では物件の基本情報のみ表示（意図通り）
- ステップ3でルート検索を実行後、移動時間が表示される
- 全て削除ボタンで一括削除が可能に

## 今後の注意事項

1. **ステップの責任範囲を明確に保つ**
   - 各ステップで行うべき処理を混在させない
   - データの段階的な構築を意識する

2. **データの整合性**
   - 物件データの更新時は全フィールドを保持する
   - 不要なデータの上書きを避ける

3. **UIの一貫性**
   - 各ステップで表示すべき情報を適切に制御
   - ユーザーの期待に沿った表示を心がける

## 関連ファイル
- `/var/www/japandatascience.com/timeline-mapping/json-generator.html`
- `/var/www/japandatascience.com/timeline-mapping/api/generate_routes.php`
- `/var/www/japandatascience.com/timeline-mapping/api/generate_pdf.php`