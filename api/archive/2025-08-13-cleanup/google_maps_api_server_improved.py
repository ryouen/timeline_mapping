#!/usr/bin/env python3
"""
Improved Google Maps Transit Scraping API Server
Uses the ultra_parser for more accurate data extraction
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
import uvicorn
import json
import traceback
from datetime import datetime
import os
import sys

# Import the improved scraping module
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_transit_improved import setup_driver, extract_route_details

app = FastAPI(title="Google Maps Transit API (Improved)", version="2.0.0")

class TransitRequest(BaseModel):
    origin: str
    destination: str
    arrival_time: Optional[str] = None
    
    @validator('origin', 'destination')
    def validate_location(cls, v):
        if not v or not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
    
    @validator('arrival_time')
    def validate_arrival_time(cls, v):
        if v is None or v == 'now':
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except:
            raise ValueError('Invalid arrival_time format. Use YYYY-MM-DD HH:MM:SS or "now"')

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    selenium_status: str
    parser_version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """サービスのヘルスチェック"""
    selenium_status = "unknown"
    try:
        driver = setup_driver()
        driver.quit()
        selenium_status = "healthy"
    except:
        selenium_status = "unhealthy"
    
    return {
        "status": "healthy",
        "service": "google-maps-transit-api-improved",
        "version": "2.0.0",
        "selenium_status": selenium_status,
        "parser_version": "ultra_parser_v1"
    }

@app.post("/api/transit/v2")
async def search_transit_v2(request: TransitRequest):
    """改良版Google Maps経路検索エンドポイント"""
    driver = None
    try:
        # Seleniumドライバーを初期化
        driver = setup_driver()
        
        # 経路情報を取得
        result = extract_route_details(
            driver, 
            request.origin, 
            request.destination, 
            request.arrival_time
        )
        
        # サービス情報を追加
        if result['status'] == 'success':
            result['service'] = 'google_maps_scraping_improved'
            result['api_version'] = '2.0.0'
            result['parser_version'] = 'ultra_parser_v1'
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # デバッグモードの場合は詳細なエラー情報を返す
        if os.environ.get('DEBUG', '').lower() == 'true':
            error_detail = {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            raise HTTPException(status_code=500, detail=error_detail)
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# Legacy endpoint for backward compatibility
@app.post("/api/transit")
async def search_transit_legacy(request: TransitRequest):
    """後方互換性のためのレガシーエンドポイント"""
    # v2エンドポイントにリダイレクト
    return await search_transit_v2(request)

if __name__ == "__main__":
    # 開発サーバーとして起動
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,  # 既存のサーバーと競合しないように別ポート
        log_level="info"
    )