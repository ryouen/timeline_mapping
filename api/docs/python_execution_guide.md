# Python実行ガイド

## 重要：必ずDockerコンテナ内で実行すること

### 基本的な実行方法

```bash
# 正しい実行方法
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/スクリプト名.py

# 例：
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_unified.py "東京駅" "渋谷駅"
```

### なぜDockerコンテナが必要か

1. **Selenium環境**
   - Selenium GridがDockerネットワーク内で動作
   - コンテナ外からはアクセスできない

2. **依存関係**
   - 必要なPythonパッケージがコンテナ内にインストール済み
   - Chrome/ChromeDriverが適切に設定済み

3. **ネットワーク設定**
   - Selenium Grid URL: `http://selenium:4444/wd/hub`
   - コンテナ内からのみアクセス可能

### よくある間違い

```bash
# ❌ 間違い：ホストマシンで直接実行
python3 /var/www/japandatascience.com/timeline-mapping/api/google_maps_unified.py

# ❌ 間違い：パスの指定ミス
docker exec vps_project-scraper-1 python google_maps_unified.py

# ✅ 正解：コンテナ内での完全パス指定
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_unified.py
```

### パスのマッピング

| ホストマシン | Dockerコンテナ内 |
|------------|----------------|
| `/var/www/japandatascience.com/` | `/app/output/japandatascience.com/` |

### デバッグ時のコツ

```bash
# コンテナ内でインタラクティブに作業
docker exec -it vps_project-scraper-1 bash

# コンテナ内で環境を確認
cd /app/output/japandatascience.com/timeline-mapping/api/
ls -la
python --version
```

### タイムアウト対策

長時間実行されるスクリプトの場合：

```bash
# タイムアウトを設定（例：5分）
timeout 300 docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/スクリプト名.py
```

### トラブルシューティング

1. **"No such file or directory"エラー**
   - パスが正しいか確認
   - `/app/output/`から始まるパスを使用

2. **"selenium.common.exceptions.WebDriverException"エラー**
   - Dockerコンテナ内で実行しているか確認
   - Selenium Gridが起動しているか確認

3. **タイムアウトエラー**
   - スクリプトに無限ループがないか確認
   - 適切な待機時間を設定

### 実行例

```bash
# 電車ルート検索
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_final.py "東京駅" "渋谷駅"

# 徒歩ルート検索
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_walking_final.py "東京駅" "渋谷駅"

# デバッグツール実行
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_transfer_debug.py "神田" "神谷町"
```

## 環境変数の扱い

Pythonスクリプトから環境変数を使用する場合：
- .envファイルは `../` にあります（apiディレクトリの親）
- 例：`/var/www/japandatascience.com/timeline-mapping/.env`
- python-dotenvなどを使用して読み込む場合は、パスに注意

```python
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv('../.env')

# APIキーを取得
google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
```

## 重要な注意事項

**必ず上記の方法でPythonスクリプトを実行してください。**
ホストマシンで直接実行すると、Selenium Gridに接続できずエラーになります。