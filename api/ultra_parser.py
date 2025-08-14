#!/usr/bin/env python3
"""
Ultra-improved parser using a cleaner approach
Based on the structure: TIME -> LOCATION -> ACTION
"""

import re
import json
from datetime import datetime

def parse_google_maps_panel(panel_text):
    """
    Parse Google Maps directions panel with a structured approach
    """
    lines = [line.strip() for line in panel_text.split('\n') if line.strip()]
    
    # Extract header info
    header_info = extract_header_info(lines[:5])
    
    # Create structured timeline
    timeline = create_timeline(lines)
    
    # Build route from timeline
    route = build_route_from_timeline(timeline)
    
    # Merge with header info
    route.update(header_info)
    
    return route

def extract_header_info(header_lines):
    """Extract total time and line summary from header"""
    info = {
        'total_time': None,
        'lines_summary': []
    }
    
    # Extract total time
    for line in header_lines:
        time_match = re.search(r'[（\(](\d+)\s*分', line)
        if time_match:
            info['total_time'] = int(time_match.group(1))
            break
    
    # Extract line names from header
    for line in header_lines:
        if '線' in line and len(line) < 50:
            # Extract all line names
            line_names = re.findall(r'([^\s、]+線)', line)
            info['lines_summary'].extend(line_names)
    
    return info

def create_timeline(lines):
    """Create a structured timeline of events"""
    timeline = []
    time_pattern = r'^(\d{1,2}:\d{2})$'
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a time marker
        if re.match(time_pattern, line):
            event = {
                'time': line,
                'location': None,
                'action': None,
                'details': []
            }
            
            # Get location (next line after time)
            if i + 1 < len(lines):
                event['location'] = lines[i + 1]
                i += 1
            
            # Get action and details
            i += 1
            while i < len(lines) and not re.match(time_pattern, lines[i]):
                if event['action'] is None:
                    event['action'] = lines[i]
                else:
                    event['details'].append(lines[i])
                i += 1
            
            timeline.append(event)
        else:
            i += 1
    
    return timeline

def build_route_from_timeline(timeline):
    """Build route structure from timeline events"""
    route = {
        'wait_time_minutes': 0,
        'walk_to_station': 0,
        'station_used': None,
        'trains': [],
        'walk_from_station': 0
    }
    
    for i, event in enumerate(timeline):
        action = event['action'] if event['action'] else ''
        location = event['location'] if event['location'] else ''
        
        # Walking segment
        if '徒歩' in action:
            duration = extract_walk_duration(event['details'])
            
            # Determine walk type based on position and surrounding context
            is_first_walk = i <= 1
            is_last_walk = i >= len(timeline) - 2
            
            # Check if there's a train before or after this walk
            has_train_before = False
            has_train_after = False
            
            for j in range(max(0, i-2), i):
                if j < len(timeline) and timeline[j]['action'] and '線' in timeline[j]['action']:
                    has_train_before = True
                    break
            
            for j in range(i+1, min(len(timeline), i+3)):
                if j < len(timeline) and timeline[j]['action'] and '線' in timeline[j]['action']:
                    has_train_after = True
                    break
            
            if is_first_walk and not has_train_before:
                route['walk_to_station'] = duration
            elif is_last_walk and not has_train_after:
                route['walk_from_station'] = duration
            # Otherwise it's a transfer walk
            else:
                # This will be handled as transfer time
                pass
        
        # Transit segment
        elif '線' in action or any(train_keyword in action for train_keyword in ['各停', '急行', '快速', 'JR']):
            # Extract line name
            line_name = extract_line_name(action)
            
            # Current station (from location)
            from_station = clean_station_name(location)
            
            # Find destination station (next event with station)
            to_station = None
            for j in range(i + 1, len(timeline)):
                # Check location for station name
                if timeline[j]['location'] and '駅' in timeline[j]['location']:
                    # Make sure it's not the same station (transfer case)
                    candidate = clean_station_name(timeline[j]['location'])
                    if candidate and candidate != from_station:
                        to_station = candidate
                        break
            
            # Extract duration
            duration = extract_train_duration(event['details'])
            
            # Set station_used if not set
            if not route['station_used'] and from_station:
                route['station_used'] = from_station
            
            # Calculate wait time for first train
            if not route['trains'] and i > 0:
                wait_time = calculate_wait_time(timeline[i-1]['time'], event['time'])
                route['wait_time_minutes'] = wait_time
            
            train = {
                'line': line_name,
                'time': duration,
                'from': from_station,
                'to': to_station or '不明'
            }
            
            # Check for transfer
            if i + 1 < len(timeline) and '徒歩' in timeline[i + 1].get('action', ''):
                transfer_duration = extract_walk_duration(timeline[i + 1]['details'])
                # Check if there's another train after the walk
                if i + 2 < len(timeline):
                    for j in range(i + 2, len(timeline)):
                        future_action = timeline[j].get('action', '')
                        if future_action and '線' in future_action:
                            next_line = extract_line_name(future_action)
                            train['transfer_after'] = {
                                'time': transfer_duration,
                                'to_line': next_line
                            }
                            break
            
            route['trains'].append(train)
    
    return route

