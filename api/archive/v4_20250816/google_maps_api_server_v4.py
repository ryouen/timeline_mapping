#!/usr/bin/env python3
"""
Google Maps Transit Scraping API Server v4
HTTPサービスとしてGoogle Maps経路検索機能を提供
v4スクレイパー統合版
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
import uvicorn
import json
import traceback
from datetime import datetime, timedelta
import os
import sys
import pytz

# v4スクレイピングモジュールをインポート
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper_v4_complete import GoogleMapsScraperV4

app = FastAPI(title="Google Maps Transit API v4", version="4.0.0")

# グローバルスクレイパーインスタンス（再利用）
scraper = None

class TransitRequest(BaseModel):
    origin: str
    destination: str
    arrival_time: Optional[str] = None
    days_ahead: Optional[int] = None  # 何日後か（0=今日, 1=明日）
    target_time: Optional[str] = None  # "10:00"形式の時刻
    
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

@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    selenium_status = "ready" if scraper and scraper.driver else "not_initialized"
    return {
        "status": "ok",
        "service": "google-maps-transit-api-v4",
        "version": "4.0.0",
        "selenium_status": selenium_status
    }

@app.post("/api/transit")
async def get_transit_route(request: TransitRequest):
    """
    経路検索エンドポイント
    デフォルトは明日の10時到着
    """
    global scraper
    
    try:
        # スクレイパーの初期化（必要に応じて）
        if scraper is None:
            scraper = GoogleMapsScraperV4()
            scraper.setup_driver()
            print("Scraper initialized")
        
        # 到着時刻の処理
        arrival_time = None
        if request.arrival_time:
            if request.arrival_time != 'now':
                # 文字列から datetime オブジェクトに変換
                arrival_time = datetime.strptime(request.arrival_time, '%Y-%m-%d %H:%M:%S')
                arrival_time = pytz.timezone('Asia/Tokyo').localize(arrival_time)
        
        # days_aheadまたはtarget_timeが指定されている場合の処理
        if request.days_ahead is not None or request.target_time:
            # get_arrival_timeメソッドを使用（存在する場合）
            if hasattr(scraper, 'get_arrival_time'):
                arrival_time = scraper.get_arrival_time(request.target_time, request.days_ahead)
        
        # デフォルトは明日の10時
        if arrival_time is None:
            jst = pytz.timezone('Asia/Tokyo')
            tomorrow = datetime.now(jst) + timedelta(days=1)
            arrival_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        print(f"Route search: {request.origin} -> {request.destination}")
        print(f"Arrival time: {arrival_time.strftime('%Y-%m-%d %H:%M')}")
        
        # スクレイピング実行
        result = scraper.scrape_route(
            origin_address=request.origin,
            dest_address=request.destination,
            arrival_time=arrival_time,
            target_time=request.target_time if hasattr(scraper, 'get_arrival_time') else None,
            days_ahead=request.days_ahead if hasattr(scraper, 'get_arrival_time') else None
        )
        
        if result['success']:
            # APIレスポンス形式に変換
            response = {
                "status": "success",
                "route": {
                    "total_time": result['travel_time'],
                    "route_type": result.get('route_type', '公共交通機関'),
                    "departure_time": result.get('departure_time'),
                    "arrival_time": result.get('arrival_time'),
                    "fare": result.get('fare'),
                    "details": {
                        "walk_to_station": 5,  # デフォルト値
                        "station_used": "神田",
                        "trains": [],
                        "walk_from_station": 5,
                        "wait_time_minutes": 3
                    }
                }
            }
            
            # 追加情報
            if 'all_routes' in result:
                response['alternative_routes'] = [
                    {
                        "travel_time": r['travel_time'],
                        "route_type": r.get('route_type'),
                        "departure_time": r.get('departure_time'),
                        "arrival_time": r.get('arrival_time')
                    }
                    for r in result['all_routes'][:3]
                ]
            
            return response
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to get route information')
            )
            
    except Exception as e:
        print(f"Error in get_transit_route: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """シャットダウン時のクリーンアップ"""
    global scraper
    if scraper:
        scraper.close()
        print("Scraper closed")

if __name__ == "__main__":
    # サーバー起動
    uvicorn.run(app, host="0.0.0.0", port=8000)