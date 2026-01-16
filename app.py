import os
import random # 랜덤 뽑기용
from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

# ---------------------------------------------------------
# 🎭 인간 코스프레용 가면 (User-Agent 리스트)
# ---------------------------------------------------------
USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Whale (Naver Browser) - 네이버 뚫을 때 효과적
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Whale/3.23.214.17 Safari/537.36",
    # Safari (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

def get_headers(referer_url):
    """
    진짜 사람처럼 보이는 헤더를 생성하는 함수
    """
    return {
        'User-Agent': random.choice(USER_AGENTS), # 가면 랜덤 착용
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7', # 한국인인 척
        'Referer': referer_url, # "나 네이버 메인에서 검색해서 들어온거야"라고 뻥치기
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

@app.route('/')
def home():
    try:
        return send_file('index.html')
    except Exception as e:
        return str(e)

# ---------------------------------------------------------
# ⛏️ 만능 채굴기 (DuckDuckGo)
# ---------------------------------------------------------
def scrape_ddg(term, country_code):
    # 국가별 코드 매핑
    regions = {'KR': 'kr-kr', 'JP': 'jp-jp', 'CN': 'cn-zh', 'VN': 'vn-vi', 
               'FR': 'fr-fr', 'DE': 'de-de', 'ES': 'es-es', 'RU': 'ru-ru', 
               'BR': 'br-pt', 'MX': 'mx-es'}
    region = regions.get(country_code, 'wt-wt')

    suffix = "meaning"
    if country_code == 'KR': suffix = "뜻 의미"
    if country_code == 'JP': suffix = "とは 意味"
    
    url = "https://lite.duckduckgo.com/lite/"
    payload = {'q': f"{term} {suffix}", 'kl': region}
    
    # 여기서도 사람인 척!
    headers = get_headers('https://duckduckgo.com/')
    
    results = []
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table:nth-of-type(3) tr')
        
        current_title = ""
        for row in rows:
            link_tag = row.select_one('.result-link')
            if link_tag:
                current_title = link_tag.get_text(strip=True)
                current_link = link_tag['href']
                continue
            
            snippet_tag = row.select_one('.result-snippet')
            if snippet_tag and current_title:
                results.append({
                    'word': current_title,
                    'definition': snippet_tag.get_text(strip=True),
                    'example': current_link,
                    'thumbs_up': 'Web Search'
                })
                current_title = ""
                if len(results) >= 4: break
    except Exception as e:
        print(f"DDG Error: {e}")
        
    return results

# ---------------------------------------------------------
# 🚀 메인 라우터
# ---------------------------------------------------------
@app.route('/scrape')
def scrape():
    term = request.args.get('term')
    country = request.args.get('country')
    
    if not term: return jsonify({'error': 'No term'})

    print(f"🕵️ Human-like Request: {country} - {term}")
    data_list = []

    try:
        # 1. 🇰🇷 한국 (네이버 오픈사전)
        if country == 'KR':
            try:
                # 네이버는 Referer(이전 주소)를 체크하므로 꼭 넣어줘야 함
                base_url = "https://dict.naver.com/"
                search_url = f"https://dict.naver.com/search.dict?dicQuery={urllib.parse.quote(term)}&query={urllib.parse.quote(term)}&target=dict&ie=utf8&query_utf=&isOnlyViewEE="
                
                # ★ 핵심: 네이버 전용 가면 착용
                headers = get_headers(base_url)
                
                res = requests.get(search_url, headers=headers, timeout=3)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # 선택자 수정 (네이버가 HTML을 자주 바꿔서 넓게 잡음)
                items = soup.select('.search_list li')
                
                for item in items[:4]:
                    dt = item.select_one('dt')
                    dd = item.select_one('dd')
                    
                    if dt and dd:
                        word_text = dt.get_text(strip=True)
                        # 검색어랑 비슷한 것만 가져오기
                        if term in word_text or word_text in term:
                            link_tag = dt.select_one('a')
                            link = "https://dict.naver.com/" + link_tag['href'] if link_tag else "#"
                            
                            data_list.append({
                                'word': word_text,
                                'definition': dd.get_text(strip=True),
                                'example': link,
                                'thumbs_up': 'Naver Dict'
                            })
            except Exception as e:
                print(f"Naver Fail: {e}")
            
            # 실패하면 덕덕고 투입
            if not data_list: data_list = scrape_ddg(term, 'KR')

        # 2. 🇯🇵 일본 (Weblio)
        elif country == 'JP':
            try:
                url = f"https://www.weblio.jp/content/{urllib.parse.quote(term)}"
                headers = get_headers('https://www.google.co.jp/')
                
                res = requests.get(url, headers=headers, timeout=3)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                title = soup.select_one('.midashigo')
                desc = soup.select_one('.kiji')
                
                if title and desc:
                    data_list.append({
                        'word': title.get_text(strip=True),
                        'definition': desc.get_text(strip=True)[:150] + "...",
                        'example': url,
                        'thumbs_up': 'Weblio'
                    })
            except Exception as e:
                print(f"Weblio Fail: {e}")

            if not data_list: data_list = scrape_ddg(term, 'JP')

        # 3. 🇺🇸 영미권 (Urban Dictionary API)
        elif country in ['US', 'GB', 'AU', 'CA']:
            try:
                # API 호출할 때도 헤더 넣으면 더 안전함
                headers = get_headers('https://www.urbandictionary.com/')
                res = requests.get(f"https://api.urbandictionary.com/v0/define?term={term}", headers=headers, timeout=5)
                data_list = res.json().get('list', [])
            except:
                pass

        # 4. 그 외 국가
        else:
            data_list = scrape_ddg(term, country)

    except Exception as e:
        return jsonify({'error': str(e)})

    return jsonify({'mode': 'SCRAPE', 'list': data_list})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
