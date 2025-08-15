# 府中ルート デバッグセッション記録
最終更新: 2025-08-15 02:10 JST

## 現在の問題
府中ルート（東京都千代田区神田須田町1-20-1 → 東京都府中市住吉町5-22-5）のスクレイピングが失敗している。

### 現在の状態
- properties.json: **48分**（誤り）
- 正しいデータ: **67-69分**（ユーザー提供のゴールデンデータ）

## ゴールデンデータ（ユーザー提供）

### 9時出発（67分）
```
小川町駅から 9:09
└─ 徒歩約11分 550m
小川町駅 9:09
└─ 都営地下鉄新宿線各停 本八幡行き
   9:09-9:24（15分、7駅）330円
新宿駅 9:24-9:30
└─ 徒歩約4分 210m
新宿駅 9:30-9:52
└─ 京王線準特急 高尾山口行き
   9:30-9:52（22分、7駅）220円
中河原駅 9:52
└─ 徒歩約5分 350m
到着 10:16（1時間7分）
```

### 10時到着（69分）
```
神田駅まで 8:51
└─ 徒歩約4分
神田駅 8:51
└─ JR中央線快速 高尾行き
   8:51-9:07（16分、5駅）170円
新宿駅 9:07-9:29
└─ 京王線準特急 高尾山口行き
   9:29-9:51（22分、7駅）220円
中河原駅 9:51
└─ 徒歩約5分 350m
到着 10:00（1時間9分）
```

## 技術的な課題

### 1. HTMLファイルのサイズ問題
デバッグ用に保存されたHTMLファイルが大きすぎる（約750KB-870KB）。
- 最新ファイル: `/var/www/japandatascience.com/timeline-mapping/api/debug/page_source_東京都千代田区神田須-東京都府中市住吉町5_20250814_170713.html`
- サイズ: 754,316 bytes

### 2. 現在のスクレイパーの問題点
1. **複数路線への対応不足**: 新宿線→京王線、中央線→京王線のような乗り換えパターンに対応していない
2. **セレクタの不一致**: Google Mapsの長距離ルートは異なるHTML構造を持つ
3. **フォールバック処理**: エラー時に「神田→日本橋 8分」という偽データを返していた（2025-08-14に修正済み）

### 3. デバッグ結果
- 現在のスクレイパー（google_maps_scraper.py）: "No route information could be extracted"エラー
- 改良版（google_maps_scraper_improved.py）: セレクタが見つからず失敗

## 作業ファイル

### メインファイル
- `/var/www/japandatascience.com/timeline-mapping/api/google_maps_scraper.py` - 現在のスクレイパー
- `/var/www/japandatascience.com/timeline-mapping/api/google_maps_scraper_improved.py` - 改良版（作成中）
- `/var/www/japandatascience.com/timeline-mapping/data/properties.json` - 更新が必要

### デバッグファイル
- `/var/www/japandatascience.com/timeline-mapping/api/test_fuchu_route_debug.py` - HTMLパーサー
- `/var/www/japandatascience.com/timeline-mapping/api/test_fuchu_scraping.py` - テストスクリプト

### 参考ファイル
- `/var/www/japandatascience.com/timeline-mapping/data/golden.html` - テストルートのリンク集
- `/home/ubuntu/backup/20250815/google_maps_scraper_010000.py` - バックアップ版

## 次のステップ
1. HTMLファイルから正しいセレクタを特定
2. 複数路線に対応したパーサーを実装
3. 府中ルートでテスト
4. properties.jsonを更新

## 重要な注意事項
- **作業ディレクトリ**: `/var/www/japandatascience.com/timeline-mapping/`
- **Dockerコンテナ経由で実行**: `docker exec vps_project-scraper-1 python3 /app/output/...`
- **バックアップ**: 変更前に必ず `/home/ubuntu/backup/YYYYMMDD/` に保存