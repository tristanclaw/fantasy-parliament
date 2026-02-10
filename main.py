from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select
from models import MP, init_db, db
from scraper import run_sync
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(title="Canadian Politics Fantasy League API")

origins = [
    "https://fantasy-parliament.onrender.com",
    "http://localhost:5173",
]

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
        database=os.getenv('DB_NAME', 'fantasy_politics')
    )
    
    # Auto-migration for schema updates (ensure total_score exists)
    try:
        with db_session:
            db.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
    except Exception as e:
        print(f"Migration warning: {e}")

@app.get("/mps")
@db_session
def get_mps():
    mps = select(m for m in MP).order_by(lambda m: -m.total_score)
    return [{"name": m.name, "party": m.party, "score": m.total_score, "slug": m.slug} for m in mps]

@app.get("/mps/search")
@db_session
def search_mps(name: Optional[str] = Query(None), party: Optional[str] = Query(None)):
    query = select(m for m in MP)
    if name:
        query = query.filter(lambda m: name.lower() in m.name.lower())
    if party:
        query = query.filter(lambda m: party.lower() in m.party.lower())
    
    results = query.order_by(lambda m: -m.total_score)
    return [{"name": m.name, "party": m.party, "score": m.total_score, "slug": m.slug} for m in results]

@app.get("/scoreboard")
@db_session
def get_scoreboard():
    mps = select(m for m in MP).order_by(lambda m: -m.total_score)[:10]
    return [{"name": m.name, "party": m.party, "score": m.total_score, "slug": m.slug} for m in mps]

@app.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    background_tasks.add_task(run_sync)
    return {"message": "Sync started in background"}

@app.get("/health")
def health():
    return {"status": "ok"}
