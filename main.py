from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends, Query, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pony.orm import db_session, select, desc
from models import MP, LeaderboardEntry, Bill, Speech, VoteAttendance, init_db, run_migrations, db
from scraper import run_sync
import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

load_dotenv()

app = FastAPI(title="Canadian Politics Fantasy League API")

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

admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/migrate")
async def manual_migrate(api_key: str = Depends(verify_api_key)):
    print("ADMIN: Triggering manual migration...")
    db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL_INTERNAL') or os.getenv('DATABASE_URL')
    
    success = False
    msg = ""

    if db_url:
        dsn = db_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)
        success, msg = run_migrations(dsn)
    else:
        # Construct kwargs from environment if using separate vars
        # This matches what we do in startup
        db_password = os.getenv('DB_PASSWORD')
        if not db_password:
             raise HTTPException(status_code=500, detail="DB_PASSWORD missing in environment")
             
        kwargs = {
            'user': os.getenv('DB_USER', 'postgres'),
            'password': db_password,
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'fantasy_politics'),
        }
        success, msg = run_migrations(None, **kwargs)

    if success:
        return {"status": "success", "message": msg}
    else:
        raise HTTPException(status_code=500, detail=msg)

@admin_router.post("/sync")
async def manual_sync(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    print("ADMIN: Triggering manual sync...")
    background_tasks.add_task(run_sync_with_logging)
    return {"message": "Sync started in background via Admin"}

@app.get("/admin/logs")
def get_admin_logs(api_key: str = Header(None)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    if os.path.exists("sync.log"):
        with open("sync.log", "r") as f:
            return {"logs": f.read()}
    return {"logs": "No log file found"}

async def run_sync_with_logging():
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    
    try:
        print(f"BACKGROUND: Starting sync at {datetime.now()}...")
        await run_sync()
        print(f"BACKGROUND: Sync finished successfully at {datetime.now()}.")
    except Exception as e:
        import traceback
        print(f"BACKGROUND ERROR: Sync failed: {e}")
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout
        with open("sync.log", "w") as f:
            f.write(mystdout.getvalue())

app.include_router(admin_router)

@app.on_event("startup")
async def startup():
    print("STARTUP: Initializing...")
    
    db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL_INTERNAL') or os.getenv('DATABASE_URL')
    if db_url:
        print(f"STARTUP: Using {'INTERNAL_DATABASE_URL' if os.getenv('INTERNAL_DATABASE_URL') else 'DATABASE_URL_INTERNAL' if os.getenv('DATABASE_URL_INTERNAL') else 'DATABASE_URL'}...")
        init_db(db_url)
    else:
        db_password = os.getenv('DB_PASSWORD')
        if not db_password:
            print("STARTUP ERROR: DB_PASSWORD missing")
            raise ValueError("DB_PASSWORD environment variable is required")
            
        print(f"STARTUP: Connecting to {os.getenv('DB_HOST')}...")
        init_db(
            'postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=db_password,
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'fantasy_politics'),
            sslmode='require'
        )
    print("STARTUP: Database initialized successfully")
    
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

@app.get("/diag/db")
@db_session
def diag_db():
    try:
        mp_count = MP.select().count()
        lb_count = LeaderboardEntry.select().count()
        bill_count = Bill.select().count()
        speech_count = Speech.select().count()
        vote_count = VoteAttendance.select().count()
        return {
            "status": "connected",
            "counts": {
                "mp": mp_count,
                "leaderboard": lb_count,
                "bill": bill_count,
                "speech": speech_count,
                "vote": vote_count
            },
            "database": str(db.provider_name)
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/mps")
@db_session
def get_mps():
    print("DEBUG: Entering /mps endpoint")
    try:
        mps = MP.select().order_by(desc(MP.total_score))
        return [mp_to_dict(m) for m in mps]
    except Exception as e:
        import traceback
        print(f"ERROR in /mps: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mps/search")
@db_session
def search_mps(q: Optional[str] = Query(None)):
    query = MP.select()
    if q:
        search_term = f"%{q.lower()}%"
        query = query.filter(lambda m: search_term in m.name.lower() or 
                             (m.party and search_term in m.party.lower()) or 
                             (m.riding and search_term in m.riding.lower()))
    
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
