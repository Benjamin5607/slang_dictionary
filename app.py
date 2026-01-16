import os
import json
import random
from flask import Flask, request, jsonify, send_file
from groq import Groq
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ✅ 시크릿(환경변수)에서 키 가져오기
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# 키가 없을 경우를 대비한 안전장치
if not GROQ_API_KEY:
    print("🚨 경고: GROQ_API_KEY가 설정되지 않았습니다! (Secrets에 등록 필요)")

client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    try:
        return send_file('index.html')
    except:
        return "index.html 파일이 없습니다."

# ⛏️ 정보 수집꾼 (DuckDuckGo Lite)
def mine_info(term, country):
    # 검색어 최적화
    if country == 'KR': query = f'site:namu.wiki "{term}" OR "{term}" 뜻 유래'
    elif country == 'JP': query = f'{term} とは スラング 元ネタ'
    else: query = f'{term} slang meaning origin'

    try:
        url = "https://lite.duckduckgo.com/lite/"
        payload = {'q': query, 'kl': 'wt-wt'}
        # 랜덤 유저 에이전트로 차단 회피
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        res = requests.post(url, data=payload, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        snippets = []
        for row in soup.select('table:nth-of-type(3) tr .result-snippet'):
            snippets.append(row.get_text(strip=True))
            
        return " ".join(snippets[:5])
    except Exception as e:
        print(f"Mining Error: {e}")
        return ""

# 🧠 AI 큐레이터 라우트 (여기가 있어야 404가 안 뜹니다!)
@app.route('/curate')
def curate():
    term = request.args.get('term')
    country = request.args.get('country')
    
    if not term: return jsonify({'error': 'No term'})

    # 1. 정보 수집
    raw_data = mine_info(term, country)
    
    # 2. AI에게 요약 지시
    # "웹사이트 언어 설정"은 프론트엔드에서 처리하므로, AI는 항상 JSON만 주면 됨
    prompt = f"""
    You are a professional Slang Curator.
    Analyze the raw data and explain the slang "{term}" ({country}).
    
    [RAW DATA]
    {raw_data}
    [END DATA]

    Return strictly a JSON object with these fields:
    {{
        "definition": "Simple definition (explain in Korean if term is KR, otherwise in English)",
        "origin": "Origin/Nuance/Usage caution (explain in Korean if term is KR, otherwise in English)",
        "example": "A realistic conversation example in original language"
    }}
    
    If raw data is empty, use your own LLM knowledge.
    Only return JSON string. No markdown.
    """

    try:
        if not GROQ_API_KEY:
            raise Exception("API Key Missing")

        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        ai_response = chat.choices[0].message.content
        
        clean_json = ai_response.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        return jsonify({'status': 'ok', 'data': result})
        
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({'status': 'error', 'msg': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
