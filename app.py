import os
from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

# 국가별 DuckDuckGo 지역 코드 매핑
DDG_REGIONS = {
    'CN': 'cn-zh', 'VN': 'vn-vi', 'TH': 'th-en', 'ID': 'id-id', # 아시아
    'FR': 'fr-fr', 'DE': 'de-de', 'ES': 'es-es', 'RU': 'ru-ru', # 유럽
    'BR': 'br-pt', 'MX': 'mx-es', 'SA': 'xa-ar'                 # 기타
}

@app.route('/')
def home():
    return send_file('index.html')

def scrape_ddg(term, country_code):
    """덕덕고 라이트 버전을 크롤링하는 만능 함수"""
    region = DDG_REGIONS.get(country_code, 'wt-wt') # 없으면 전세계(wt-wt)
    # 검색어에 'slang meaning'을 붙여서 검색 정확도 높임
    query = f"{term} slang meaning"
    
    url = "https://lite.duckduckgo.com/lite/"
    payload = {'q': query, 'kl': region}
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    results = []
    try:
        res = requests.post(url, data=payload, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 덕덕고 Lite의 결과 테이블 파싱
        rows = soup.select('table:nth-of-type(3) tr')
        
        current_title = ""
        for row in rows:
            # 제목 줄 (링크)
            link_tag = row.select_one('.result-link')
            if link_tag:
                current_title = link_tag.get_text(strip=True)
                current_link = link_tag['href']
                continue
            
            # 요약 줄 (Snippet)
            snippet_tag = row.select_one('.result-snippet')
            if snippet_tag and current_title:
                results.append({
                    'word': current_title, # 검색 결과 제목
                    'definition': snippet_tag.get_text(strip=True), # 요약 내용
                    'example': current_link, # 링크
                    'thumbs_up': 'DuckDuckGo'
                })
                current_title = "" # 초기화
                
                if len(results) >= 5: # 5개만 수집
                    break
    except Exception as e:
        print(f"DDG Error: {e}")
        
    return results

@app.route('/scrape')
def scrape():
    term = request.args.get('term')
    country = request.args.get('country')
    
    if not term:
        return jsonify({'error': 'No term'})

    print(f"⛏️ Mining: {country} - {term}")
    data_list = []

    try:
        # 1. 🇰🇷 한국 (네이버)
        if country == 'KR':
            url = f"https://dict.naver.com/search.dict?dicQuery={urllib.parse.quote(term)}&query={urllib.parse.quote(term)}&target=dict&ie=utf8&query_utf=&isOnlyViewEE="
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('.dic_search_result .search_list li')
            for item in items[:4]:
                word_elem = item.select_one('dt > a')
                mean_elem = item.select_one('dd')
                if word_elem and mean_elem:
                    data_list.append({
                        'word': word_elem.get_text(strip=True),
                        'definition': mean_elem.get_text(strip=True),
                        'example': "https://dict.naver.com/" + word_elem['href'],
                        'thumbs_up': 'Naver'
                    })

        # 2. 🇯🇵 일본 (Weblio)
        elif country == 'JP':
            url = f"https://www.weblio.jp/content/{urllib.parse.quote(term)}"
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            title = soup.select_one('.midashigo')
            desc = soup.select_one('.kiji')
            if title and desc:
                data_list.append({
                    'word': title.get_text(strip=True),
                    'definition': desc.get_text(strip=True)[:200] + "...",
                    'example': url,
                    'thumbs_up': 'Weblio'
                })

        # 3. 🇺🇸 영미권 (Urban Dictionary API)
        elif country in ['US', 'GB', 'AU', 'CA']:
            res = requests.get(f"https://api.urbandictionary.com/v0/define?term={term}")
            data_list = res.json().get('list', [])

        # 4. 🌏 그 외 모든 국가 (DuckDuckGo 만능키)
        else:
            data_list = scrape_ddg(term, country)

    except Exception as e:
        return jsonify({'error': str(e)})

    # 결과가 없으면 프론트에서 처리하도록 빈 리스트 반환
    return jsonify({'mode': 'SCRAPE', 'list': data_list})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
