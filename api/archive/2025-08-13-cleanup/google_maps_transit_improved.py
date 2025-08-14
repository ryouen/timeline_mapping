#!/usr/bin/env python3
"""
Improved Google Maps Transit Scraping API
Uses the ultra_parser for accurate data extraction
"""

import json
import sys
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback

# Import the ultra parser functions
from ultra_parser import parse_google_maps_panel

def setup_driver():
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--lang=ja')
    
    # Connect to Selenium Grid container
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    return driver

def extract_route_details(driver, origin, destination, arrival_time=None):
    """Extract transit route details from Google Maps using improved parser"""
    
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
        
        print(f"Accessing URL: {url}", file=sys.stderr)
        driver.get(url)
        
        # Wait for directions panel to load
        wait = WebDriverWait(driver, 30)
        
        # Wait for transit routes to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-trip-index]')))
        time.sleep(5)  # Allow dynamic content to fully load
        
        # Click on the first route to expand details
        try:
            route_element = driver.find_element(By.CSS_SELECTOR, '[data-trip-index="0"]')
            route_element.click()
            time.sleep(3)
        except:
            print("Could not click on route to expand", file=sys.stderr)
        
        # Get the directions panel text
        panel_text = None
        panel_selectors = [
            '[role="main"]',
            '.m6QErb.WNBkOb',
            '.directions-mode-group-summary',
            'div[class*="directions"]'
        ]
        
        for selector in panel_selectors:
            try:
                panel_element = driver.find_element(By.CSS_SELECTOR, selector)
                panel_text = panel_element.text
                if panel_text and len(panel_text) > 100:  # Make sure we got substantial text
                    print(f"Found panel text with selector: {selector}, length: {len(panel_text)}", file=sys.stderr)
                    break
            except:
                continue
        
        if not panel_text:
            raise Exception("Could not extract directions panel text")
        
        # Parse the panel text using ultra parser
        try:
            parsed_route = parse_google_maps_panel(panel_text)
            
            # Build response in the expected format
            route_details = {
                'wait_time_minutes': parsed_route.get('wait_time_minutes', 0),
                'walk_to_station': parsed_route.get('walk_to_station', 0),
                'station_used': parsed_route.get('station_used', '不明'),
                'trains': parsed_route.get('trains', []),
                'walk_from_station': parsed_route.get('walk_from_station', 0)
            }
            
            # Calculate total time
            total_time = parsed_route.get('total_time')
            if not total_time:
                # Recalculate from components
                total_time = (
                    route_details['wait_time_minutes'] + 
                    route_details['walk_to_station'] + 
                    route_details['walk_from_station'] +
                    sum(train['time'] for train in route_details['trains']) +
                    sum(train.get('transfer_after', {}).get('time', 0) for train in route_details['trains'])
                )
            
            return {
                'status': 'success',
                'search_info': {
                    'type': 'departure' if not arrival_time or arrival_time == 'now' else 'arrival',
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'day_of_week': datetime.now().strftime('%A'),
                    'lines_summary': parsed_route.get('lines_summary', [])
                },
                'route': {
                    'total_time': total_time,
                    'details': route_details
                }
            }
            
        except Exception as parse_error:
            print(f"Parse error: {str(parse_error)}", file=sys.stderr)
            print(f"Panel text sample: {panel_text[:500]}...", file=sys.stderr)
            raise parse_error
            
    except TimeoutException:
        return {
            'status': 'error',
            'message': 'Timeout waiting for route information'
        }
    except Exception as e:
        # Save screenshot for debugging
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f'/app/output/japandatascience.com/timeline-mapping/data/debug_screenshots/error_{timestamp}.png'
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved: {screenshot_path}", file=sys.stderr)
        except:
            pass
            
        return {
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }

def main():
    """Main function for testing or command line usage"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: python google_maps_transit_improved.py <origin> <destination> [arrival_time]'
        }))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = sys.argv[3] if len(sys.argv) > 3 else None
    
    driver = None
    try:
        driver = setup_driver()
        result = extract_route_details(driver, origin, destination, arrival_time)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }))
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    main()