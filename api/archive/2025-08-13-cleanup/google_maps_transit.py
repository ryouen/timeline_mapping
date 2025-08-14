#!/usr/bin/env python3
"""
Google Maps Transit Scraping API
Scrapes public transit routes from Google Maps and returns data in Yahoo Transit API compatible format
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

def setup_driver():
    """Setup Chrome driver with remote Selenium Grid"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Connect to Selenium Grid container
    try:
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=options
        )
        return driver
    except Exception as e:
        # Fallback to localhost if container name resolution fails
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',
            options=options
        )
        return driver

def parse_time_string(time_str):
    """Parse time string like '午前9:15' or '9:15 AM' to minutes since midnight"""
    try:
        # Remove Japanese AM/PM markers
        time_str = time_str.replace('午前', '').replace('午後', '').strip()
        
        # Parse time
        if '午後' in time_str or 'PM' in time_str:
            hours, minutes = map(int, re.findall(r'\d+', time_str))
            if hours != 12:
                hours += 12
        else:
            hours, minutes = map(int, re.findall(r'\d+', time_str))
            if hours == 12:  # 12 AM is midnight
                hours = 0
                
        return hours * 60 + minutes
    except:
        return 0

def extract_route_details(driver, origin, destination, arrival_time=None):
    """Extract transit route details from Google Maps"""
    
    # Build URL for transit directions
    base_url = "https://www.google.com/maps/dir/"
    url_parts = [base_url, origin, destination]
    url = '/'.join(url_parts) + '/'
    
    # Add transit mode parameter
    url += '@35.6762,139.6503,12z/data=!3m1!4b1!4m2!4m1!3e3'  # 3e3 = transit mode
    
    driver.get(url)
    
    # Wait for directions panel to load
    wait = WebDriverWait(driver, 30)
    
    try:
        # Wait for route options to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-trip-index]')))
        time.sleep(3)  # Allow dynamic content to fully load
        
        # Click on time options if we need to set arrival time
        if arrival_time and arrival_time != 'now':
            try:
                # Click on "Leave now" dropdown
                time_selector = driver.find_element(By.CSS_SELECTOR, '[aria-label*="出発時刻"], [aria-label*="Depart at"], [aria-label*="Leave"]')
                time_selector.click()
                time.sleep(1)
                
                # Select "Arrive by"
                arrive_option = driver.find_element(By.XPATH, "//span[contains(text(), '到着時刻') or contains(text(), 'Arrive by')]")
                arrive_option.click()
                time.sleep(1)
                
                # Set arrival time
                time_input = driver.find_element(By.CSS_SELECTOR, 'input[aria-label*="時刻"], input[aria-label*="Time"]')
                time_input.clear()
                time_input.send_keys(arrival_time.strftime('%H:%M'))
                
                # Click done/search
                done_button = driver.find_element(By.XPATH, "//button[contains(text(), '完了') or contains(text(), 'Done')]")
                done_button.click()
                time.sleep(3)
            except:
                pass  # If time setting fails, continue with default
        
        # Get first (recommended) route
        route_element = driver.find_element(By.CSS_SELECTOR, '[data-trip-index="0"]')
        
        # Extract total time
        total_time_text = route_element.find_element(By.CSS_SELECTOR, '[jsan*="分"], [jsan*="min"]').text
        total_minutes = int(re.findall(r'\d+', total_time_text)[0])
        
        # Click on the route to see details
        route_element.click()
        time.sleep(2)
        
        # Extract detailed segments
        segments = []
        wait_time_minutes = 0
        walk_to_station = 0
        walk_from_station = 0
        station_used = None
        trains = []
        
        # Find all step elements
        steps = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-ved]')
        
        for i, step in enumerate(steps):
            try:
                # Determine step type by icon or text
                step_text = step.text
                
                if '徒歩' in step_text or 'Walk' in step_text or 'walk' in step_text.lower():
                    # Walking segment
                    duration_match = re.search(r'(\d+)\s*分', step_text)
                    if duration_match:
                        walk_time = int(duration_match.group(1))
                        
                        if i == 0:  # First segment - walk to station
                            walk_to_station = walk_time
                        elif i == len(steps) - 1:  # Last segment - walk from station
                            walk_from_station = walk_time
                        else:  # Transfer walk
                            # This will be handled as part of train transfer
                            pass
                            
                elif '電車' in step_text or '地下鉄' in step_text or 'Train' in step_text or 'Subway' in step_text:
                    # Train segment
                    # Extract line name
                    line_match = re.search(r'([^\n]+線[^\n]*|[^\n]+Line[^\n]*)', step_text)
                    line_name = line_match.group(1) if line_match else '不明'
                    
                    # Extract duration
                    duration_match = re.search(r'(\d+)\s*分', step_text)
                    train_time = int(duration_match.group(1)) if duration_match else 10
                    
                    # Extract stations
                    # Look for station names (usually before and after line name)
                    stations = re.findall(r'([^\n]+駅|[^\n]+Station)', step_text)
                    from_station = stations[0] if len(stations) > 0 else '不明'
                    to_station = stations[1] if len(stations) > 1 else '不明'
                    
                    # Clean station names
                    from_station = from_station.replace('駅', '').replace('Station', '').strip()
                    to_station = to_station.replace('駅', '').replace('Station', '').strip()
                    
                    if not station_used:
                        station_used = from_station
                    
                    train_info = {
                        'line': line_name,
                        'time': train_time,
                        'from': from_station,
                        'to': to_station
                    }
                    
                    # Check if next step is a transfer walk
                    if i + 1 < len(steps):
                        next_step = steps[i + 1]
                        next_text = next_step.text
                        if '徒歩' in next_text or 'Walk' in next_text:
                            transfer_match = re.search(r'(\d+)\s*分', next_text)
                            if transfer_match and i + 2 < len(steps):
                                # This is a transfer walk
                                transfer_time = int(transfer_match.group(1))
                                # Look ahead to get the next train line
                                next_train_step = steps[i + 2]
                                next_line_match = re.search(r'([^\n]+線[^\n]*|[^\n]+Line[^\n]*)', next_train_step.text)
                                next_line = next_line_match.group(1) if next_line_match else '不明'
                                
                                train_info['transfer_after'] = {
                                    'time': transfer_time,
                                    'to_line': next_line
                                }
                    
                    trains.append(train_info)
                    
            except Exception as e:
                continue
        
        # If no station was found, try to extract from the route summary
        if not station_used and trains:
            station_used = trains[0]['from']
        
        # Calculate wait time at first station (estimate based on typical wait times)
        # Google Maps doesn't provide exact wait times, so we estimate
        wait_time_minutes = 3  # Default wait time
        
        # Build response in Yahoo Transit API format
        route_details = {
            'wait_time_minutes': wait_time_minutes,
            'walk_to_station': walk_to_station,
            'station_used': station_used,
            'trains': trains,
            'walk_from_station': walk_from_station
        }
        
        # Recalculate total time to match our segments
        recalculated_total = (
            wait_time_minutes + 
            walk_to_station + 
            walk_from_station +
            sum(train['time'] for train in trains) +
            sum(train.get('transfer_after', {}).get('time', 0) for train in trains)
        )
        
        return {
            'status': 'success',
            'search_info': {
                'type': 'departure' if not arrival_time or arrival_time == 'now' else 'arrival',
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A')
            },
            'route': {
                'total_time': recalculated_total,
                'original_total_time': total_minutes,
                'details': route_details
            }
        }
        
    except TimeoutException:
        return {
            'status': 'error',
            'message': 'Timeout waiting for route information'
        }
    except Exception as e:
        # Save screenshot for debugging
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f'/var/www/japandatascience.com/timeline-mapping/api/error_screenshots/google_maps_error_{timestamp}.png'
            driver.save_screenshot(screenshot_path)
        except:
            pass
            
        return {
            'status': 'error',
            'message': f'Error extracting route: {str(e)}',
            'traceback': traceback.format_exc()
        }

def main():
    """Main function to handle command line arguments and execute scraping"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'status': 'error',
            'message': 'Usage: python google_maps_transit.py <origin> <destination> [arrival_time]'
        }))
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    arrival_time = None
    
    if len(sys.argv) > 3:
        if sys.argv[3] == 'now':
            arrival_time = 'now'
        else:
            try:
                arrival_time = datetime.strptime(sys.argv[3], '%Y-%m-%d %H:%M:%S')
            except:
                arrival_time = None
    
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