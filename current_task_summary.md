# 現在の課題と修正計画のサマリー

## 課題の概要

モバイル版で並び替えシート（`#sortBottomSheet`）が表示された際に、以下の問題が発生しています。
1.  シートの下部が見切れてしまい、特に「適用」ボタンが押せない。
2.  シートのヘッダーに「並び替え」という不要なテキストが表示されている。
3.  シートを閉じるための「✕」ボタンが、並び替え項目の右側に配置されていない。

## これまでの議論と問題の特定

*   初期表示時に並び替えモーダルが表示されてしまう問題は、CSSのメディアクエリ内で`.bottom-sheet`に`display: block;`が設定されていたことが原因と特定済み。これは以前の修正で削除済み。
*   `replace`ツールを用いた直接的なHTML/CSSの変更が、厳密な文字列マッチングの要件により失敗するケースが多発。

## 今後の修正計画（詳細）

ファイル全体を読み込み、メモリ上で変更を加えてから書き戻す方法で、以下の修正を一度に適用します。

### 1. 並び替えシートの表示位置調整

*   **目的**: 並び替えシートが画面下部で見切れないように、表示位置を上方向に調整する。
*   **変更内容**:
    *   CSSの`.bottom-sheet.active`セレクタの`transform`プロパティを調整します。
    *   現在の`transform: translateY(0);`を、例えば`transform: translateY(-100px);`のように、より大きな負の値に変更します。

### 2. 並び替えシートのヘッダー変更

*   **目的**: 不要な「並び替え」テキストを削除し、並び替え項目の右側に「✕」ボタンを配置する。
*   **変更内容**:
    *   **HTMLの変更**:
        *   `id="sortBottomSheet"`内の`<div class="panel-header">`から`<h2>並び替え</h2>`の行を削除します。
        *   `id="sortBottomSheet"`内の`<div class="sheet-content">`にある`<h3>並び替え項目</h3>`を新しい`div`要素（例: `<div class="sort-options-header">`）で囲み、その中に「✕」ボタン（`<button class="close-btn-sort" onclick="toggleSortBottomSheet()">&times;</button>`）を追加します。
    *   **CSSの追加**:
        *   `.sort-options-header`に`display: flex; align-items: center; justify-content: space-between;`などのスタイルを追加し、`<h3>`と「✕」ボタンを横並びに配置します。
        *   `.close-btn-sort`に、見た目を「✕」ボタンらしくするためのスタイル（フォントサイズ、色、背景、パディングなど）を定義します。

## 実行方法

1.  `index.html`の全内容を読み込む。
2.  読み込んだ内容を文字列として保持し、Pythonの文字列操作で上記のHTMLおよびCSSの変更を適用する。
3.  変更後の文字列を`index.html`に上書き保存する。

---