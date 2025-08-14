#!/usr/bin/env python3
"""
Improved parser for Google Maps directions panel text
Extracts structured transit information from the full text
"""

import re
import json
from datetime import datetime

def parse_directions_panel_text(panel_text):
    """
    Parse the full directions panel text to extract route details
    
    Input example:
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
    
    # Clean the text
    lines = [line.strip() for line in panel_text.split('\n') if line.strip()]
    
    # Extract total journey time from header
    total_time = None
    header_pattern = r'(\d+:\d+)[^-]+-\s*(\d+:\d+)\s*[（\(](\d+)\s*分'
    for line in lines[:5]:  # Check first few lines
        match = re.search(header_pattern, line)
        if match:
            start_time = match.group(1)
            end_time = match.group(2)
            total_time = int(match.group(3))
            break
    
    # Find all time entries (HH:MM format)
    time_pattern = r'^(\d{1,2}:\d{2})$'
    time_indices = []
    for i, line in enumerate(lines):
        if re.match(time_pattern, line):
            time_indices.append((i, line))
    
    # Parse each segment between time entries
    segments = []
    for i in range(len(time_indices)):
        start_idx = time_indices[i][0]
        end_idx = time_indices[i+1][0] if i+1 < len(time_indices) else len(lines)
        
        segment_time = time_indices[i][1]
        segment_lines = lines[start_idx+1:end_idx]
        
        segments.append({
            'time': segment_time,
            'content': segment_lines
        })
    
    # Analyze segments to build route
    route_steps = []
    wait_time = None
    station_names = []  # Track all station names
    
    # First pass: collect all station names
    for segment in segments:
        for line in segment['content']:
            if '駅' in line and not any(skip in line for skip in ['徒歩', '約', '分']):
                station_names.append(line)
    
    for i, segment in enumerate(segments):
        content = '\n'.join(segment['content'])
        
        # Check if it's a walking segment
        if '徒歩' in content:
            # Extract walking duration
            walk_match = re.search(r'約?\s*(\d+)\s*分', content)
            walk_duration = int(walk_match.group(1)) if walk_match else 0
            
            # Extract distance
            distance_match = re.search(r'(\d+)\s*m', content)
            distance = int(distance_match.group(1)) if distance_match else 0
            
            # Determine if it's to/from station based on position
            if i == 0:
                step_type = 'walk_to_station'
            elif i == len(segments) - 1:
                step_type = 'walk_from_station'
            else:
                step_type = 'transfer_walk'
            
            route_steps.append({
                'type': step_type,
                'time': segment['time'],
                'duration': walk_duration,
                'distance': distance
            })
        
        # Check if it's a transit segment
        elif any(keyword in content for keyword in ['線', '各停', '急行', '快速', 'JR']):
            # Extract line name
            line_match = re.search(r'([^各停急行快速\n]*線)', content)
            if not line_match:
                # Try alternative patterns
                line_match = re.search(r'(JR[^\n]+)', content)
            
            line_name = line_match.group(1).strip() if line_match else '電車'
            
            # Extract station name (should be in previous line or segment)
            station_name = None
            if '駅' in segment['content'][0]:
                station_name = segment['content'][0]
            elif i > 0 and segments[i-1]['content']:
                for line in reversed(segments[i-1]['content']):
                    if '駅' in line:
                        station_name = line
                        break
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*分', content)
            duration = int(duration_match.group(1)) if duration_match else 0
            
            # Extract number of stops
            stops_match = re.search(r'(\d+)\s*駅', content)
            stops = int(stops_match.group(1)) if stops_match else 0
            
            # Calculate wait time if this is the first transit
            if not wait_time and i > 0:
                # Compare departure time with arrival at station
                if route_steps and route_steps[-1]['type'] == 'walk_to_station':
                    prev_time = segments[i-1]['time']
                    curr_time = segment['time']
                    try:
                        prev_dt = datetime.strptime(prev_time, '%H:%M')
                        curr_dt = datetime.strptime(curr_time, '%H:%M')
                        wait_minutes = int((curr_dt - prev_dt).total_seconds() / 60)
                        wait_time = max(0, wait_minutes)
                    except:
                        wait_time = 0
            
            route_steps.append({
                'type': 'transit',
                'time': segment['time'],
                'line': line_name,
                'from_station': station_name,
                'duration': duration,
                'stops': stops
            })
    
    # Build the final route structure
    trains = []
    walk_to_station = 0
    walk_from_station = 0
    station_used = None
    
    # Check if the last step is walking (walk_from_station)
    if route_steps and route_steps[-1]['type'] in ['transfer_walk', 'walk_from_station']:
        walk_from_station = route_steps[-1]['duration']
    
    for i, step in enumerate(route_steps):
        if step['type'] == 'walk_to_station':
            walk_to_station = step['duration']
        elif step['type'] == 'walk_from_station' and i == len(route_steps) - 1:
            walk_from_station = step['duration']
        elif step['type'] == 'transit':
            # Find the destination station (next station in list)
            to_station = None
            
            # Look for the next station name after this transit segment
            from_station_clean = step['from_station'].replace('駅', '').strip() if step['from_station'] else None
            if from_station_clean:
                # Find the index of current station in station_names list
                for idx, stn in enumerate(station_names):
                    if from_station_clean in stn:
                        # Get the next station in the list
                        if idx + 1 < len(station_names):
                            to_station = station_names[idx + 1]
                        break
            
            if not station_used and step['from_station']:
                station_used = step['from_station'].replace('駅', '').strip()
            
            train = {
                'line': step['line'],
                'time': step['duration'],
                'from': step['from_station'].replace('駅', '').strip() if step['from_station'] else '不明',
                'to': to_station.replace('駅', '').strip() if to_station else '不明'
            }
            
            # Check for transfer (only if there's another transit after the transfer walk)
            if (i + 1 < len(route_steps) and 
                route_steps[i + 1]['type'] == 'transfer_walk' and
                i + 2 < len(route_steps) and
                route_steps[i + 2]['type'] == 'transit'):
                train['transfer_after'] = {
                    'time': route_steps[i + 1]['duration'],
                    'to_line': route_steps[i + 2]['line']
                }
            
            trains.append(train)
    
    return {
        'total_time': total_time,
        'wait_time_minutes': wait_time or 0,
        'walk_to_station': walk_to_station,
        'station_used': station_used or '不明',
        'trains': trains,
        'walk_from_station': walk_from_station
    }

def extract_route_lines(panel_text):
    """Extract just the train lines from the header"""
    lines = []
    
    # Look for lines in the header (first few lines)
    text_lines = panel_text.split('\n')[:10]
    for line in text_lines:
        # Pattern for train lines
        if re.search(r'[線]', line) and len(line) < 50:
            # Extract individual lines
            line_matches = re.findall(r'([^、\s]+線)', line)
            lines.extend(line_matches)
    
    return lines

# Test function
if __name__ == '__main__':
    test_text = """
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
    
    result = parse_directions_panel_text(test_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))