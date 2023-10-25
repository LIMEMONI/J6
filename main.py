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
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from typing import Optional
from fastapi.responses import PlainTextResponse
from pathlib import Path
import shutil
import matplotlib.pyplot as plt
import io
import base64
import logging
import re

# FastAPI 애플리케이션 초기화
app = FastAPI()

# -------------------------------------------------------------------------------------- 여기부터 기능 처리 코드 ---------------------------------------------------------------------------------------------------

## SessionMiddleware 설정
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key",  # 보안을 위해 비밀 키 설정
    same_site="none",
    max_age=3600,
    https_only=True,
)

logger = logging.getLogger(__name__)

# SQLAlchemy 데이터베이스 연결 설정
DATABASE_URL = "mysql+mysqlconnector://oneday:1234@limemoni-2.cfcq69qzg7mu.ap-northeast-1.rds.amazonaws.com/j6database"

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
# db = mysql.connector.connect(
#     host="127.0.0.1",
#     user="root",
#     password="sejong131!#!",
#     database="ion",
# )

db = mysql.connector.connect(
    host="limemoni-2.cfcq69qzg7mu.ap-northeast-1.rds.amazonaws.com",
    user="oneday",
    password="1234",
    database="j6database",
)


# 커서 생성
cursor = db.cursor()

# 정적 파일 디렉터리 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 로그인 처리 (POST 요청)
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, mem_id: str = Form(None), mem_pass: str = Form(None)):
    if mem_id is None or mem_pass is None:
        return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호를 입력하세요."})

    # 데이터베이스 연결
    connection = create_connection()
    if connection is None:
        return templates.TemplateResponse("index.html", {"request": request, "message": "데이터베이스 연결 오류."})

    cursor = connection.cursor()

    try:
        # 데이터베이스에서 아이디와 해싱된 비밀번호 가져오기
        cursor.execute("SELECT mem_name, mem_pass FROM member WHERE mem_id = %s", (mem_id,))
        user_data = cursor.fetchone()

        if user_data:
            # 데이터베이스에서 가져온 해시된 비밀번호
            mem_name, mem_pass_db = user_data

            # 비밀번호 검증을 여기서 수행하고, 해싱된 비밀번호와 비교합니다.
            # 해싱된 비밀번호와 비교하는 대신, 일반적으로 비밀번호는 해시화하고 저장해야 합니다.
            # 이 예시에서는 비밀번호가 해시화되지 않았다고 가정하겠습니다.
            if mem_pass_db == mem_pass:
                # 비밀번호 일치, 세션에 사용자 아이디와 이름 저장
                request.session["mem_id"] = mem_id
                request.session["mem_name"] = mem_name
                return RedirectResponse(url="/main.html")
            else:
                return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})
        else:
            return templates.TemplateResponse("index.html", {"request": request, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})

    except Error as e:
        return templates.TemplateResponse("index.html", {"request": request, "message": f"데이터베이스 오류: {e}"})

    finally:
        cursor.close()
        connection.close()


# 로그아웃 처리
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()  # 세션 초기화
    response = RedirectResponse(url="/")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# MySQL 데이터베이스 연결 설정
def create_connection():
    try:
        connection = mysql.connector.connect(
            host="limemoni-2.cfcq69qzg7mu.ap-northeast-1.rds.amazonaws.com",
            user="oneday",
            password="1234",
            database="j6database",
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

    # 회원가입이 완료되면 세션에 사용자 아이디 및 이름 저장하고 리디렉트
    request.session["mem_id"] = user.mem_id
    request.session["mem_name"] = user.mem_name
    connection.close()

    # / 페이지로 리디렉트
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)

