# server.py
import http.server
import socketserver
import urllib.request
import urllib.parse
import json

PORT = 8080

class MyProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 1. '/search' 로 들어오는 요청을 낚아챕니다.
        if self.path.startswith('/search'):
            # URL에서 단어(term) 파싱
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            term = params.get('term', [''])[0]
            
            if not term:
                self.send_error(400, "검색어가 없습니다.")
                return

            print(f"🔍 검색 요청 받음: {term}") # 로그 출력

            # 2. 파이썬이 직접 얼반딕셔너리에 요청 (CORS 없음!)
            target_url = f"https://api.urbandictionary.com/v0/define?term={urllib.parse.quote(term)}"
            try:
                # 브라우저인 척 헤더 속이기 (User-Agent)
                req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = response.read()
                    
                # 3. 결과를 브라우저에게 그대로 전달
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*') # 모든 접근 허용
                self.end_headers()
                self.wfile.write(data)
                print("✅ 데이터 전송 성공!")
                
            except Exception as e:
                print(f"❌ 에러: {e}")
                self.send_error(500, str(e))
                
        else:
            # 나머지 요청은 그냥 index.html 파일을 보여줌
            super().do_GET()

# 서버 실행 (재사용 가능하도록 설정)
with socketserver.TCPServer(("", PORT), MyProxyHandler) as httpd:
    print(f"🚀 서버가 {PORT} 포트에서 시작되었습니다.")
    print("브라우저를 열어 확인하세요.")
    httpd.allow_reuse_address = True
    httpd.serve_forever()
