#!/usr/bin/env python3
"""
Google Maps スクレイピング検証テスト
ゴールデンファイルテストによる品質保証
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Tuple
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# テストケースの定義
TEST_CASES = [
    {
        "id": "simple_route",
        "name": "シンプルルート（乗り換えなし）",
        "origin": "東京都千代田区神田須田町1-20-1 ルフォンプログレ神田プレミア",
        "destination": "東京都中央区日本橋2-5-1 髙島屋三井ビルディング",
        "modes": ["departure", "arrival"]
    },
    {
        "id": "complex_route",
        "name": "複数乗り換えルート",
        "origin": "東京都千代田区神田須田町1-20-1",
        "destination": "東京都港区六本木6-10-1 六本木ヒルズ",
        "modes": ["departure", "arrival"]
    },
    {
        "id": "long_walk_route",
        "name": "徒歩が長いルート",
        "origin": "東京都中央区佃2丁目22-3",
        "destination": "東京都江東区青海1-1-10 ダイバーシティ東京",
        "modes": ["departure", "arrival"]
    }
]

def create_golden_file_template(test_case: Dict, mode: str) -> Dict:
    """
    ゴールデンファイルのテンプレートを作成
    ユーザーが手動で埋めるための構造を提供
    """
    return {
        "test_info": {
            "test_id": test_case["id"],
            "test_name": test_case["name"],
            "mode": mode,
            "origin": test_case["origin"],
            "destination": test_case["destination"],
            "created_at": datetime.now().isoformat(),
            "verified_manually": False
        },
        "expected_result": {
            "status": "success",
            "search_info": {
                "type": mode,
                "day_of_week": "Thursday",
                "arrival_time": "2025-08-14 10:00:00" if mode == "arrival" else None
            },
            "route": {
                "total_time": 0,  # TODO: 実際の値を入力
                "details": {
                    "wait_time_minutes": 3,
                    "walk_to_station": 0,  # TODO: 実際の値を入力
                    "station_used": "",  # TODO: 実際の駅名を入力
                    "trains": [
                        {
                            "line": "",  # TODO: 路線名を入力
                            "time": 0,  # TODO: 乗車時間を入力
                            "from": "",  # TODO: 出発駅を入力
                            "to": ""  # TODO: 到着駅を入力
                        }
                    ],
                    "walk_from_station": 0  # TODO: 実際の値を入力
                }
            }
        }
    }

def initialize_golden_files():
    """
    ゴールデンファイルディレクトリを作成し、テンプレートを生成
    """
    golden_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/test_golden')
    golden_dir.mkdir(parents=True, exist_ok=True)
    
    for test_case in TEST_CASES:
        for mode in test_case["modes"]:
            filename = f"{test_case['id']}_{mode}.json"
            filepath = golden_dir / filename
            
            if not filepath.exists():
                template = create_golden_file_template(test_case, mode)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                logger.info(f"Created template: {filename}")

def run_scraping(origin: str, destination: str, mode: str) -> Dict:
    """
    スクレイピングを実行して結果を取得
    """
    script_path = '/app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_ultimate.py'
    
    cmd = ['python', script_path, origin, destination]
    
    if mode == "arrival":
        cmd.extend(['arrival', '10AM'])
    else:
        cmd.extend(['departure', '9AM'])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"Scraping failed: {result.stderr}")
            return None
            
        return json.loads(result.stdout)
        
    except subprocess.TimeoutExpired:
        logger.error("Scraping timeout")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {e}")
        logger.debug(f"Response: {result.stdout}")
        return None
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return None

def compare_results(actual: Dict, expected: Dict) -> Tuple[bool, List[str]]:
    """
    実際の結果と期待値を比較（独自実装）
    """
    def normalize_value(value):
        """値の正規化（比較のため）"""
        if value is None or value == "":
            return None
        return value
    
    def compare_dicts(d1: Dict, d2: Dict, path: str = "", exclude_fields: List[str] = None) -> List[str]:
        """再帰的に辞書を比較"""
        if exclude_fields is None:
            exclude_fields = ['datetime', 'extraction_info', 'debug_info']
        
        differences = []
        
        # d1のキーをチェック
        for key in d1:
            if key in exclude_fields:
                continue
                
            current_path = f"{path}.{key}" if path else key
            
            if key not in d2:
                differences.append(f"Missing key in actual: {current_path}")
                continue
            
            v1 = normalize_value(d1[key])
            v2 = normalize_value(d2[key])
            
            if isinstance(v1, dict) and isinstance(v2, dict):
                # 再帰的に辞書を比較
                sub_diffs = compare_dicts(v1, v2, current_path, exclude_fields)
                differences.extend(sub_diffs)
            elif isinstance(v1, list) and isinstance(v2, list):
                # リストを比較（順序も考慮）
                if len(v1) != len(v2):
                    differences.append(f"List length mismatch at {current_path}: expected {len(v1)}, got {len(v2)}")
                else:
                    for i, (item1, item2) in enumerate(zip(v1, v2)):
                        if isinstance(item1, dict) and isinstance(item2, dict):
                            sub_diffs = compare_dicts(item1, item2, f"{current_path}[{i}]", exclude_fields)
                            differences.extend(sub_diffs)
                        elif item1 != item2:
                            differences.append(f"Value mismatch at {current_path}[{i}]: expected {item1}, got {item2}")
            elif v1 != v2:
                differences.append(f"Value mismatch at {current_path}: expected {v1}, got {v2}")
        
        # d2の余分なキーをチェック
        for key in d2:
            if key in exclude_fields:
                continue
            if key not in d1:
                current_path = f"{path}.{key}" if path else key
                differences.append(f"Extra key in actual: {current_path}")
        
        return differences
    
    # 期待される結果と実際の結果を比較
    expected_result = expected.get('expected_result', {})
    differences = compare_dicts(expected_result, actual)
    
    return len(differences) == 0, differences

def validate_data_quality(result: Dict) -> Tuple[bool, List[str]]:
    """
    データ品質の検証（サニティチェック）
    """
    errors = []
    
    if result.get('status') != 'success':
        return False, [f"Status is not success: {result.get('status')}"]
    
    route = result.get('route', {})
    details = route.get('details', {})
    
    # 総所要時間の妥当性
    total_time = route.get('total_time', 0)
    if not (0 < total_time < 300):  # 5時間以内
        errors.append(f"Total time out of range: {total_time} minutes")
    
    # 徒歩時間の妥当性
    walk_to = details.get('walk_to_station', 0)
    walk_from = details.get('walk_from_station', 0)
    
    if walk_to > 30:
        errors.append(f"Walk to station too long: {walk_to} minutes")
    if walk_from > 30:
        errors.append(f"Walk from station too long: {walk_from} minutes")
    
    # 電車情報の検証
    trains = details.get('trains', [])
    if not trains:
        errors.append("No train information found")
    
    for i, train in enumerate(trains):
        if not train.get('line'):
            errors.append(f"Train {i}: Missing line name")
        if not train.get('from') or train['from'] == '不明':
            errors.append(f"Train {i}: Missing from station")
        if not train.get('to') or train['to'] == '不明':
            errors.append(f"Train {i}: Missing to station")
        if not (0 < train.get('time', 0) < 120):
            errors.append(f"Train {i}: Invalid duration {train.get('time')} minutes")
    
    # 時間の整合性
    calculated_total = (
        details.get('wait_time_minutes', 0) +
        walk_to + walk_from +
        sum(train.get('time', 0) for train in trains)
    )
    
    if abs(calculated_total - total_time) > 10:  # 10分以上の差
        errors.append(f"Time mismatch: calculated {calculated_total} vs reported {total_time}")
    
    return len(errors) == 0, errors

def run_validation_tests():
    """
    検証テストを実行
    """
    golden_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/test_golden')
    results_dir = Path('/app/output/japandatascience.com/timeline-mapping/api/test_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    test_summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    for test_case in TEST_CASES:
        for mode in test_case["modes"]:
            test_summary["total"] += 1
            
            # ゴールデンファイルの読み込み
            golden_file = golden_dir / f"{test_case['id']}_{mode}.json"
            if not golden_file.exists():
                logger.warning(f"Golden file not found: {golden_file}")
                test_summary["failed"] += 1
                test_summary["errors"].append(f"{test_case['id']}_{mode}: Golden file not found")
                continue
            
            with open(golden_file, 'r', encoding='utf-8') as f:
                golden_data = json.load(f)
            
            if not golden_data['test_info'].get('verified_manually'):
                logger.warning(f"Golden file not manually verified: {golden_file}")
                test_summary["failed"] += 1
                test_summary["errors"].append(f"{test_case['id']}_{mode}: Not manually verified")
                continue
            
            # スクレイピング実行
            logger.info(f"Running test: {test_case['name']} ({mode})")
            actual_result = run_scraping(
                test_case['origin'],
                test_case['destination'],
                mode
            )
            
            if not actual_result:
                test_summary["failed"] += 1
                test_summary["errors"].append(f"{test_case['id']}_{mode}: Scraping failed")
                continue
            
            # 結果の保存
            result_file = results_dir / f"{test_case['id']}_{mode}_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(actual_result, f, ensure_ascii=False, indent=2)
            
            # データ品質検証
            quality_ok, quality_errors = validate_data_quality(actual_result)
            if not quality_ok:
                logger.warning(f"Data quality issues: {quality_errors}")
            
            # 結果の比較
            match, differences = compare_results(actual_result, golden_data)
            
            if match and quality_ok:
                logger.info(f"✓ Test passed: {test_case['id']}_{mode}")
                test_summary["passed"] += 1
            else:
                logger.error(f"✗ Test failed: {test_case['id']}_{mode}")
                test_summary["failed"] += 1
                
                if differences:
                    logger.error(f"Differences: {differences}")
                    test_summary["errors"].append(f"{test_case['id']}_{mode}: {differences}")
                
                if quality_errors:
                    test_summary["errors"].extend([f"{test_case['id']}_{mode}: {e}" for e in quality_errors])
    
    # サマリーの出力
    print("\n" + "="*50)
    print("VALIDATION TEST SUMMARY")
    print("="*50)
    print(f"Total tests: {test_summary['total']}")
    print(f"Passed: {test_summary['passed']}")
    print(f"Failed: {test_summary['failed']}")
    
    if test_summary['errors']:
        print("\nErrors:")
        for error in test_summary['errors']:
            print(f"  - {error}")
    
    # 結果をファイルに保存
    summary_file = results_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, ensure_ascii=False, indent=2)
    
    return test_summary['failed'] == 0

def main():
    """
    メイン処理
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Maps scraping validation test')
    parser.add_argument('--init', action='store_true', help='Initialize golden files')
    parser.add_argument('--test', action='store_true', help='Run validation tests')
    
    args = parser.parse_args()
    
    if args.init:
        initialize_golden_files()
        print("Golden file templates created. Please fill them with actual data.")
    elif args.test:
        success = run_validation_tests()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()