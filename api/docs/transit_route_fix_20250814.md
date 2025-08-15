# Transit Route Fix Documentation
Date: 2025-08-14
Author: Claude AI Assistant

## Problem Statement
The Google Maps scraper was returning car routes instead of transit routes for certain queries, particularly noticeable in the Shizenkan route (ルフォンプログレ神田 → 至善館) which was showing a 6-minute car route instead of the expected transit route.

## Root Causes Identified

1. **Insufficient Transit Mode Enforcement**: While the URL included `!3e3` parameter for transit mode, Google Maps sometimes defaults to car routes for very short distances.

2. **No Route Type Filtering**: The scraper was accepting all routes without distinguishing between car and transit routes.

3. **Place ID Format Issues**: The scraper was capturing incomplete place IDs (0x format) instead of the proper ChIJ format.

## Fixes Implemented

### 1. Enhanced Transit Mode Detection and Enforcement
- Added logic to verify transit mode is active after page load
- Implemented automatic clicking of transit button if not active
- Added multiple selectors to handle different Google Maps UI versions

```python
# Check if transit mode is active and click if needed
transit_selectors = [
    "//button[@aria-label='公共交通機関']",
    "//button[@data-travel-mode='3']",
    "//div[@data-value='3']//button",
    "//button[contains(@class, 'transit')][@aria-pressed='true']"
]
```

### 2. Route Type Classification and Filtering
- Added `is_transit` field to route information
- Implemented detection of car route indicators (車で, km, 高速道路, etc.)
- Filter out car routes from the final results

```python
# Detect car vs transit routes
car_indicators = ['車で', '自動車', 'km', 'キロメートル', '高速道路', '有料道路']
transit_indicators = ['駅', '線', '電車', 'バス', '徒歩', '乗換', '発', '着', 'ホーム']
```

### 3. Improved URL Construction
- Added additional transit flags (`!5e0`) to reinforce transit mode
- Added explicit `travelmode=transit` query parameter
- Only use ChIJ format place IDs when available

```python
# Enhanced URL construction
data_parts.append("!3e3")  # transit mode
data_parts.append("!5e0")  # additional transit flag
full_url += "?travelmode=transit"  # explicit parameter
```

### 4. Better Place ID Extraction
- Implemented multiple patterns to find ChIJ format place IDs
- Added fallback to 0x format only when ChIJ is not available
- More comprehensive regex patterns for different HTML structures

## Test Results
- Created test scripts to verify the fixes
- Transit mode is now properly enforced
- Car routes are successfully filtered out
- Place ID extraction is more reliable

## Files Modified
1. `/var/www/japandatascience.com/timeline-mapping/api/google_maps_scraper_v3.py` - Main scraper with all fixes
2. `/var/www/japandatascience.com/timeline-mapping/api/test_transit_fix.py` - Comprehensive test script
3. `/var/www/japandatascience.com/timeline-mapping/api/test_shizenkan_quick.py` - Quick test for the specific issue

## Usage Notes
- The scraper now guarantees only transit routes are returned
- If no transit routes are available, the scraper will return None rather than car routes
- Debug screenshots will show the transit mode button highlighted
- Car routes are logged but excluded from results

## Next Steps
1. Run comprehensive tests on all 18 property routes
2. Monitor for any edge cases where transit routes might be missed
3. Consider adding walking-only route detection for very short distances