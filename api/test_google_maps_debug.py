#!/usr/bin/env python3
"""
Google Maps Transit スクレイピングのデバッグ版
成功時もスクリーンショットを保存し、取得した情報を詳細に出力
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

def debug_extract_route(driver, origin, destination, arrival_time=None):
    """Extract route with debug information and screenshots"""
    # arrival_time format: 'YYYY-MM-DD HH:MM:SS' or 'now'
    try:
        # Build URL with proper transit parameters
        # Use /data parameter format for more reliable transit routing
        from urllib.parse import quote
        encoded_origin = quote(origin)
        encoded_dest = quote(destination)
        
        # Google Maps transit URL format with arrival time
        if arrival_time and arrival_time != 'now':
            # Convert arrival_time to timestamp for Google Maps
            from datetime import datetime
            try:
                dt = datetime.strptime(arrival_time, '%Y-%m-%d %H:%M:%S')
                # Google Maps uses seconds since epoch for arrival_time parameter
                timestamp = int(dt.timestamp())
                # URL with arrival time
                url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/@35.6762,139.6503,12z/data=!3m1!4b1!4m6!4m5!2m3!6e1!7e2!8j{timestamp}!3e3'
            except:
                # Fallback to default URL
                url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/data=!3m1!4b1!4m2!4m1!3e3'
        else:
            # Default URL without specific time
            url = f'https://www.google.com/maps/dir/{encoded_origin}/{encoded_dest}/data=!3m1!4b1!4m2!4m1!3e3'
        
        print(f"Original URL format:")
        print(f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=transit&hl=ja")
        print(f"\nNew URL format:")
        print(url)
        
        print(f"URL: {url}")
        driver.get(url)
        
        # Wait for route to load
        wait = WebDriverWait(driver, 30)
        
        # Take screenshot after loading
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_dir = '/app/output/japandatascience.com/timeline-mapping/data/debug_screenshots'
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Wait and take initial screenshot
        time.sleep(5)
        screenshot_path = f'{screenshot_dir}/google_maps_loaded_{timestamp}.png'
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: google_maps_loaded_{timestamp}.png")
        
        # Try to find route details
        route_selectors = [
            "section[aria-labelledby*='section-directions-trip']",
            "div[data-trip-index]",
            "div.section-directions-trip-description",
            "[class*='trip-details']",
            "[class*='transit-container']"
        ]
        
        route_element = None
        for selector in route_selectors:
            try:
                route_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"Found route element with selector: {selector}")
                break
            except:
                continue
        
        if not route_element:
            print("Could not find route element")
            return {'status': 'error', 'message': 'Route element not found'}
        
        # Get all text from the route
        route_text = route_element.text
        print("\n=== ROUTE TEXT ===")
        print(route_text)
        print("=== END ROUTE TEXT ===\n")
        
        # Try to find step elements
        step_selectors = [
            "div.section-directions-trip-travel-mode-icon",
            "[class*='directions-mode-group']",
            "[class*='transit-stop']",
            "[role='button'][aria-label*='詳細']",
            "span[jsan*='transit']"
        ]
        
        # Look for all possible step containers
        all_steps = []
        for selector in step_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    for elem in elements:
                        text = elem.text.strip()
                        if text:
                            all_steps.append(text)
                            print(f"  Step text: {text}")
            except:
                continue
        
        # Try to click on the route to expand details
        try:
            route_element.click()
            time.sleep(2)
            
            # Take screenshot after clicking
            screenshot_path2 = f'{screenshot_dir}/google_maps_expanded_{timestamp}.png'
            driver.save_screenshot(screenshot_path2)
            print(f"Screenshot saved after click: google_maps_expanded_{timestamp}.png")
            
            # Get expanded text
            expanded_text = driver.find_element(By.TAG_NAME, 'body').text
            print("\n=== EXPANDED TEXT (first 2000 chars) ===")
            print(expanded_text[:2000])
            print("=== END EXPANDED TEXT ===\n")
            
        except Exception as e:
            print(f"Could not click/expand route: {e}")
        
        # Extract route information with better patterns
        line_patterns = [
            r'([^、\n]*線)',
            r'(JR[^\s]*)',
            r'([^\n]*Line)',
            r'(東京メトロ[^\n]*)',
            r'(都営[^\n]*)',
            r'(東急[^\n]*)',
            r'(小田急[^\n]*)',
            r'(京王[^\n]*)',
            r'(西武[^\n]*)',
            r'(東武[^\n]*)',
            r'(京急[^\n]*)',
            r'(京成[^\n]*)',
        ]
        
        found_lines = []
        for pattern in line_patterns:
            matches = re.findall(pattern, route_text)
            if matches:
                found_lines.extend(matches)
                print(f"Pattern '{pattern}' found: {matches}")
        
        # Station patterns
        station_patterns = [
            r'([^、\s]+駅)',
            r'([^、\s]+[駅站])',
            r'から([^、\n]+)まで',
            r'→\s*([^、\n]+)',
        ]
        
        found_stations = []
        for pattern in station_patterns:
            matches = re.findall(pattern, route_text)
            if matches:
                found_stations.extend(matches)
                print(f"Station pattern '{pattern}' found: {matches}")
        
        # Save debug info
        debug_info = {
            'timestamp': timestamp,
            'origin': origin,
            'destination': destination,
            'route_text': route_text[:1000],  # First 1000 chars
            'found_lines': list(set(found_lines)),
            'found_stations': list(set(found_stations)),
            'all_steps': all_steps[:20],  # First 20 steps
            'screenshots': [
                f"https://japandatascience.com/timeline-mapping/data/debug_screenshots/google_maps_loaded_{timestamp}.png",
                f"https://japandatascience.com/timeline-mapping/data/debug_screenshots/google_maps_expanded_{timestamp}.png"
            ]
        }
        
        return {
            'status': 'success',
            'debug_info': debug_info
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")
        
        # Save error screenshot
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f'{screenshot_dir}/google_maps_error_{timestamp}.png'
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved: google_maps_error_{timestamp}.png")
        except:
            pass
        
        return {
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        }

def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: python test_google_maps_debug.py <origin> <destination> [arrival_time]'
        }))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = sys.argv[3] if len(sys.argv) > 3 else None
    
    driver = None
    try:
        driver = setup_driver()
        result = debug_extract_route(driver, origin, destination, arrival_time)
        print(json.dumps(result, ensure_ascii=False, indent=2))
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