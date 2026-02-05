from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# 1. .env 파일에서 비밀번호 가져오기
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URL")

# 2. DB 연결 엔진 만들기
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. 접속 세션 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 모델들이 상속받을 기본 클래스
Base = declarative_base()

# 5. DB 세션을 가져오는 함수 (나중에 API에서 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()