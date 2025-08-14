#!/usr/bin/env python3
"""
Google Maps出力を理想的なJSON形式に変換
details.total_timeは削除（未使用のため）
"""
import json

# 路線名の正規化辞書
LINE_NAME_MAP = {
    "銀座線": "東京メトロ銀座線",
    "丸ノ内線": "東京メトロ丸ノ内線",
    "日比谷線": "東京メトロ日比谷線",
    "東西線": "東京メトロ東西線",
    "千代田線": "東京メトロ千代田線",
    "有楽町線": "東京メトロ有楽町線",
    "半蔵門線": "東京メトロ半蔵門線",
    "南北線": "東京メトロ南北線",
    "副都心線": "東京メトロ副都心線",
    "山手線": "JR山手線",
    "中央線": "JR中央線",
    "京浜東北線": "JR京浜東北線",
    "浅草線": "都営浅草線",
    "三田線": "都営三田線",
    "新宿線": "都営新宿線",
    "大江戸線": "都営大江戸線"
}

def normalize_line_name(line_name):
    """路線名を正規化"""
    if not line_name:
        return line_name
    
    # 既にマッピングに存在する場合はそのまま返す
    if line_name in LINE_NAME_MAP.values():
        return line_name
    
    # マッピングから検索
    for short_name, full_name in LINE_NAME_MAP.items():
        if short_name in line_name:
            return full_name
    
    return line_name

def normalize_station_name(station_name):
    """駅名を正規化（「(東京都)」を追加）"""
    if not station_name:
        return station_name
    
    # 既に「(東京都)」が含まれている場合はそのまま
    if "(東京都)" in station_name:
        return station_name
    
    # 「駅」を削除して「(東京都)」を追加
    cleaned_name = station_name.replace("駅", "")
    return f"{cleaned_name}(東京都)"

def convert_to_properties_format(google_result, destination_id, destination_name):
    """
    Google Maps出力をproperties.json形式に変換
    details.total_timeは含めない（未使用のため）
    """
    
    if google_result.get("status") != "success":
        return None
    
    route = google_result.get("route", {})
    details = route.get("details", {})
    
    # 待ち時間の集計（train内のwait_timeを合計）
    total_wait_time = 0
    for train in details.get("trains", []):
        total_wait_time += train.get("wait_time", 0)
    
    # 最初の電車の待ち時間は含めない（既存のロジックに合わせる）
    if details.get("trains") and len(details.get("trains")) > 0:
        first_train_wait = details.get("trains")[0].get("wait_time", 0)
        total_wait_time = max(0, total_wait_time - first_train_wait)
    
    # 路線情報の正規化
    normalized_trains = []
    for i, train in enumerate(details.get("trains", [])):
        normalized_train = {
            "line": normalize_line_name(train.get("line", "")),
            "time": train.get("time", 0),
            "from": normalize_station_name(train.get("from", "")),
            "to": normalize_station_name(train.get("to", ""))
        }
        
        # 乗り換え情報の処理
        if "transfer_after" in train:
            transfer = train["transfer_after"]
            normalized_train["transfer_after"] = {
                "time": transfer.get("time", 0),
                "to_line": normalize_line_name(transfer.get("to_line", ""))
            }
            
            # 徒歩の場合の特別処理
            if "徒歩" in transfer.get("to_line", ""):
                normalized_train["transfer_after"]["to_line"] = f"徒歩{transfer.get('time', 0)}分"
        
        # 待ち時間は個別には含めない（wait_time_minutesに統合）
        # ただし、初回以外の待ち時間は乗り換え時間として扱う可能性があるため保持
        if i > 0 and train.get("wait_time", 0) > 0:
            # 乗り換え待ち時間として処理する場合のロジック
            pass
        
        normalized_trains.append(normalized_train)
    
    # 最終的な形式に変換
    return {
        "destination": destination_id,
        "destination_name": destination_name,
        "total_time": route.get("total_time", 0),
        "details": {
            # total_timeは削除（未使用のため）
            "walk_to_station": details.get("walk_to_station", 0),
            "station_used": normalize_station_name(details.get("station_used", "")),
            "trains": normalized_trains,
            "walk_from_station": details.get("walk_from_station", 0),
            "wait_time_minutes": total_wait_time
        }
    }

def convert_walking_route(google_result, destination_id, destination_name):
    """徒歩のみのルートを変換"""
    if google_result.get("status") != "success":
        return None
    
    route = google_result.get("route", {})
    details = route.get("details", {})
    
    # 徒歩のみの場合の形式
    return {
        "destination": destination_id,
        "destination_name": destination_name,
        "total_time": route.get("total_time", 0),
        "details": {
            "walk_only": True,
            "walk_time": route.get("total_time", 0),
            "walk_to_station": route.get("total_time", 0),  # 互換性のため
            "distance_meters": details.get("distance_meters", 0),
            "station_used": "",
            "trains": [],
            "walk_from_station": 0,
            "wait_time_minutes": 0
        }
    }

def main():
    """テスト用のメイン関数"""
    # サンプルデータ（神谷町への電車ルート）
    sample_google_result = {
        "status": "success",
        "route": {
            "total_time": 22,
            "details": {
                "walk_to_station": 3,
                "station_used": "神田駅",
                "trains": [
                    {
                        "line": "銀座線",
                        "time": 6,
                        "from": "神田",
                        "to": "銀座",
                        "transfer_after": {
                            "time": 4,
                            "to_line": "日比谷線"
                        }
                    },
                    {
                        "line": "日比谷線",
                        "time": 6,
                        "from": "銀座",
                        "to": "神谷町",
                        "wait_time": 6
                    }
                ],
                "walk_from_station": 3
            }
        }
    }
    
    # 変換実行
    result = convert_to_properties_format(
        sample_google_result,
        "kamiyacho_ee_office",
        "神谷町(EE)"
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()