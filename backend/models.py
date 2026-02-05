from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# 1. 사용자 테이블
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True) # 학번 (20233531)
    name = Column(String(50))
    
    # 내 풀이 기록과 연결
    logs = relationship("SolveLog", back_populates="user")

# 2. 개념(Concept) - 보고서의 "Tree 구조" 구현
class Concept(Base):
    __tablename__ = "concepts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100)) # 개념 이름 (예: 지수함수)
    
    # 부모 개념 ID (이게 있어야 트리 구조가 됨)
    # 예: '지수함수'의 부모는 '함수'
    parent_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)
    
    children = relationship("Concept") # 하위 개념들
    problems = relationship("Problem", back_populates="concept")

# 3. 문제(Problem)
class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=True) # 문제 내용
    image_url = Column(String(255), nullable=True) # 문제 이미지 파일 이름을 저장할 칸
    answer = Column(String(255)) # 정답
    difficulty = Column(String(20)) # 난이도 (상/중/하)
    solution = Column(Text, nullable=True) # 풀이 과정
    
    # 어떤 개념에 속하는 문제인지 연결
    concept_id = Column(Integer, ForeignKey("concepts.id"))
    concept = relationship("Concept", back_populates="problems")

# 4. 풀이 기록(SolveLog) - "오답 원인 태그" 저장
class SolveLog(Base):
    __tablename__ = "solve_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    problem_id = Column(Integer, ForeignKey("problems.id"))
    
    is_correct = Column(Boolean) # 정답 여부
    user_answer = Column(String(255)) # 사용자가 쓴 답
    
    # 핵심: 오답 원인 태그 (개념오류/계산실수/풀이과정미흡)
    error_tag = Column(String(50), nullable=True) 
    
    ai_feedback = Column(Text, nullable=True) # AI 피드백

    solved_at = Column(DateTime, default=datetime.now) # 푼 시간 (망각주기용)
    
    user = relationship("User", back_populates="logs")