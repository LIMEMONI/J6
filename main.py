from fastapi import FastAPI, HTTPException, Form, Request, WebSocket, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel
from datetime import datetime
import plotly.graph_objs as go
import pandas as pd
import time
import asyncio
import json
import random
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import Optional
from fastapi.responses import PlainTextResponse
from pathlib import Path
import shutil
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from pathlib import Path
import shutil
import matplotlib.pyplot as plt
import io
import base64



# SQLAlchemy 데이터베이스 연결 설정
DATABASE_URL = "mysql+mysqlconnector://root:tmdghks7627@127.0.0.1/ion"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델 정의
Base = declarative_base()

class Member(Base):
    __tablename__ = "member"
    
    mem_id = Column(String(20), primary_key=True)
    mem_pass = Column(String(20))
    mem_pass2 = Column(String(30))
    mem_name = Column(String(10))
    mem_regno = Column(String(8))
    mem_ph = Column(String(11))

# FastAPI 애플리케이션 초기화
app = FastAPI()

# SessionMiddleware 설정
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")  # 비밀 키를 지정해야 합니다.



# MySQL 데이터베이스 연결 설정
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="tmdghks7627",
    database="ion",
)

# 커서 생성
cursor = db.cursor()


# 정적 파일 디렉터리 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML 템플릿 설정
templates = Jinja2Templates(directory="templates")


# 홈 페이지를 렌더링하는 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 홈 페이지에 대한 POST 요청 처리
@app.post("/", response_class=HTMLResponse)
async def process_home_post(request: Request):
    # POST 요청 처리 코드를 추가
    # 예를 들어, 데이터를 저장하거나 다른 작업을 수행할 수 있습니다.

    # POST 요청 처리가 완료되면 홈 페이지로 리다이렉트
    return RedirectResponse(url="/")

# 회원가입 페이지를 렌더링하는 엔드포인트
@app.get("/regist.html", response_class=HTMLResponse)
async def render_registration_page(request: Request):
    return templates.TemplateResponse("regist.html", {"request": request})



# 대쉬보드 메인페이지를 렌더링하는 엔드포인트
@app.get("/dashboard.html", response_class=HTMLResponse)
async def render_dashboard_page(request: Request):
    # 세션에서 사용자 아이디 가져오기
    mem_id = request.session.get("mem_id", None)

    if mem_id:
        # 세션에 사용자 아이디가 있는 경우, 사용자 정보를 데이터베이스에서 가져온다.
        # 여기에서는 사용자 정보를 mem_name으로 대체한다.
        mem_name = mem_id
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard.html", {"request": request, "mem_name": mem_name}) 



# 로그인 처리
@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    mem_id: str = Form(None),
    mem_pass: str = Form(None),
):
    if mem_id is None or mem_pass is None:
        return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호를 입력하세요."})

    # 데이터베이스에서 아이디와 비밀번호 확인
    cursor.execute("SELECT * FROM member WHERE mem_id = %s AND mem_pass = %s", (mem_id, mem_pass))
    existing_user = cursor.fetchone()

    if existing_user:
        # 아이디와 비밀번호가 일치하면 대시보드 페이지로 리디렉션
        request.session["mem_id"] = mem_id  # 세션에 사용자 아이디 저장
        request.session["mem_name"] = existing_user  # 세션에 사용자 이름 저장
        return RedirectResponse(url="/dashboard.html")
    else:
        # 아이디 또는 비밀번호가 일치하지 않을 때 오류 메시지를 표시하고 다시 index.html 페이지로 렌더링
        return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})



# 로그아웃 처리
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()  # 세션 초기화
    return RedirectResponse(url="/")

# test.html 페이지를 렌더링하는 엔드포인트
@app.get("/test.html", response_class=HTMLResponse)
async def render_test_page(request: Request):
    
    # MySQL에서 데이터 조회
    cursor.execute("SELECT * FROM ion.member")
    result = cursor.fetchall()
    
    # 세션에서 사용자 아이디 및 사용자 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", None)

    if mem_id:
        return templates.TemplateResponse("test.html", {"request": request, "mem_name": mem_name})
    else:
        # 로그인되지 않은 경우 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")




# 사용자가 입력한 아이디 중복 확인
@app.post("/check_username")
async def check_username(username: str = Form(...)):
    # 아이디 중복 확인
    cursor.execute("SELECT * FROM member WHERE mem_id = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        return JSONResponse(content={"is_valid": False})  # 이미 존재하는 아이디

    return JSONResponse(content={"is_valid": True})  # 사용 가능한 아이디

# MySQL 데이터베이스 연결 설정
def create_connection():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="tmdghks7627",
            database="ion",
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# 사용자 정보를 저장할 데이터 모델
class User(BaseModel):
    mem_name: str
    mem_regno: int
    mem_ph: str
    mem_id: str
    mem_pass: str
    mem_pass2: str

# 회원가입 처리
@app.post("/process_registration", response_class=JSONResponse)
async def process_registration(user: User, request: Request):
    
    # 비밀번호와 비밀번호 확인 일치 여부 확인
    if user.mem_pass != user.mem_pass2:
        raise HTTPException(status_code=400, detail="비밀번호가 다릅니다. 다시 시도해주세요.")

    # 아이디 중복 확인
    cursor.execute("SELECT * FROM member WHERE mem_id = %s", (user.mem_id,))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다. 다른 아이디를 사용해주세요.")

    # 데이터베이스에 회원 정보 저장
    insert_query = """
        INSERT INTO member (mem_name, mem_regno, mem_ph, mem_id, mem_pass, mem_pass2)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (
        user.mem_name,
        user.mem_regno,
        user.mem_ph,
        user.mem_id,
        user.mem_pass,
        user.mem_pass2,
    )
    cursor.execute(insert_query, values)
    db.commit()

    # 회원가입이 완료되면 JSON 응답 반환
    return JSONResponse(content={"message": "회원가입이 완료되었습니다."})

@app.post("/run_python_script/")
async def run_python_script(script: UploadFile):
    # 업로드한 파일을 저장할 디렉토리 지정
    upload_dir = "uploaded_scripts"
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    # 파일을 디렉토리에 저장
    with open(f"{upload_dir}/{script.filename}", "wb") as f:
        shutil.copyfileobj(script.file, f)

    # 파이썬 스크립트 실행
    try:
        # 시각화 생성
        result1 = {}
        exec(open(f"{upload_dir}/{script.filename}").read(), {}, result1)
        plt.savefig("static/graph.png")  # 시각화를 이미지 파일로 저장

        # 이미지를 Base64로 인코딩
        img_base64 = base64.b64encode(open("static/graph.png", "rb").read()).decode("utf-8")
        return f'<img src="data:image/png;base64,{img_base64}" alt="Graph">'
    except Exception as e:
        return str(e)



# ------------------------------------------------------------------------------------------------------------------------------------------------------------- #
# FastAPI 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)