# front에서 이미지를 받음

from pydantic import BaseModel
from typing import Optional

# 1. 학생이 보낼 데이터 (문제 번호 + 손글씨 이미지)
class AnswerSubmit(BaseModel):
    user_id: int
    problem_id: int
    answer_image: str  # 이미지 데이터 (Base64 문자열)

# 2. 서버가 돌려줄 데이터 (AI 분석 결과)
class AnswerResponse(BaseModel):
    is_correct: bool
    message: str
    error_tag: Optional[str] = None
    ai_feedback: Optional[str] = None