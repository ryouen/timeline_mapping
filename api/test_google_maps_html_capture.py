#!/usr/bin/env python3
"""
Google Maps HTMLソースコード取得・解析ツール
複数のルートパターンでHTMLを保存し、構造を分析
"""

import sys
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re
import os

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=ja')
    
    # Connect to Selenium Grid
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )
    
    return driver

def capture_route_html(driver, origin, destination, arrival_time=None, route_name=""):
    """Capture HTML source code and screenshots for a route"""
    
    try:
        # Build URL with proper transit parameters
        from urllib.parse import quote
        encoded_origin = quote(origin)
        encoded_dest = quote(destination)
        
        # Google Maps transit URL format with arrival time
        if arrival_time and arrival_time != 'now':
            from datetime import datetime as dt
            try:
                datetime_obj = dt.strptime(arrival_time, '%Y-%m-%d %H:%M:%S')
                timestamp = int(datetime_obj.timestamp())
                url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/@35.6762,139.6503,12z/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{timestamp}!3e3'
            except:
                url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/data=!3m1!4b1!4m2!4m1!3e3'
        else:
            url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/data=!3m1!4b1!4m2!4m1!3e3'
        
        print(f"\nProcessing route: {route_name}")
        print(f"URL: {url}")
        
        driver.get(url)
        
        # Wait for route to load
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-trip-index]')))
        time.sleep(5)  # Allow dynamic content to fully load
        
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f'/app/output/japandatascience.com/timeline-mapping/data/html_analysis/{timestamp}_{route_name}'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save initial HTML
        initial_html = driver.page_source
        with open(f'{output_dir}/initial.html', 'w', encoding='utf-8') as f:
            f.write(initial_html)
        print(f"Saved initial HTML: {len(initial_html)} bytes")
        
        # Take screenshot
        screenshot_path = f'{output_dir}/initial_screenshot.png'
        driver.save_screenshot(screenshot_path)
        print(f"Saved initial screenshot")
        
        # Try to click on the first route to expand details
        try:
            route_element = driver.find_element(By.CSS_SELECTOR, '[data-trip-index="0"]')
            route_element.click()
            time.sleep(3)
            
            # Save expanded HTML
            expanded_html = driver.page_source
            with open(f'{output_dir}/expanded.html', 'w', encoding='utf-8') as f:
                f.write(expanded_html)
            print(f"Saved expanded HTML: {len(expanded_html)} bytes")
            
            # Take expanded screenshot
            expanded_screenshot_path = f'{output_dir}/expanded_screenshot.png'
            driver.save_screenshot(expanded_screenshot_path)
            print(f"Saved expanded screenshot")
            
        except Exception as e:
            print(f"Could not expand route: {e}")
        
        # Extract and save relevant HTML sections
        sections_to_extract = {
            'route_panel': '[data-trip-index]',
            'directions_panel': '[role="main"]',
            'trip_details': '.section-directions-trip-description',
            'transit_details': '[class*="transit"]',
            'time_info': '[jsan*="分"]',
            'station_info': '[jsan*="駅"]'
        }
        
        extracted_sections = {}
        for section_name, selector in sections_to_extract.items():
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    extracted_sections[section_name] = []
                    for i, elem in enumerate(elements[:5]):  # Save up to 5 elements
                        html = elem.get_attribute('outerHTML')
                        text = elem.text
                        extracted_sections[section_name].append({
                            'html': html[:1000],  # First 1000 chars
                            'text': text,
                            'tag': elem.tag_name,
                            'classes': elem.get_attribute('class')
                        })
                    print(f"Found {len(elements)} elements for {section_name}")
            except:
                pass
        
        # Save extracted sections as JSON
        with open(f'{output_dir}/extracted_sections.json', 'w', encoding='utf-8') as f:
            json.dump(extracted_sections, f, ensure_ascii=False, indent=2)
        
        # Analyze structure and save findings
        analysis = analyze_html_structure(initial_html, expanded_html, extracted_sections)
        
        with open(f'{output_dir}/analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return {
            'status': 'success',
            'route_name': route_name,
            'output_dir': output_dir.replace('/app/output/japandatascience.com/', ''),
            'files_created': [
                'initial.html',
                'expanded.html',
                'initial_screenshot.png',
                'expanded_screenshot.png',
                'extracted_sections.json',
                'analysis.json'
            ],
            'summary': analysis.get('summary', {})
        }
        
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'route_name': route_name,
            'message': str(e),
            'traceback': traceback.format_exc()
        }

