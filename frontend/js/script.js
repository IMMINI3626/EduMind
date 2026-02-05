let currentMode = 'draw'; 
const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');
let isDrawing = false;
let currentTool = 'pen'; 

// 페이지 로딩 시 랜덤 문제 가져오기
window.onload = async function() {
    setWhiteBackground(); // 캔버스 배경 흰색으로
    await loadRandomProblem(); // 서버에서 문제 가져오기 함수 실행
};

// 랜덤 문제 가져오기 함수 추가
async function loadRandomProblem() {
    try {
        const response = await fetch("/study/random");
        const data = await response.json();

        if (data.message) {
            alert("DB에 문제가 없습니다! insert_data.py를 실행했는지 확인하세요.");
            return;
        }

        // 1. 문제 ID 저장
        document.getElementById('current-problem-id').value = data.problem_id;

        // 2. 텍스트 문제 보여주기 & 수학 공식 렌더링
        const textElem = document.getElementById('problem-text');
        
        if (data.content) {
            // DB에서 가져온 텍스트($x^2...$)를 넣습니다.
            textElem.innerHTML = data.content; 
            textElem.style.display = "block";
            
            // ★ MathJax에게 "방금 넣은 텍스트를 수학 공식으로 바꿔줘!"라고 명령
            if (window.MathJax) {
                window.MathJax.typesetPromise([textElem]).then(() => {
                    console.log("수학 공식 렌더링 완료!");
                }).catch((err) => console.log("MathJax 에러:", err));
            }
        } else {
            textElem.style.display = "none";
        }

        // 3. 이미지는 이제 필요 없으면 숨깁니다.
        // (만약 이미지가 꼭 필요한 도형 문제라면 보여주도록 남겨둘 수도 있습니다)
        const imgElem = document.getElementById('problem-image');
        
        // 일단 이미지는 숨김 처리 (텍스트 위주로 가기로 했으므로)
        imgElem.style.display = "none"; 
        imgElem.src = "";

    } catch (error) {
        console.error("문제 로딩 실패:", error);
    }
}

// 캔버스 초기화
function setWhiteBackground() {
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

// 도구 변경
function setTool(tool) {
    currentTool = tool;
    document.getElementById('btn-pen').classList.remove('active');
    document.getElementById('btn-eraser').classList.remove('active');
    
    if (tool === 'pen') {
        document.getElementById('btn-pen').classList.add('active');
    } else {
        document.getElementById('btn-eraser').classList.add('active');
    }
}

// 탭 전환
function switchTab(mode) {
    currentMode = mode;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    if (mode === 'draw') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('draw-mode').classList.remove('hidden');
        document.getElementById('upload-mode').classList.add('hidden');
    } else {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('draw-mode').classList.add('hidden');
        document.getElementById('upload-mode').classList.remove('hidden');
    }
}

// 그리기 로직
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('touchstart', (e) => startDrawing(e.touches[0]));
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('touchmove', (e) => { e.preventDefault(); draw(e.touches[0]); });
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseout', stopDrawing);
canvas.addEventListener('touchend', stopDrawing);

function startDrawing(e) { isDrawing = true; draw(e); }
function stopDrawing() { isDrawing = false; ctx.beginPath(); }

function draw(e) {
    if (!isDrawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.pageX) - rect.left;
    const y = (e.clientY || e.pageY) - rect.top;
    
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    if (currentTool === 'pen') {
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'black';
    } else {
        ctx.lineWidth = 20;
        ctx.strokeStyle = 'white';
    }
    
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
}

function clearCanvas() { setWhiteBackground(); }

// 답안 제출
async function submitAnswer() {
    let imageBase64 = "";

    if (currentMode === 'draw') {
        imageBase64 = canvas.toDataURL("image/png");
    } else {
        const fileInput = document.getElementById('imageInput');
        if (fileInput.files.length === 0) {
            alert("사진을 선택해주세요!");
            return;
        }
        imageBase64 = await toBase64(fileInput.files[0]);
    }

    // 현재 화면에 떠있는 문제 번호를 가져옴 (고정값 1 아님)
    const currentProblemId = document.getElementById('current-problem-id').value;
    
    if (!currentProblemId) {
        alert("문제 정보가 없습니다. 새로고침 해주세요.");
        return;
    }

    const payload = {
        user_id: 1,      
        problem_id: currentProblemId, // 중요
        answer_image: imageBase64
    };

    const submitBtn = document.querySelector('.submit-btn');
    const originalText = submitBtn.innerText;
    submitBtn.innerText = "채점 중... ";
    submitBtn.disabled = true;

    try {
        const response = await fetch("/study/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        const resultArea = document.getElementById('result-area');
        resultArea.classList.remove('hidden');
        document.getElementById('res-correct').innerText = data.is_correct ? "정답입니다! 🎉" : "오답입니다.";
        
        const tagSpan = document.getElementById('res-tag');
        tagSpan.innerText = data.error_tag || "없음";
        tagSpan.className = "tag " + (data.is_correct ? "correct" : "error");

        document.getElementById('res-advice').innerText = data.ai_feedback;

    } catch (error) {
        alert("에러 발생: " + error);
        console.error(error);
    } finally {
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;
    }
}

const toBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
});