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
from datetime import datetime

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

### 오류 상세페이지---------------------------------------------------------------------------------
### -----------------------------------------------------------------------------------------------

# html연결
templates = Jinja2Templates(directory="templates")

# bootstrap연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# db연결
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
db = mysql.connector.connect(
    host="limemoni-2.cfcq69qzg7mu.ap-northeast-1.rds.amazonaws.com",
    user="oneday",
    password="1234",
    database="j6database",
)

# 커서 생성
cursor = db.cursor()

### -----------------------------------------------------------------------------------------------

@app.get("/charts")
async def page_chart(request: Request, time: str = None, xlim_s: int = 925, xlim_e: int = 964):
    ### chart_draw
    cursor.execute("""SELECT distinct DATE_FORMAT(input_time, '%H:%i:%s'), ACTUALROTATIONANGLE, FIXTURETILTANGLE,
                                                    ETCHBEAMCURRENT,IONGAUGEPRESSURE,
                                                    ETCHGASCHANNEL1READBACK, ETCHPBNGASREADBACK,
                                                    ACTUALSTEPDURATION, ETCHSOURCEUSAGE,
                                                    FLOWCOOLFLOWRATE,FLOWCOOLPRESSURE
                    FROM j6database.input_data_1;""")
    existing_user = cursor.fetchall()
    
    colnames = cursor.description # 변수정보
    cols = [[i, colnames[i][0], colnames[i+1][0]] for i in range(1, len(colnames), 2)] # 변수명
    
    chart_dic = {}
    for i in range(1, len(existing_user[0])):
        chart_dic.update({'chart{}'.format(i) : [{'time': val[0], 'col':val[i]} for val in existing_user]}) # line_chart
        
        
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
    
    return templates.TemplateResponse("charts.html", {"request":request,
                                                      'cols':cols,
                                                      'dic':chart_dic,
                                                      'bar_lis':bar_lis,
                                                      'line_lis':line_lis,
                                                      "time": time, "xlim_s": xlim_s, "xlim_e": xlim_e})


### test페이지
### -----------------------------------------------------------------------------------------------

@app.get("/test")
async def page_test(request: Request, tst: int = 1):
    cursor.execute("""SELECT row_index
                    FROM (SELECT rul_time, ROW_NUMBER() OVER (ORDER BY input_time) AS row_index
                        FROM j6database.rul_1) AS temp
                    WHERE rul_time = 0;""")
    existing_user = cursor.fetchall()
    
    
    return templates.TemplateResponse("test.html", {"request": request, 'tt': tst})