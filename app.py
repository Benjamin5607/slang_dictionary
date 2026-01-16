import os
import json
import random
from flask import Flask, request, jsonify, send_file
from groq import Groq
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ✅ 안전한 클라이언트 초기화
# 키가 없으면 client를 None으로 설정해서 서버 폭발을 막음
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = None

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq Client 연결 성공!")
    except Exception as e:
        print(f"⚠️ Groq 초기화 실패: {e}")
else:
    print("🚨 경고: GROQ_API_KEY가 없습니다. AI 기능이 작동하지 않습니다.")

@app.route('/')
def home():
    try:
        return send_file('index.html')
    except:
        return "index.html 파일이 없습니다."

# ⛏️ 정보 수집꾼
def mine_info(term, country):
    if country == 'KR': query = f'site:namu.wiki "{term}" OR "{term}" 뜻 유래'
    elif country == 'JP': query = f'{term} とは スラング 元ネタ'
    else: query = f'{term} slang meaning origin'

    try:
        url = "https://lite.duckduckgo.com/lite/"
        payload = {'q': query, 'kl': 'wt-wt'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        res = requests.post(url, data=payload, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        snippets = []
        for row in soup.select('table:nth-of-type(3) tr .result-snippet'):
            snippets.append(row.get_text(strip=True))
            
        return " ".join(snippets[:5])
    except:
        return ""

# 🧠 AI 큐레이터
@app.route('/curate')
def curate():
    # 1. 키가 없는 경우 바로 에러 반환 (서버 다운 방지)
    if not client:
        return jsonify({
            'status': 'error', 
            'msg': '서버 설정 오류: API 키가 없습니다. (Render Environment 설정을 확인하세요)'
        })

    term = request.args.get('term')
    country = request.args.get('country')
    if not term: return jsonify({'error': 'No term'})

    raw_data = mine_info(term, country)
    
    prompt = f"""
    You are a professional Slang Curator.
    Analyze the raw data and explain the slang "{term}" ({country}).
    [RAW DATA] {raw_data} [END DATA]
    Return strictly a JSON object:
    {{
        "definition": "Simple definition (Korean for KR/JP, English for others)",
        "origin": "Origin/Nuance (Korean for KR/JP, English for others)",
        "example": "Conversation example"
    }}
    Only JSON.
    """

    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        clean_json = chat.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        return jsonify({'status': 'ok', 'data': result})
        
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
