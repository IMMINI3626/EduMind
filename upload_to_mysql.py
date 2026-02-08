import pandas as pd
import pymysql
import zipfile
import json
import os
import io

# =================================================================
#환경에 맞게 수정
# =================================================================
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '0000',       # <-- MySQL 비밀번호
    'db': 'edumind_db',       # <-- 워크벤치 스키마 이름
    'charset': 'utf8mb4'
}

# 엑셀 파일들의 경로 (2개)
# 경로 앞에 r 붙이기
excel_files = [
    r"C:\university\univer4_1\Capstone Design\tranning_data\수학 과목 문제생성 데이터\Other\수학 과목 문제 생성 엑셀 정리.xlsx",
    r"C:\university\univer4_1\Capstone Design\tranning_data\수학 과목 자동 풀이 데이터\Other\수학과목 자동 풀이 데이터.xlsx" 
]

# 2. ZIP 폴더들 (총 4개)
zip_folders = [
    # 문제생성 데이터 폴더
    r"C:\university\univer4_1\Capstone Design\tranning_data\수학 과목 문제생성 데이터\Training\라벨링데이터",
    r"C:\university\univer4_1\Capstone Design\tranning_data\수학 과목 문제생성 데이터\Validation\라벨링데이터",
    # 자동풀이 데이터 폴더
    r"C:\university\univer4_1\Capstone Design\tranning_data\수학 과목 자동 풀이 데이터\Training\라벨링데이터",
    r"C:\university\univer4_1\Capstone Design\tranning_data\수학 과목 자동 풀이 데이터\Validation\라벨링데이터"
]

# =================================================================
# [함수] ZIP 파일 속 JSON에서 해설, 수식 가져오기
# =================================================================
def get_json_info_from_zip(target_id):
    # 지정된 4개의 폴더를 하나씩 순회합니다.
    for folder_path in zip_folders:
        if not os.path.exists(folder_path):
            continue
            
        # 폴더 내의 모든 파일을 확인
        for zip_name in os.listdir(folder_path):
            if zip_name.endswith('.zip'):
                full_zip_path = os.path.join(folder_path, zip_name)
                
                try:
                    # 압축을 풀지 않고 내부 확인
                    with zipfile.ZipFile(full_zip_path, 'r') as z:
                        for file_info in z.infolist():
                            # 파일명에 ID가 포함된 JSON 찾기
                            if target_id in file_info.filename and file_info.filename.endswith('.json'):
                                with z.open(file_info) as f:
                                    data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                                    
                                    # 필요한 데이터 추출
                                    question_text = data.get('OCR_info', [{}])[0].get('question_text', '')
                                    standard = data.get('source_data_info', {}).get('2015_achievement_standard', [''])[0]
                                    
                                    explanation = ""
                                    for item in data.get('learning_data_info', []):
                                        if "해설" in item.get('class_name', ''):
                                            explanation = item.get('class_info_list', [{}])[0].get('text_description', '')
                                    
                                    return question_text, standard, explanation, zip_name
                except Exception:
                    continue 
    return None, None, None, None

# =================================================================
# 데이터 통합 및 MySQL 전송
# =================================================================
def run_integration():
    print("엑셀 파일들을 읽어서 하나로 합치는 중입니다...")
    
    df_list = []
    for path in excel_files:
        if os.path.exists(path):
            try:
                # 엑셀을 읽을 때 필요한 컬럼만 읽음 (에러 방지)
                # 컬럼 이름이 파일마다 조금 다를 수 있어서 기본적으로 다 읽고 처리합니다.
                temp_df = pd.read_excel(path)
                # 필요한 컬럼만 통일 (이름이 다르면 여기서 조정 가능)
                # 여기서는 id가 있는지만 확인하고 다 가져옵니다.
                if 'id' in temp_df.columns:
                    df_list.append(temp_df)
                    print(f"  OK: {os.path.basename(path)} 로드 완료!")
                else:
                    print(f"  SKIP: {os.path.basename(path)} (id 컬럼이 없어서 건너뜁니다)")
            except Exception as e:
                print(f"  ERROR: {os.path.basename(path)} 읽기 실패 - {e}")
        else:
            print(f"  WARNING: 파일이 없습니다 - {path}")

    if not df_list:
        print("처리할 엑셀 파일이 하나도 없습니다!")
        return

    # 두 엑셀을 위아래로 합칩니다.
    df = pd.concat(df_list, ignore_index=True)
    
    print("MySQL 데이터베이스에 연결 중...")
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
    except Exception as e:
        print(f"MySQL 연결 실패! 아이디/비번을 확인해주세요.\n{e}")
        return

    # 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_questions (
            id VARCHAR(50) PRIMARY KEY,
            grade VARCHAR(10),
            topic_name TEXT,
            difficulty INT,
            question_latex TEXT,
            achievement_standard TEXT,
            explanation TEXT,
            zip_location TEXT
        )
    """)
    
    total_count = len(df)
    print(f"총 {total_count}개의 통합 데이터를 처리하기 시작합니다.")
    print(" (두 과목 데이터를 모두 뒤지느라 시간이 좀 걸립니다. 힘내세요!)")
    
    processed_count = 0
    
    # 통합된 리스트를 돌면서 작업 수행
    for index, row in df.iterrows():
        q_id = str(row['id'])
        
        # 4개의 폴더를 뒤져서 JSON 정보 가져오기
        q_latex, standard, expl, zip_loc = get_json_info_from_zip(q_id)
        
        # MySQL에 저장
        sql = """
            INSERT INTO all_questions 
            (id, grade, topic_name, difficulty, question_latex, achievement_standard, explanation, zip_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE topic_name=VALUES(topic_name)
        """
        
        # 컬럼 이름이 파일마다 다를 수 있으니 안전하게 가져오기 (.get 사용)
        grade = row.get('question_grade', '')
        topic = row.get('question_topic_name', '')
        diff = row.get('question_difficulty', 0)

        cursor.execute(sql, (
            q_id, grade, topic, diff, q_latex, standard, expl, zip_loc
        ))
        
        processed_count += 1
        
        if processed_count % 100 == 0:
            conn.commit()
            print(f"   - [{processed_count}/{total_count}] 처리 완료... (현재 ID: {q_id})")

    conn.commit()
    conn.close()
    print("\n" + "="*50)
    print("대성공! 문제생성 + 자동풀이 데이터가 모두 MySQL에 들어갔습니다.")
    print("="*50)

if __name__ == "__main__":
    run_integration()
