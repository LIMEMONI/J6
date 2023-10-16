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
import logging
import re


# FastAPI 애플리케이션 초기화
app = FastAPI()

# SessionMiddleware 설정
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")  # 비밀 키를 지정해야 합니다.

logger = logging.getLogger(__name__)

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
    logger.info("Reached the home endpoint")
    return templates.TemplateResponse("index.html", {"request": request})

# 회원가입 페이지를 렌더링하는 엔드포인트
@app.get("/regist.html", response_class=HTMLResponse)
async def render_registration_page(request: Request):
    return templates.TemplateResponse("regist.html", {"request": request})

@app.get("/dashboard.html", response_class=HTMLResponse)
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
            mem_name = "Unknown"
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
        return RedirectResponse(url="/dashboard.html")
    else:
        # 아이디 또는 비밀번호가 일치하지 않을 때 오류 메시지를 표시하고 다시 index.html 페이지로 렌더링
        return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})

# 로그아웃 처리
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()  # 세션 초기화
    return RedirectResponse(url="/")

# 테스트 페이지를 렌더링하는 엔드포인트
@app.get("/alram.html", response_class=HTMLResponse)
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
            mem_name = "Unknown"
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("alram.html", {"request": request, "mem_name": mem_name})


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
        return HTMLResponse(content="이미 존재하는 아이디입니다.")
    else:
        return HTMLResponse(content="사용 가능한 아이디입니다.")

# 가입하기 버튼을 눌렀을 때 회원가입을 처리하는 엔드포인트
@app.post("/process_registration", response_class=HTMLResponse)
async def process_registration(request: Request, user: User):
    # 데이터베이스 연결
    connection = create_connection()
    if connection is None:
        return templates.TemplateResponse("regist.html", {"request": request, "message": "데이터베이스 연결 오류."})

    cursor = connection.cursor()

    # 데이터베이스에 사용자 정보 저장
    try:
        cursor.execute(
            "INSERT INTO member (mem_name, mem_regno, mem_ph, mem_id, mem_pass, mem_pass2) VALUES (%s, %s, %s, %s, %s, %s)",
            (user.mem_name, user.mem_regno, user.mem_ph, user.mem_id, user.mem_pass, user.mem_pass2)
        )
        connection.commit()
    except Error as e:
        return templates.TemplateResponse("regist.html", {"request": request, "message": f"데이터베이스 오류: {e}"})

    # 회원가입이 완료되면 세션에 사용자 아이디 저장하고 리디렉트
    request.session["mem_id"] = user.mem_id
    connection.close()
    
    # / 페이지로 리디렉트
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)


# FastAPI에서 데이터 업로드 및 처리하는 엔드포인트
@app.post("/upload-data/")
async def upload_data(
    request: Request,
    file: UploadFile = File(...)
):
    # CSV 파일인지 확인
    if not file.filename.endswith(".csv"):
        return HTMLResponse(content="업로드한 파일은 CSV 형식이 아닙니다.", status_code=400)

    # 업로드한 CSV 파일을 처리 및 그래프 생성 함수로 전달
    graph_data = process_and_generate_graph(file.file)

    # 그래프를 웹 페이지에 표시
    plotly_figure = go.Figure(data=[go.Scatter(x=graph_data['x'], y=graph_data['y'])])
    plot_div = plotly_figure.to_html(full_html=False)

    return HTMLResponse(content=plot_div, status_code=200)

# 데이터 처리 및 그래프 생성 함수 (예시)
def process_and_generate_graph(file):
    # 업로드한 CSV 파일을 데이터프레임으로 읽음 (pandas 사용)
    df = pd.read_csv(file)

    # 데이터 처리 및 그래프 생성 작업 수행 (예: Matplotlib 사용)
    x = df['x']
    y = df['y']

    # 여기에서 그래프 데이터 생성 및 반환
    graph_data = {'x': x, 'y': y}

    return graph_data

@app.post("/uploadfile/")
async def upload_file(file: UploadFile):
    # 업로드한 파일을 Pandas DataFrame으로 읽기
    content = await file.read()
    decoded_content = content.decode('ANSI')
    df = pd.read_csv(StringIO(decoded_content))

    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    plt.rc('font', family = 'Malgun Gothic', size=10)
    
    df.rename(columns={'2015' : '년도별','전통(재래) 시장' : '마켓별', '계' : '연령별','29.4': '이용률'}, inplace=True)
    
    df11 = df[df['마켓별'] == '대형마트 (3,000m2 이상)'].drop('마켓별', axis=1)
    df11.reset_index(drop=True, inplace=True)
     # 시각화할 그래프의 크기를 지정합니다.
    plt.figure(figsize=[15, 8])

    # 전통시장에 대한 막대 그래프를 그립니다.
    plt.bar(df11['연령별'], df11['전통시장'], label='전통시장', 
            color='#61b299', edgecolor='black', linewidth=1)

    # 그래프의 제목을 설정합니다.
    plt.title('테스트 년도 연령별 이용률 비교', size=18)
    # x축의 레이블을 설정합니다.
    plt.xlabel('연령별', fontsize=15)
    # y축의 레이블을 설정합니다.
    plt.ylabel('이용률 (%)', fontsize=15)
    
    # x축의 눈금 레이블의 크기를 설정합니다.
    plt.xticks(fontsize=15)
    # y축의 눈금 레이블을 지정합니다.
    plt.yticks([0, 20, 40, 60, 80], fontsize=15)

    # 범례를 표시합니다.
    plt.legend()

    # 그래프를 깔끔하게 배치합니다.
    plt.tight_layout()
    
    # 그래프를 표시합니다.
    plt.show()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    # 그래프를 base64로 인코딩된 이미지 데이터로 변환합니다.
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.read()).decode("utf-8")

    return JSONResponse(content={"plot_data": plot_data})

@app.get("/plotly_graph")
async def plotly_graph():
    # 데이터 생성 (예시 데이터)
    data = [
        go.Scatter(
            x=[1, 2, 3, 4, 5],
            y=[10, 11, 12, 13, 14],
            mode="lines",
            name="Series 1"
        )
    ]

    layout = go.Layout(
        title="Plotly Graph Example",
        xaxis=dict(title="X-axis"),
        yaxis=dict(title="Y-axis")
    )

    fig = go.Figure(data=data, layout=layout)

    # 그래프를 JSON 형식으로 반환
    return fig.to_json()

# FastAPI 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
