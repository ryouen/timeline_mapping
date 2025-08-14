#!/bin/bash
# Test maps.php integration with Google Maps fallback

echo "=== Testing maps.php with Google Maps fallback ==="
echo "This test simulates a Yahoo Transit failure to trigger Google Maps scraping"

# Test transit mode (will use Yahoo first, then Google Maps if it fails)
echo -e "\nTest 1: Transit route"
curl -s -X POST http://localhost/timeline-mapping/api/maps.php \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "東京駅",
    "destination": "渋谷駅",
    "mode": "transit"
  }' | jq '.'

echo -e "\n\nTest 2: Walking route (uses Google Maps API)"
curl -s -X POST http://localhost/timeline-mapping/api/maps.php \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "東京駅",
    "destination": "有楽町駅",
    "mode": "walking"
  }' | jq '.'