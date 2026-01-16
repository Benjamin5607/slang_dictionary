import os
import random
from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

# ---------------------------------------------------------
# 🎭 인간 코스프레 헤더 (User-Agent)
# ---------------------------------------------------------
def get_random_header():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/'
    }

@app.route('/')
def home():
    try:
        return send_file('index.html')
    except:
        return "index.html 파일을 찾을 수 없습니다."

# ---------------------------------------------------------
# ⛏️ 핵심 엔진: DuckDuckGo Lite 파서
# ---------------------------------------------------------
def scrape_duckduckgo(term, country_code):
    """
    네이버/구글 대신 차단이 덜한 'DuckDuckGo Lite' 버전을 긁습니다.
    """
    base_url = "https://lite.duckduckgo.com/lite/"
    
    # 1. 검색어 전략 (Search Strategy)
    # 한국이면 '나무위키' 내용을 우선적으로 찾도록 유도
    if country_code == 'KR':
        # "중꺾마 site:namu.wiki" 형태로 검색 -> 나무위키 내용만 쏙 뽑아옴
        query = f'site:namu.wiki "{term}"'
    elif country_code == 'JP':
        query = f'{term} とは スラング'
    else:
        query = f'{term} slang meaning'

    payload = {
        'q': query,
        'kl': 'wt-wt' # 지역 제한 해제 (더 많은 결과)
    }
    
    print(f"🕵️ Searching DDG: {query}") # 로그 확인용

    try:
        # 타임아웃 10초로 넉넉하게
        res = requests.post(base_url, data=payload, headers=get_random_header(), timeout=10)
        
        # HTML 파싱
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # DuckDuckGo Lite의 결과는 테이블 구조로 되어 있음
        # table 3번째꺼의 tr들을 가져와야 함
        results = []
        tables = soup.find_all('table')
        
        if len(tables) < 3:
            print("❌ DDG 구조 변경됨 or 차단됨")
            return []

        rows = tables[2].find_all('tr')
        
        current_title = None
        current_link = None

        for row in rows:
            # 1. 제목 줄 (Title)
            link_tag = row.select_one('.result-link')
            if link_tag:
                current_title = link_tag.get_text(strip=True)
                current_link = link_tag['href']
                continue # 다음 줄로 (다음 줄이 요약문임)
            
            # 2. 요약 줄 (Snippet)
            snippet_tag = row.select_one('.result-snippet')
            if snippet_tag and current_title:
                clean_snippet = snippet_tag.get_text(strip=True)
                
                # 나무위키 결과라면 제목에서 ' - 나무위키' 같은거 떼기
                clean_title = current_title.replace(" - 나무위키", "").replace(" - NamuWiki", "")

                results.append({
                    'word': clean_title,
                    'definition': clean_snippet,
                    'example': current_link,
                    'thumbs_up': 'NamuWiki' if country_code == 'KR' else 'Web Search'
                })
                
                # 초기화
                current_title = None
                
                if len(results) >= 5: break

        return results

    except Exception as e:
        print(f"❌ DDG Error: {e}")
        return []

# ---------------------------------------------------------
# 🚀 API 라우트
# ---------------------------------------------------------
@app.route('/scrape')
def scrape():
    term = request.args.get('term')
    country = request.args.get('country')
    
    if not term: return jsonify({'error': 'No term'})

    print(f"🚀 Request: {country} - {term}")
    data_list = []

    # 1. 영미권 (API 사용 - 가장 빠름)
    if country in ['US', 'GB', 'AU', 'CA']:
        try:
            res = requests.get(f"https://api.urbandictionary.com/v0/define?term={term}", timeout=5)
            data_list = res.json().get('list', [])
        except:
            pass # 실패하면 아래 DDG로 넘어감

    # 2. 그 외 모든 국가 (한국 포함) -> DuckDuckGo로 통합 처리
    if not data_list:
        data_list = scrape_duckduckgo(term, country)

    # 3. 그래도 없으면? 
    # 프론트엔드에게 "결과 없음"을 명확히 전달
    if not data_list:
        print("😥 모든 방법 실패. 결과 0개.")
    
    return jsonify({'mode': 'SCRAPE', 'list': data_list})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
