import os
import json
from flask import Flask, request, jsonify, send_file
from groq import Groq # AI 라이브러리
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔑 여기에 Groq API Key를 붙여넣으세요! (따옴표 안에)
GROQ_API_KEY = "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"

# Groq 클라이언트 준비
client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    try:
        return send_file('index.html')
    except:
        return "index.html 파일이 없습니다."

# 1. ⛏️ 정보 수집꾼 (DuckDuckGo)
def mine_info(term, country):
    print(f"⛏️ 채굴 시작: {term} ({country})")
    
    # 검색어 최적화
    if country == 'KR': query = f'site:namu.wiki "{term}" OR "{term}" 뜻 유래'
    elif country == 'JP': query = f'{term} とは スラング 元ネタ'
    else: query = f'{term} slang meaning origin'

    try:
        url = "https://lite.duckduckgo.com/lite/"
        payload = {'q': query, 'kl': 'wt-wt'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        res = requests.post(url, data=payload, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 검색 결과 텍스트만 싹 긁어모으기
        snippets = []
        for row in soup.select('table:nth-of-type(3) tr .result-snippet'):
            snippets.append(row.get_text(strip=True))
            
        return " ".join(snippets[:5]) # 상위 5개 요약본 합치기
    except:
        return ""

# 2. 🧠 AI 편집장 (Groq)
@app.route('/curate')
def curate():
    term = request.args.get('term')
    country = request.args.get('country')
    
    if not term: return jsonify({'error': 'No term'})

    # 1) 정보 수집
    raw_data = mine_info(term, country)
    
    # 2) AI에게 지시 (프롬프트)
    prompt = f"""
    You are a professional Slang Curator.
    Analyze the raw data below and explain the slang "{term}" ({country}).
    
    [RAW DATA]
    {raw_data}
    [END DATA]

    Output Format (JSON only):
    {{
        "definition": "한 문장으로 핵심 뜻 (한국어로 설명)",
        "origin": "유래나 뉘앙스, 사용할 때 주의점 (한국어로 설명)",
        "example": "원어민이 실제로 쓸법한 대화 예시 (원어로)"
    }}
    
    If data is insufficient, use your own knowledge (LLM).
    Only return JSON string. No markdown.
    """

    try:
        # Groq Llama3 모델 호출 (엄청 빠름)
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        ai_response = chat.choices[0].message.content
        
        # JSON 변환 시도
        clean_json = ai_response.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        return jsonify({'status': 'ok', 'data': result})
        
    except Exception as e:
        print(f"AI Error: {e}")
        # 에러나면 기본값 리턴
        return jsonify({'status': 'error', 'data': {
            'definition': 'AI가 잠시 졸고 있습니다.',
            'origin': '다시 시도해주세요.',
            'example': '-'
        }})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
