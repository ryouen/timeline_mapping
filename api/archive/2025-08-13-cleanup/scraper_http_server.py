#!/usr/bin/env python3
"""
Scraper Container HTTP Server
Dockerコンテナ間通信用のHTTPサーバー
"""
import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class RouteHandler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        """POST リクエストを処理"""
        if self.path == '/route':
            self.handle_route_request()
        elif self.path == '/health':
            self.handle_health_check()
        else:
            self.send_error(404, 'Not Found')
    
    def do_GET(self):
        """GET リクエストを処理"""
        if self.path == '/health':
            self.handle_health_check()
        else:
            self.send_error(404, 'Not Found')
    
    def handle_route_request(self):
        """ルート検索リクエストを処理"""
        try:
            # リクエストボディを読み込み
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # JSONをパース
            request_data = json.loads(post_data.decode('utf-8'))
            origin = request_data.get('origin', '')
            destination = request_data.get('destination', '')
            
            if not origin or not destination:
                self.send_json_response(400, {
                    'status': 'error',
                    'message': 'Origin and destination are required'
                })
                return
            
            # Google Maps スクリプトを実行
            result = self.call_google_maps_script(origin, destination)
            
            # レスポンス送信
            if result['success']:
                self.send_json_response(200, result['data'])
            else:
                self.send_json_response(500, {
                    'status': 'error',
                    'message': result['error']
                })
                
        except json.JSONDecodeError:
            self.send_json_response(400, {
                'status': 'error',
                'message': 'Invalid JSON'
            })
        except Exception as e:
            self.send_json_response(500, {
                'status': 'error',
                'message': str(e)
            })
    
    def handle_health_check(self):
        """ヘルスチェック"""
        self.send_json_response(200, {
            'status': 'healthy',
            'timestamp': time.time()
        })
    
    def call_google_maps_script(self, origin, destination):
        """Google Maps スクリプトを呼び出し"""
        try:
            script_path = '/app/output/japandatascience.com/timeline-mapping/api/google_maps_combined.py'
            
            # スクリプト実行
            cmd = ['python', script_path, origin, destination]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Script failed: {result.stderr}'
                }
            
            # JSON解析
            try:
                data = json.loads(result.stdout)
                return {
                    'success': True,
                    'data': data
                }
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': f'Invalid JSON output: {result.stdout[:200]}'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Script timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_json_response(self, status_code, data):
        """JSON レスポンスを送信"""
        response_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(response_data.encode('utf-8'))))
        self.end_headers()
        
        self.wfile.write(response_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        sys.stderr.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}\n")

def start_server(port=8000):
    """HTTPサーバーを開始"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, RouteHandler)
    
    print(f"Starting HTTP server on port {port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Route endpoint: http://localhost:{port}/route")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port)