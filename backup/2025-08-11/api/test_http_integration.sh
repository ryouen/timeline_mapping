#!/bin/bash
# Test HTTP API integration

echo "=== Testing Google Maps Transit HTTP API ==="

echo -e "\n1. Testing API server directly"
curl -s -X POST http://localhost:8000/api/transit \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "東京駅",
    "destination": "渋谷駅",
    "arrival_time": null
  }' | python3 -m json.tool | head -30

echo -e "\n\n2. Testing PHP wrapper (google_maps_transit_http.php)"
curl -s -X POST http://localhost/timeline-mapping/api/google_maps_transit_http.php \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "新宿駅", 
    "destination": "品川駅"
  }' | python3 -m json.tool | head -30

echo -e "\n\n3. Testing health check"
curl -s http://localhost:8000/health | python3 -m json.tool

echo -e "\n\n4. Testing error handling - invalid input"
curl -s -X POST http://localhost:8000/api/transit \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "",
    "destination": "test"
  }' | python3 -m json.tool

echo -e "\n\n5. Testing performance - multiple concurrent requests"
echo "Sending 3 parallel requests..."
for i in {1..3}; do
  (
    time curl -s -X POST http://localhost:8000/api/transit \
      -H "Content-Type: application/json" \
      -d "{
        \"origin\": \"東京タワー\",
        \"destination\": \"スカイツリー\",
        \"arrival_time\": null
      }" > /dev/null && echo "Request $i completed"
  ) &
done
wait

echo -e "\n=== Test Complete ==="