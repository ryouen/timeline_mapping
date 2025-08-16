#!/usr/bin/env python3
"""
Google Maps Transit Scraping API Server v5
HTTPサービスとしてGoogle Maps経路検索機能を提供
v5最終版スクレイパー統合版
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

# メインスクレイピングモジュールをインポート
sys.path.append('/app/output/japandatascience.com/timeline-mapping/api')
from google_maps_scraper import GoogleMapsScraper

app = FastAPI(title="Google Maps Transit API v5", version="5.0.0")

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
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                raise ValueError('arrival_time must be ISO format')
        return v

def get_or_create_scraper():
    """スクレイパーインスタンスを取得または作成"""
    global scraper
    if scraper is None:
        print("[API] スクレイパーインスタンスを初期化中...")
        scraper = GoogleMapsScraper()
        scraper.setup_driver()
        print("[API] スクレイパー初期化完了")
    return scraper

def determine_arrival_time(request: TransitRequest):
    """リクエストから到着時刻を決定"""
    jst = pytz.timezone('Asia/Tokyo')
    
    # arrival_timeが指定されている場合（ISO形式）
    if request.arrival_time:
        try:
            dt = datetime.fromisoformat(request.arrival_time.replace('Z', '+00:00'))
            return dt.astimezone(jst)
        except Exception as e:
            print(f"[API] arrival_time解析エラー: {e}")
    
    # days_aheadとtarget_timeが指定されている場合
    now = datetime.now(jst)
    
    if request.days_ahead is not None:
        target_date = now + timedelta(days=request.days_ahead)
    else:
        # デフォルトは明日
        target_date = now + timedelta(days=1)
    
    # 時刻の解析
    if request.target_time:
        try:
            hour, minute = map(int, request.target_time.split(':'))
        except:
            hour, minute = 10, 0
    else:
        # デフォルトは10:00
        hour, minute = 10, 0
    
    arrival_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # 過去の時刻チェック
    if arrival_time < now:
        print(f"[API] 過去の時刻のため明日に変更: {arrival_time}")
        arrival_time = arrival_time + timedelta(days=1)
    
    return arrival_time

@app.post("/api/transit")
async def get_transit_route(request: TransitRequest):
    """
    Google Mapsから公共交通機関のルート情報を取得
    """
    try:
        print(f"[API] リクエスト受信: {request.origin} → {request.destination}")
        
        # 到着時刻を決定
        arrival_time = determine_arrival_time(request)
        print(f"[API] 到着時刻: {arrival_time.strftime('%Y-%m-%d %H:%M')} JST")
        
        # スクレイパーを取得
        scraper = get_or_create_scraper()
        
        # ルート情報をスクレイピング
        result = scraper.scrape_route(
            origin_address=request.origin,
            dest_address=request.destination,
            dest_name=request.destination,  # 簡略化のため目的地名と同じ
            arrival_time=arrival_time
        )
        
        if result.get('success'):
            # 成功レスポンス
            response = {
                "status": "success",
                "data": {
                    "origin": request.origin,
                    "destination": request.destination,
                    "travel_time": result['travel_time'],
                    "departure_time": result.get('departure_time'),
                    "arrival_time": result.get('arrival_time'),
                    "fare": result.get('fare'),
                    "route_type": result['route_type'],
                    "all_routes": result.get('all_routes', []),
                    "place_ids": result.get('place_ids', {}),
                    "from_cache": result.get('from_cache', False)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # キャッシュからの場合はログに記録
            if result.get('from_cache'):
                print(f"[API] ⚡ キャッシュから返却")
            else:
                print(f"[API] ✅ 新規取得: {result['travel_time']}分")
            
            return response
        else:
            # エラーレスポンス
            error_msg = result.get('error', 'ルート情報を取得できませんでした')
            print(f"[API] ❌ エラー: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] システムエラー: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    global scraper
    return {
        "status": "healthy",
        "version": "5.0.0",
        "scraper_initialized": scraper is not None
    }

@app.on_event("shutdown")
async def shutdown_event():
    """シャットダウン時の処理"""
    global scraper
    if scraper:
        print("[API] スクレイパーを終了中...")
        scraper.close()
        scraper = None
        print("[API] スクレイパー終了完了")

if __name__ == "__main__":
    # デバッグ用: 直接実行
    print("Google Maps Transit API v5 を起動中...")
    print("URL: http://localhost:8000")
    print("ドキュメント: http://localhost:8000/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )