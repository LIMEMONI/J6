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

app = FastAPI()

# SQLAlchemy 데이터베이스 연결 설정
DATABASE_URL = "mysql+mysqlconnector://root:sejong131!#!@127.0.0.1/ion"
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

# MySQL 데이터베이스 연결 설정
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="sejong131!#!",
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
    logger.info("Reached the home endpoint")
    return templates.TemplateResponse("index.html", {"request": request})

# 회원가입 페이지를 렌더링하는 엔드포인트
@app.get("/regist.html", response_class=HTMLResponse)
async def render_registration_page(request: Request):
    return templates.TemplateResponse("regist.html", {"request": request})

@app.get("/dashboard1.html", response_class=HTMLResponse)
async def render_dashboard_page(request: Request):
    # 세션에서 사용자 아이디 가져오기
    mem_id = request.session.get("mem_id", None)

    if mem_id:
        # 세션에 사용자 아이디가 있는 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", "Unknown")
        else:
            # 사용자를 찾을 수 없을 때 처리
            return RedirectResponse(url="/")
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard1.html", {"request": request, "mem_name": mem_name})

@app.get("/dashboard1p.html", response_class=HTMLResponse)
async def render_dashboard_page(request: Request):
    # 세션에서 사용자 아이디 가져오기
    mem_id = request.session.get("mem_id", None)

    if mem_id:
        # 세션에 사용자 아이디가 있는 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", "Unknown")
        else:
            # 사용자를 찾을 수 없을 때 처리
            return RedirectResponse(url="/")
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard1p.html", {"request": request, "mem_name": mem_name})

@app.get("/dashboard2.html", response_class=HTMLResponse)
async def render_dashboard_page(request: Request):
    # 세션에서 사용자 아이디 가져오기
    mem_id = request.session.get("mem_id", None)

    if mem_id:
        # 세션에 사용자 아이디가 있는 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", "Unknown")
        else:
            # 사용자를 찾을 수 없을 때 처리
            return RedirectResponse(url="/")
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard2.html", {"request": request, "mem_name": mem_name})

# 로그인 처리
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, mem_id: str = Form(None), mem_pass: str = Form(None)):
    if mem_id is None or mem_pass is None:
        return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호를 입력하세요."})

    # 데이터베이스에서 아이디, 비밀번호, 그리고 mem_grade 확인
    cursor.execute("SELECT mem_pass, mem_grade FROM member WHERE mem_id = %s", (mem_id,))
    user_data = cursor.fetchone()

    if user_data:
        # mem_grade 확인
        mem_pass_db, mem_grade = user_data
        if mem_pass_db == mem_pass:
            # 비밀번호 일치, mem_grade에 따라 페이지 리디렉션
            if mem_grade == 0:
                request.session["mem_id"] = mem_id  # 세션에 사용자 아이디 저장
                return RedirectResponse(url="/dashboard1.html")
            elif mem_grade == 1:
                request.session["mem_id"] = mem_id  # 세션에 사용자 아이디 저장
                return RedirectResponse(url="/dashboard1p.html")

    # 아이디 또는 비밀번호가 일치하지 않을 때 오류 메시지를 표시하고 다시 index.html 페이지로 렌더링
    return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})


# 로그아웃 처리
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()  # 세션 초기화
    return RedirectResponse(url="/")


@app.get("/alram.html", response_class=HTMLResponse)
async def render_alram_page(request: Request):
    return templates.TemplateResponse("alram.html", {"request": request})

@app.get("/test.html", response_class=HTMLResponse)
async def render_test_page(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})


# MySQL 데이터베이스 연결 설정
def create_connection():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="sejong131!#!",
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
    mem_ph: int
    mem_id: int
    mem_pass: str
    mem_pass2: str
    
# 아이디 중복 확인
@app.post("/check_username", response_class=HTMLResponse)
async def check_username(request: Request):
    form_data = await request.form()
    username = form_data.get('username')

    connection = create_connection()
    if connection is None:
        return HTMLResponse(content="데이터베이스 연결 오류.")

    cursor = connection.cursor()

    # 아이디 중복 확인
    cursor.execute("SELECT * FROM member WHERE mem_id = %s", (username,))
    existing_user = cursor.fetchone()
    connection.close()

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

# 생명주기 HTML 생성
@app.get("/rul-times/", response_class=HTMLResponse)
async def get_rul_times(request: Request):
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT rul_time FROM rul ORDER BY input_time DESC LIMIT 10;")
        result_rul = cursor.fetchall()
        rul_times = [int(item['rul_time']) for item in result_rul]

        cursor.execute("SELECT multi_pred FROM multi ORDER BY input_time DESC LIMIT 10;")
        result_multi = cursor.fetchall()
        multi_preds = [int(item['multi_pred']) for item in result_multi]

        return templates.TemplateResponse("rul-times.html", {"request": request, "rul_times": rul_times, "multi_preds":multi_preds})
    except Exception as e:
        return str(e)

# ------------------------------------------------------------------------------------------------------------------------------------------------------------- #
# FastAPI 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
