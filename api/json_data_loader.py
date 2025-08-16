#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONファイルから正確にデータを読み込むためのローダー関数
ハルシネーションを防ぐため、必ずファイルから読み込む
"""

import json
import os
from typing import List, Dict, Optional

class JsonDataLoader:
    """
    properties.jsonとdestinations.jsonから正確にデータを読み込むクラス
    """
    
    def __init__(self, base_path: str = "/app/output/japandatascience.com/timeline-mapping/data"):
        """
        初期化
        
        Args:
            base_path: JSONファイルが格納されているディレクトリのパス
        """
        self.base_path = base_path
        self.properties_file = os.path.join(base_path, "properties_base.json")  # 正しいファイル名
        self.destinations_file = os.path.join(base_path, "destinations.json")
        
        # ファイルの存在確認
        if not os.path.exists(self.properties_file):
            raise FileNotFoundError(f"properties_base.json not found at {self.properties_file}")
        if not os.path.exists(self.destinations_file):
            raise FileNotFoundError(f"destinations.json not found at {self.destinations_file}")
        
        # データを読み込み
        self._load_data()
    
    def _load_data(self):
        """JSONファイルからデータを読み込む"""
        with open(self.properties_file, 'r', encoding='utf-8') as f:
            self.properties_data = json.load(f)
        
        with open(self.destinations_file, 'r', encoding='utf-8') as f:
            self.destinations_data = json.load(f)
        
        print(f"✅ {len(self.properties_data['properties'])}件の物件を読み込みました")
        print(f"✅ {len(self.destinations_data['destinations'])}件の目的地を読み込みました")
    
    def get_all_properties(self) -> List[Dict]:
        """
        すべての物件情報を返す
        
        Returns:
            物件情報のリスト（住所は一文字も変更しない）
        """
        properties = []
        for i, prop in enumerate(self.properties_data['properties']):
            # rentを正規化（カンマと円を除去して数値に）
            rent_str = prop.get('rent', '')
            rent_normalized = 0
            if rent_str:
                # "280,000円" -> 280000
                rent_cleaned = rent_str.replace(',', '').replace('円', '').strip()
                try:
                    rent_normalized = int(rent_cleaned)
                except ValueError:
                    rent_normalized = 0
            
            # properties_base.jsonの実際の構造に合わせる
            properties.append({
                'id': f"property_{i+1}",  # IDは自動生成
                'name': prop.get('name', ''),
                'address': prop.get('address', ''),  # 絶対に変更しない
                'rent': rent_str,  # 元の文字列
                'rent_normalized': rent_normalized,  # 正規化された数値
                'area': prop.get('area', ''),  # 文字列のまま保持
                # properties_base.jsonにないフィールドは空文字列
                'floor': '',
                'building_floors': '',
                'age': '',
                'station_walk': '',
                'url': ''
            })
        return properties
    
    def get_all_destinations(self) -> List[Dict]:
        """
        すべての目的地情報を返す
        
        Returns:
            目的地情報のリスト（住所は一文字も変更しない）
        """
        destinations = []
        for dest in self.destinations_data['destinations']:
            destinations.append({
                'id': dest.get('id', ''),
                'name': dest.get('name', ''),
                'category': dest.get('category', ''),
                'address': dest.get('address', ''),  # 絶対に変更しない
                'owner': dest.get('owner', ''),
                'monthly_frequency': dest.get('monthly_frequency', 0),
                'time_preference': dest.get('time_preference', '')
            })
        return destinations
    
    def get_property_by_index(self, index: int) -> Optional[Dict]:
        """
        インデックスで物件を取得
        
        Args:
            index: 物件のインデックス（0始まり）
        
        Returns:
            物件情報、存在しない場合はNone
        """
        properties = self.get_all_properties()
        if 0 <= index < len(properties):
            return properties[index]
        return None
    
    def get_property_by_name(self, name: str) -> Optional[Dict]:
        """
        名前で物件を検索
        
        Args:
            name: 物件名（部分一致）
        
        Returns:
            最初にマッチした物件情報、見つからない場合はNone
        """
        for prop in self.get_all_properties():
            if name in prop['name']:
                return prop
        return None
    
    def get_destination_by_name(self, name: str) -> Optional[Dict]:
        """
        名前で目的地を検索
        
        Args:
            name: 目的地名（部分一致）
        
        Returns:
            最初にマッチした目的地情報、見つからない場合はNone
        """
        for dest in self.get_all_destinations():
            if name in dest['name']:
                return dest
        return None
    
    def get_unique_property_addresses(self) -> List[Dict]:
        """
        ユニークな物件住所のリストを返す
        
        Returns:
            ユニークな住所とその物件名のリスト
        """
        unique_addresses = {}
        for prop in self.get_all_properties():
            address = prop['address']
            if address not in unique_addresses:
                unique_addresses[address] = {
                    'address': address,
                    'properties': [prop['name']],
                    'count': 1
                }
            else:
                unique_addresses[address]['properties'].append(prop['name'])
                unique_addresses[address]['count'] += 1
        
        return list(unique_addresses.values())
    
    def validate_address(self, address: str, source: str = 'both') -> bool:
        """
        アドレスが正しいJSONデータに存在するか検証
        
        Args:
            address: 検証するアドレス
            source: 'properties', 'destinations', 'both'
        
        Returns:
            アドレスが存在する場合True
        """
        valid = False
        
        if source in ['properties', 'both']:
            for prop in self.get_all_properties():
                if prop['address'] == address:
                    valid = True
                    break
        
        if not valid and source in ['destinations', 'both']:
            for dest in self.get_all_destinations():
                if dest['address'] == address:
                    valid = True
                    break
        
        return valid
    
    def get_test_matrix(self) -> List[Dict]:
        """
        テスト用のマトリックス（物件×目的地）を生成
        
        Returns:
            すべての組み合わせのリスト
        """
        properties = self.get_unique_property_addresses()
        destinations = self.get_all_destinations()
        
        matrix = []
        for prop in properties:
            for dest in destinations:
                matrix.append({
                    'property_address': prop['address'],
                    'property_names': prop['properties'],
                    'destination_name': dest['name'],
                    'destination_address': dest['address'],
                    'destination_category': dest['category']
                })
        
        return matrix
    
    def print_summary(self):
        """データのサマリーを表示"""
        print("\n" + "="*80)
        print("📊 データサマリー")
        print("="*80)
        
        properties = self.get_all_properties()
        destinations = self.get_all_destinations()
        unique_addresses = self.get_unique_property_addresses()
        
        print(f"\n物件数: {len(properties)}件")
        print(f"ユニーク住所数: {len(unique_addresses)}件")
        print(f"目的地数: {len(destinations)}件")
        print(f"テストマトリックス: {len(unique_addresses)} × {len(destinations)} = {len(unique_addresses) * len(destinations)}ルート")
        
        print("\n【物件リスト（最初の5件）】")
        for i, prop in enumerate(properties[:5], 1):
            print(f"  {i}. {prop['name'][:30]:30} - {prop['address'][:40]}...")
        
        print("\n【目的地リスト】")
        for i, dest in enumerate(destinations, 1):
            print(f"  {i}. {dest['name']:20} ({dest['category']:8}) - {dest['address'][:40]}...")
        
        print("\n【重複住所がある物件】")
        for addr_info in unique_addresses:
            if addr_info['count'] > 1:
                print(f"  {addr_info['address'][:40]}...")
                for name in addr_info['properties']:
                    print(f"    - {name}")


# テスト用のメイン関数
if __name__ == "__main__":
    # ローダーのテスト
    loader = JsonDataLoader()
    loader.print_summary()
    
    # 検証テスト
    print("\n【アドレス検証テスト】")
    test_addresses = [
        "東京都千代田区神田須田町１丁目２０−１",  # 正しい
        "東京都中野区中野３丁目４９−１",  # 間違い（私が作った偽住所）
        "東京都新宿区西早稲田１丁目６ 11号館",  # 正しい
    ]
    
    for addr in test_addresses:
        is_valid = loader.validate_address(addr)
        status = "✅ 正しい" if is_valid else "❌ 偽住所"
        print(f"  {status}: {addr[:40]}...")
    
    # 最初の物件×9目的地のテストケース生成
    print("\n【最初の物件のテストケース】")
    first_property = loader.get_property_by_index(0)
    if first_property:
        print(f"物件: {first_property['name']}")
        print(f"住所: {first_property['address']}")
        
        destinations = loader.get_all_destinations()
        print(f"\n{len(destinations)}個の目的地:")
        for i, dest in enumerate(destinations, 1):
            print(f"  {i}. {dest['name']:20} → {dest['address'][:40]}...")