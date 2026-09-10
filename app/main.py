# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

import logging

from app.routers import auth, uploads, recommend, chat, chat_session, reports
from app.core.security import decode_token
from app.core.redis_client import redis_client
from app.routers import auth
from app import models
from app.core.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

app = FastAPI()

origins = [
    "http://localhost:8081",  # Expo Web dev 서버
    "http://127.0.0.1:8081",
    "https://mentalcare-api-v2-ct42qawfuq-du.a.run.app",
    "https://mentalcare-299d2.web.app",
]


# --- CORS 설정 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 등록 ---
app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(reports.router)
app.include_router(recommend.router)
app.include_router(chat.router)
app.include_router(chat_session.router)

@app.on_event("startup")
async def on_startup():
    try:
        pong = redis_client.ping()  # ✅ sync 호출
        print("✅ Redis OK:", pong)
    except Exception as e:
        print("❌ Redis connection failed:", repr(e))


@app.on_event("shutdown")
async def on_shutdown():
    # 이벤트 루프가 내려갈 때 연결 정리
    try:
        redis_client.close()
        print("🔌 Redis connection closed.")
    except Exception:
        pass

@app.get("/cache")
async def cache_example():
    # = 값 넣고/읽고/TTL 주기
    redis_client.set("hello", "world", ex=60)
    return {
        "hello": redis_client.get("hello"),
        "ttl":   redis_client.ttl("hello"),
    }

# 서버 시작할때 스케쥴러 등록
@app.on_event("startup")
def startup_event():
    start_scheduler()