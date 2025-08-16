#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transit route fix test script
Tests the fixes for ensuring transit routes are returned instead of car routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_maps_scraper_v3 import scrape_route
from datetime import datetime, timedelta
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_shizenkan_route():
    """Test the Shizenkan route that was showing 6 minutes (car) instead of transit"""
    
    # ルフォンプログレ神田 → 至善館
    origin = "ルフォンプログレ神田"
    destination = "至善館"
    
    logger.info("=" * 60)
    logger.info(f"Testing route: {origin} → {destination}")
    logger.info("Expected: Transit route (not 6-minute car route)")
    logger.info("=" * 60)
    
    # 現在時刻で検索
    result = scrape_route(origin, destination, save_debug=True)
    
    if result:
        print(f"\nRoute found:")
        print(f"Origin: {result['origin']}")
        print(f"  Place ID: {result['origin_details'].get('place_id', 'N/A')}")
        print(f"  Coordinates: {result['origin_details'].get('lat', 'N/A')}, {result['origin_details'].get('lng', 'N/A')}")
        print(f"Destination: {result['destination']}")
        print(f"  Place ID: {result['destination_details'].get('place_id', 'N/A')}")
        print(f"  Coordinates: {result['destination_details'].get('lat', 'N/A')}, {result['destination_details'].get('lng', 'N/A')}")
        print(f"Shortest travel time: {result['travel_time']} minutes")
        print(f"URL: {result['url']}")
        
        print(f"\nAll route options found:")
        for i, route in enumerate(result['all_routes']):
            is_transit = route.get('is_transit', True)
            route_type = "transit" if is_transit else "car"
            print(f"  Route {i+1}: {route['total_time']} minutes ({route_type})")
            if route.get('trains'):
                print(f"    Transport: {', '.join(route['trains'][:3])}...")
        
        # Check if we got transit routes
        transit_routes = [r for r in result['all_routes'] if r.get('is_transit', True)]
        if transit_routes:
            print(f"\n✓ Success: Found {len(transit_routes)} transit route(s)")
            if result['travel_time'] < 10:
                print("⚠ Warning: Travel time is very short - please verify it's a transit route")
        else:
            print("\n✗ Error: No transit routes found!")
    else:
        print("Failed to scrape route")

def test_fuchu_route():
    """Test the Fuchu route as a control"""
    
    origin = "東京都千代田区神田須田町1-20-1" 
    destination = "東京都府中市住吉町5-22-5"
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Testing control route: {origin[:20]}... → {destination[:20]}...")
    logger.info("Expected: ~67 minutes transit route")
    logger.info("=" * 60)
    
    # 明日の9時で検索
    tomorrow = datetime.now() + timedelta(days=1)
    departure_9am = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    
    result = scrape_route(origin, destination, departure_time=departure_9am, save_debug=True)
    
    if result:
        print(f"\nRoute found:")
        print(f"Travel time: {result['travel_time']} minutes")
        
        # Check if it's close to expected 67 minutes
        if 60 <= result['travel_time'] <= 75:
            print("✓ Success: Travel time is within expected range (60-75 minutes)")
        else:
            print(f"⚠ Warning: Travel time {result['travel_time']} is outside expected range")

if __name__ == "__main__":
    print("Testing transit route fixes...")
    print("This will test if car routes are properly filtered out\n")
    
    # Test the problematic Shizenkan route
    test_shizenkan_route()
    
    # Test control route
    test_fuchu_route()
    
    print("\nTest complete. Check the debug folder for screenshots and HTML files.")