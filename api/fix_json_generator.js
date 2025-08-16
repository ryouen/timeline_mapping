// json-generator.htmlの修正版generateId関数

// 改善版1: 日本語を保持しつつ、記号のみ処理
function generateIdV2(name) {
    return name.toLowerCase()
        .replace(/[()（）\s]+/g, '_')  // 括弧とスペースをアンダースコアに
        .replace(/_+/g, '_')           // 連続するアンダースコアを1つに
        .replace(/^_|_$/g, '')         // 先頭と末尾のアンダースコアを削除
        .substring(0, 50);             // 50文字まで（日本語対応のため拡張）
}

// 改善版2: 事前定義されたIDマッピングを使用
const PREDEFINED_IDS = {
    'Shizenkan University': 'shizenkan_university',
    '東京アメリカンクラブ': 'tokyo_american_club',
    'axle御茶ノ水': 'axle_ochanomizu',
    'Yawara': 'yawara',
    '神谷町(EE)': 'kamiyacho_ee',
    '早稲田大学': 'waseda_university',
    '東京駅': 'tokyo_station',
    '羽田空港': 'haneda_airport',
    '府中オフィス': 'fuchu_office'
};

function generateIdWithMapping(name) {
    // 事前定義されたIDがあれば使用
    if (PREDEFINED_IDS[name]) {
        return PREDEFINED_IDS[name];
    }
    
    // なければ改善版のID生成を使用
    return generateIdV2(name);
}

// 既存データのID修正関数
function fixExistingDestinations(destinations) {
    return destinations.map(dest => {
        // 正しいIDに修正
        const correctId = generateIdWithMapping(dest.name);
        if (dest.id !== correctId) {
            console.log(`ID修正: ${dest.id} → ${correctId}`);
            dest.id = correctId;
        }
        return dest;
    });
}

// テストコード
function testIdGeneration() {
    const testCases = [
        'Shizenkan University',
        '東京アメリカンクラブ',
        'axle御茶ノ水',
        'Yawara',
        '神谷町(EE)',
        '早稲田大学',
        '東京駅',
        '羽田空港',
        '府中オフィス'
    ];
    
    console.log('=== ID生成テスト ===');
    testCases.forEach(name => {
        const oldId = name.toLowerCase()
            .replace(/[^\w\s]/gi, '')
            .replace(/\s+/g, '_')
            .substring(0, 20);
        const newId = generateIdWithMapping(name);
        console.log(`${name}:`);
        console.log(`  旧: ${oldId}`);
        console.log(`  新: ${newId}`);
    });
}

// 実行
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateIdV2,
        generateIdWithMapping,
        fixExistingDestinations,
        PREDEFINED_IDS
    };
}