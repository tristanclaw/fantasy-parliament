from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, desc
from models import MP, LeaderboardEntry, init_db, db
from scraper import run_sync
import os
import traceback
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

load_dotenv()

app = FastAPI(title="Canadian Politics Fantasy League API")

# DEBUG: Global exception handler to expose tracebacks
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("SYNC_API_KEY")

async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="SYNC_API_KEY not configured on server")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.on_event("startup")
async def startup():
    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        raise ValueError("DB_PASSWORD environment variable is required")
        
    init_db(
        provider='postgres',
        user=os.getenv('DB_USER', 'postgres'),
        password=db_password,
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'fantasy_politics'),
        sslmode='require'
    )
    
    # Auto-migration for schema updates (ensure total_score exists)
    try:
        with db_session:
            db.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
            db.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
    except Exception as e:
        print(f"Migration warning: {e}")

def mp_to_dict(mp):
    return {
        "id": mp.id,
        "name": mp.name,
        "party": mp.party,
        "constituency": mp.riding,
        "score": mp.total_score,
        "slug": mp.slug,
        "image_url": mp.image_url
    }

@app.get("/mps")
@db_session
def get_mps():
    mps = MP.select().order_by(desc(MP.total_score))
    return [mp_to_dict(m) for m in mps]

@app.get("/mps/search")
@db_session
def search_mps(q: Optional[str] = Query(None)):
    query = MP.select()
    if q:
        query = query.filter(lambda m: q.lower() in m.name.lower() or (m.party and q.lower() in m.party.lower()) or (m.riding and q.lower() in m.riding.lower()))
    
    results = query.order_by(desc(MP.total_score))
    return [mp_to_dict(m) for m in results]

@app.get("/scoreboard")
@db_session
def get_scoreboard():
    mps = MP.select().order_by(desc(MP.total_score))[:10]
    return [mp_to_dict(m) for m in mps]

class LeaderboardSubmission(BaseModel):
    username: str
    score: int

@app.get("/leaderboard")
@db_session
def get_leaderboard():
    entries = LeaderboardEntry.select().order_by(desc(LeaderboardEntry.score))[:50]
    return [{"username": e.username, "score": e.score, "updated_at": e.updated_at.isoformat()} for e in entries]

@app.post("/leaderboard")
@db_session
def update_leaderboard(submission: LeaderboardSubmission):
    entry = LeaderboardEntry.get(username=submission.username)
    if entry:
        entry.score = submission.score
        entry.updated_at = datetime.now()
    else:
        LeaderboardEntry(username=submission.username, score=submission.score, updated_at=datetime.now())
    return {"status": "success"}

@app.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    background_tasks.add_task(run_sync)
    return {"message": "Sync started in background"}

@app.get("/health")
def health():
    return {"status": "ok"}
