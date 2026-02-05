from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import FileResponse
from database import engine
import models
from routers import study
import os

models.Base.metadata.create_all(bind=engine) 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(study.router)

if os.path.exists("static/problems"):
    app.mount("/static/problems", StaticFiles(directory="static/problems"), name="problems")
else:
    print("경고: 'static/problems' 폴더가 없습니다. 이미지가 안 나올 수 있어요.")


app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("../frontend/index.html")