def analyze_html_structure(initial_html, expanded_html, extracted_sections):
    """Analyze HTML structure to find patterns for data extraction"""
    
    analysis = {
        'html_sizes': {
            'initial': len(initial_html),
            'expanded': len(expanded_html)
        },
        'found_patterns': {},
        'potential_selectors': [],
        'summary': {}
    }
    
    # Look for common patterns
    patterns = {
        'route_lines': [
            r'<span[^>]*>([^<]*(?:線|Line)[^<]*)</span>',
            r'aria-label="([^"]*(?:線|Line)[^"]*)"',
            r'<div[^>]*>([^<]*(?:銀座線|丸ノ内線|日比谷線|東西線|千代田線|有楽町線|半蔵門線|南北線|副都心線)[^<]*)</div>'
        ],
        'stations': [
            r'<span[^>]*>([^<]*駅)</span>',
            r'から\s*([^<\s]+)\s*まで',
            r'→\s*([^<\s]+)',
        ],
        'times': [
            r'(\d+)\s*分',
            r'(\d+):(\d+)',
            r'所要時間[：:]\s*(\d+)',
        ],
        'walk_info': [
            r'徒歩\s*(\d+)\s*分',
            r'歩いて\s*(\d+)\s*分',
            r'(\d+)\s*m\s*歩く'
        ]
    }
    
    for pattern_type, pattern_list in patterns.items():
        analysis['found_patterns'][pattern_type] = []
        for pattern in pattern_list:
            matches = re.findall(pattern, expanded_html, re.IGNORECASE)
            if matches:
                # Remove duplicates and limit to 10 items
                unique_matches = list(dict.fromkeys(matches[:10]))
                analysis['found_patterns'][pattern_type].extend(unique_matches)
    
    # Analyze extracted sections
    if extracted_sections:
        # Look for route information in extracted sections
        for section_name, elements in extracted_sections.items():
            for elem in elements:
                text = elem.get('text', '')
                if '線' in text or '駅' in text or '分' in text:
                    analysis['potential_selectors'].append({
                        'section': section_name,
                        'text': text[:100],
                        'classes': elem.get('classes', '')
                    })
    
    # Create summary
    analysis['summary'] = {
        'lines_found': list(set([item for item in analysis['found_patterns'].get('route_lines', []) if isinstance(item, str)])),
        'stations_found': list(set([item for item in analysis['found_patterns'].get('stations', []) if isinstance(item, str)])),
        'times_found': list(set([item for item in analysis['found_patterns'].get('times', []) if isinstance(item, str)])),
        'walk_info_found': list(set([item for item in analysis['found_patterns'].get('walk_info', []) if isinstance(item, str)]))
    }
    
    return analysis

def main():
    """Test multiple route patterns"""
    
    # Define test routes
    test_routes = [
        {
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都中央区日本橋２丁目５−１ 髙島屋三井ビルディング 17階',
            'name': 'kanda_to_shizenkan',
            'expected': '銀座線'
        },
        {
            'origin': '東京都千代田区神田須田町1-20-1',
            'destination': '東京都港区虎ノ門４丁目２−６ 第二扇屋ビル 1F',
            'name': 'kanda_to_kamiyacho',
            'expected': '銀座線→日比谷線'
        },
        {
            'origin': '東京駅',
            'destination': '渋谷駅',
            'name': 'tokyo_to_shibuya',
            'expected': '山手線'
        },
        {
            'origin': '新宿駅',
            'destination': '横浜駅',
            'name': 'shinjuku_to_yokohama',
            'expected': '湘南新宿ライン等'
        }
    ]
    
    # Calculate next Tuesday 10:00
    from datetime import datetime, timedelta
    today = datetime.now()
    days_until_tuesday = (1 - today.weekday() + 7) % 7
    if days_until_tuesday == 0:
        days_until_tuesday = 7
    next_tuesday = today + timedelta(days=days_until_tuesday)
    next_tuesday = next_tuesday.replace(hour=10, minute=0, second=0)
    arrival_time = next_tuesday.strftime('%Y-%m-%d %H:%M:%S')
    
    driver = None
    results = []
    
    try:
        driver = setup_driver()
        
        for route in test_routes:
            result = capture_route_html(
                driver, 
                route['origin'], 
                route['destination'], 
                arrival_time,
                route['name']
            )
            result['expected'] = route['expected']
            results.append(result)
            
            # Wait between routes
            time.sleep(2)
        
        # Save overall summary
        summary = {
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'routes_tested': len(results),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'results': results
        }
        
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'message': str(e)
        }))
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    main()