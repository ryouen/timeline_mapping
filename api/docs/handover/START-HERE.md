# 🚀 Timeline Mapping プロジェクト - START HERE

## 新しいセッションを開始する方へ

このファイルがあなたの道標です。

### 📍 現在の状況（2025-08-12 17:15時点）

**✅ 解決済み:**
1. **APIサーバーは正常動作中** (port 8000)
2. **テラス月島801のエラーは解消済み** 
3. **修正適用済み・テスト完了**

**現在のステータス:**
- 全184物件×8目的地=1,472ルート：すべて正常取得可能
- エラー件数：0件
- 最新の引き継ぎ：`COMPLETE_HANDOVER_20250812.md`を参照

### 🔥 必須コマンド（この順番で実行）

```bash
# 1. 引き継ぎシステムでセッション開始
node /var/www/japandatascience.com/timeline-mapping/api/docs/handover/system/start-session.js

# 2. 最新の引き継ぎドキュメントを確認
cat /var/www/japandatascience.com/timeline-mapping/api/docs/handover/SESSION_HANDOVER_20250812.md

# 3. APIサーバーの状態確認
docker ps | grep scraper
curl http://localhost:8000/health || echo "API not responding"

# 4. APIサーバーが死んでいる場合は再起動
docker restart vps_project-scraper-1
sleep 10
curl http://localhost:8000/health
```

### 📋 プロジェクト概要

**Google Maps移行プロジェクト**
- Yahoo乗換案内 → Google Maps への移行
- 184物件 × 8目的地 = 1,472ルートの検索
- 98.4%は成功、1.6%（3件）でエラー発生

**主要コンポーネント:**
```
json-generator.html (フロントエンド)
    ↓
google_maps_integration.php (APIゲートウェイ)
    ↓
APIサーバー :8000 (Pythonスクレイパー)
    ↓
google_maps_unified.py (Selenium)
    ↓
Google Maps
```

### ⚠️ 既知の問題

1. **テラス月島801のエラー**
   - 住所: 東京都中央区佃2丁目 22-3
   - 失敗ルート: 東京駅、羽田空港、神谷町(EE)
   - 原因: URLパラメータ `data=!3m1!4b1!4m2!4m1!3e0` が問題
   - 修正: `google_maps_unified_safe.py` で解決済み（未適用）

2. **乗り換え時間の不正確さ**
   - 実際は1分なのに5分と表示される
   - 優先度: 中（動作はする）

### 🛠️ 修正の適用手順

```bash
# 1. 現在のファイルをバックアップ
docker exec vps_project-scraper-1 cp /app/src/google_maps_unified.py /app/src/google_maps_unified_backup_$(date +%Y%m%d).py

# 2. 修正版をコンテナにコピー
docker cp /var/www/japandatascience.com/timeline-mapping/api/google_maps_unified_safe.py vps_project-scraper-1:/app/src/google_maps_unified.py

# 3. APIサーバーを再起動
docker restart vps_project-scraper-1

# 4. 30秒待って確認
sleep 30
curl http://localhost:8000/health

# 5. テラス月島のルートをテスト
curl -X POST http://localhost:8000/api/transit \
  -H "Content-Type: application/json" \
  -d '{"origin": "東京都中央区佃2丁目 22-3", "destination": "東京駅"}' \
  -m 30
```

### 🧪 動作確認

1. **APIレベルの確認**
   ```bash
   # 3つの失敗ルートをテスト
   for dest in "東京駅" "羽田空港" "神谷町駅"; do
     echo "Testing: テラス月島 → $dest"
     curl -s -X POST http://localhost:8000/api/transit \
       -H "Content-Type: application/json" \
       -d "{\"origin\": \"東京都中央区佃2丁目 22-3\", \"destination\": \"$dest\"}" \
       -m 30 | jq '.success'
   done
   ```

2. **json-generator.htmlでの確認**
   - ブラウザで https://japandatascience.com/timeline-mapping/json-generator.html を開く
   - ローカルストレージを確認: `localStorage.getItem('timeline_data')`
   - テラス月島のルートのみ再検索

### 📁 重要なファイルの場所

- **引き継ぎシステム**: `/api/docs/handover/`
- **最新の引き継ぎ**: `/api/docs/handover/SESSION_HANDOVER_20250812.md`
- **エラー分析**: `/api/docs/handover/error_analysis.md`
- **修正済みコード**: `/api/google_maps_unified_safe.py`
- **現在のコード**: コンテナ内 `/app/src/google_maps_unified.py`

### 🎯 成功の判定基準

1. ✅ APIサーバーが `{"status":"healthy"}` を返す
2. ✅ テラス月島の3ルートが正常に取得できる
3. ✅ json-generator.htmlでエラーが0件になる
4. ✅ ユーザーに完了を報告できる

### 💡 Tips

- APIサーバーが不安定な場合は、メモリ不足の可能性あり
- Seleniumのタイムアウトは20秒だが、複雑なルートは30秒以上かかることがある
- Google MapsのURL形式は繊細。`!` を含むパラメータは避ける
- 住所の「丁目」の後のスペースが問題を起こすことがある

---
最終更新: 2025-08-12
このファイルは編集不要です。最新情報は `/api/docs/handover/ACTIVE/` を参照してください。