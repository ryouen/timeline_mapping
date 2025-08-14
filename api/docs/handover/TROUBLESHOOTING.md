# 🔧 トラブルシューティングガイド

## APIサーバーが応答しない場合

### 症状
```bash
curl http://localhost:8000/health
# 結果: Connection refused または タイムアウト
```

### 対処法

#### 1. コンテナの確認
```bash
# コンテナが動いているか
docker ps | grep scraper
# 結果例: 1fb5c27f6da9   vps_project-scraper   Up 43 hours

# コンテナは動いているがAPIが死んでいる場合
docker exec vps_project-scraper-1 ps aux | grep python
# pythonプロセスがない、または古い場合は問題
```

#### 2. コンテナの再起動
```bash
# ソフトリスタート
docker restart vps_project-scraper-1

# 30秒待つ
sleep 30

# 確認
curl http://localhost:8000/health
```

#### 3. それでもダメな場合
```bash
# ログを確認
docker logs vps_project-scraper-1 --tail 100

# コンテナを完全に再作成
docker-compose -f /home/ubuntu/vps_project/docker-compose.yml restart scraper
```

## 修正を適用してもエラーが続く場合

### 1. ファイルが正しくコピーされたか確認
```bash
# コンテナ内のファイルを確認
docker exec vps_project-scraper-1 head -50 /app/src/google_maps_unified.py | grep "travelmode"
# "?travelmode=transit" が見つかればOK
```

### 2. APIサーバーのプロセスが新しいコードを読み込んでいるか
```bash
# プロセスの開始時刻を確認
docker exec vps_project-scraper-1 ps aux | grep python
# STARTカラムが古い場合は再起動が必要
```

### 3. キャッシュの問題
```bash
# Pythonのキャッシュをクリア
docker exec vps_project-scraper-1 find /app -name "*.pyc" -delete
docker exec vps_project-scraper-1 find /app -name "__pycache__" -type d -exec rm -rf {} +
docker restart vps_project-scraper-1
```

## json-generator.htmlでまだエラーが出る場合

### 1. ブラウザのキャッシュ
- 開発者ツールを開く（F12）
- Networkタブで「Disable cache」にチェック
- ページをリロード（Ctrl+Shift+R）

### 2. ローカルストレージの確認
```javascript
// コンソールで実行
const data = JSON.parse(localStorage.getItem('timeline_data'));
const terrace = data.properties.find(p => p.name.includes('テラス月島'));
console.log('テラス月島のルート数:', terrace.routes ? terrace.routes.length : 0);
```

### 3. 部分的なデータのクリア
```javascript
// テラス月島のルートだけクリア
const data = JSON.parse(localStorage.getItem('timeline_data'));
const terrace = data.properties.find(p => p.name.includes('テラス月島'));
if (terrace) {
    terrace.routes = [];
    localStorage.setItem('timeline_data', JSON.stringify(data));
    console.log('テラス月島のルートをクリアしました');
}
```

## エラーメッセージ別対処法

### "Route search failed"
- APIサーバーがエラーを返している
- `google_maps_unified.py`の修正が適用されていない可能性大

### "504 Gateway Time-out"
- 処理に30秒以上かかっている
- タイムアウト値を増やす必要があるかも
- または、APIサーバーがハングしている

### "Connection refused"
- APIサーバーが起動していない
- ポート8000が閉じている
- dockerコンテナの再起動が必要

## デバッグ用ワンライナー

```bash
# 全体の健全性チェック
echo "=== System Health Check ===" && \
docker ps | grep -E "(scraper|apache)" && \
echo -e "\n=== API Health ===" && \
curl -s http://localhost:8000/health | jq '.' && \
echo -e "\n=== Test Route ===" && \
curl -s -X POST http://localhost:8000/api/transit \
  -H "Content-Type: application/json" \
  -d '{"origin": "東京駅", "destination": "渋谷駅"}' \
  -m 10 | jq '.success, .data.total_time'
```

## 最終手段

すべて失敗した場合：
1. `/var/www/japandatascience.com/timeline-mapping/api/google_maps_unified_backup_*.py` から元のファイルを復元
2. 一時的に問題のある物件をスキップするようjson-generator.htmlを修正
3. ユーザーに状況を説明し、手動でテラス月島のデータを追加することを提案

---
記録日: 2025-08-12
問題: テラス月島801のルート検索エラー