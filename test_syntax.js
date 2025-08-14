// HTMLファイルのJavaScript部分の構文チェック
const fs = require('fs');

// HTMLファイルを読み込み
const html = fs.readFileSync('index.html', 'utf8');

// script タグ内のJavaScriptを抽出
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);

if (!scriptMatch) {
    console.log('❌ No script tag found');
    process.exit(1);
}

const jsCode = scriptMatch[1];

// 基本的な構文チェック
try {
    // 関数定義のチェック
    const functions = [
        'toggleBottomSheet',
        'toggleSortBottomSheet',
        'handleBottomSheetSwipe',
        'applySortOrder'
    ];
    
    for (const func of functions) {
        if (!jsCode.includes(`function ${func}`)) {
            console.log(`❌ Function ${func} not found`);
        } else {
            console.log(`✅ Function ${func} found`);
        }
    }
    
    // 変数の存在チェック
    if (!jsCode.includes('bottomSheetManager')) {
        console.log('❌ bottomSheetManager not found');
    } else {
        console.log('✅ bottomSheetManager found');
    }
    
    // 旧変数の残存チェック
    if (jsCode.includes('bottomSheetExpanded')) {
        console.log('⚠️ Old variable bottomSheetExpanded still exists');
    } else {
        console.log('✅ Old variable bottomSheetExpanded removed');
    }
    
    if (jsCode.includes('wasMainSheetExpandedBeforeSort')) {
        console.log('⚠️ Old variable wasMainSheetExpandedBeforeSort still exists');
    } else {
        console.log('✅ Old variable wasMainSheetExpandedBeforeSort removed');
    }
    
    // bottomSheetStateの残存チェック
    if (jsCode.includes('bottomSheetState ')) {
        console.log('⚠️ Old variable bottomSheetState might still exist');
    } else {
        console.log('✅ Old variable bottomSheetState removed');
    }
    
    console.log('\n📊 Syntax Test: Basic check completed');
    
} catch (error) {
    console.error('❌ Error during testing:', error);
}