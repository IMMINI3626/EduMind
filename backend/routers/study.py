from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func # 랜덤 정렬을 위해 필요
from database import get_db
import models, schemas
from datetime import datetime
import os
import google.generativeai as genai
import base64
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/study", tags=["study"])

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# ---------------------------------------------------------
# 랜덤 문제 가져오기 API
# ---------------------------------------------------------
@router.get("/random")
def get_random_problem(db: Session = Depends(get_db)):
    # DB에서 랜덤으로 문제 1개를 뽑습니다.
    problem = db.query(models.Problem).order_by(func.random()).first()
    
    if not problem:
        return {"message": "문제가 없습니다. DB를 확인해주세요."}
    
    return {
        "problem_id": problem.id,
        "content": problem.content,     # 텍스트 문제 (없을 수도 있음)
        "image_url": problem.image_url, # 이미지 파일명 (예: H_1_01.jpg)
        "difficulty": problem.difficulty
    }

# ---------------------------------------------------------
# 기존 기능 수정: 답안 제출 및 AI 분석
# ---------------------------------------------------------
@router.post("/submit", response_model=schemas.AnswerResponse)
async def submit_answer(submit: schemas.AnswerSubmit, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == submit.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    # 이미지 변환
    try:
        img_str = submit.answer_image
        if "," in img_str:
            img_str = img_str.split(",")[1]
        image_bytes = base64.b64decode(img_str)
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return {"is_correct": False, "message": "이미지 오류", "ai_feedback": "이미지 처리 실패"}

    # ★ [수정됨] 프롬프트: 이모티콘 금지, 객관적 분석 모드
    prompt = f"""
    당신은 수학 문제 풀이 과정을 정밀하게 분석하는 AI 평가 시스템입니다.
    학생이 제출한 [이미지]의 풀이 과정을 분석하여 피드백을 제공하십시오.

    [문제 정보]
    - 정답: {problem.answer}
    - 해설: {problem.solution if problem.solution else "제공되지 않음"}

    [분석 가이드라인]
    1. 이모티콘이나 감정적인 표현(예: '아쉽네요', '화이팅', '잘했어요')을 절대 사용하지 마십시오.
    2. 정답 여부를 판단하고, 오답인 경우 원인을 명확히 지적하십시오.
    3. 볼드체(**), 마크다운 없이 오직 줄글(Plain Text)로만 작성하십시오.
    4. 분석 결과는 객관적인 문체로 작성하십시오.

    [응답 포맷]
    정답여부: X (또는 O)
    태그: 개념 오류 (또는 계산 실수, 풀이 미흡, 정답)
    피드백: (학생의 풀이에서 틀린 부분을 구체적으로 지적하고 올바른 개념을 설명)
    """
    
    try:
        response = model.generate_content([prompt, image])
        result = response.text
        
        # 결과 파싱
        is_correct = "정답여부: O" in result
        
        error_tag = "알 수 없음"
        if "태그:" in result:
            error_tag = result.split("태그:")[1].split("\n")[0].strip()
        
        ai_msg = "분석 불가"
        if "피드백:" in result:
            ai_msg = result.split("피드백:")[1].strip()
        elif "풀이:" in result: # 혹시 모를 예전 포맷 대응
            ai_msg = result.split("풀이:")[1].strip()
            
    except Exception as e:
        print(f"AI Error: {e}")
        return {"is_correct": False, "message": "AI 에러", "ai_feedback": "시스템 오류 발생"}

    # ★ [수정됨] DB 저장 시 ai_feedback 컬럼에 데이터 저장
    new_log = models.SolveLog(
        user_id=submit.user_id, 
        problem_id=submit.problem_id,
        is_correct=is_correct, 
        user_answer="image", 
        error_tag=error_tag, 
        ai_feedback=ai_msg, # 분석 내용 저장
        solved_at=datetime.now()
    )
    db.add(new_log)
    db.commit()

    return {"is_correct": is_correct, "message": "완료", "error_tag": error_tag, "ai_feedback": ai_msg}