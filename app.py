from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

@app.route('/')
def home():
    return send_file('index.html')

@app.route('/scrape')
def scrape():
    term = request.args.get('term')
    country = request.args.get('country') # KR, JP, US, VN, FR ...
    
    if not term:
        return jsonify({'error': 'No search term provided'})

    print(f"⛏️ 요청 국가: {country} / 검색어: {term}")
    
    data_list = []
    mode = "SCRAPE" # 기본 모드: 긁어오기

    try:
        # ----------------------------------
        # 1. 🇰🇷 한국 (네이버 오픈사전)
        # ----------------------------------
        if country == 'KR':
            url = f"https://dict.naver.com/search.dict?dicQuery={urllib.parse.quote(term)}&query={urllib.parse.quote(term)}&target=dict&ie=utf8&query_utf=&isOnlyViewEE="
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            results = soup.select('.dic_search_result .search_list li')
            
            for item in results[:3]:
                word_elem = item.select_one('dt > a')
                word = word_elem.get_text(strip=True) if word_elem else term
                mean_elem = item.select_one('dd')
                meaning = mean_elem.get_text(strip=True) if mean_elem else ""
                link = "https://dict.naver.com/" + word_elem['href'] if word_elem else "#"
                
                data_list.append({
                    'word': word,
                    'definition': meaning,
                    'example': link,
                    'thumbs_up': 'Naver'
                })

        # ----------------------------------
        # 2. 🇯🇵 일본 (Weblio)
        # ----------------------------------
        elif country == 'JP':
            url = f"https://www.weblio.jp/content/{urllib.parse.quote(term)}"
            res = requests.get(url)
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

        # ----------------------------------
        # 3. 🇺🇸 영미권 (Urban Dictionary API)
        # ----------------------------------
        elif country in ['US', 'GB', 'AU', 'CA', 'NZ', 'Global']:
            # 파이썬 서버가 대신 API를 호출해줌 (CORS 문제 해결)
            res = requests.get(f"https://api.urbandictionary.com/v0/define?term={term}")
            json_data = res.json()
            data_list = json_data.get('list', [])

        # ----------------------------------
        # 4. 그 외 국가 (아직 채굴기 없음 -> 링크 모드)
        # ----------------------------------
        else:
            mode = "LINK" # 프론트엔드에게 "링크 버튼 띄워줘"라고 신호 보냄
            
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'error': str(e)})

    return jsonify({
        'mode': mode,
        'country': country,
        'list': data_list
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
