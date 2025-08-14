#!/bin/bash
# Direct test of Google Maps scraping

echo "=== Testing Google Maps Transit Scraping ==="
echo "Test 1: Simple route"
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py "東京都中央区日本橋本町4-14-2" "東京都中央区日本橋2-5-1"

echo -e "\n\nTest 2: Station to station"
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py "東京駅" "渋谷駅"

echo -e "\n\nTest 3: With arrival time (now)"
docker exec vps_project-scraper-1 python /app/output/japandatascience.com/timeline-mapping/api/google_maps_transit_docker.py "新宿駅" "品川駅" "now"