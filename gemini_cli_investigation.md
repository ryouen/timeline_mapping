# Gemini CLI 調査依頼書

## 🎯 問題の概要
- JSONジェネレーターのPHPファイル（api/generate.php等）がコードとして表示され、実行されない
- phpinfo.phpも同様にコードがそのまま表示される
- Webサーバー設定またはPHP設定に問題がある可能性

## 📋 調査項目

### 1. PHP インストール・設定状況
```bash
# PHP のインストール確認
php --version
which php
php-fpm --version  # Nginx使用時

# PHP モジュール確認
php -m | grep -E "(apache|fpm|cgi)"

# PHP設定ファイル確認
php --ini
```

### 2. Webサーバー確認
```bash
# Apache の場合
systemctl status apache2
apache2 -v
apache2ctl -M | grep php
a2enmod php  # PHPモジュールが無効の場合

# Nginx の場合
systemctl status nginx
nginx -v
systemctl status php-fpm  # PHP-FPMの状態確認
```

### 3. サイト設定ファイル確認
```bash
# Apache Virtual Host 設定
cat /etc/apache2/sites-available/japandatascience.com.conf
# または
cat /etc/apache2/sites-available/000-default.conf

# Nginx サイト設定
cat /etc/nginx/sites-available/japandatascience.com
cat /etc/nginx/sites-available/default
```

### 4. ディレクトリ・権限確認
```bash
# 権限確認
ls -la /var/www/japandatascience.com/
ls -la /var/www/japandatascience.com/timeline-mapping/
ls -la /var/www/japandatascience.com/timeline-mapping/api/

# 所有者確認
stat /var/www/japandatascience.com/timeline-mapping/phpinfo.php
```

### 5. .htaccess 動作確認
```bash
# Apache の場合：AllowOverride 設定確認
cat /etc/apache2/apache2.conf | grep -A 5 -B 5 "AllowOverride"
cat /etc/apache2/sites-available/* | grep -A 5 -B 5 "AllowOverride"
```

### 6. エラーログ確認
```bash
# Apache エラーログ
tail -50 /var/log/apache2/error.log

# Nginx エラーログ
tail -50 /var/log/nginx/error.log

# PHP エラーログ
tail -50 /var/log/php*.log
find /var/log -name "*php*" -type f 2>/dev/null
```

### 7. ネットワーク・プロセス確認
```bash
# Webサーバープロセス確認
ps aux | grep -E "(apache|nginx|php)"

# ポート確認
netstat -tlnp | grep -E ":80|:443"
ss -tlnp | grep -E ":80|:443"
```

### 8. 設定テスト
```bash
# Apache 設定テスト
apache2ctl configtest

# Nginx 設定テスト
nginx -t

# PHP設定テスト
php -l /var/www/japandatascience.com/timeline-mapping/phpinfo.php
```

## 🔧 期待される修正アクション

### Apache + mod_php の場合
1. `a2enmod php8.1` (または適切なバージョン)
2. `systemctl restart apache2`
3. VirtualHost設定でPHPを有効化

### Nginx + PHP-FPM の場合
1. `systemctl start php-fpm`
2. Nginxの設定でPHP処理を追加:
```nginx
location ~ \.php$ {
    fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    include fastcgi_params;
}
```

### 権限問題の場合
```bash
chown -R www-data:www-data /var/www/japandatascience.com/timeline-mapping/
chmod -R 644 /var/www/japandatascience.com/timeline-mapping/*.php
chmod 755 /var/www/japandatascience.com/timeline-mapping/api/
```

## 📊 現在判明している情報

- **サイトURL**: https://japandatascience.com/timeline-mapping/
- **問題**: PHPファイルが実行されずコードが表示される
- **影響範囲**: 
  - `/timeline-mapping/phpinfo.php` → コード表示
  - `/timeline-mapping/api/debug.php` → コード表示
  - `/timeline-mapping/api/generate.php` → 空レスポンス（JSONパースエラー）

## ⚡ 緊急度
**高**: JSONジェネレーター機能がPHPに依存しているため、PHP実行問題の解決が最優先

## 🎯 成功の判定基準
1. `https://japandatascience.com/timeline-mapping/phpinfo.php` でPHP情報が表示される
2. `https://japandatascience.com/timeline-mapping/api/debug.php` で以下が表示される:
```
Step 1: Basic output OK
Step 2: Headers set OK
Step 3: .env file exists
Step 4: .env file read successfully (N lines)
Step 5: GEMINI_API_KEY found: AIzaSyBkHT...
Step 6: POST data length: 0
Step 7: Testing JSON output...
{"test":"success","time":"YYYY-MM-DD HH:MM:SS"}

All steps completed!
```

---
*調査依頼者: Claude Code Assistant*  
*作成日時: 2024-08-09*  
*優先度: 高*