# 데이터베이스에서 필요한 데이터를 쿼리하여 bar_lis를 생성
def fetch_bar_lis_from_database():
    cursor.execute("""SELECT distinct DATE_FORMAT(input_time, '%H:%i:%s'), ACTUALROTATIONANGLE, FIXTURETILTANGLE,
                        ETCHBEAMCURRENT,IONGAUGEPRESSURE,
                        ETCHGASCHANNEL1READBACK, ETCHPBNGASREADBACK,
                        ACTUALSTEPDURATION, ETCHSOURCEUSAGE,
                        FLOWCOOLFLOWRATE,FLOWCOOLPRESSURE
                    FROM j6database.input_data;""")
    existing_user = cursor.fetchall()
    
    colnames = cursor.description  # 변수정보
    cols = [[i, colnames[i][0], colnames[i+1][0]] for i in range(1, len(colnames), 2)]  # 변수명
    
    alram_dic = {}
    for i in range(1, len(existing_user[0])):
        alram_dic.update({'alram{}'.format(i): [{'time': val[0], 'col': val[i]} for val in existing_user]})  # line_alram
    
    try:
        cursor.execute("""SELECT row_index
                        FROM (SELECT rul_time, ROW_NUMBER() OVER (ORDER BY input_time) AS row_index
                            FROM j6database.rul_1) AS temp
                        WHERE rul_time = 0;""")
        existing_user = cursor.fetchall()
    
        line_lis = [val[0] for val in existing_user]
    
        cursor.execute("""SELECT temp.*, (row_index - LAG(row_index) OVER (ORDER BY row_index)) as diff
                        FROM (SELECT multi_pred, input_time, ROW_NUMBER() OVER (ORDER BY input_time) AS row_index
                            FROM j6database.multi_1) AS temp
                        WHERE multi_pred = 1;""")
        existing_user = cursor.fetchall()
    
        bar_lis = [[existing_user[0][1], existing_user[0][2]]]
        cnt = 0
        for i in range(1, len(existing_user)):
            if existing_user[i][-1] != 1:
                bar_lis[len(bar_lis) - 1].append(existing_user[i - 1][2])
                bar_lis.append([existing_user[i][1], existing_user[i][2]])
        bar_lis[-1].append(existing_user[-1][2])
    
    except:
        line_lis = None
        bar_lis = [[None, 0, 0]]
    
    return bar_lis

# -------------------------------------------------------------------------------------- 여기까지 기능 처리 코드 ---------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------- 여기부터 HTML 주소 코드 ---------------------------------------------------------------------------------------------------

# 홈 페이지를 렌더링하는 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Reached the home endpoint")
    return templates.TemplateResponse("index.html", {"request": request})

# "/" 주소에 대한 POST 요청을 처리
@app.post("/", response_class=HTMLResponse)
async def process_post_home(request: Request):
    # POST 요청 처리 코드
    return templates.TemplateResponse("index.html", {"request": request})

# 회원가입 페이지를 렌더링하는 엔드포인트
@app.get("/regist.html", response_class=HTMLResponse)
async def render_registration_page(request: Request):
    return templates.TemplateResponse("regist.html", {"request": request})


# 메인 페이지로의 POST 요청을 처리
@app.post("/main.html", response_class=HTMLResponse)
async def process_main_page_post(request: Request):
    
    # 데이터베이스에서 bar_lis 데이터를 가져옴
    bar_lis = fetch_bar_lis_from_database()
    
    # 세션에서 사용자 아이디 및 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", "Unknown")

    if mem_id:
        # 사용자가 로그인한 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", mem_name)
            
            # 설비 수명 상태(0: 만료 / 1: 정상 / 2: 주의)
            tool1_status = 1
            tool2_status = 1
            tool3_status = 2
            tool4_status = 0
            # 설비 타이머 시작시간(처음으로 받는 데이터의 시간부터 측정)
            start_times = {
                "설비 1": "2022-10-23T23:11:11", # 임의 설정값으로부터 타이머 시작 
                "설비 2": datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0).isoformat(), # 현재 시각으로부터 타이머 시작
                "설비 3": datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0).isoformat(), # 설비 3의 시작시간
                "설비 4": datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0).isoformat(), # 설비 4의 시작시간
            }
            # 설비별 처리중인 Lot 번호
            lot_query = "SELECT Lot FROM input_data LIMIT 4" # 일단 임의의 4개 Lot 번호를 가져옵니다.

            # SQL 쿼리 실행
            cursor.execute(lot_query)

            # 결과 가져오기
            Lots = []
            result = cursor.fetchall()
            for i in range(len(result)):
                Lots.append(result[i][0])
            return templates.TemplateResponse("main.html", {"request": request,
                                                            "tool1_status": tool1_status,
                                                            "tool2_status": tool2_status,
                                                            "tool3_status": tool3_status,
                                                            "tool4_status": tool4_status,
                                                            "start_times": start_times,
                                                            "Lots": Lots,
                                                            "bar_lis": bar_lis})
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")
    


@app.get("/dashboard.html", response_class=HTMLResponse)
async def render_dashboard_page(request: Request):
   
    # 데이터베이스에서 bar_lis 데이터를 가져옴
    bar_lis = fetch_bar_lis_from_database()
    
    # 세션에서 사용자 아이디 및 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", "Unknown")

    if mem_id:
        # 사용자가 로그인한 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", mem_name)
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard.html", {"request": request, "mem_name": mem_name, "bar_lis": bar_lis})

# 대쉬보드 1탭
@app.get("/dashboard1.html", response_class=HTMLResponse)
async def render_dashboard1_page(request: Request):
    # 세션에서 사용자 아이디 및 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", "Unknown")

    if mem_id:
        # 사용자가 로그인한 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", mem_name)
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리다이렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard1.html", {"request": request, "mem_name": mem_name})

