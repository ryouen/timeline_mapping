# Google Maps Scraper バージョン比較分析
作成日: 2025-08-16

## 基本構成
| 機能 | v5 (623行) | improved (388行) | current (709行) |
|------|------------|------------------|-----------------|
| **構成** | クラス(GoogleMapsScraperV5) | 関数ベース | クラス(GoogleMapsScraper) |
| **行数** | 623 | 388 | 709 |
| **ログレベル** | INFO | DEBUG/INFO切替可能 | INFO |

## v5が持っていて、improved/currentにない機能
| 機能 | v5の実装 | improved | current |
|------|----------|----------|---------|
| **generate_google_maps_timestamp()** | 96-103行: タイムスタンプ生成 | ❌ なし | ❌ なし |
| **build_url_with_timestamp()** | 166-211行: Place ID含むURL構築 | ❌ なし | ❌ なし（類似処理はscrape_route内） |
| **extract_route_details()** | 354-435行: **時刻抽出が動作** | ❌ なし | ❌ _extract_route_info()あるが時刻取得できず |
| **時刻正規表現** | 382-389行: 時刻パターンマッチ | ❌ なし | 607-621行: あるが動作しない |
| **Place ID複数パターン** | 130-141行: 0x形式のみ | ❌ なし | ✅ 124-156行: ChIJ形式も対応 |
| **座標抽出** | 144-149行: lat/lon取得 | ❌ なし | ❌ なし |

## improvedだけが持つ機能（v5/currentにない）
| 機能 | improved実装 | v5 | current | 重要度 |
|------|-------------|-----|---------|--------|
| **normalize_id()** | 32-36行: ID正規化 | ❌ なし | ❌ なし | 低 |
| **extract_route_from_expanded_trip()** | 100-229行: 展開済み旅程から抽出 | ❌ なし | ❌ なし | **高** |
| **save_debug_info()** | 231-255行: デバッグ情報保存 | ❌ なし | ❌ なし | 中 |
| **ステップ要素詳細解析** | 136-222行: 複数路線対応 | ❌ なし | ❌ なし | **高** |
| **駅名抽出** | 182-183行: 駅パターン | ❌ なし | ❌ なし | 中 |
| **departure_time抽出** | 196-202行: trainInfo内 | ❌ なし | ❌ なし | **高** |

## currentだけが持つ機能（v5/improvedにない） 
| 機能 | current実装 | v5 | improved | 重要度 |
|------|------------|-----|----------|--------|
| **ChIJ形式Place ID** | 124-128行: 新形式対応 | ❌ 0x形式のみ | ❌ なし | **高** |
| **ビル名削除処理** | 93-102行: 髙島屋など削除 | ❌ なし | ❌ なし | 中 |
| **click_transit_and_set_time_optimized()** | 180-239行: 高速化版 | click_transit_and_set_time() | ❌ なし | 中 |
| **_click_element_fast()** | 241-271行: 動的待機時間 | ❌ なし | ❌ なし | 低 |
| **_input_datetime_fast()** | 273-316行: 高速入力 | ❌ なし | ❌ なし | 低 |
| **_input_field_fast()** | 318-342行: フィールド入力 | ❌ なし | ❌ なし | 低 |
| **implicit wait制御** | 63,187-188行 | ❌ なし | ❌ なし | 低 |
| **メモリ最適化引数** | 50-56行: 詳細設定 | 58-60行: 基本のみ | ❌ なし | 中 |
| **9ルートごと再起動** | 652-657行 | 447-452行: 30ルートごと | ❌ なし | 中 |

## 重要な違い - 時刻抽出部分

### v5 (動作する) - 382-389行
```python
time_pattern = r'(\d{1,2}:\d{2})[^\d]*(?:\([^)]+\)[^\d]*)?\s*-\s*(\d{1,2}:\d{2})'
time_match = re.search(time_pattern, text)
if time_match:
    departure_time = time_match.group(1)
    arrival_time = time_match.group(2)
```
**特徴**: ハイフン区切りの時刻ペアを正確に抽出

### current (動作しない) - 612-619行
```python
time_pattern = r'(\d{1,2}:\d{2})'
time_matches = re.findall(time_pattern, text)
if len(time_matches) >= 2:
    times['departure'] = time_matches[0]
    times['arrival'] = time_matches[-1]
```
**問題**: 単純な時刻パターンのため、関係ない時刻も拾ってしまう

