from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

# 1. 메인 화면 보여주기
@app.route('/')
def home():
    return send_file('index.html')

# 2. 크롤링 API (핵심!)
@app.route('/scrape')
def scrape():
    term = request.args.get('term')
    country = request.args.get('country')
    
    if not term:
        return jsonify({'error': '검색어가 없습니다.'})

    print(f"⛏️ 채굴 시작: {country} - {term}")
    
    data_list = []

    # ----------------------------------
    # 🇰🇷 한국: 네이버 오픈사전 크롤링
    # ----------------------------------
    if country == 'KR':
        # 네이버 오픈사전 검색 URL
        url = f"https://dict.naver.com/search.dict?dicQuery={urllib.parse.quote(term)}&query={urllib.parse.quote(term)}&target=dict&ie=utf8&query_utf=&isOnlyViewEE="
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 검색 결과에서 '단어'와 '뜻' 찾기 (네이버 HTML 구조 분석)
            # dic_search_result 영역 안의 데이터 추출
            results = soup.select('.dic_search_result .search_list li')
            
            for item in results[:5]: # 상위 5개만
                try:
                    # 단어 (dt > a)
                    word_elem = item.select_one('dt > a')
                    word = word_elem.get_text(strip=True) if word_elem else term
                    
                    # 뜻 (dd)
                    mean_elem = item.select_one('dd')
                    meaning = mean_elem.get_text(strip=True) if mean_elem else "뜻을 가져올 수 없습니다."
                    
                    # 링크
                    link = "https://dict.naver.com/" + word_elem['href'] if word_elem else "#"

                    data_list.append({
                        'word': word,
                        'definition': meaning,
                        'example': link, # 예문 대신 링크 저장
                        'thumbs_up': 'Naver'
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"KR Error: {e}")

    # ----------------------------------
    # 🇯🇵 일본: Weblio 사전 (속어/신조어)
    # ----------------------------------
    elif country == 'JP':
        url = f"https://www.weblio.jp/content/{urllib.parse.quote(term)}"
        try:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Weblio 구조 추출
            title = soup.select_one('.midashigo')
            desc = soup.select_one('.kiji')
            
            if title and desc:
                clean_desc = desc.get_text(strip=True)[:200] + "..." # 너무 길면 자름
                data_list.append({
                    'word': title.get_text(strip=True),
                    'definition': clean_desc,
                    'example': url,
                    'thumbs_up': 'Weblio'
                })
        except Exception as e:
             print(f"JP Error: {e}")

    # ----------------------------------
    # 🇺🇸 영미권: Urban Dictionary API (그대로 사용)
    # ----------------------------------
    else: 
        # 이건 프론트엔드에서 처리하거나 여기서 호출해도 됨.
        # 편의상 빈 리스트 리턴하고 프론트엔드가 API 부르게 둠
        pass 

    return jsonify({'list': data_list})

if __name__ == '__main__':
    # 8080 포트에서 실행
    app.run(host='0.0.0.0', port=8080)
