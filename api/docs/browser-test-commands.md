# ブラウザコンソールで実行するテストコマンド

## 1. LocalStorageの内容確認

```javascript
// LocalStorageのデータを確認
const data = JSON.parse(localStorage.getItem('timeline_data'));
console.log('Destinations:', data.destinations.length);
console.log('Properties:', data.properties.length);
console.log('First property:', data.properties[0]);
```

## 2. 手動でsaveJSONFiles()を実行

```javascript
// 手動保存を実行してレスポンスを確認
(async () => {
    try {
        const result = await saveJSONFiles();
        console.log('Save result:', result);
    } catch (error) {
        console.error('Save error:', error);
    }
})();
```

## 3. fetch直接実行でデバッグ

```javascript
// LocalStorageからデータを取得して直接送信
(async () => {
    const data = JSON.parse(localStorage.getItem('timeline_data'));
    const payload = {
        destinations: { destinations: data.destinations },
        properties: { properties: data.properties }
    };
    
    console.log('Sending payload:', payload);
    
    try {
        const response = await fetch('/timeline-mapping/api/save-debug.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        console.log('Response status:', response.status);
        const result = await response.json();
        console.log('Response data:', result);
    } catch (error) {
        console.error('Fetch error:', error);
    }
})();
```

## 4. デバッグログの確認

実行後、以下のファイルを確認：
```bash
ls -la /var/www/japandatascience.com/timeline-mapping/data/save-debug-*.json
```