# 대쉬보드 2탭
@app.get("/dashboard2.html", response_class=HTMLResponse)
async def render_dashboard2_page(request: Request):
    # 세션에서 사용자 아이디 및 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", "Unknown")

    if mem_id:
        # 사용자가 로그인한 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", mem_name)
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리디렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard2.html", {"request": request, "mem_name": mem_name})

# 대쉬보드 3탭
@app.get("/dashboard3.html", response_class=HTMLResponse)
async def render_dashboard3_page(request: Request):
    # 세션에서 사용자 아이디 및 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", "Unknown")

    if mem_id:
        # 사용자가 로그인한 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", mem_name)
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리디렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard3.html", {"request": request, "mem_name": mem_name})

# 대쉬보드 4탭
@app.get("/dashboard4.html", response_class=HTMLResponse)
async def render_dashboard4_page(request: Request):
    # 세션에서 사용자 아이디 및 이름 가져오기
    mem_id = request.session.get("mem_id", None)
    mem_name = request.session.get("mem_name", "Unknown")

    if mem_id:
        # 사용자가 로그인한 경우, 사용자 정보를 데이터베이스에서 가져온다.
        cursor.execute("SELECT * FROM member WHERE mem_id = %s", (mem_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # 결과를 딕셔너리로 변환
            column_names = cursor.column_names
            user_dict = {column_names[i]: existing_user[i] for i in range(len(column_names))}

            # mem_name 필드 추출
            mem_name = user_dict.get("mem_name", mem_name)
    else:
        # 세션에 사용자 아이디가 없는 경우, 로그인 페이지로 리디렉트
        return RedirectResponse(url="/")

    return templates.TemplateResponse("dashboard4.html", {"request": request, "mem_name": mem_name})

@app.get("/alram.html")
async def page_alram(request: Request, time: str = None, xlim_s: int = 925, xlim_e: int = 964):
    ### alram_draw
    cursor.execute("""SELECT distinct DATE_FORMAT(input_time, '%H:%i:%s'), ACTUALROTATIONANGLE, FIXTURETILTANGLE,
                                                    ETCHBEAMCURRENT,IONGAUGEPRESSURE,
                                                    ETCHGASCHANNEL1READBACK, ETCHPBNGASREADBACK,
                                                    ACTUALSTEPDURATION, ETCHSOURCEUSAGE,
                                                    FLOWCOOLFLOWRATE,FLOWCOOLPRESSURE
                    FROM j6database.input_data;""")
    existing_user = cursor.fetchall()
    
    colnames = cursor.description # 변수정보
    cols = [[i, colnames[i][0], colnames[i+1][0]] for i in range(1, len(colnames), 2)] # 변수명
    
    alram_dic = {}
    for i in range(1, len(existing_user[0])):
        alram_dic.update({'alram{}'.format(i) : [{'time': val[0], 'col':val[i]} for val in existing_user]}) # line_alram
        
    try:
        ### rul_line_draw
        cursor.execute("""SELECT row_index
                            FROM (SELECT rul_time, ROW_NUMBER() OVER (ORDER BY input_time) AS row_index
                                FROM j6database.rul_1) AS temp
                            WHERE rul_time = 0;""")
        existing_user = cursor.fetchall()
        
        line_lis = [val[0] for val in existing_user]
        
        
        ### side_bar_list
        cursor.execute("""SELECT temp.*, (row_index - LAG(row_index) OVER (ORDER BY row_index)) as diff
                            FROM (SELECT multi_pred, input_time, ROW_NUMBER() OVER (ORDER BY input_time) AS row_index
                                FROM j6database.multi_1) AS temp
                            WHERE multi_pred = 1;""")
        existing_user = cursor.fetchall()
        
        bar_lis = [[existing_user[0][1], existing_user[0][2]]]
        cnt = 0
        for i in range(1, len(existing_user)):
            if existing_user[i][-1] != 1 :
                bar_lis[len(bar_lis)-1].append(existing_user[i-1][2])
                bar_lis.append([existing_user[i][1], existing_user[i][2]])
        bar_lis[-1].append(existing_user[-1][2])
        
    except:
        line_lis = None
        bar_lis = [[None, 0, 0]]
    
    return templates.TemplateResponse("alram.html", {"request":request,
                                                      'cols':cols,
                                                      'dic':alram_dic,
                                                      'bar_lis':bar_lis,
                                                      'line_lis':line_lis,
                                                      "time": time, "xlim_s": xlim_s, "xlim_e": xlim_e})
    


# -------------------------------------------------------------------------------------- 여기까지 HTML 주소 코드 ---------------------------------------------------------------------------------------------------

# FastAPI 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