def extract_walk_duration(details):
    """Extract walking duration from details"""
    for detail in details:
        match = re.search(r'約?\s*(\d+)\s*分', detail)
        if match:
            return int(match.group(1))
    return 0

def extract_train_duration(details):
    """Extract train ride duration from details"""
    for detail in details:
        # Look for duration not in parentheses (to avoid "4駅乗車")
        if '分' in detail and '駅' not in detail:
            match = re.search(r'(\d+)\s*分', detail)
            if match:
                return int(match.group(1))
    return 0

def extract_line_name(action):
    """Extract train line name from action text"""
    # First try to find specific line patterns
    patterns = [
        r'(東京メトロ[^各停急行快速\s]+線)',
        r'(都営[^各停急行快速\s]+線)',
        r'(JR[^各停急行快速\s]+)',
        r'([^各停急行快速\s]+線)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, action)
        if match:
            return match.group(1).strip()
    
    # Fallback
    if '線' in action:
        # Split by common delimiters and find the part with 線
        parts = re.split(r'[各停急行快速]', action)
        for part in parts:
            if '線' in part:
                return part.strip()
    
    return '電車'

def clean_station_name(location):
    """Clean station name from location string"""
    if not location or '〒' in location:
        return None
    
    # Remove common suffixes
    station = location.replace('駅', '').strip()
    
    # Remove any address info after station name
    station = re.split(r'[、,]', station)[0]
    
    return station

def calculate_wait_time(arrival_time, departure_time):
    """Calculate wait time between arrival and departure"""
    try:
        arr = datetime.strptime(arrival_time, '%H:%M')
        dep = datetime.strptime(departure_time, '%H:%M')
        diff = (dep - arr).total_seconds() / 60
        return max(0, int(diff))
    except:
        return 0

# Test the parser
if __name__ == '__main__':
    # Test case 1: Complex route with transfer
    test_text1 = """
9:35 (火曜日) - 9:58 （23 分）
銀座線  日比谷線 
神田駅から 9:38
180円  7 分
9:35
〒101-0041 東京都千代田区神田須田町１丁目２０−１ 吉川ビル
徒歩
約 3 分、210 m
9:38
神田駅
銀座線各停渋谷行
7 分
（4 駅乗車）
9:45
銀座駅
徒歩
約 1 分
9:49
銀座駅
日比谷線各停中目黒行
6 分
（4 駅乗車）
9:55
神谷町駅
徒歩
約 3 分、170 m
9:58
〒105-0001 東京都港区虎ノ門４丁目２−６
"""
    
    # Test case 2: Simple route
    test_text2 = """
9:50 (火曜日) - 9:57 （7 分）
銀座線
神田駅から 9:53
180円  4 分
9:50
〒101-0041 東京都千代田区神田須田町１丁目２０−１ 吉川ビル
徒歩
約 3 分、210 m
9:53
神田駅
銀座線各停渋谷行
3 分
（2 駅乗車）
9:56
日本橋駅
徒歩
約 1 分、230 m
9:57
日本橋髙島屋三井ビルディング
"""
    
    print("Test Case 1: Complex route with transfer")
    print("=" * 50)
    result = parse_google_maps_panel(test_text1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\nTest Case 2: Simple route")
    print("=" * 50)
    result = parse_google_maps_panel(test_text2)
    print(json.dumps(result, ensure_ascii=False, indent=2))