#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for Shizenkan route
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_maps_scraper_v3 import scrape_route
import logging

logging.basicConfig(level=logging.INFO)

# Test the problematic route
origin = "ルフォンプログレ神田"
destination = "至善館"

print(f"Testing: {origin} → {destination}")
print("Expected: Transit route (NOT 6-minute car route)\n")

result = scrape_route(origin, destination, save_debug=True)

if result:
    print(f"\nResult:")
    print(f"Travel time: {result['travel_time']} minutes")
    print(f"Number of routes found: {len(result['all_routes'])}")
    
    # Show all routes
    print("\nAll routes:")
    for i, route in enumerate(result['all_routes']):
        is_transit = route.get('is_transit', True)
        print(f"Route {i+1}: {route['total_time']} min - {'Transit' if is_transit else 'Car'}")
        if route.get('trains'):
            print(f"  Transport: {', '.join(route['trains'][:3])}")
    
    # Check for car routes
    car_routes = [r for r in result['all_routes'] if not r.get('is_transit', True)]
    transit_routes = [r for r in result['all_routes'] if r.get('is_transit', True)]
    
    print(f"\nSummary:")
    print(f"Transit routes: {len(transit_routes)}")
    print(f"Car routes: {len(car_routes)} (should be 0)")
    
    if car_routes:
        print("\n⚠ WARNING: Car routes detected!")
        for route in car_routes:
            print(f"  - {route['total_time']} minutes")
    else:
        print("\n✓ SUCCESS: No car routes detected!")
else:
    print("Failed to get route")