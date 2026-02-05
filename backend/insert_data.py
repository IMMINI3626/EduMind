import os
import json
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# 1. DB 테이블 생성 (혹시 없으면 만듦)
models.Base.metadata.create_all(bind=engine)

def insert_data():
    db: Session = SessionLocal()
    
    # 정민님이 파일 빼둔 폴더 경로
    json_dir = "data"              # JSON 파일 있는 곳
    image_dir = "static/problems"  # 이미지 파일 있는 곳
    
    # 폴더 확인
    if not os.path.exists(json_dir):
        print(f"'{json_dir}' 폴더가 없습니다.")
        return
    if not os.path.exists(image_dir):
        print(f"'{image_dir}' 폴더가 없습니다.")
        return

    print("데이터 입력을 시작합니다...")

    files = os.listdir(json_dir)
    count = 0

    for filename in files:
        if filename.endswith(".json"):
            json_path = os.path.join(json_dir, filename)
            
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 1. 이미지 파일 찾기 (이름 매칭)
                json_img_name = data.get("question_filename", "")
                if not json_img_name:
                    continue

                real_img_name = None
                
                # (1) 이름이 완벽하게 같은 파일이 있는지 확인
                if os.path.exists(os.path.join(image_dir, json_img_name)):
                    real_img_name = json_img_name
                else:
                    # (2) 확장자가 달라도(png vs jpg) 이름 같으면 찾기
                    base_name = os.path.splitext(json_img_name)[0]
                    for img_f in os.listdir(image_dir):
                        if img_f.startswith(base_name):
                            real_img_name = img_f
                            break
                
                if not real_img_name:
                    print(f"이미지 파일 없음 패스: {json_img_name}")
                    continue

                # 2. 정보 뽑기
                ocr_list = data.get("OCR_info", [])
                content_text = ocr_list[0].get("question_text", "") if ocr_list else ""

                q_info = data.get("question_info", [])
                topic_name = "기타"
                difficulty = "중"
                
                if q_info:
                    topic_name = q_info[0].get("question_topic_name", "기타")
                    diff_num = q_info[0].get("question_difficulty", 3)
                    difficulty = str(diff_num)

                answer_text = data.get("answer", "정답 참조") 

                # 3. DB 저장
                
                # [개념 등록]
                concept = db.query(models.Concept).filter(models.Concept.name == topic_name).first()
                if not concept:
                    concept = models.Concept(name=topic_name)
                    db.add(concept)
                    db.commit()
                    db.refresh(concept)
                
                # [문제 등록]
                existing_prob = db.query(models.Problem).filter(models.Problem.image_url == real_img_name).first()
                if not existing_prob:
                    new_problem = models.Problem(
                        content = content_text,
                        image_url = real_img_name, 
                        answer = answer_text,
                        difficulty = difficulty,
                        solution = "AI 선생님에게 물어보세요!",
                        concept_id = concept.id
                    )
                    db.add(new_problem)
                    db.commit()
                    print(f"저장 완료: {real_img_name}")
                    count += 1
                else:
                    print(f"이미 있음: {real_img_name}")

            except Exception as e:
                print(f"에러 ({filename}): {e}")

    print("-" * 30)
    print(f"총 {count}개의 문제가 DB에 저장되었습니다!")
    db.close()

if __name__ == "__main__":
    insert_data()