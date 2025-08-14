// データローダーモジュール
class DataLoader {
    constructor() {
        this.properties = [];
        this.destinations = [];
        this.isLoaded = false;
    }

    // JSONファイルを読み込む
    async loadData() {
        try {
            // 並列でJSONファイルを読み込む
            const [propertiesResponse, destinationsResponse] = await Promise.all([
                fetch('./data/properties.json'),
                fetch('./data/destinations.json')
            ]);
            
            if (!propertiesResponse.ok || !destinationsResponse.ok) {
                throw new Error('データファイルの読み込みに失敗しました');
            }
            
            const propertiesData = await propertiesResponse.json();
            const destinationsData = await destinationsResponse.json();
            
            // destinationsデータを保存
            this.destinationData = destinationsData.destinations;
            
            // データの整形と検証
            this.processData(propertiesData);
            this.isLoaded = true;
            
            return {
                properties: this.properties,
                destinations: this.destinations
            };
        } catch (error) {
            console.error('データの読み込みに失敗しました:', error);
            throw error;
        }
    }

    // データを処理して内部形式に変換
    processData(data) {
        if (!data.properties || !Array.isArray(data.properties)) {
            throw new Error('不正なデータ形式です');
        }

        // 目的地を抽出（重複を除く）
        const destinationSet = new Map();
        
        data.properties.forEach((property, index) => {
            // 物件データを整形
            const processedProperty = {
                id: index,
                name: property.name,
                address: property.address,
                rent: this.parseRent(property.rent),
                rentDisplay: property.rent,
                stations: property.stations || [],
                routes: [],
                total_monthly_travel_time: property.total_monthly_travel_time || 0,
                total_monthly_walk_time: property.total_monthly_walk_time || 0,
                score: 0
            };

            // ルート情報を処理
            if (property.routes && Array.isArray(property.routes)) {
                property.routes.forEach(route => {
                    // 目的地を記録（destinations.jsonから情報を取得）
                    if (!destinationSet.has(route.destination)) {
                        const destInfo = this.findDestinationInfo(route.destination);
                        if (destInfo) {
                            destinationSet.set(route.destination, {
                                id: destInfo.id,
                                name: destInfo.name,
                                owner: destInfo.owner,
                                frequency: destInfo.monthly_frequency || 1,
                                category: destInfo.category
                            });
                        }
                    }

                    // ルート情報を追加
                    processedProperty.routes.push({
                        destination: route.destination,
                        totalTime: route.total_time || route.totalTime,
                        details: route.details
                    });
                });
            }

            this.properties.push(processedProperty);
        });

        // 目的地リストを作成
        this.destinations = Array.from(destinationSet.values());
        
        // 各物件のスコアを計算
        this.calculateScores();
    }

    // 家賃文字列を数値に変換
    parseRent(rentString) {
        if (typeof rentString === 'number') return rentString;
        
        // "280,000円" -> 280000
        const cleaned = rentString.replace(/[^0-9]/g, '');
        return parseInt(cleaned) || 0;
    }

    // destinations.jsonから目的地情報を検索
    findDestinationInfo(destinationName) {
        if (!this.destinationData) return null;
        
        // 名前で直接検索（完全一致）
        const destination = this.destinationData.find(d => d.name === destinationName);
        
        if (!destination) {
            console.warn(`目的地 "${destinationName}" がdestinations.jsonに見つかりません`);
        }
        
        return destination || null;
    }

    // 各物件の総合スコアを計算
    calculateScores() {
        this.properties.forEach(property => {
            let totalScore = 0;
            let routeCount = 0;

            property.routes.forEach(route => {
                const destination = this.destinations.find(d => d.name === route.destination);
                if (destination) {
                    // 移動時間が短いほど高スコア（60分を基準）
                    const timeScore = Math.max(0, 60 - route.totalTime) / 60 * 100;
                    // 訪問頻度で重み付け
                    totalScore += timeScore * destination.frequency;
                    routeCount += destination.frequency;
                }
            });

            // 平均スコアを計算
            property.score = routeCount > 0 ? Math.round(totalScore / routeCount) : 0;
        });
    }

    // フィルタリング機能
    filterProperties(filters = {}) {
        return this.properties.filter(property => {
            // 家賃フィルター
            if (filters.maxRent && property.rent > filters.maxRent) {
                return false;
            }

            // 移動時間フィルター
            if (filters.maxTime) {
                const hasLongRoute = property.routes.some(route => route.totalTime > filters.maxTime);
                if (hasLongRoute) return false;
            }

            // エリアフィルター
            if (filters.area && !property.address.includes(filters.area)) {
                return false;
            }

            return true;
        });
    }

    // ランキング取得
    getRanking(count = 10) {
        return [...this.properties]
            .sort((a, b) => b.score - a.score)
            .slice(0, count);
    }

    // 特定の目的地への移動時間でソート
    sortByDestination(destinationName) {
        return [...this.properties].sort((a, b) => {
            const routeA = a.routes.find(r => r.destination === destinationName);
            const routeB = b.routes.find(r => r.destination === destinationName);
            
            const timeA = routeA ? routeA.totalTime : Infinity;
            const timeB = routeB ? routeB.totalTime : Infinity;
            
            return timeA - timeB;
        });
    }
}

// グローバルインスタンスを作成
window.dataLoader = new DataLoader();