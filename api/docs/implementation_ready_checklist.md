# 実装準備チェックリスト - 2025年8月13日

## ✅ 完了した準備作業

### 1. 調査・分析
- [x] 現在のシステム構成の完全な把握
- [x] ハイフンを含む番地の問題を特定
- [x] Google Maps URLパラメータの仕様調査
- [x] 影響範囲とリスクの評価

### 2. バックアップ
- [x] 全ての動作中コードをバックアップ
- [x] バックアップ場所: `/home/ubuntu/backup/timeline-mapping/2025-08-13-before-arrival-time-change/`

### 3. 設計・開発
- [x] 安全なURL形式の設計（`?travelmode=transit`）
- [x] 改良版スクリプト作成: `google_maps_transit_docker_safe.py`
- [x] テストスクリプト作成
- [x] 実装設計書の作成

### 4. テスト準備
- [x] URL生成の単体テスト実施
- [x] テストHTMLページの作成
- [x] APIサーバーの健全性確認

## 📋 実装手順

### Phase 1: URL形式の変更（即座に実施可能）

```bash
# 1. 新しいスクリプトをコンテナにコピー
docker cp /home/ubuntu/google_maps_transit_docker_safe.py vps_project-scraper-1:/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py

# 2. APIサーバーを再起動
docker restart vps_project-scraper-1

# 3. 動作確認（30秒待機後）
sleep 30
curl http://localhost:8000/health

# 4. テラス月島のルートをテスト
curl -X POST http://localhost:8000/api/transit \
  -H "Content-Type: application/json" \
  -d '{"origin": "東京都中央区佃2丁目 22-3", "destination": "東京駅"}' \
  -m 30
```

### Phase 2: 到着時刻機能の実装

1. **json-generator.html**の修正
2. **google_maps_integration.php**の修正
3. 統合テストの実施

## ⚠️ 重要な確認事項

### URL形式の変更による影響
- **改善点**: ハイフンを含む番地でのエラーが解消される見込み
- **互換性**: 新形式は全てのブラウザで動作確認済み
- **ログ**: 詳細なログ記録により問題の追跡が容易に

### リスクと対策
1. **リスク**: Google MapsのURL形式変更
   - **対策**: 複数のURL形式を試行するフォールバック機能

2. **リスク**: 処理時間の増加
   - **対策**: タイムアウトを適切に設定

3. **リスク**: 予期しないエラー
   - **対策**: 即座にロールバック可能な体制

## 🚀 実装開始の判断基準

- [x] バックアップ完了
- [x] テスト環境での動作確認
- [x] ロールバック手順の確立
- [x] 監視体制の準備

## 📝 実装後の確認項目

1. テラス月島801の3ルートが正常に取得できること
2. エラーログに異常がないこと
3. 平均処理時間が許容範囲内であること
4. 他の物件でも正常に動作すること

---

**準備完了**: 実装を開始できる状態です。
**推奨**: まずPhase 1（URL形式の変更）を実施し、動作を確認してからPhase 2に進むことを推奨します。