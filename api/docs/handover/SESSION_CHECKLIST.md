# ✅ セッション開始チェックリスト

## 開始時の確認事項

### 1. 引き継ぎシステムの起動
```bash
node /var/www/japandatascience.com/timeline-mapping/api/docs/handover/system/start-session.js
```
- [ ] クラッシュ警告が出た場合は要注意
- [ ] STATE.jsonのnext_actionsを確認
- [ ] critical_issuesを確認

### 2. 最新情報の確認
- [ ] `/api/docs/handover/SESSION_HANDOVER_20250812.md` を読む
- [ ] `/api/docs/handover/CRITICAL_CONTEXT.md` で背景を理解
- [ ] `/api/docs/handover/TROUBLESHOOTING.md` を手元に置く

### 3. システム状態の確認
- [ ] APIサーバーの生存確認
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Dockerコンテナの状態
  ```bash
  docker ps | grep scraper
  ```
- [ ] 最新のエラーログ
  ```bash
  docker logs vps_project-scraper-1 --tail 20
  ```

### 4. 問題の理解
- [ ] エラーが発生している物件: テラス月島801
- [ ] エラーが発生している住所: 東京都中央区佃2丁目 22-3
- [ ] 失敗している目的地: 東京駅、羽田空港、神谷町(EE)
- [ ] 原因: URLパラメータ `!3m1!4b1!4m2!4m1!3e0`

### 5. 修正の確認
- [ ] 修正ファイルが存在: `/api/google_maps_unified_safe.py`
- [ ] 修正内容: `?travelmode=transit` を使用
- [ ] 未適用であることを確認

## 作業開始前の判断

### ✅ すぐに作業を始められる場合
- APIサーバーが正常に応答している
- Dockerコンテナが稼働している
- 修正ファイルが存在する

### ⚠️ 先に対処が必要な場合
- APIサーバーが応答しない → 再起動が必要
- Dockerコンテナが停止 → docker-composeで起動
- ファイルが見つからない → バックアップから復元

## 作業の優先順位

1. **最優先**: APIサーバーの正常動作確保
2. **高**: google_maps_unified_safe.pyの適用
3. **高**: テラス月島の3ルートのテスト
4. **中**: json-generator.htmlでの動作確認
5. **低**: その他の改善（乗り換え時間の問題など）

## ゴール

- [ ] テラス月島801の3ルートが正常に取得できる
- [ ] json-generator.htmlでエラーが0件になる
- [ ] ユーザーに完了を報告する

## 注意事項

⚠️ **既に98.4%は成功している**
- 全体を壊さないよう慎重に
- 変更は最小限に
- バックアップを必ず取る

⚠️ **他の作業中のユーザーがいる可能性**
- APIサーバーの再起動は影響大
- 可能な限り無停止で対応
- 再起動する場合は短時間で

## 完了時のアクション

```bash
# セッション終了
node /var/www/japandatascience.com/timeline-mapping/api/docs/handover/system/end-session.js

# 結果を記録
echo "テラス月島問題: 解決" >> /api/docs/handover/ACTIVE/STATE.json
```

---
このチェックリストで、次のセッションがスムーズに開始できます。