## improvedの駅名・路線名抽出の詳細動作

### improvedの駅名・路線抽出 (165-209行)
```python
# 路線名を抽出
line_patterns = [
    r'([\u4e00-\u9fff]+線)',  # 日本語の線名
    r'(JR[\u4e00-\u9fff]+線)',  # JR線
    r'(京王[\u4e00-\u9fff]+)',  # 京王線など
    r'(地下鉄[\u4e00-\u9fff]+線)'  # 地下鉄線
]

# 駅名を抽出
station_pattern = r'([\u4e00-\u9fff]+駅)'
stations = re.findall(station_pattern, step_text)

if line_name and len(stations) >= 2:
    train_info = {
        'line': line_name,
        'time': duration if duration > 0 else 10,
        'from': stations[0].replace('駅', ''),  # 最初の駅
        'to': stations[-1].replace('駅', '')    # 最後の駅
    }
    
    # 最初の駅を記録
    if not route_info['station_used']:
        route_info['station_used'] = train_info['from']
```

### v5の路線抽出 (396-401行)
```python
# 路線名パターン（「線」「ライン」などを含む）
line_pattern = r'([^\s]+(?:線|ライン|Line))'
line_matches = re.findall(line_pattern, text)
if line_matches:
    train_lines = list(set(line_matches))  # 重複を除去
```

### 違いの分析

| 項目 | improved | v5 | 影響 |
|------|----------|-----|------|
| **路線名パターン** | 4つの詳細パターン | 1つの汎用パターン | improvedの方が正確 |
| **駅名抽出** | ✅ あり（出発駅・到着駅） | ❌ なし | improvedの方が詳細 |
| **複数路線対応** | ✅ trains配列で管理 | ❌ train_lines配列のみ | improvedの方が構造化 |
| **各路線の時間** | ✅ 路線ごとの所要時間 | ❌ 全体時間のみ | improvedの方が詳細 |
| **乗換駅情報** | ✅ station_used記録 | ❌ なし | improvedの方が詳細 |

### improvedのメリット
1. **詳細な路線情報**: 各路線の出発駅・到着駅が分かる
2. **乗換情報**: どの駅で乗り換えるか記録
3. **路線ごとの時間**: 各区間の所要時間を個別管理
4. **構造化データ**: trains配列で複数路線を整理

### improvedのデメリット
1. **複雑性**: 処理が複雑で保守が難しい
2. **前提条件**: ステップ要素が展開されている必要がある
3. **パフォーマンス**: 詳細解析のため処理時間が長い

## 推奨される統合方針

1. **ベース**: v5を使用（時刻抽出が動作する唯一のバージョン）
2. **必須の追加機能**:
   - currentのChIJ形式Place ID対応（新Google Maps必須）
   - currentのビル名削除処理（Place ID精度向上）
3. **検討すべき追加機能**:
   - improvedの駅名・路線詳細抽出（必要に応じて）
   - currentの9ルートごと再起動（メモリ管理改善）

## 気になる点・注意事項

1. **料金抽出の違い**:
   - v5: `r'([\d,]+)\s*円'` - カンマ対応
   - current: `r'¥\s*(\d+)'` - ¥マーク対応だがカンマ非対応
   - **問題**: currentは1,000円以上を正しく抽出できない可能性

2. **WebDriver再起動タイミング**:
   - v5: 30ルートごと
   - current: 9ルートごと（1物件分）
   - **推奨**: currentの9ルートごとの方がメモリ効率的

3. **デバッグ機能**:
   - improvedのsave_debug_info()は開発時に有用
   - 本番環境では不要だが、トラブルシューティング時に便利

4. **Place ID戻り値の違い**:
   - v5: 辞書形式 `{'place_id': xxx, 'lat': yyy, 'lon': zzz}`
   - current: 文字列のみ
   - **影響**: v5の座標情報は地図表示に有用

5. **エラーハンドリング**:
   - v5: 基本的なtry-catch
   - improved: 詳細なトレースバック
   - current: 段階的な復旧試行
   - **推奨**: currentの段階的アプローチが堅牢