import os
import json
from flask import Flask, request, jsonify, send_file
from groq import Groq
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ✅ 안전한 클라이언트 초기화
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = None

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq Client 연결 성공!")
    except Exception as e:
        print(f"⚠️ Groq 초기화 실패: {e}")
else:
    print("🚨 경고: GROQ_API_KEY가 없습니다.")

@app.route('/')
def home():
    try:
        return send_file('index.html')
    except:
        return "index.html 파일이 없습니다."

# ---------------------------------------------------------
# 🤖 [NEW] 문 두들기고 가능한 놈 데려오는 함수
# ---------------------------------------------------------
def get_best_model():
    """
    Groq API에게 '지금 가능한 모델 리스트'를 달라고 한 뒤,
    가장 똑똑한(70b) 녀석을 우선적으로 뽑아옵니다.
    """
    default_model = "llama3-8b-8192" # 최후의 보루 (혹시 리스트 못 받아오면 씀)

    if not client: return default_model

    try:
        # 1. Groq야, 지금 활동 중인 애들 명단 줘봐.
        models = client.models.list()
        available_models = [m.id for m in models.data]
        
        # 2. 우선순위: 최신 Llama 3.3 > 3.1 > 70b(똑똑한놈) > 8b(빠른놈)
        # 리스트를 훑으면서 가장 먼저 걸리는 놈을 채용함
        priority_keywords = [
            "llama-3.3-70b", 
            "llama-3.1-70b", 
            "llama3-70b", 
            "mixtral-8x7b", 
            "gemma2-9b",
            "llama-3.1-8b"
        ]

        print(f"📋 현재 현역 모델들: {available_models}")

        for keyword in priority_keywords:
            for model_id in available_models:
                if keyword in model_id:
                    print(f"👉 채용된 모델: {model_id}")
                    return model_id
        
        # 3. 원하는 놈 없으면 아무 텍스트 모델이나 잡아옴 (whisper는 음성용이라 제외)
        for model_id in available_models:
            if "whisper" not in model_id:
                return model_id

        return default_model

    except Exception as e:
        print(f"모델 선발 실패 (기본값 사용): {e}")
        return default_model

# ---------------------------------------------------------
# ⛏️ 정보 수집꾼
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 🧠 AI 큐레이터
# ---------------------------------------------------------
@app.route('/curate')
def curate():
    if not client:
        return jsonify({'status': 'error', 'msg': 'API 키 없음'})

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
        # [핵심] 여기서 '지금 가능한 놈'을 호출합니다.
        current_best_model = get_best_model()

        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=current_best_model, # <--- 여기가 동적으로 바뀜!
        )
        clean_json = chat.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        return jsonify({'status': 'ok', 'data': result})
        
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({'status': 'error', 'msg': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
