# json-generator.html エラー分析

## エラー発生状況
- 日時: 2025-08-12
- 症状: json-generator.htmlでルート検索を実行した際、3件のエラーが発生
- エラーの詳細: ブラウザのコンソールログで確認が必要

## エラー確認方法

### 1. ブラウザのコンソールログから確認
json-generator.htmlのエラーハンドリング:
- 成功/失敗カウント: `successfulRoutes` / `failedRoutes`
- エラーログ: `console.error('Route search failed for ${property.name} -> ${destination.name}:', error)`
- 警告ログ: `console.warn('No route found for ${property.name} -> ${destination.name}')`

### 2. ローカルストレージの確認
```javascript
// ブラウザのコンソールで実行
const saved = localStorage.getItem('timeline_data');
if (saved) {
    const data = JSON.parse(saved);
    console.log('保存されたデータ:', data);
    
    // エラーになった可能性のあるルートを特定
    data.properties.forEach(property => {
        console.log(`物件: ${property.name}`);
        console.log(`  ルート数: ${property.routes ? property.routes.length : 0}`);
        if (property.routes) {
            property.routes.forEach(route => {
                console.log(`  - ${route.destination_name}: ${route.total_time}分`);
            });
        }
    });
}
```

## 考えられるエラー原因

### 1. タイムアウト
- 現在の設定: APIタイムアウト30秒
- 一部のルート検索が30秒を超える可能性

### 2. 住所の解析エラー
- 全角・半角の混在
- 特殊文字（例: １−２０−１）
- 長い住所（ビル名含む）
- 曖昧な住所

### 3. APIサーバーの問題
- Seleniumのメモリ不足
- 同時接続数の制限
- Google Mapsの一時的なブロック

## デバッグ用スクリプト

### エラーログを詳細に記録する改良版
```javascript
// json-generator.htmlに追加する改良版エラーハンドリング
const errorLog = [];

async function searchSingleRouteWithLogging(origin, destination, destinationId, destinationName) {
    const startTime = Date.now();
    const logEntry = {
        timestamp: new Date().toISOString(),
        origin: origin,
        destination: destination,
        destinationId: destinationId,
        destinationName: destinationName,
        status: 'pending'
    };
    
    try {
        const route = await searchSingleRoute(origin, destination, destinationId, destinationName);
        const duration = Date.now() - startTime;
        
        logEntry.status = route ? 'success' : 'no_route';
        logEntry.duration = duration;
        logEntry.route = route;
        
        if (!route) {
            console.warn(`No route found: ${origin} -> ${destination} (${duration}ms)`);
        }
        
        return route;
        
    } catch (error) {
        const duration = Date.now() - startTime;
        logEntry.status = 'error';
        logEntry.duration = duration;
        logEntry.error = {
            message: error.message,
            stack: error.stack
        };
        
        console.error(`Route search failed: ${origin} -> ${destination} (${duration}ms)`, error);
        throw error;
        
    } finally {
        errorLog.push(logEntry);
        
        // エラーログをローカルストレージに保存
        localStorage.setItem('timeline_error_log', JSON.stringify(errorLog));
    }
}

// エラーログの確認
function showErrorLog() {
    const saved = localStorage.getItem('timeline_error_log');
    if (saved) {
        const logs = JSON.parse(saved);
        console.table(logs.filter(log => log.status !== 'success'));
    }
}
```

## 推奨対処法

1. **即時対応**
   - ブラウザのコンソールログを確認
   - ローカルストレージのデータを確認
   - 具体的なエラー内容を特定

2. **改善案**
   - タイムアウトを30秒→60秒に延長
   - エラー時の自動リトライ機能追加
   - エラーログの永続化（ファイル保存）
   - 住所の正規化処理追加

3. **デバッグ方法**
   - 問題のあった物件・目的地の組み合わせを個別にテスト
   - APIサーバーのログを詳細に確認
   - Seleniumの動作を直接確認（スクリーンショット取得）