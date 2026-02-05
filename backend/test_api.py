from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("📋 사용 가능한 모델 목록을 조회합니다...")
try:
    # 모델 목록을 다 가져와서 'generateContent' 기능이 있는 것만 보여줌
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            
except Exception as e:
    print(f"에러 발생: {e}")